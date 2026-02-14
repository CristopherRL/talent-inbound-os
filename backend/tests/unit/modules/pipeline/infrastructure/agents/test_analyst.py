"""Unit tests for the Analyst agent (scoring logic, skip INCOMPLETE_INFO)."""

from unittest.mock import AsyncMock

import pytest

from talent_inbound.modules.pipeline.infrastructure.agents.analyst import (
    create_analyst_node,
)
from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.shared.domain.enums import WorkModel


def _make_profile(**overrides) -> CandidateProfile:
    defaults = {
        "candidate_id": "user-1",
        "display_name": "Test User",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "min_salary": 80000,
        "preferred_currency": "EUR",
        "work_model": WorkModel.REMOTE,
    }
    defaults.update(overrides)
    return CandidateProfile(**defaults)


def _make_repo(profile: CandidateProfile | None):
    repo = AsyncMock()
    repo.find_by_candidate_id.return_value = profile
    return repo


class TestAnalystAgent:
    """Tests for the mock/heuristic analyst scoring."""

    async def test_scores_good_match(self):
        profile = _make_profile()
        repo = _make_repo(profile)
        node = create_analyst_node(model=None, profile_repo=repo)

        state = {
            "extracted_data": {
                "company_name": "Acme",
                "role_title": "Senior Backend Engineer",
                "tech_stack": ["Python", "FastAPI", "AWS"],
                "salary_range": "$150-180K",
                "work_model": "REMOTE",
                "missing_fields": [],
            },
            "candidate_id": "user-1",
            "raw_input": "",
            "pipeline_log": [],
        }

        result = await node(state)
        assert result["match_score"] is not None
        assert result["match_score"] >= 60
        assert result["match_reasoning"] is not None

    async def test_scores_poor_match(self):
        profile = _make_profile(skills=["Java", "Spring"])
        repo = _make_repo(profile)
        node = create_analyst_node(model=None, profile_repo=repo)

        state = {
            "extracted_data": {
                "company_name": "Corp",
                "role_title": "Frontend Developer",
                "tech_stack": ["React", "TypeScript", "Vue"],
                "salary_range": "$50-70K",
                "work_model": "ONSITE",
                "missing_fields": [],
            },
            "candidate_id": "user-1",
            "raw_input": "",
            "pipeline_log": [],
        }

        result = await node(state)
        assert result["match_score"] is not None
        assert result["match_score"] < 60

    async def test_skips_when_missing_fields(self):
        node = create_analyst_node(model=None, profile_repo=None)

        state = {
            "extracted_data": {
                "company_name": "Acme",
                "missing_fields": ["salary_range", "tech_stack"],
            },
            "raw_input": "",
            "pipeline_log": [],
        }

        result = await node(state)
        assert result["match_score"] is None
        assert result["match_reasoning"] is None
        assert result["pipeline_log"][0]["status"] == "skipped"

    async def test_works_without_profile(self):
        repo = _make_repo(None)
        node = create_analyst_node(model=None, profile_repo=repo)

        state = {
            "extracted_data": {
                "tech_stack": ["Python"],
                "missing_fields": [],
            },
            "candidate_id": "user-1",
            "raw_input": "",
            "pipeline_log": [],
        }

        result = await node(state)
        assert result["match_score"] is not None
        assert result["pipeline_log"][0]["status"] == "completed"

    async def test_work_model_match_increases_score(self):
        profile = _make_profile(skills=[], min_salary=None)
        repo = _make_repo(profile)
        node = create_analyst_node(model=None, profile_repo=repo)

        state_match = {
            "extracted_data": {"work_model": "REMOTE", "missing_fields": []},
            "candidate_id": "user-1",
            "raw_input": "",
            "pipeline_log": [],
        }
        state_mismatch = {
            "extracted_data": {"work_model": "ONSITE", "missing_fields": []},
            "candidate_id": "user-1",
            "raw_input": "",
            "pipeline_log": [],
        }

        result_match = await node(state_match)
        result_mismatch = await node(state_mismatch)
        assert result_match["match_score"] > result_mismatch["match_score"]

    async def test_logs_step_metadata(self):
        node = create_analyst_node(model=None, profile_repo=None)

        state = {
            "extracted_data": {"missing_fields": []},
            "raw_input": "",
            "pipeline_log": [],
        }

        result = await node(state)
        assert len(result["pipeline_log"]) == 1
        log = result["pipeline_log"][0]
        assert log["step"] == "analyst"
        assert log["latency_ms"] >= 0

    async def test_custom_weights(self):
        profile = _make_profile(skills=["Python"], min_salary=None)
        repo = _make_repo(profile)
        weights = {
            "base": 10,
            "skills": 80,
            "wm_match": 5,
            "wm_mismatch": -5,
            "sal_meets": 5,
            "sal_below": -5,
        }
        node = create_analyst_node(model=None, profile_repo=repo, scoring_weights=weights)

        state = {
            "extracted_data": {
                "tech_stack": ["Python"],
                "missing_fields": [],
            },
            "candidate_id": "user-1",
            "raw_input": "",
            "pipeline_log": [],
        }

        result = await node(state)
        # base(10) + skills(80 * 1.0) = 90
        assert result["match_score"] == 90
