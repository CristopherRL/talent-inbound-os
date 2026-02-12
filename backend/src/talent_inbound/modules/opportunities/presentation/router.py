"""Opportunities API router — list and detail endpoints."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from talent_inbound.container import Container
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.presentation.dependencies import get_current_user
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.opportunities.presentation.schemas import (
    OpportunityListItem,
)

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("", response_model=list[OpportunityListItem])
@inject
async def list_opportunities(
    current_user: User = Depends(get_current_user),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> list[OpportunityListItem]:
    opportunities = await opportunity_repo.list_by_candidate(current_user.id)
    return [
        OpportunityListItem(
            id=opp.id,
            company_name=opp.company_name,
            client_name=opp.client_name,
            role_title=opp.role_title,
            salary_range=opp.salary_range,
            tech_stack=opp.tech_stack,
            work_model=opp.work_model.value if opp.work_model else None,
            recruiter_name=opp.recruiter_name,
            recruiter_type=opp.recruiter_type.value if opp.recruiter_type else None,
            match_score=opp.match_score,
            missing_fields=opp.missing_fields,
            status=opp.status.value,
            is_archived=opp.is_archived,
            created_at=opp.created_at,
            updated_at=opp.updated_at,
        )
        for opp in opportunities
    ]
