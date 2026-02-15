"""Unit tests for the Communicator agent (draft generation)."""

import pytest

from talent_inbound.modules.pipeline.infrastructure.agents.communicator import (
    create_communicator_node,
    generate_draft_standalone,
)


def _make_state(extracted_data=None, candidate_id="cand-1"):
    """Build a minimal PipelineState dict for testing."""
    return {
        "raw_input": "Some recruiter message",
        "interaction_id": "int-1",
        "opportunity_id": "opp-1",
        "candidate_id": candidate_id,
        "extracted_data": extracted_data or {
            "company_name": "Acme Corp",
            "role_title": "Senior Backend Engineer",
            "salary_range": "$120-150K",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
            "work_model": "REMOTE",
            "recruiter_name": "Sarah Smith",
            "recruiter_company": "TechRecruit Inc",
            "missing_fields": [],
        },
        "pipeline_log": [],
    }


class TestCommunicatorNodeMock:
    """Tests for the mock/template-based communicator (no LLM)."""

    async def test_generates_express_interest_by_default(self):
        node = create_communicator_node()
        state = _make_state()
        result = await node(state)

        assert result["draft_response"]  # non-empty string
        assert "Acme Corp" in result["draft_response"]
        assert result["current_step"] == "communicator"
        assert len(result["pipeline_log"]) == 1
        assert result["pipeline_log"][0]["step"] == "communicator"
        assert result["pipeline_log"][0]["status"] == "completed"

    async def test_generates_request_info(self):
        node = create_communicator_node(response_type="REQUEST_INFO")
        state = _make_state()
        result = await node(state)

        draft = result["draft_response"]
        assert draft
        # Request info drafts should ask for more details
        assert "additional details" in draft.lower() or \
               "information" in draft.lower()

    async def test_generates_decline(self):
        node = create_communicator_node(response_type="DECLINE")
        state = _make_state()
        result = await node(state)

        draft = result["draft_response"]
        assert draft
        assert "pass" in draft.lower() or "decline" in draft.lower()

    async def test_references_company_name(self):
        node = create_communicator_node()
        state = _make_state()
        result = await node(state)

        assert "Acme Corp" in result["draft_response"]

    async def test_references_recruiter_name(self):
        node = create_communicator_node()
        state = _make_state()
        result = await node(state)

        assert "Sarah" in result["draft_response"]

    async def test_handles_minimal_extracted_data(self):
        node = create_communicator_node()
        state = _make_state(extracted_data={
            "company_name": None,
            "role_title": None,
            "tech_stack": [],
            "recruiter_name": None,
            "missing_fields": [],
        })
        result = await node(state)

        # Should still produce a draft without crashing
        assert result["draft_response"]

    async def test_pipeline_log_has_communicator_detail(self):
        node = create_communicator_node()
        state = _make_state()
        result = await node(state)

        log = result["pipeline_log"][0]
        assert "EXPRESS_INTEREST" in log["detail"]
        assert "template" in log["detail"]


class TestGenerateDraftStandalone:
    """Tests for the standalone draft generation function."""

    async def test_generates_express_interest(self):
        extracted = {
            "company_name": "BigCo",
            "role_title": "Staff Engineer",
            "tech_stack": ["Go", "Kubernetes"],
            "recruiter_name": "John",
            "missing_fields": [],
        }
        draft = await generate_draft_standalone("EXPRESS_INTEREST", extracted)
        assert draft
        assert "BigCo" in draft

    async def test_generates_request_info(self):
        extracted = {
            "company_name": "StartupX",
            "role_title": "Backend Dev",
            "tech_stack": [],
            "missing_fields": ["salary_range", "work_model"],
        }
        draft = await generate_draft_standalone("REQUEST_INFO", extracted)
        assert draft
        assert "StartupX" in draft

    async def test_generates_decline(self):
        extracted = {
            "company_name": "OldCo",
            "role_title": "Junior Dev",
            "tech_stack": ["COBOL"],
            "missing_fields": [],
        }
        draft = await generate_draft_standalone("DECLINE", extracted)
        assert draft
        assert "OldCo" in draft
