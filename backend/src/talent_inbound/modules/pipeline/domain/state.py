"""Pipeline state definition for the LangGraph processing graph."""

import operator
from typing import Annotated

from typing_extensions import TypedDict


class ExtractedData(TypedDict, total=False):
    """Structured data extracted from a recruiter message."""

    company_name: str | None
    client_name: str | None
    role_title: str | None
    salary_range: str | None
    tech_stack: list[str]
    work_model: str | None
    recruiter_name: str | None
    recruiter_type: str | None
    recruiter_company: str | None
    missing_fields: list[str]


class StepLog(TypedDict):
    """Single pipeline step log entry."""

    step: str
    status: str
    latency_ms: float
    tokens: int
    timestamp: str
    detail: str


class PipelineState(TypedDict, total=False):
    """State carried through the LangGraph processing pipeline.

    Each node reads what it needs and returns partial updates.
    pipeline_log uses Annotated + operator.add for append-only semantics.
    """

    # Input
    raw_input: str
    interaction_id: str
    opportunity_id: str
    candidate_id: str

    # Guardrail output
    sanitized_text: str
    pii_items_found: int
    prompt_injection_detected: bool

    # Gatekeeper output
    classification: str  # REAL_OFFER | SPAM | NOT_AN_OFFER
    classification_confidence: float

    # Extractor output
    extracted_data: ExtractedData

    # Analyst output (stub in US4, implemented in US5)
    match_score: int | None
    match_reasoning: str | None

    # Communicator output (stub in US4, implemented in US7)
    draft_response: str | None

    # Stage Detector output
    suggested_stage: str | None
    suggested_stage_reason: str | None

    # Metadata
    current_step: str
    pipeline_log: Annotated[list[StepLog], operator.add]
