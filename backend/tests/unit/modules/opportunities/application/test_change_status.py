"""Unit tests for ChangeStatus use case (unusual jump detection, logging)."""

from unittest.mock import AsyncMock

import pytest

from talent_inbound.modules.opportunities.application.change_status import (
    ChangeStatus,
    ChangeStatusCommand,
)
from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.shared.domain.enums import OpportunityStatus, TransitionTrigger


def _make_opp(**overrides) -> Opportunity:
    defaults = {
        "candidate_id": "user-1",
        "status": OpportunityStatus.ACTION_REQUIRED,
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


def _make_repo(opportunity: Opportunity | None):
    repo = AsyncMock()
    repo.find_by_id.return_value = opportunity
    repo.update.return_value = opportunity
    repo.save_transition.side_effect = lambda t: t
    return repo


class TestChangeStatus:
    async def test_normal_transition(self):
        opp = _make_opp()
        repo = _make_repo(opp)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id=opp.id,
            new_status="REVIEWING",
        )
        transition = await uc.execute(cmd)

        assert transition.from_status == OpportunityStatus.ACTION_REQUIRED
        assert transition.to_status == OpportunityStatus.REVIEWING
        assert transition.is_unusual is False
        assert transition.triggered_by == TransitionTrigger.USER
        repo.update.assert_awaited_once()
        repo.save_transition.assert_awaited_once()

    async def test_unusual_skip_transition(self):
        opp = _make_opp(status=OpportunityStatus.NEW)
        repo = _make_repo(opp)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id=opp.id,
            new_status="REVIEWING",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_unusual_backward_transition(self):
        opp = _make_opp(status=OpportunityStatus.INTERVIEWING)
        repo = _make_repo(opp)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id=opp.id,
            new_status="ACTION_REQUIRED",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_unusual_from_terminal(self):
        opp = _make_opp(status=OpportunityStatus.REJECTED)
        repo = _make_repo(opp)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id=opp.id,
            new_status="REVIEWING",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_transition_with_note(self):
        opp = _make_opp()
        repo = _make_repo(opp)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id=opp.id,
            new_status="REVIEWING",
            note="Moving forward after interview",
        )
        transition = await uc.execute(cmd)

        assert transition.note == "Moving forward after interview"

    async def test_not_found_raises(self):
        repo = _make_repo(None)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id="nonexistent",
            new_status="REVIEWING",
        )
        with pytest.raises(OpportunityNotFoundError):
            await uc.execute(cmd)

    async def test_system_triggered(self):
        opp = _make_opp()
        repo = _make_repo(opp)
        uc = ChangeStatus(opportunity_repo=repo)

        cmd = ChangeStatusCommand(
            opportunity_id=opp.id,
            new_status="REVIEWING",
            triggered_by=TransitionTrigger.SYSTEM,
        )
        transition = await uc.execute(cmd)

        assert transition.triggered_by == TransitionTrigger.SYSTEM
