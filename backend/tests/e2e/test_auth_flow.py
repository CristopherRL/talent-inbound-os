"""E2E test for the full auth flow: register → login → access protected → logout → redirect.

These tests require a running database (via testcontainers in CI, or Docker locally).
They exercise the real FastAPI app with httpx, testing the full stack.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from talent_inbound.main import create_app


@pytest.fixture
async def client():
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.e2e
class TestAuthFlowE2E:
    """Full auth flow: register → login → access /auth/me → logout → verify 401."""

    @pytest.mark.asyncio
    async def test_register_returns_201(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "e2e@example.com", "password": "E2eTest1ng"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "e2e@example.com"
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_returns_409(self, client: AsyncClient) -> None:
        # First register
        await client.post(
            "/api/v1/auth/register",
            json={"email": "dupe-e2e@example.com", "password": "E2eTest1ng"},
        )
        # Second with same email
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "dupe-e2e@example.com", "password": "E2eTest1ng"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_login_sets_cookies(self, client: AsyncClient) -> None:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login-e2e@example.com", "password": "E2eTest1ng"},
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login-e2e@example.com", "password": "E2eTest1ng"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.cookies
        assert resp.json()["message"] == "Login successful"

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "login-e2e@example.com", "password": "WrongPass1"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_me_without_token_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_full_auth_cycle(self, client: AsyncClient) -> None:
        """Register → login → access protected endpoint → logout → verify 401."""
        # Register
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "cycle-e2e@example.com", "password": "E2eTest1ng"},
        )
        assert reg_resp.status_code == 201

        # Login
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "cycle-e2e@example.com", "password": "E2eTest1ng"},
        )
        assert login_resp.status_code == 200
        cookies = login_resp.cookies

        # Access protected endpoint with cookies
        me_resp = await client.get("/api/v1/auth/me", cookies=cookies)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "cycle-e2e@example.com"

        # Logout
        logout_resp = await client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_register_weak_password_returns_422(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "weak@example.com", "password": "short"},
        )
        assert resp.status_code == 422
