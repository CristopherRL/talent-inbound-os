"""Unit tests for CandidateProfile domain entity."""

import pytest

from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.modules.profile.domain.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    ProfileNotFoundError,
)
from talent_inbound.shared.domain.enums import WorkModel


class TestCandidateProfileEntity:
    """Tests for the CandidateProfile Pydantic domain entity."""

    def test_create_profile_with_required_fields(self):
        profile = CandidateProfile(
            candidate_id="user-123",
            display_name="John Doe",
        )
        assert profile.candidate_id == "user-123"
        assert profile.display_name == "John Doe"
        assert profile.id  # Auto-generated UUID
        assert profile.created_at is not None
        assert profile.updated_at is not None

    def test_create_profile_with_all_fields(self):
        profile = CandidateProfile(
            candidate_id="user-123",
            display_name="Jane Smith",
            professional_title="Senior Backend Engineer",
            skills=["Python", "FastAPI", "PostgreSQL"],
            min_salary=80000,
            preferred_currency="EUR",
            work_model=WorkModel.REMOTE,
            preferred_locations=["Spain", "EU Remote"],
            industries=["FinTech", "HealthTech"],
            follow_up_days=5,
            ghosting_days=10,
        )
        assert profile.professional_title == "Senior Backend Engineer"
        assert profile.skills == ["Python", "FastAPI", "PostgreSQL"]
        assert profile.min_salary == 80000
        assert profile.preferred_currency == "EUR"
        assert profile.work_model == WorkModel.REMOTE
        assert profile.preferred_locations == ["Spain", "EU Remote"]
        assert profile.industries == ["FinTech", "HealthTech"]
        assert profile.follow_up_days == 5
        assert profile.ghosting_days == 10

    def test_default_values(self):
        profile = CandidateProfile(
            candidate_id="user-123",
            display_name="Test",
        )
        assert profile.professional_title is None
        assert profile.skills == []
        assert profile.min_salary is None
        assert profile.preferred_currency is None
        assert profile.work_model is None
        assert profile.preferred_locations == []
        assert profile.industries == []
        assert profile.cv_filename is None
        assert profile.cv_storage_path is None
        assert profile.cv_extracted_text is None
        assert profile.follow_up_days == 7
        assert profile.ghosting_days == 14

    def test_profile_touch_updates_timestamp(self):
        profile = CandidateProfile(
            candidate_id="user-123",
            display_name="Test",
        )
        original = profile.updated_at
        profile.touch()
        assert profile.updated_at >= original

    def test_cv_fields_can_be_set(self):
        profile = CandidateProfile(
            candidate_id="user-123",
            display_name="Test",
            cv_filename="resume.pdf",
            cv_storage_path="/uploads/abc123.pdf",
            cv_extracted_text="Experienced Python developer...",
        )
        assert profile.cv_filename == "resume.pdf"
        assert profile.cv_storage_path == "/uploads/abc123.pdf"
        assert "Python" in profile.cv_extracted_text


class TestProfileExceptions:
    """Tests for profile domain exceptions."""

    def test_profile_not_found_message(self):
        err = ProfileNotFoundError("user-456")
        assert "user-456" in str(err)
        assert err.candidate_id == "user-456"

    def test_invalid_file_type_message(self):
        err = InvalidFileTypeError("resume.exe")
        assert "resume.exe" in str(err)
        assert err.filename == "resume.exe"

    def test_file_too_large_message(self):
        err = FileTooLargeError(15.5, 10)
        assert "15.5" in str(err)
        assert err.size_mb == 15.5
        assert err.max_mb == 10
