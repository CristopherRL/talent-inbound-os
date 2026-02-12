"""CandidateProfile domain entity for the profile module."""

from talent_inbound.shared.domain.base_entity import Entity
from talent_inbound.shared.domain.enums import WorkModel


class CandidateProfile(Entity):
    """Structured preferences for match scoring. One per Candidate (1:1)."""

    candidate_id: str
    display_name: str
    professional_title: str | None = None
    skills: list[str] = []
    min_salary: int | None = None
    preferred_currency: str | None = None
    work_model: WorkModel | None = None
    preferred_locations: list[str] = []
    industries: list[str] = []
    cv_filename: str | None = None
    cv_storage_path: str | None = None
    cv_extracted_text: str | None = None
    follow_up_days: int = 7
    ghosting_days: int = 14
