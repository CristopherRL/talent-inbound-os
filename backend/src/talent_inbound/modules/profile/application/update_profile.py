"""UpdateProfile use case — create or update candidate profile."""

from dataclasses import dataclass

from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.modules.profile.domain.repositories import ProfileRepository
from talent_inbound.shared.domain.enums import WorkModel


@dataclass
class UpdateProfileCommand:
    candidate_id: str
    display_name: str
    professional_title: str | None = None
    skills: list[str] | None = None
    min_salary: int | None = None
    preferred_currency: str | None = None
    work_model: str | None = None
    preferred_locations: list[str] | None = None
    industries: list[str] | None = None
    follow_up_days: int = 7
    ghosting_days: int = 14


class UpdateProfile:
    """Creates a new profile or updates existing one for the candidate."""

    def __init__(self, profile_repo: ProfileRepository) -> None:
        self._profile_repo = profile_repo

    async def execute(self, command: UpdateProfileCommand) -> CandidateProfile:
        existing = await self._profile_repo.find_by_candidate_id(command.candidate_id)

        work_model = WorkModel(command.work_model) if command.work_model else None

        if existing:
            existing.display_name = command.display_name
            existing.professional_title = command.professional_title
            existing.skills = command.skills or []
            existing.min_salary = command.min_salary
            existing.preferred_currency = command.preferred_currency
            existing.work_model = work_model
            existing.preferred_locations = command.preferred_locations or []
            existing.industries = command.industries or []
            existing.follow_up_days = command.follow_up_days
            existing.ghosting_days = command.ghosting_days
            existing.touch()
            return await self._profile_repo.update(existing)

        profile = CandidateProfile(
            candidate_id=command.candidate_id,
            display_name=command.display_name,
            professional_title=command.professional_title,
            skills=command.skills or [],
            min_salary=command.min_salary,
            preferred_currency=command.preferred_currency,
            work_model=work_model,
            preferred_locations=command.preferred_locations or [],
            industries=command.industries or [],
            follow_up_days=command.follow_up_days,
            ghosting_days=command.ghosting_days,
        )
        return await self._profile_repo.save(profile)
