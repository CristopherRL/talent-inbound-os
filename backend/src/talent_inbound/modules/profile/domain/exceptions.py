"""Profile domain exceptions."""


class ProfileNotFoundError(Exception):
    """Raised when a profile is not found for the candidate."""

    def __init__(self, candidate_id: str) -> None:
        super().__init__(f"Profile not found for candidate {candidate_id}")
        self.candidate_id = candidate_id


class InvalidFileTypeError(Exception):
    """Raised when an uploaded file has an unsupported type."""

    def __init__(self, filename: str) -> None:
        super().__init__(f"Unsupported file type: {filename}. Allowed: PDF, DOCX, MD")
        self.filename = filename


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, size_mb: float, max_mb: int = 10) -> None:
        super().__init__(f"File size {size_mb:.1f}MB exceeds limit of {max_mb}MB")
        self.size_mb = size_mb
        self.max_mb = max_mb
