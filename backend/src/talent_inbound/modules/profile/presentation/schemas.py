"""Profile API schemas — request/response models for the profile endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ProfileRequest(BaseModel):
    """Request body for creating/updating a profile."""

    display_name: str = Field(min_length=1, max_length=255)
    professional_title: str | None = None
    skills: list[str] = []
    min_salary: int | None = Field(default=None, ge=0)
    preferred_currency: str | None = Field(default=None, max_length=3)
    work_model: str | None = None
    preferred_locations: list[str] = []
    industries: list[str] = []
    follow_up_days: int = Field(default=7, ge=1, le=90)
    ghosting_days: int = Field(default=14, ge=1, le=180)


class ProfileResponse(BaseModel):
    """Response body for profile data."""

    display_name: str
    professional_title: str | None = None
    skills: list[str] = []
    min_salary: int | None = None
    preferred_currency: str | None = None
    work_model: str | None = None
    preferred_locations: list[str] = []
    industries: list[str] = []
    cv_filename: str | None = None
    follow_up_days: int = 7
    ghosting_days: int = 14
    updated_at: datetime


class CVUploadResponse(BaseModel):
    """Response body after CV upload."""

    cv_filename: str
    message: str = "CV uploaded successfully"
