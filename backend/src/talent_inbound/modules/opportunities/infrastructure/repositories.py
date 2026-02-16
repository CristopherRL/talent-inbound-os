"""SQLAlchemy implementation of the OpportunityRepository."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _enum_value(val) -> str | None:
    """Safely extract .value from an enum or return the string as-is."""
    if val is None:
        return None
    return val.value if isinstance(val, StrEnum) else str(val)

from talent_inbound.modules.opportunities.domain.entities import (
    Opportunity,
    StageTransition,
)
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.opportunities.infrastructure.orm_models import (
    OpportunityModel,
    StageTransitionModel,
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
        self,
        candidate_id: str,
        archived_filter: str | None = None,
        stage_filter: str | None = None,
    ) -> list[Opportunity]:
        stmt = select(OpportunityModel).where(
            OpportunityModel.candidate_id == candidate_id
        )
        if archived_filter == "only":
            stmt = stmt.where(OpportunityModel.is_archived == True)  # noqa: E712
        elif archived_filter == "all":
            pass  # no filter — show everything
        else:
            # Default: non-archived only
            stmt = stmt.where(OpportunityModel.is_archived == False)  # noqa: E712
        if stage_filter:
            stmt = stmt.where(OpportunityModel.stage == stage_filter)
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
        model.work_model = _enum_value(opportunity.work_model)
        model.recruiter_name = opportunity.recruiter_name
        model.recruiter_type = _enum_value(opportunity.recruiter_type)
        model.recruiter_company = opportunity.recruiter_company
        model.match_score = opportunity.match_score
        model.match_reasoning = opportunity.match_reasoning
        model.missing_fields = opportunity.missing_fields
        model.stage = _enum_value(opportunity.stage)
        model.suggested_stage = _enum_value(opportunity.suggested_stage)
        model.suggested_stage_reason = opportunity.suggested_stage_reason
        model.is_archived = opportunity.is_archived
        model.last_interaction_at = opportunity.last_interaction_at
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def save_transition(self, transition: StageTransition) -> StageTransition:
        model = StageTransitionModel.from_domain(transition)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def list_transitions(self, opportunity_id: str) -> list[StageTransition]:
        stmt = (
            select(StageTransitionModel)
            .where(StageTransitionModel.opportunity_id == opportunity_id)
            .order_by(StageTransitionModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]

    async def list_stale(
        self, candidate_id: str, before: datetime
    ) -> list[Opportunity]:
        stmt = (
            select(OpportunityModel)
            .where(OpportunityModel.candidate_id == candidate_id)
            .where(OpportunityModel.is_archived == False)  # noqa: E712
            .where(OpportunityModel.last_interaction_at < before)
        )
        stmt = stmt.order_by(OpportunityModel.last_interaction_at.asc())
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [m.to_domain() for m in models]
