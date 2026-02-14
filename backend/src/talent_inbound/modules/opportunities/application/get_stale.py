"""GetStaleOpportunities use case — find opportunities at risk of ghosting."""

from datetime import datetime, timedelta, timezone

from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.profile.domain.repositories import ProfileRepository


class GetStaleOpportunities:
    """Return opportunities whose last_interaction_at exceeds the candidate's thresholds."""

    def __init__(
        self,
        opportunity_repo: OpportunityRepository,
        profile_repo: ProfileRepository,
    ) -> None:
        self._opp_repo = opportunity_repo
        self._profile_repo = profile_repo

    async def execute(self, candidate_id: str) -> list[Opportunity]:
        profile = await self._profile_repo.find_by_candidate_id(candidate_id)

        # Use profile thresholds or sensible defaults
        follow_up_days = 7
        if profile and profile.follow_up_days is not None:
            follow_up_days = profile.follow_up_days

        cutoff = datetime.now(timezone.utc) - timedelta(days=follow_up_days)
        return await self._opp_repo.list_stale(candidate_id, before=cutoff)
