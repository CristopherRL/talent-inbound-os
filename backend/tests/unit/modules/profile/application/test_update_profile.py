"""Unit tests for UpdateProfile and UploadCV use cases."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from talent_inbound.modules.profile.application.update_profile import (
    UpdateProfile,
    UpdateProfileCommand,
)
from talent_inbound.modules.profile.application.upload_cv import (
    UploadCV,
    UploadCVCommand,
)
from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.modules.profile.domain.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    ProfileNotFoundError,
)
from talent_inbound.shared.domain.enums import WorkModel


class TestUpdateProfile:
    """Tests for the UpdateProfile use case."""

    @pytest.fixture
    def mock_repo(self):
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def use_case(self, mock_repo):
        return UpdateProfile(profile_repo=mock_repo)

    async def test_create_new_profile(self, use_case, mock_repo):
        mock_repo.find_by_candidate_id.return_value = None
        mock_repo.save.return_value = CandidateProfile(
            candidate_id="user-1",
            display_name="John Doe",
            skills=["Python"],
            work_model=WorkModel.REMOTE,
        )

        result = await use_case.execute(
            UpdateProfileCommand(
                candidate_id="user-1",
                display_name="John Doe",
                skills=["Python"],
                work_model="REMOTE",
            )
        )

        assert result.display_name == "John Doe"
        mock_repo.save.assert_called_once()

    async def test_update_existing_profile(self, use_case, mock_repo):
        existing = CandidateProfile(
            candidate_id="user-1",
            display_name="Old Name",
        )
        mock_repo.find_by_candidate_id.return_value = existing
        mock_repo.update.return_value = CandidateProfile(
            candidate_id="user-1",
            display_name="New Name",
            skills=["Rust"],
        )

        result = await use_case.execute(
            UpdateProfileCommand(
                candidate_id="user-1",
                display_name="New Name",
                skills=["Rust"],
            )
        )

        assert result.display_name == "New Name"
        mock_repo.update.assert_called_once()
        mock_repo.save.assert_not_called()

    async def test_create_profile_with_all_fields(self, use_case, mock_repo):
        mock_repo.find_by_candidate_id.return_value = None
        mock_repo.save.return_value = CandidateProfile(
            candidate_id="user-1",
            display_name="Jane",
            professional_title="Staff Engineer",
            skills=["Go", "K8s"],
            min_salary=120000,
            preferred_currency="USD",
            work_model=WorkModel.HYBRID,
            preferred_locations=["NYC"],
            industries=["FinTech"],
            follow_up_days=3,
            ghosting_days=21,
        )

        result = await use_case.execute(
            UpdateProfileCommand(
                candidate_id="user-1",
                display_name="Jane",
                professional_title="Staff Engineer",
                skills=["Go", "K8s"],
                min_salary=120000,
                preferred_currency="USD",
                work_model="HYBRID",
                preferred_locations=["NYC"],
                industries=["FinTech"],
                follow_up_days=3,
                ghosting_days=21,
            )
        )

        assert result.min_salary == 120000
        assert result.work_model == WorkModel.HYBRID


class TestUploadCV:
    """Tests for the UploadCV use case."""

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage(self):
        storage = AsyncMock()
        storage.save.return_value = "/uploads/abc.pdf"
        return storage

    @pytest.fixture
    def mock_parser(self):
        parser = MagicMock()
        parser.extract_text_from_bytes.return_value = "Extracted CV text"
        return parser

    @pytest.fixture
    def use_case(self, mock_repo, mock_storage, mock_parser):
        return UploadCV(
            profile_repo=mock_repo,
            storage_backend=mock_storage,
            cv_parser=mock_parser,
        )

    async def test_upload_pdf_success(self, use_case, mock_repo, mock_storage):
        existing = CandidateProfile(
            candidate_id="user-1", display_name="Test"
        )
        mock_repo.find_by_candidate_id.return_value = existing
        mock_repo.update.return_value = CandidateProfile(
            candidate_id="user-1",
            display_name="Test",
            cv_filename="resume.pdf",
            cv_storage_path="/uploads/abc.pdf",
            cv_extracted_text="Extracted CV text",
        )

        result = await use_case.execute(
            UploadCVCommand(
                candidate_id="user-1",
                filename="resume.pdf",
                content=b"fake pdf content",
            )
        )

        assert result.cv_filename == "resume.pdf"
        mock_storage.save.assert_called_once()
        mock_repo.update.assert_called_once()

    async def test_upload_replaces_old_cv(self, use_case, mock_repo, mock_storage):
        existing = CandidateProfile(
            candidate_id="user-1",
            display_name="Test",
            cv_storage_path="/uploads/old.pdf",
        )
        mock_repo.find_by_candidate_id.return_value = existing
        mock_repo.update.return_value = existing

        await use_case.execute(
            UploadCVCommand(
                candidate_id="user-1",
                filename="new.pdf",
                content=b"new content",
            )
        )

        mock_storage.delete.assert_called_once_with("/uploads/old.pdf")

    async def test_upload_rejects_invalid_type(self, use_case, mock_repo):
        with pytest.raises(InvalidFileTypeError):
            await use_case.execute(
                UploadCVCommand(
                    candidate_id="user-1",
                    filename="resume.exe",
                    content=b"bad",
                )
            )

    async def test_upload_rejects_too_large(self, use_case, mock_repo):
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        with pytest.raises(FileTooLargeError):
            await use_case.execute(
                UploadCVCommand(
                    candidate_id="user-1",
                    filename="big.pdf",
                    content=large_content,
                )
            )

    async def test_upload_requires_existing_profile(self, use_case, mock_repo):
        mock_repo.find_by_candidate_id.return_value = None
        with pytest.raises(ProfileNotFoundError):
            await use_case.execute(
                UploadCVCommand(
                    candidate_id="user-1",
                    filename="resume.pdf",
                    content=b"content",
                )
            )

    async def test_upload_docx_accepted(self, use_case, mock_repo):
        existing = CandidateProfile(
            candidate_id="user-1", display_name="Test"
        )
        mock_repo.find_by_candidate_id.return_value = existing
        mock_repo.update.return_value = existing

        await use_case.execute(
            UploadCVCommand(
                candidate_id="user-1",
                filename="resume.docx",
                content=b"docx content",
            )
        )
        # No exception = success

    async def test_upload_markdown_accepted(self, use_case, mock_repo):
        existing = CandidateProfile(
            candidate_id="user-1", display_name="Test"
        )
        mock_repo.find_by_candidate_id.return_value = existing
        mock_repo.update.return_value = existing

        await use_case.execute(
            UploadCVCommand(
                candidate_id="user-1",
                filename="cv.md",
                content=b"# My CV",
            )
        )
