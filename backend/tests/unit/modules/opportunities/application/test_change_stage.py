"""Unit tests for ChangeStage use case (unusual jump detection, logging)."""

from unittest.mock import AsyncMock

import pytest

from talent_inbound.modules.opportunities.application.change_stage import (
    ChangeStage,
    ChangeStageCommand,
)
from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.shared.domain.enums import OpportunityStage, TransitionTrigger


def _make_opp(**overrides) -> Opportunity:
    defaults = {
        "candidate_id": "user-1",
        "stage": OpportunityStage.DISCOVERY,
    }
    defaults.update(overrides)
    return Opportunity(**defaults)


def _make_repo(opportunity: Opportunity | None):
    repo = AsyncMock()
    repo.find_by_id.return_value = opportunity
    repo.update.return_value = opportunity
    repo.save_transition.side_effect = lambda t: t
    return repo


class TestChangeStage:
    async def test_normal_transition(self):
        opp = _make_opp()
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="ENGAGING",
        )
        transition = await uc.execute(cmd)

        assert transition.from_stage == OpportunityStage.DISCOVERY
        assert transition.to_stage == OpportunityStage.ENGAGING
        assert transition.is_unusual is False
        assert transition.triggered_by == TransitionTrigger.USER
        repo.update.assert_awaited_once()
        repo.save_transition.assert_awaited_once()

    async def test_unusual_skip_transition(self):
        opp = _make_opp(stage=OpportunityStage.DISCOVERY)
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="INTERVIEWING",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_unusual_backward_transition(self):
        opp = _make_opp(stage=OpportunityStage.INTERVIEWING)
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="DISCOVERY",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_unusual_from_terminal(self):
        opp = _make_opp(stage=OpportunityStage.REJECTED)
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="ENGAGING",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_transition_with_note(self):
        opp = _make_opp()
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="ENGAGING",
            note="Moving forward after evaluation",
        )
        transition = await uc.execute(cmd)

        assert transition.note == "Moving forward after evaluation"

    async def test_not_found_raises(self):
        repo = _make_repo(None)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id="nonexistent",
            new_stage="ENGAGING",
        )
        with pytest.raises(OpportunityNotFoundError):
            await uc.execute(cmd)

    async def test_system_triggered(self):
        opp = _make_opp()
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="ENGAGING",
            triggered_by=TransitionTrigger.SYSTEM,
        )
        transition = await uc.execute(cmd)

        assert transition.triggered_by == TransitionTrigger.SYSTEM

    async def test_offer_without_negotiating_is_unusual(self):
        opp = _make_opp(stage=OpportunityStage.ENGAGING)
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="OFFER",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is True

    async def test_offer_from_negotiating_is_normal(self):
        opp = _make_opp(stage=OpportunityStage.NEGOTIATING)
        repo = _make_repo(opp)
        uc = ChangeStage(opportunity_repo=repo)

        cmd = ChangeStageCommand(
            opportunity_id=opp.id,
            new_stage="OFFER",
        )
        transition = await uc.execute(cmd)

        assert transition.is_unusual is False
