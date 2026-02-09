"""Integration test fixtures with real PostgreSQL via testcontainers."""

import pytest
from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.orm import sessionmaker, Session

from talent_inbound.shared.infrastructure.database import Base


@pytest.fixture(scope="session")
def db_engine():
    """Create a test PostgreSQL instance via testcontainers."""
    try:
        from testcontainers.postgres import PostgresContainer

        with PostgresContainer("postgres:16-alpine") as pg:
            engine = create_sync_engine(pg.get_connection_url())
            Base.metadata.create_all(engine)
            yield engine
            Base.metadata.drop_all(engine)
    except ImportError:
        pytest.skip("testcontainers not installed")


@pytest.fixture
def db_session(db_engine) -> Session:
    """Per-test session with rollback for isolation."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
