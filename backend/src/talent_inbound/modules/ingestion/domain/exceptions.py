"""Domain exceptions for the ingestion module."""


class EmptyContentError(Exception):
    """Raised when raw_content is empty or whitespace-only."""

    def __init__(self) -> None:
        super().__init__("Message content cannot be empty.")


class ContentTooLongError(Exception):
    """Raised when raw_content exceeds the maximum length."""

    def __init__(self, length: int, max_length: int = 50000) -> None:
        self.length = length
        self.max_length = max_length
        super().__init__(
            f"Message content is {length} characters, exceeding the {max_length} limit."
        )


class DuplicateInteractionError(Exception):
    """Raised when a duplicate message is detected."""

    def __init__(self, existing_opportunity_id: str) -> None:
        self.existing_opportunity_id = existing_opportunity_id
        super().__init__(
            f"Duplicate message detected. Existing opportunity: {existing_opportunity_id}"
        )
