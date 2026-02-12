"""UploadCV use case — validate, store, and parse CV file."""

from dataclasses import dataclass
from pathlib import Path

from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.modules.profile.domain.exceptions import (
    FileTooLargeError,
    InvalidFileTypeError,
    ProfileNotFoundError,
)
from talent_inbound.modules.profile.domain.repositories import ProfileRepository
from talent_inbound.modules.profile.infrastructure.cv_parser import CVParser
from talent_inbound.modules.profile.infrastructure.storage import StorageBackend

MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".md"}


@dataclass
class UploadCVCommand:
    candidate_id: str
    filename: str
    content: bytes


class UploadCV:
    """Validates file, saves via StorageBackend, extracts text, updates profile."""

    def __init__(
        self,
        profile_repo: ProfileRepository,
        storage_backend: StorageBackend,
        cv_parser: CVParser,
    ) -> None:
        self._profile_repo = profile_repo
        self._storage = storage_backend
        self._cv_parser = cv_parser

    async def execute(self, command: UploadCVCommand) -> CandidateProfile:
        # Validate file type
        ext = Path(command.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError(command.filename)

        # Validate file size
        size_mb = len(command.content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise FileTooLargeError(size_mb, MAX_FILE_SIZE_MB)

        # Find existing profile
        profile = await self._profile_repo.find_by_candidate_id(command.candidate_id)
        if not profile:
            raise ProfileNotFoundError(command.candidate_id)

        # Delete old CV if exists
        if profile.cv_storage_path:
            try:
                await self._storage.delete(profile.cv_storage_path)
            except FileNotFoundError:
                pass

        # Save new file
        storage_path = await self._storage.save(command.content, command.filename)

        # Extract text
        extracted_text = self._cv_parser.extract_text_from_bytes(
            command.content, command.filename
        )

        # Update profile
        profile.cv_filename = command.filename
        profile.cv_storage_path = storage_path
        profile.cv_extracted_text = extracted_text
        profile.touch()

        return await self._profile_repo.update(profile)
