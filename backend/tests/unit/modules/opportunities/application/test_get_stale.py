"""Unit tests for GetStaleOpportunities use case."""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

from talent_inbound.modules.opportunities.application.get_stale import (
    GetStaleOpportunities,
)
from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.shared.domain.enums import OpportunityStage


def _make_opp(days_ago: int, **overrides) -> Opportunity:
    defaults = {
        "candidate_id": "user-1",
        "stage": OpportunityStage.DISCOVERY,
        "last_interaction_at": datetime.now(timezone.utc) - timedelta(days=days_ago),
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


class TestGetStaleOpportunities:
    async def test_returns_stale_opportunities(self):
        stale = [_make_opp(days_ago=10), _make_opp(days_ago=20)]
        opp_repo = AsyncMock()
        opp_repo.list_stale.return_value = stale

        profile = CandidateProfile(
            candidate_id="user-1",
            display_name="Test",
            follow_up_days=7,
        )
        profile_repo = AsyncMock()
        profile_repo.find_by_candidate_id.return_value = profile

        uc = GetStaleOpportunities(
            opportunity_repo=opp_repo, profile_repo=profile_repo
        )
        result = await uc.execute("user-1")

        assert len(result) == 2
        opp_repo.list_stale.assert_awaited_once()

    async def test_uses_default_when_no_profile(self):
        opp_repo = AsyncMock()
        opp_repo.list_stale.return_value = []

        profile_repo = AsyncMock()
        profile_repo.find_by_candidate_id.return_value = None

        uc = GetStaleOpportunities(
            opportunity_repo=opp_repo, profile_repo=profile_repo
        )
        await uc.execute("user-1")

        # Should still call list_stale with default 7-day cutoff
        opp_repo.list_stale.assert_awaited_once()
        call_args = opp_repo.list_stale.call_args
        cutoff = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("before", call_args[0][-1])
        expected = datetime.now(timezone.utc) - timedelta(days=7)
        assert abs((cutoff - expected).total_seconds()) < 5

    async def test_uses_profile_follow_up_days(self):
        opp_repo = AsyncMock()
        opp_repo.list_stale.return_value = []

        profile = CandidateProfile(
            candidate_id="user-1",
            display_name="Test",
            follow_up_days=3,
        )
        profile_repo = AsyncMock()
        profile_repo.find_by_candidate_id.return_value = profile

        uc = GetStaleOpportunities(
            opportunity_repo=opp_repo, profile_repo=profile_repo
        )
        await uc.execute("user-1")

        call_args = opp_repo.list_stale.call_args
        cutoff = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("before", call_args[0][-1])
        expected = datetime.now(timezone.utc) - timedelta(days=3)
        assert abs((cutoff - expected).total_seconds()) < 5

    async def test_empty_when_no_stale(self):
        opp_repo = AsyncMock()
        opp_repo.list_stale.return_value = []

        profile_repo = AsyncMock()
        profile_repo.find_by_candidate_id.return_value = None

        uc = GetStaleOpportunities(
            opportunity_repo=opp_repo, profile_repo=profile_repo
        )
        result = await uc.execute("user-1")

        assert result == []
