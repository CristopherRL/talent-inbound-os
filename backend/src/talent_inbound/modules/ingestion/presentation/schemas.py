"""Pydantic schemas for the ingestion API endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field

from talent_inbound.shared.domain.enums import InteractionSource


class SubmitMessageRequest(BaseModel):
    """Request body for POST /ingestion/messages."""

    raw_content: str = Field(..., min_length=1, max_length=50000)
    source: InteractionSource


class SubmitMessageResponse(BaseModel):
    """Response for POST /ingestion/messages (202 Accepted)."""

    interaction_id: str
    opportunity_id: str
    stage: str
    message: str = "Pipeline processing started"


class InteractionResponse(BaseModel):
    """Response for GET /ingestion/messages/{id}."""

    id: str
    opportunity_id: str | None
    source: str
    interaction_type: str
    processing_status: str
    classification: str | None
    pipeline_log: list[dict]
    created_at: datetime
