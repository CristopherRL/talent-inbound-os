"""Opportunities API router — list, detail, status change, archive, stale."""

from datetime import datetime, timezone

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.container import Container
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.presentation.dependencies import get_current_user
from talent_inbound.modules.opportunities.application.archive import (
    ArchiveOpportunity,
    UnarchiveOpportunity,
)
from talent_inbound.modules.opportunities.application.change_status import (
    ChangeStatus,
    ChangeStatusCommand,
)
from talent_inbound.modules.opportunities.application.get_stale import (
    GetStaleOpportunities,
)
from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.opportunities.application.edit_draft import EditDraft
from talent_inbound.modules.opportunities.application.generate_draft import (
    GenerateDraft,
)
from talent_inbound.modules.opportunities.presentation.schemas import (
    ArchiveResponse,
    ChangeStatusRequest,
    ChangeStatusResponse,
    DraftResponseItem,
    EditDraftRequest,
    GenerateDraftRequest,
    InteractionSummary,
    OpportunityDetailResponse,
    OpportunityListItem,
    StaleOpportunityItem,
    StatusTransitionItem,
)
from talent_inbound.shared.domain.enums import TransitionTrigger

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


def _opp_to_list_item(opp) -> OpportunityListItem:
    return OpportunityListItem(
        id=opp.id,
        company_name=opp.company_name,
        client_name=opp.client_name,
        role_title=opp.role_title,
        salary_range=opp.salary_range,
        tech_stack=opp.tech_stack,
        work_model=opp.work_model.value if hasattr(opp.work_model, "value") else opp.work_model,
        recruiter_name=opp.recruiter_name,
        recruiter_type=opp.recruiter_type.value if hasattr(opp.recruiter_type, "value") else opp.recruiter_type,
        match_score=opp.match_score,
        missing_fields=opp.missing_fields,
        status=opp.status.value if hasattr(opp.status, "value") else opp.status,
        is_archived=opp.is_archived,
        created_at=opp.created_at,
        updated_at=opp.updated_at,
    )


@router.get("", response_model=list[OpportunityListItem])
@inject
async def list_opportunities(
    current_user: User = Depends(get_current_user),
    status: str | None = Query(None, description="Filter by status"),
    archived: str | None = Query(
        None,
        description="Archive filter: omit for active only, 'only' for archived only, 'all' for everything",
    ),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> list[OpportunityListItem]:
    opportunities = await opportunity_repo.list_by_candidate(
        current_user.id,
        archived_filter=archived,
        status_filter=status,
    )
    return [_opp_to_list_item(opp) for opp in opportunities]


@router.get("/stale", response_model=list[StaleOpportunityItem])
@inject
async def get_stale_opportunities(
    current_user: User = Depends(get_current_user),
    get_stale_uc: GetStaleOpportunities = Depends(
        Provide[Container.get_stale_uc]
    ),
) -> list[StaleOpportunityItem]:
    stale = await get_stale_uc.execute(current_user.id)
    now = datetime.now(timezone.utc)
    return [
        StaleOpportunityItem(
            id=opp.id,
            company_name=opp.company_name,
            role_title=opp.role_title,
            status=opp.status.value if hasattr(opp.status, "value") else opp.status,
            last_interaction_at=opp.last_interaction_at,
            days_since_interaction=(
                (now - opp.last_interaction_at).days
                if opp.last_interaction_at
                else None
            ),
        )
        for opp in stale
    ]


@router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
@inject
async def get_opportunity_detail(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> OpportunityDetailResponse:
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    # Load transitions
    transitions = await opportunity_repo.list_transitions(opportunity_id)

    # Load interactions for this opportunity
    from talent_inbound.modules.ingestion.infrastructure.orm_models import (
        InteractionModel,
    )
    from talent_inbound.shared.infrastructure.database import get_current_session

    session = get_current_session()
    stmt = (
        select(InteractionModel)
        .where(InteractionModel.opportunity_id == opportunity_id)
        .order_by(InteractionModel.created_at.asc())
    )
    result = await session.execute(stmt)
    interaction_models = result.scalars().all()

    interactions = [
        InteractionSummary(
            id=i.id,
            interaction_type=i.interaction_type,
            source=i.source,
            raw_content=i.raw_content,
            created_at=i.created_at,
        )
        for i in interaction_models
    ]

    status_history = [
        StatusTransitionItem(
            id=t.id,
            from_status=t.from_status.value if hasattr(t.from_status, "value") else t.from_status,
            to_status=t.to_status.value if hasattr(t.to_status, "value") else t.to_status,
            triggered_by=t.triggered_by.value if hasattr(t.triggered_by, "value") else t.triggered_by,
            is_unusual=t.is_unusual,
            note=t.note,
            created_at=t.created_at,
        )
        for t in transitions
    ]

    # Load draft responses (empty for now — implemented in Phase 9)
    from talent_inbound.modules.opportunities.infrastructure.orm_models import (
        DraftResponseModel,
    )

    draft_stmt = (
        select(DraftResponseModel)
        .where(DraftResponseModel.opportunity_id == opportunity_id)
        .order_by(DraftResponseModel.created_at.desc())
    )
    draft_result = await session.execute(draft_stmt)
    draft_models = draft_result.scalars().all()

    drafts = [
        DraftResponseItem(
            id=d.id,
            response_type=d.response_type,
            generated_content=d.generated_content,
            edited_content=d.edited_content,
            is_final=d.is_final,
            created_at=d.created_at,
        )
        for d in draft_models
    ]

    return OpportunityDetailResponse(
        id=opp.id,
        company_name=opp.company_name,
        client_name=opp.client_name,
        role_title=opp.role_title,
        salary_range=opp.salary_range,
        tech_stack=opp.tech_stack,
        work_model=opp.work_model.value if hasattr(opp.work_model, "value") else opp.work_model,
        recruiter_name=opp.recruiter_name,
        recruiter_type=opp.recruiter_type.value if hasattr(opp.recruiter_type, "value") else opp.recruiter_type,
        recruiter_company=opp.recruiter_company,
        match_score=opp.match_score,
        match_reasoning=opp.match_reasoning,
        missing_fields=opp.missing_fields,
        status=opp.status.value if hasattr(opp.status, "value") else opp.status,
        is_archived=opp.is_archived,
        interactions=interactions,
        status_history=status_history,
        draft_responses=drafts,
        created_at=opp.created_at,
        updated_at=opp.updated_at,
        last_interaction_at=opp.last_interaction_at,
    )


@router.patch("/{opportunity_id}/status", response_model=ChangeStatusResponse)
@inject
async def change_status(
    opportunity_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(get_current_user),
    change_status_uc: ChangeStatus = Depends(
        Provide[Container.change_status_uc]
    ),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> ChangeStatusResponse:
    # Verify ownership
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        cmd = ChangeStatusCommand(
            opportunity_id=opportunity_id,
            new_status=body.new_status,
            triggered_by=TransitionTrigger.USER,
            note=body.note,
        )
        transition = await change_status_uc.execute(cmd)
    except OpportunityNotFoundError:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ChangeStatusResponse(
        id=opportunity_id,
        status=transition.to_status.value if hasattr(transition.to_status, "value") else transition.to_status,
        is_unusual=transition.is_unusual,
        transition=StatusTransitionItem(
            id=transition.id,
            from_status=transition.from_status.value if hasattr(transition.from_status, "value") else transition.from_status,
            to_status=transition.to_status.value if hasattr(transition.to_status, "value") else transition.to_status,
            triggered_by=transition.triggered_by.value if hasattr(transition.triggered_by, "value") else transition.triggered_by,
            is_unusual=transition.is_unusual,
            note=transition.note,
            created_at=transition.created_at,
        ),
    )


@router.post("/{opportunity_id}/archive", response_model=ArchiveResponse)
@inject
async def archive_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    archive_uc: ArchiveOpportunity = Depends(
        Provide[Container.archive_uc]
    ),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> ArchiveResponse:
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        await archive_uc.execute(opportunity_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ArchiveResponse(id=opportunity_id, is_archived=True, message="Opportunity archived")


@router.post("/{opportunity_id}/unarchive", response_model=ArchiveResponse)
@inject
async def unarchive_opportunity(
    opportunity_id: str,
    current_user: User = Depends(get_current_user),
    unarchive_uc: UnarchiveOpportunity = Depends(
        Provide[Container.unarchive_uc]
    ),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> ArchiveResponse:
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    await unarchive_uc.execute(opportunity_id)
    return ArchiveResponse(id=opportunity_id, is_archived=False, message="Opportunity unarchived")


@router.post(
    "/{opportunity_id}/drafts",
    response_model=DraftResponseItem,
    status_code=201,
)
@inject
async def generate_draft(
    opportunity_id: str,
    body: GenerateDraftRequest,
    current_user: User = Depends(get_current_user),
    generate_draft_uc: GenerateDraft = Depends(
        Provide[Container.generate_draft_uc]
    ),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> DraftResponseItem:
    # Verify ownership
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        result = await generate_draft_uc.execute(
            opportunity_id=opportunity_id,
            response_type=body.response_type,
            additional_context=body.additional_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return DraftResponseItem(**result)


@router.put(
    "/{opportunity_id}/drafts/{draft_id}",
    response_model=DraftResponseItem,
)
@inject
async def edit_draft(
    opportunity_id: str,
    draft_id: str,
    body: EditDraftRequest,
    current_user: User = Depends(get_current_user),
    edit_draft_uc: EditDraft = Depends(
        Provide[Container.edit_draft_uc]
    ),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> DraftResponseItem:
    # Verify ownership
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    try:
        result = await edit_draft_uc.execute(
            opportunity_id=opportunity_id,
            draft_id=draft_id,
            edited_content=body.edited_content,
            is_final=body.is_final,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return DraftResponseItem(**result)


@router.delete(
    "/{opportunity_id}/drafts/{draft_id}",
    status_code=204,
)
@inject
async def delete_draft(
    opportunity_id: str,
    draft_id: str,
    current_user: User = Depends(get_current_user),
    opportunity_repo: OpportunityRepository = Depends(
        Provide[Container.opportunity_repo]
    ),
) -> None:
    opp = await opportunity_repo.find_by_id(opportunity_id)
    if opp is None or opp.candidate_id != current_user.id:
        raise HTTPException(status_code=404, detail="Opportunity not found")

    from talent_inbound.modules.opportunities.infrastructure.orm_models import (
        DraftResponseModel,
    )
    from talent_inbound.shared.infrastructure.database import get_current_session

    session = get_current_session()
    stmt = select(DraftResponseModel).where(
        DraftResponseModel.id == draft_id,
        DraftResponseModel.opportunity_id == opportunity_id,
    )
    result = await session.execute(stmt)
    draft_model = result.scalar_one_or_none()
    if draft_model is None:
        raise HTTPException(status_code=404, detail="Draft not found")

    await session.delete(draft_model)
    await session.flush()
