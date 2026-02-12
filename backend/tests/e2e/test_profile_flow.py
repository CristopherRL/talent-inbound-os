"""E2E test for profile CRUD and CV upload.

Tests the full flow: register → login → create profile → update → upload CV → download CV.
The client fixture (from conftest.py) uses rollback-only sessions — no data persists.
"""

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient, email: str) -> dict:
    """Helper: register a user, login, return cookies."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass1"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "TestPass1"},
    )
    return dict(login.cookies)


@pytest.mark.e2e
class TestProfileFlowE2E:
    """Full profile flow: create → get → update → upload CV → download."""

    @pytest.mark.asyncio
    async def test_get_profile_404_when_none(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "profile-404@test.com")
        resp = await client.get("/api/v1/profile/me", cookies=cookies)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_profile(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "profile-create@test.com")
        resp = await client.put(
            "/api/v1/profile/me",
            json={
                "display_name": "Jane Doe",
                "professional_title": "Senior Backend Engineer",
                "skills": ["Python", "FastAPI"],
                "min_salary": 80000,
                "preferred_currency": "EUR",
                "work_model": "REMOTE",
                "preferred_locations": ["Spain"],
                "industries": ["FinTech"],
            },
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "Jane Doe"
        assert data["skills"] == ["Python", "FastAPI"]
        assert data["work_model"] == "REMOTE"

    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "profile-update@test.com")
        # Create
        await client.put(
            "/api/v1/profile/me",
            json={"display_name": "Before"},
            cookies=cookies,
        )
        # Update
        resp = await client.put(
            "/api/v1/profile/me",
            json={
                "display_name": "After",
                "skills": ["Rust"],
                "follow_up_days": 3,
            },
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["display_name"] == "After"
        assert data["skills"] == ["Rust"]
        assert data["follow_up_days"] == 3

    @pytest.mark.asyncio
    async def test_get_profile_returns_data(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "profile-get@test.com")
        await client.put(
            "/api/v1/profile/me",
            json={"display_name": "Get Test"},
            cookies=cookies,
        )
        resp = await client.get("/api/v1/profile/me", cookies=cookies)
        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Get Test"

    @pytest.mark.asyncio
    async def test_upload_cv_requires_profile(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "cv-noprofile@test.com")
        resp = await client.post(
            "/api/v1/profile/me/cv",
            files={"file": ("resume.md", b"# My CV", "text/markdown")},
            cookies=cookies,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_cv_markdown(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "cv-upload@test.com")
        # Create profile first
        await client.put(
            "/api/v1/profile/me",
            json={"display_name": "CV Test"},
            cookies=cookies,
        )
        # Upload CV
        resp = await client.post(
            "/api/v1/profile/me/cv",
            files={"file": ("cv.md", b"# Senior Engineer\n\nPython, FastAPI", "text/markdown")},
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["cv_filename"] == "cv.md"

    @pytest.mark.asyncio
    async def test_upload_cv_invalid_type_returns_415(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "cv-invalid@test.com")
        await client.put(
            "/api/v1/profile/me",
            json={"display_name": "Bad CV"},
            cookies=cookies,
        )
        resp = await client.post(
            "/api/v1/profile/me/cv",
            files={"file": ("resume.exe", b"bad", "application/octet-stream")},
            cookies=cookies,
        )
        assert resp.status_code == 415

    @pytest.mark.asyncio
    async def test_download_cv_no_upload_returns_404(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client, "cv-nofile@test.com")
        await client.put(
            "/api/v1/profile/me",
            json={"display_name": "No CV"},
            cookies=cookies,
        )
        resp = await client.get("/api/v1/profile/me/cv", cookies=cookies)
        assert resp.status_code == 404
