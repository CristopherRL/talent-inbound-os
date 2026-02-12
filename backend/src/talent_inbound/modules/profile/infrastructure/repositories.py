"""SQLAlchemy implementation of the ProfileRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.modules.profile.domain.repositories import ProfileRepository
from talent_inbound.modules.profile.infrastructure.orm_models import (
    CandidateProfileModel,
)


class SqlAlchemyProfileRepository(ProfileRepository):
    """Adapter: persists CandidateProfile entities via SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, profile: CandidateProfile) -> CandidateProfile:
        model = CandidateProfileModel.from_domain(profile)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def find_by_candidate_id(
        self, candidate_id: str
    ) -> CandidateProfile | None:
        stmt = select(CandidateProfileModel).where(
            CandidateProfileModel.candidate_id == candidate_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, profile: CandidateProfile) -> CandidateProfile:
        stmt = select(CandidateProfileModel).where(
            CandidateProfileModel.id == profile.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one()

        model.display_name = profile.display_name
        model.professional_title = profile.professional_title
        model.skills = profile.skills
        model.min_salary = profile.min_salary
        model.preferred_currency = profile.preferred_currency
        model.work_model = profile.work_model.value if profile.work_model else None
        model.preferred_locations = profile.preferred_locations
        model.industries = profile.industries
        model.cv_filename = profile.cv_filename
        model.cv_storage_path = profile.cv_storage_path
        model.cv_extracted_text = profile.cv_extracted_text
        model.follow_up_days = profile.follow_up_days
        model.ghosting_days = profile.ghosting_days

        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()
