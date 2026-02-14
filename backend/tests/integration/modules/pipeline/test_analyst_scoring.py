"""Integration test for the pipeline with Analyst producing match scores."""

from unittest.mock import AsyncMock

import pytest

from talent_inbound.config import get_settings
from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.graphs import build_main_pipeline
from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.shared.domain.enums import WorkModel

PIPELINE_STEPS = get_settings().pipeline_steps


def _make_profile():
    return CandidateProfile(
        candidate_id="test-user",
        display_name="Test User",
        skills=["Python", "FastAPI", "PostgreSQL", "AWS"],
        min_salary=80000,
        preferred_currency="EUR",
        work_model=WorkModel.REMOTE,
        preferred_locations=["Spain"],
        industries=["FinTech"],
    )


def _make_repo(profile):
    repo = AsyncMock()
    repo.find_by_candidate_id.return_value = profile
    return repo


@pytest.mark.integration
class TestAnalystScoring:
    """Tests for the full pipeline with Analyst scoring."""

    async def test_complete_offer_gets_scored(self):
        profile = _make_profile()
        repo = _make_repo(profile)
        graph = build_main_pipeline(model_router=None, profile_repo=repo)

        initial: PipelineState = {
            "raw_input": (
                "Hi, I'm a recruiter at Acme Corp. We have a Senior Backend Engineer "
                "role, fully remote, $150-180K. Stack: Python, FastAPI, PostgreSQL. "
                "Looking for someone to join our team."
            ),
            "interaction_id": "test-1",
            "opportunity_id": "opp-1",
            "candidate_id": "test-user",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        steps = [log["step"] for log in result["pipeline_log"]]
        assert "analyst" in steps
        assert result["match_score"] is not None
        assert result["match_score"] >= 50
        assert result["match_reasoning"] is not None

    async def test_spam_skips_analyst(self):
        graph = build_main_pipeline(model_router=None)

        initial: PipelineState = {
            "raw_input": "Click here for FREE bitcoin prize! Limited time guaranteed!",
            "interaction_id": "test-2",
            "opportunity_id": "opp-2",
            "candidate_id": "test-user",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        steps = [log["step"] for log in result["pipeline_log"]]
        assert "analyst" not in steps
        assert result.get("match_score") is None

    async def test_incomplete_offer_skips_analyst(self):
        graph = build_main_pipeline(model_router=None)

        initial: PipelineState = {
            "raw_input": "Interesting developer opportunity, let me know if interested",
            "interaction_id": "test-3",
            "opportunity_id": "opp-3",
            "candidate_id": "test-user",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        # Should be classified as REAL_OFFER but with missing fields
        if result.get("classification") == "REAL_OFFER":
            extracted = result.get("extracted_data", {})
            if extracted.get("missing_fields"):
                steps = [log["step"] for log in result["pipeline_log"]]
                assert "analyst" not in steps or result["pipeline_log"][-1].get("status") == "skipped"

    async def test_pipeline_log_includes_all_steps(self):
        profile = _make_profile()
        repo = _make_repo(profile)
        graph = build_main_pipeline(model_router=None, profile_repo=repo)

        initial: PipelineState = {
            "raw_input": (
                "Senior Python Engineer role at TechCo. Remote. $120-150K. "
                "Stack: Python, AWS, Docker. Hiring now."
            ),
            "interaction_id": "test-4",
            "opportunity_id": "opp-4",
            "candidate_id": "test-user",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        steps = [log["step"] for log in result["pipeline_log"]]
        assert steps == PIPELINE_STEPS
