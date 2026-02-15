"""Pydantic schemas for the opportunities API endpoints."""

from datetime import datetime

from pydantic import BaseModel


class OpportunityListItem(BaseModel):
    """Single opportunity in the list response."""

    id: str
    company_name: str | None
    client_name: str | None
    role_title: str | None
    salary_range: str | None
    tech_stack: list[str]
    work_model: str | None
    recruiter_name: str | None
    recruiter_type: str | None
    match_score: int | None
    missing_fields: list[str]
    status: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime


# --- Detail view ---


class InteractionSummary(BaseModel):
    id: str
    interaction_type: str
    source: str
    raw_content: str
    created_at: datetime


class StatusTransitionItem(BaseModel):
    id: str
    from_status: str
    to_status: str
    triggered_by: str
    is_unusual: bool
    note: str | None
    created_at: datetime


class DraftResponseItem(BaseModel):
    id: str
    response_type: str
    generated_content: str
    edited_content: str | None
    is_final: bool
    is_sent: bool = False
    sent_at: datetime | None = None
    created_at: datetime


class OpportunityDetailResponse(BaseModel):
    """Full opportunity detail with timeline data."""

    id: str
    company_name: str | None
    client_name: str | None
    role_title: str | None
    salary_range: str | None
    tech_stack: list[str]
    work_model: str | None
    recruiter_name: str | None
    recruiter_type: str | None
    recruiter_company: str | None
    match_score: int | None
    match_reasoning: str | None
    missing_fields: list[str]
    status: str
    is_archived: bool
    interactions: list[InteractionSummary]
    status_history: list[StatusTransitionItem]
    draft_responses: list[DraftResponseItem]
    created_at: datetime
    updated_at: datetime
    last_interaction_at: datetime | None


# --- Requests ---


class GenerateDraftRequest(BaseModel):
    response_type: str  # REQUEST_INFO | EXPRESS_INTEREST | DECLINE
    additional_context: str | None = None  # Optional user instructions for the draft


class EditDraftRequest(BaseModel):
    edited_content: str | None = None
    is_final: bool | None = None


class ChangeStatusRequest(BaseModel):
    new_status: str
    note: str | None = None


# --- Responses ---


class ChangeStatusResponse(BaseModel):
    id: str
    status: str
    is_unusual: bool
    transition: StatusTransitionItem


class ArchiveResponse(BaseModel):
    id: str
    is_archived: bool
    message: str


class StaleOpportunityItem(BaseModel):
    id: str
    company_name: str | None
    role_title: str | None
    status: str
    last_interaction_at: datetime | None
    days_since_interaction: int | None


class ConfirmSentResponse(BaseModel):
    draft_id: str
    interaction_id: str


class SubmitFollowUpRequest(BaseModel):
    raw_content: str
    source: str  # LINKEDIN | EMAIL | FREELANCE_PLATFORM | OTHER


class SubmitFollowUpResponse(BaseModel):
    interaction_id: str
    opportunity_id: str
