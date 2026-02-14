"""ChangeStatus use case — manually change an opportunity's status."""

from talent_inbound.modules.opportunities.domain.entities import StatusTransition
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.shared.domain.enums import OpportunityStatus, TransitionTrigger


class ChangeStatusCommand:
    def __init__(
        self,
        opportunity_id: str,
        new_status: str,
        triggered_by: TransitionTrigger = TransitionTrigger.USER,
        note: str | None = None,
    ) -> None:
        self.opportunity_id = opportunity_id
        self.new_status = OpportunityStatus(new_status)
        self.triggered_by = triggered_by
        self.note = note


class ChangeStatus:
    """Change an opportunity's status and log the transition."""

    def __init__(self, opportunity_repo: OpportunityRepository) -> None:
        self._repo = opportunity_repo

    async def execute(self, command: ChangeStatusCommand) -> StatusTransition:
        opportunity = await self._repo.find_by_id(command.opportunity_id)
        if opportunity is None:
            raise OpportunityNotFoundError(command.opportunity_id)

        transition = opportunity.change_status(
            new_status=command.new_status,
            triggered_by=command.triggered_by,
            note=command.note,
        )

        await self._repo.update(opportunity)
        await self._repo.save_transition(transition)

        return transition
