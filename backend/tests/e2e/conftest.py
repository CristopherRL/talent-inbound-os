"""E2E test fixtures with full FastAPI app and httpx AsyncClient."""

import pytest
from httpx import ASGITransport, AsyncClient

from talent_inbound.main import create_app


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
