"""ChangeStage use case — manually change an opportunity's stage."""

from talent_inbound.modules.opportunities.domain.entities import StageTransition
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.shared.domain.enums import OpportunityStage, TransitionTrigger


class ChangeStageCommand:
    def __init__(
        self,
        opportunity_id: str,
        new_stage: str,
        triggered_by: TransitionTrigger = TransitionTrigger.USER,
        note: str | None = None,
    ) -> None:
        self.opportunity_id = opportunity_id
        self.new_stage = OpportunityStage(new_stage)
        self.triggered_by = triggered_by
        self.note = note


class ChangeStage:
    """Change an opportunity's stage and log the transition."""

    def __init__(self, opportunity_repo: OpportunityRepository) -> None:
        self._repo = opportunity_repo

    async def execute(self, command: ChangeStageCommand) -> StageTransition:
        opportunity = await self._repo.find_by_id(command.opportunity_id)
        if opportunity is None:
            raise OpportunityNotFoundError(command.opportunity_id)

        transition = opportunity.change_stage(
            new_stage=command.new_stage,
            triggered_by=command.triggered_by,
            note=command.note,
        )

        await self._repo.update(opportunity)
        await self._repo.save_transition(transition)

        return transition
