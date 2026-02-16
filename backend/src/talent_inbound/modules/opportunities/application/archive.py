"""Archive / Unarchive use cases for opportunities."""

from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.shared.domain.enums import TERMINAL_STAGES


class ArchiveOpportunity:
    """Archive an opportunity. Only allowed for terminal stages."""

    def __init__(self, opportunity_repo: OpportunityRepository) -> None:
        self._repo = opportunity_repo

    async def execute(self, opportunity_id: str) -> Opportunity:
        opportunity = await self._repo.find_by_id(opportunity_id)
        if opportunity is None:
            raise OpportunityNotFoundError(opportunity_id)

        if opportunity.stage not in TERMINAL_STAGES:
            raise ValueError(
                f"Cannot archive: stage '{opportunity.stage.value}' is not terminal. "
                "Only OFFER, REJECTED, or GHOSTED opportunities can be archived."
            )

        opportunity.is_archived = True
        opportunity.touch()
        return await self._repo.update(opportunity)


class UnarchiveOpportunity:
    """Restore an archived opportunity."""

    def __init__(self, opportunity_repo: OpportunityRepository) -> None:
        self._repo = opportunity_repo

    async def execute(self, opportunity_id: str) -> Opportunity:
        opportunity = await self._repo.find_by_id(opportunity_id)
        if opportunity is None:
            raise OpportunityNotFoundError(opportunity_id)

        opportunity.is_archived = False
        opportunity.touch()
        return await self._repo.update(opportunity)
