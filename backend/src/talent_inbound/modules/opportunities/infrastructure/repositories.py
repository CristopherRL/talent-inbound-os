"""SQLAlchemy implementation of the OpportunityRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.opportunities.infrastructure.orm_models import (
    OpportunityModel,
)


class SqlAlchemyOpportunityRepository(OpportunityRepository):
    """Adapter: persists Opportunity entities via SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, opportunity: Opportunity) -> Opportunity:
        model = OpportunityModel.from_domain(opportunity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def find_by_id(self, opportunity_id: str) -> Opportunity | None:
        stmt = select(OpportunityModel).where(OpportunityModel.id == opportunity_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def list_by_candidate(
        self, candidate_id: str, include_archived: bool = False
    ) -> list[Opportunity]:
        stmt = select(OpportunityModel).where(
            OpportunityModel.candidate_id == candidate_id
        )
        if not include_archived:
            stmt = stmt.where(OpportunityModel.is_archived == False)  # noqa: E712
        stmt = stmt.order_by(OpportunityModel.created_at.desc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def update(self, opportunity: Opportunity) -> Opportunity:
        stmt = select(OpportunityModel).where(
            OpportunityModel.id == opportunity.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Opportunity not found: {opportunity.id}")

        model.company_name = opportunity.company_name
        model.client_name = opportunity.client_name
        model.role_title = opportunity.role_title
        model.salary_range = opportunity.salary_range
        model.tech_stack = opportunity.tech_stack
        model.work_model = (
            opportunity.work_model.value if opportunity.work_model else None
        )
        model.recruiter_name = opportunity.recruiter_name
        model.recruiter_type = (
            opportunity.recruiter_type.value if opportunity.recruiter_type else None
        )
        model.recruiter_company = opportunity.recruiter_company
        model.match_score = opportunity.match_score
        model.match_reasoning = opportunity.match_reasoning
        model.missing_fields = opportunity.missing_fields
        model.status = opportunity.status.value
        model.is_archived = opportunity.is_archived
        model.last_interaction_at = opportunity.last_interaction_at
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()
