"""E2E test for the ingestion flow: submit message and opportunity creation.

Tests the full stack: API → use case → domain → persistence.
The client fixture (from conftest.py) uses rollback-only sessions — no data persists.
"""

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> dict:
    """Helper: register a user and login, returning cookies."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "ingest-e2e@example.com", "password": "E2eTest1ng"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ingest-e2e@example.com", "password": "E2eTest1ng"},
    )
    return dict(resp.cookies)


@pytest.mark.e2e
class TestIngestionFlowE2E:
    """Full ingestion flow: login → submit message → check interaction → check opportunity."""

    @pytest.mark.asyncio
    async def test_submit_message_returns_202(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/ingestion/messages",
            json={
                "raw_content": "Hi, I have a Senior Backend Engineer role at Acme Corp. Remote, $150-180K, Python/FastAPI stack.",
                "source": "LINKEDIN",
            },
            cookies=cookies,
        )
        assert resp.status_code == 202
        data = resp.json()
        assert "interaction_id" in data
        assert "opportunity_id" in data
        assert data["status"] == "ANALYZING"

    @pytest.mark.asyncio
    async def test_submit_message_unauthenticated_returns_401(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/ingestion/messages",
            json={"raw_content": "Some message", "source": "LINKEDIN"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_empty_message_returns_400(
        self, client: AsyncClient
    ) -> None:
        cookies = await _register_and_login(client)
        resp = await client.post(
            "/api/v1/ingestion/messages",
            json={"raw_content": "   ", "source": "LINKEDIN"},
            cookies=cookies,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_get_interaction_by_id(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client)
        submit_resp = await client.post(
            "/api/v1/ingestion/messages",
            json={
                "raw_content": "Job offer for Staff Engineer at BigCorp.",
                "source": "EMAIL",
            },
            cookies=cookies,
        )
        interaction_id = submit_resp.json()["interaction_id"]

        get_resp = await client.get(
            f"/api/v1/ingestion/messages/{interaction_id}",
            cookies=cookies,
        )
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["id"] == interaction_id
        assert data["source"] == "EMAIL"
        assert data["processing_status"] == "PENDING"

    @pytest.mark.asyncio
    async def test_submit_duplicate_returns_400(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client)
        payload = {
            "raw_content": "Unique offer message for duplicate test.",
            "source": "LINKEDIN",
        }
        # First submission
        resp1 = await client.post(
            "/api/v1/ingestion/messages", json=payload, cookies=cookies
        )
        assert resp1.status_code == 202

        # Duplicate submission
        resp2 = await client.post(
            "/api/v1/ingestion/messages", json=payload, cookies=cookies
        )
        assert resp2.status_code == 400
        assert "duplicate" in resp2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_opportunities_appear_on_list(self, client: AsyncClient) -> None:
        cookies = await _register_and_login(client)
        await client.post(
            "/api/v1/ingestion/messages",
            json={
                "raw_content": "Role: Principal Engineer at TechCo. Fully remote.",
                "source": "FREELANCE_PLATFORM",
            },
            cookies=cookies,
        )

        resp = await client.get("/api/v1/opportunities", cookies=cookies)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(opp["status"] == "ANALYZING" for opp in data)
