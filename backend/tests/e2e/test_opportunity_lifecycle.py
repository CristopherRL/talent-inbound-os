"""E2E test for opportunity status change flow and archive."""

import pytest
from httpx import AsyncClient


async def _register_and_login(client: AsyncClient) -> dict:
    """Helper: register a user and login, returning cookies."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "lifecycle-e2e@example.com", "password": "E2eTest1ng"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "lifecycle-e2e@example.com", "password": "E2eTest1ng"},
    )
    return dict(resp.cookies)


async def _submit_offer(client: AsyncClient, cookies: dict, text: str, source: str = "LINKEDIN") -> str:
    """Submit an offer and return the opportunity_id."""
    resp = await client.post(
        "/api/v1/ingestion/messages",
        json={"raw_content": text, "source": source},
        cookies=cookies,
    )
    assert resp.status_code == 202
    return resp.json()["opportunity_id"]


@pytest.mark.e2e
class TestOpportunityLifecycle:
    """Tests status changes, unusual detection, archive/unarchive."""

    async def test_change_status_normal(self, client: AsyncClient):
        cookies = await _register_and_login(client)
        opp_id = await _submit_offer(
            client, cookies,
            "Senior Python role at LifeCo. Remote. $120-150K. Stack: Python, FastAPI.",
        )

        resp = await client.patch(
            f"/api/v1/opportunities/{opp_id}/status",
            json={"new_status": "REVIEWING", "note": "Reviewed the details"},
            cookies=cookies,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "REVIEWING"
        assert data["is_unusual"] is False
        assert data["transition"]["note"] == "Reviewed the details"

    async def test_change_status_unusual_skip(self, client: AsyncClient):
        cookies = await _register_and_login(client)
        opp_id = await _submit_offer(
            client, cookies,
            "DevOps Engineer at CloudCo. Hybrid. $100-130K. Stack: AWS, Terraform.",
            source="EMAIL",
        )

        # Skip from ACTION_REQUIRED to OFFER (unusual)
        resp = await client.patch(
            f"/api/v1/opportunities/{opp_id}/status",
            json={"new_status": "OFFER"},
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["is_unusual"] is True

    async def test_archive_terminal_status(self, client: AsyncClient):
        cookies = await _register_and_login(client)
        opp_id = await _submit_offer(
            client, cookies,
            "Frontend role at UIStore. Onsite. $80-100K. Stack: React, TypeScript.",
        )

        # Move to REJECTED (terminal)
        await client.patch(
            f"/api/v1/opportunities/{opp_id}/status",
            json={"new_status": "REJECTED"},
            cookies=cookies,
        )

        # Archive
        resp = await client.post(
            f"/api/v1/opportunities/{opp_id}/archive",
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["is_archived"] is True

        # Not visible in default list
        resp = await client.get("/api/v1/opportunities", cookies=cookies)
        ids = [o["id"] for o in resp.json()]
        assert opp_id not in ids

        # Visible with archived=all
        resp = await client.get(
            "/api/v1/opportunities?archived=all", cookies=cookies
        )
        ids = [o["id"] for o in resp.json()]
        assert opp_id in ids

        # Visible with archived=only (shows only archived)
        resp = await client.get(
            "/api/v1/opportunities?archived=only", cookies=cookies
        )
        only_ids = [o["id"] for o in resp.json()]
        assert opp_id in only_ids
        for o in resp.json():
            assert o["is_archived"] is True

    async def test_archive_non_terminal_fails(self, client: AsyncClient):
        cookies = await _register_and_login(client)
        opp_id = await _submit_offer(
            client, cookies,
            "Backend role at DataCo. Remote. $110-140K. Stack: Python, Go.",
            source="EMAIL",
        )

        # Try to archive non-terminal (ACTION_REQUIRED)
        resp = await client.post(
            f"/api/v1/opportunities/{opp_id}/archive",
            cookies=cookies,
        )
        assert resp.status_code == 400

    async def test_unarchive(self, client: AsyncClient):
        cookies = await _register_and_login(client)
        opp_id = await _submit_offer(
            client, cookies,
            "ML Engineer at AICo. Remote. $150-200K. Stack: Python, PyTorch.",
        )

        # REJECTED → archive → unarchive
        await client.patch(
            f"/api/v1/opportunities/{opp_id}/status",
            json={"new_status": "REJECTED"},
            cookies=cookies,
        )
        await client.post(f"/api/v1/opportunities/{opp_id}/archive", cookies=cookies)

        resp = await client.post(
            f"/api/v1/opportunities/{opp_id}/unarchive",
            cookies=cookies,
        )
        assert resp.status_code == 200
        assert resp.json()["is_archived"] is False

    async def test_detail_includes_timeline(self, client: AsyncClient):
        cookies = await _register_and_login(client)
        opp_id = await _submit_offer(
            client, cookies,
            "Platform Engineer at ScaleCo. Remote. $130-160K. Stack: Kubernetes, Go.",
        )

        # Change status to generate transitions
        await client.patch(
            f"/api/v1/opportunities/{opp_id}/status",
            json={"new_status": "REVIEWING"},
            cookies=cookies,
        )

        resp = await client.get(
            f"/api/v1/opportunities/{opp_id}", cookies=cookies
        )
        assert resp.status_code == 200
        detail = resp.json()

        assert len(detail["interactions"]) >= 1
        assert len(detail["status_history"]) >= 1
        assert detail["status"] == "REVIEWING"

    async def test_filter_by_status(self, client: AsyncClient):
        cookies = await _register_and_login(client)

        # Submit and move one to REVIEWING
        opp_id = await _submit_offer(
            client, cookies,
            "SRE at InfraCo. Remote. $140-170K. Stack: Python, Terraform.",
            source="EMAIL",
        )
        await client.patch(
            f"/api/v1/opportunities/{opp_id}/status",
            json={"new_status": "REVIEWING"},
            cookies=cookies,
        )

        resp = await client.get(
            "/api/v1/opportunities?status=REVIEWING", cookies=cookies
        )
        assert resp.status_code == 200
        for opp in resp.json():
            assert opp["status"] == "REVIEWING"
