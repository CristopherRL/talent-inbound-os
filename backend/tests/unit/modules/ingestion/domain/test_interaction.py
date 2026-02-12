"""Unit tests for Interaction domain entity and duplicate detection."""

import pytest

from talent_inbound.modules.ingestion.domain.entities import Interaction
from talent_inbound.modules.ingestion.domain.exceptions import (
    ContentTooLongError,
    DuplicateInteractionError,
    EmptyContentError,
)
from talent_inbound.shared.domain.enums import (
    Classification,
    InteractionSource,
    InteractionType,
    ProcessingStatus,
)


class TestInteractionEntity:
    """Tests for the Interaction Pydantic domain entity."""

    def test_create_interaction_with_required_fields(self):
        interaction = Interaction(
            candidate_id="user-123",
            raw_content="Hi, I have a Senior Backend role...",
            source=InteractionSource.LINKEDIN,
        )
        assert interaction.candidate_id == "user-123"
        assert interaction.raw_content == "Hi, I have a Senior Backend role..."
        assert interaction.source == InteractionSource.LINKEDIN
        assert interaction.interaction_type == InteractionType.INITIAL
        assert interaction.processing_status == ProcessingStatus.PENDING
        assert interaction.id  # Auto-generated UUID
        assert interaction.created_at is not None

    def test_default_values(self):
        interaction = Interaction(
            candidate_id="user-123",
            raw_content="Some content",
            source=InteractionSource.EMAIL,
        )
        assert interaction.opportunity_id is None
        assert interaction.sanitized_content is None
        assert interaction.classification is None
        assert interaction.pipeline_log == []

    def test_content_hash_deterministic(self):
        i1 = Interaction(
            candidate_id="u1",
            raw_content="Hello recruiter",
            source=InteractionSource.LINKEDIN,
        )
        i2 = Interaction(
            candidate_id="u2",
            raw_content="Hello recruiter",
            source=InteractionSource.LINKEDIN,
        )
        assert i1.content_hash == i2.content_hash

    def test_content_hash_differs_by_source(self):
        i1 = Interaction(
            candidate_id="u1",
            raw_content="Hello recruiter",
            source=InteractionSource.LINKEDIN,
        )
        i2 = Interaction(
            candidate_id="u1",
            raw_content="Hello recruiter",
            source=InteractionSource.EMAIL,
        )
        assert i1.content_hash != i2.content_hash

    def test_content_hash_differs_by_content(self):
        i1 = Interaction(
            candidate_id="u1",
            raw_content="Message A",
            source=InteractionSource.LINKEDIN,
        )
        i2 = Interaction(
            candidate_id="u1",
            raw_content="Message B",
            source=InteractionSource.LINKEDIN,
        )
        assert i1.content_hash != i2.content_hash

    def test_mark_processing(self):
        interaction = Interaction(
            candidate_id="u1",
            raw_content="Content",
            source=InteractionSource.EMAIL,
        )
        interaction.mark_processing()
        assert interaction.processing_status == ProcessingStatus.PROCESSING

    def test_mark_completed(self):
        interaction = Interaction(
            candidate_id="u1",
            raw_content="Content",
            source=InteractionSource.EMAIL,
        )
        interaction.mark_completed(Classification.REAL_OFFER)
        assert interaction.processing_status == ProcessingStatus.COMPLETED
        assert interaction.classification == Classification.REAL_OFFER

    def test_mark_failed(self):
        interaction = Interaction(
            candidate_id="u1",
            raw_content="Content",
            source=InteractionSource.EMAIL,
        )
        interaction.mark_failed()
        assert interaction.processing_status == ProcessingStatus.FAILED

    def test_follow_up_type(self):
        interaction = Interaction(
            candidate_id="u1",
            raw_content="Follow-up message",
            source=InteractionSource.CHAT_FOLLOWUP,
            interaction_type=InteractionType.FOLLOW_UP,
            opportunity_id="opp-123",
        )
        assert interaction.interaction_type == InteractionType.FOLLOW_UP
        assert interaction.opportunity_id == "opp-123"


class TestIngestionExceptions:
    """Tests for ingestion domain exceptions."""

    def test_empty_content_error(self):
        err = EmptyContentError()
        assert "empty" in str(err).lower()

    def test_content_too_long_error(self):
        err = ContentTooLongError(60000, 50000)
        assert "60000" in str(err)
        assert err.length == 60000
        assert err.max_length == 50000

    def test_duplicate_interaction_error(self):
        err = DuplicateInteractionError("opp-456")
        assert "opp-456" in str(err)
        assert err.existing_opportunity_id == "opp-456"
