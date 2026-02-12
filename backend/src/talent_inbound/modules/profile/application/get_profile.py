"""GetProfile use case — retrieve candidate profile."""

from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.modules.profile.domain.exceptions import ProfileNotFoundError
from talent_inbound.modules.profile.domain.repositories import ProfileRepository


class GetProfile:
    """Returns the profile for a given candidate, or raises if not found."""

    def __init__(self, profile_repo: ProfileRepository) -> None:
        self._profile_repo = profile_repo

    async def execute(self, candidate_id: str) -> CandidateProfile:
        profile = await self._profile_repo.find_by_candidate_id(candidate_id)
        if not profile:
            raise ProfileNotFoundError(candidate_id)
        return profile
