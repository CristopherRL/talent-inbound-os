"""Unit tests for the SubmitMessage use case."""

from unittest.mock import AsyncMock

import pytest

from talent_inbound.modules.ingestion.application.submit_message import (
    SubmitMessage,
    SubmitMessageCommand,
)
from talent_inbound.modules.ingestion.domain.entities import Interaction
from talent_inbound.modules.ingestion.domain.exceptions import (
    ContentTooLongError,
    DuplicateInteractionError,
    EmptyContentError,
)
from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.shared.domain.enums import (
    InteractionSource,
    OpportunityStatus,
    ProcessingStatus,
)


class TestSubmitMessage:
    """Tests for the SubmitMessage use case."""

    @pytest.fixture
    def mock_interaction_repo(self):
        repo = AsyncMock()
        repo.find_duplicate.return_value = None
        return repo

    @pytest.fixture
    def mock_opportunity_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_event_bus(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_interaction_repo, mock_opportunity_repo, mock_event_bus):
        return SubmitMessage(
            interaction_repo=mock_interaction_repo,
            opportunity_repo=mock_opportunity_repo,
            event_bus=mock_event_bus,
            max_message_length=50000,
        )

    async def test_submit_creates_interaction_and_opportunity(
        self, use_case, mock_interaction_repo, mock_opportunity_repo
    ):
        mock_interaction_repo.save.side_effect = lambda i: i
        mock_opportunity_repo.save.side_effect = lambda o: o

        result = await use_case.execute(
            SubmitMessageCommand(
                candidate_id="user-1",
                raw_content="Hi, I have a Senior Backend role at Acme Corp...",
                source="LINKEDIN",
            )
        )

        assert result.interaction.candidate_id == "user-1"
        assert result.interaction.source == InteractionSource.LINKEDIN
        assert result.interaction.processing_status == ProcessingStatus.PENDING
        assert result.opportunity.candidate_id == "user-1"
        assert result.opportunity.status == OpportunityStatus.ANALYZING
        mock_interaction_repo.save.assert_called_once()
        mock_opportunity_repo.save.assert_called_once()

    async def test_submit_links_interaction_to_opportunity(
        self, use_case, mock_interaction_repo, mock_opportunity_repo
    ):
        mock_interaction_repo.save.side_effect = lambda i: i
        mock_opportunity_repo.save.side_effect = lambda o: o

        result = await use_case.execute(
            SubmitMessageCommand(
                candidate_id="user-1",
                raw_content="Job offer message",
                source="EMAIL",
            )
        )

        assert result.interaction.opportunity_id == result.opportunity.id

    async def test_submit_publishes_interaction_created_event(
        self, use_case, mock_interaction_repo, mock_opportunity_repo, mock_event_bus
    ):
        mock_interaction_repo.save.side_effect = lambda i: i
        mock_opportunity_repo.save.side_effect = lambda o: o

        await use_case.execute(
            SubmitMessageCommand(
                candidate_id="user-1",
                raw_content="Message content",
                source="LINKEDIN",
            )
        )

        mock_event_bus.publish.assert_called_once()

    async def test_submit_rejects_empty_content(self, use_case):
        with pytest.raises(EmptyContentError):
            await use_case.execute(
                SubmitMessageCommand(
                    candidate_id="user-1",
                    raw_content="   ",
                    source="LINKEDIN",
                )
            )

    async def test_submit_rejects_too_long_content(self, use_case):
        with pytest.raises(ContentTooLongError):
            await use_case.execute(
                SubmitMessageCommand(
                    candidate_id="user-1",
                    raw_content="x" * 50001,
                    source="LINKEDIN",
                )
            )

    async def test_submit_detects_duplicates(
        self, use_case, mock_interaction_repo
    ):
        existing = Interaction(
            candidate_id="user-1",
            raw_content="Duplicate message",
            source=InteractionSource.LINKEDIN,
            opportunity_id="existing-opp",
        )
        mock_interaction_repo.find_duplicate.return_value = existing

        with pytest.raises(DuplicateInteractionError) as exc_info:
            await use_case.execute(
                SubmitMessageCommand(
                    candidate_id="user-1",
                    raw_content="Duplicate message",
                    source="LINKEDIN",
                )
            )
        assert exc_info.value.existing_opportunity_id == "existing-opp"

    async def test_submit_with_all_sources(
        self, use_case, mock_interaction_repo, mock_opportunity_repo
    ):
        mock_interaction_repo.save.side_effect = lambda i: i
        mock_opportunity_repo.save.side_effect = lambda o: o

        for source in ["LINKEDIN", "EMAIL", "FREELANCE_PLATFORM", "OTHER"]:
            result = await use_case.execute(
                SubmitMessageCommand(
                    candidate_id="user-1",
                    raw_content=f"Message from {source}",
                    source=source,
                )
            )
            assert result.interaction.source == InteractionSource(source)
            # Reset mocks for next iteration
            mock_interaction_repo.reset_mock()
            mock_opportunity_repo.reset_mock()
            mock_interaction_repo.find_duplicate.return_value = None
            mock_interaction_repo.save.side_effect = lambda i: i
            mock_opportunity_repo.save.side_effect = lambda o: o
