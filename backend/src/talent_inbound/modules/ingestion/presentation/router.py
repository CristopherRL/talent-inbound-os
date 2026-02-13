"""Ingestion API router — message submission and retrieval."""

import structlog
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from talent_inbound.container import Container
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.presentation.dependencies import get_current_user
from talent_inbound.modules.ingestion.application.submit_message import (
    SubmitMessage,
    SubmitMessageCommand,
)
from talent_inbound.modules.ingestion.domain.exceptions import (
    ContentTooLongError,
    DuplicateInteractionError,
    EmptyContentError,
)
from talent_inbound.modules.ingestion.domain.repositories import InteractionRepository
from talent_inbound.modules.ingestion.presentation.schemas import (
    InteractionResponse,
    SubmitMessageRequest,
    SubmitMessageResponse,
)
from talent_inbound.modules.pipeline.application.process_pipeline import ProcessPipeline
from talent_inbound.modules.pipeline.infrastructure.graphs import build_main_pipeline
from talent_inbound.modules.pipeline.infrastructure.model_router import ModelRouter
from talent_inbound.modules.pipeline.infrastructure.sse import SSEEmitter

logger = structlog.get_logger()

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post(
    "/messages",
    response_model=SubmitMessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@inject
async def submit_message(
    body: SubmitMessageRequest,
    current_user: User = Depends(get_current_user),
    submit_message_uc: SubmitMessage = Depends(Provide[Container.submit_message_uc]),
    interaction_repo: InteractionRepository = Depends(Provide[Container.interaction_repo]),
    model_router: ModelRouter = Depends(Provide[Container.model_router]),
    sse_emitter: SSEEmitter = Depends(Provide[Container.sse_emitter]),
) -> SubmitMessageResponse:
    try:
        result = await submit_message_uc.execute(
            SubmitMessageCommand(
                candidate_id=current_user.id,
                raw_content=body.raw_content,
                source=body.source.value,
            )
        )
    except EmptyContentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ContentTooLongError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e)
        )
    except DuplicateInteractionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Run pipeline inline (mock agents are instant; real LLM would use Arq worker)
    try:
        from talent_inbound.modules.opportunities.domain.repositories import OpportunityRepository
        opp_repo = Container.opportunity_repo()
        graph = build_main_pipeline(model_router)
        pipeline_uc = ProcessPipeline(
            interaction_repo=interaction_repo,
            opportunity_repo=opp_repo,
            pipeline_graph=graph,
            sse_emitter=sse_emitter,
        )
        await pipeline_uc.execute(result.interaction.id)
        # Re-fetch opportunity to get updated status after pipeline
        updated_opp = await opp_repo.find_by_id(result.opportunity.id)
        final_status = updated_opp.status.value if updated_opp else result.opportunity.status.value
    except Exception:
        logger.exception("inline_pipeline_failed")
        final_status = result.opportunity.status.value

    return SubmitMessageResponse(
        interaction_id=result.interaction.id,
        opportunity_id=result.opportunity.id,
        status=final_status,
    )


@router.get("/messages/{interaction_id}", response_model=InteractionResponse)
@inject
async def get_interaction(
    interaction_id: str,
    current_user: User = Depends(get_current_user),
    interaction_repo: InteractionRepository = Depends(
        Provide[Container.interaction_repo]
    ),
) -> InteractionResponse:
    interaction = await interaction_repo.find_by_id(interaction_id)
    if interaction is None or interaction.candidate_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found."
        )
    return InteractionResponse(
        id=interaction.id,
        opportunity_id=interaction.opportunity_id,
        source=interaction.source.value,
        interaction_type=interaction.interaction_type.value,
        processing_status=interaction.processing_status.value,
        classification=(
            interaction.classification.value if interaction.classification else None
        ),
        pipeline_log=interaction.pipeline_log,
        created_at=interaction.created_at,
    )
