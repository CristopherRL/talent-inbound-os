"""Pipeline API router — SSE progress endpoint."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from talent_inbound.container import Container
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.presentation.dependencies import get_current_user
from talent_inbound.modules.pipeline.infrastructure.sse import SSEEmitter

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/progress/{interaction_id}")
@inject
async def pipeline_progress(
    interaction_id: str,
    current_user: User = Depends(get_current_user),
    sse_emitter: SSEEmitter = Depends(Provide[Container.sse_emitter]),
) -> StreamingResponse:
    """SSE endpoint: streams real-time pipeline progress events."""
    return StreamingResponse(
        sse_emitter.stream(interaction_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
