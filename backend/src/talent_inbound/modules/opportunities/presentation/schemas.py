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
