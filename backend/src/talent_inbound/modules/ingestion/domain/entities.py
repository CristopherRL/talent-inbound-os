"""Interaction domain entity for the ingestion module."""

import hashlib

from talent_inbound.shared.domain.base_entity import Entity
from talent_inbound.shared.domain.enums import (
    Classification,
    InteractionSource,
    InteractionType,
    ProcessingStatus,
)


class Interaction(Entity):
    """A raw ingested message or follow-up. Multiple Interactions per Opportunity."""

    candidate_id: str
    opportunity_id: str | None = None
    raw_content: str
    sanitized_content: str | None = None
    source: InteractionSource
    interaction_type: InteractionType = InteractionType.INITIAL
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    classification: Classification | None = None
    pipeline_log: list[dict] = []

    @property
    def content_hash(self) -> str:
        """SHA-256 hash of raw_content + source for duplicate detection."""
        payload = f"{self.raw_content}|{self.source.value}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def mark_processing(self) -> None:
        self.processing_status = ProcessingStatus.PROCESSING
        self.touch()

    def mark_completed(self, classification: Classification) -> None:
        self.processing_status = ProcessingStatus.COMPLETED
        self.classification = classification
        self.touch()

    def mark_failed(self) -> None:
        self.processing_status = ProcessingStatus.FAILED
        self.touch()
