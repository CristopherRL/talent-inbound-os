"""E2E test fixtures with full FastAPI app and httpx AsyncClient.

Uses a separate test database (talent_inbound_test) so that E2E tests
never touch the development database. The test DB is created fresh
at the start of the test session and dropped at the end.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from talent_inbound.config import get_settings

# Derive a test DB URL from the main URL by appending "_test"
_settings = get_settings()
_TEST_DB_NAME = "talent_inbound_test"
_BASE_DB_URL = _settings.database_url  # e.g. postgresql+asyncpg://...@host/talent_inbound
_TEST_DB_URL = _BASE_DB_URL.rsplit("/", 1)[0] + f"/{_TEST_DB_NAME}"
# Admin URL (connect to default 'postgres' DB to CREATE/DROP test DB)
_ADMIN_DB_URL = _BASE_DB_URL.rsplit("/", 1)[0] + "/postgres"


async def _create_test_db():
    """Create the test database if it doesn't exist."""
    engine = create_async_engine(_ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{_TEST_DB_NAME}'")
        )
        if not result.scalar():
            await conn.execute(text(f"CREATE DATABASE {_TEST_DB_NAME}"))
    await engine.dispose()


async def _run_migrations_on_test_db():
    """Create all tables in the test database via SQLAlchemy metadata."""
    from talent_inbound.shared.infrastructure.database import Base, create_engine as create_app_engine
    # Import all ORM models so Base.metadata knows about them
    import talent_inbound.modules.auth.infrastructure.orm_models  # noqa: F401
    import talent_inbound.modules.profile.infrastructure.orm_models  # noqa: F401
    import talent_inbound.modules.opportunities.infrastructure.orm_models  # noqa: F401
    import talent_inbound.modules.ingestion.infrastructure.orm_models  # noqa: F401

    engine = create_app_engine(_TEST_DB_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def _drop_test_db():
    """Drop the test database."""
    engine = create_async_engine(_ADMIN_DB_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        # Terminate other connections to the test DB
        await conn.execute(text(
            f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
            f"WHERE datname = '{_TEST_DB_NAME}' AND pid <> pg_backend_pid()"
        ))
        await conn.execute(text(f"DROP DATABASE IF EXISTS {_TEST_DB_NAME}"))
    await engine.dispose()


def _create_test_app():
    """Build the FastAPI app pointing to the test database."""
    import os
    # Override DATABASE_URL so Settings picks up the test DB
    os.environ["DATABASE_URL"] = _TEST_DB_URL

    # Clear cached settings so it re-reads with test DB URL
    from talent_inbound.config import get_settings as _gs
    _gs.cache_clear()

    from talent_inbound.main import create_app
    app = create_app()

    # Restore original URL after app creation
    os.environ["DATABASE_URL"] = _BASE_DB_URL
    _gs.cache_clear()

    return app


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def _setup_test_db():
    """Create test DB before all tests, drop it after."""
    await _create_test_db()
    await _run_migrations_on_test_db()
    yield
    await _drop_test_db()


@pytest.fixture
async def client():
    app = _create_test_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup: truncate all tables in the TEST database after each test
    from talent_inbound.shared.infrastructure.database import create_engine as create_app_engine, create_session_factory
    engine = create_app_engine(_TEST_DB_URL)
    factory = create_session_factory(engine)
    async with factory() as session:
        await session.execute(
            text(
                "TRUNCATE draft_responses, interactions, opportunities, "
                "stage_transitions, candidate_profiles, users CASCADE"
            )
        )
        await session.commit()
    await engine.dispose()
