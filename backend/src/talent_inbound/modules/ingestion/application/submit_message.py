"""SubmitMessage use case — validates and creates an Interaction + Opportunity."""

from dataclasses import dataclass

from talent_inbound.modules.ingestion.domain.entities import Interaction
from talent_inbound.modules.ingestion.domain.events import InteractionCreated
from talent_inbound.modules.ingestion.domain.exceptions import (
    ContentTooLongError,
    DuplicateInteractionError,
    EmptyContentError,
)
from talent_inbound.modules.ingestion.domain.repositories import InteractionRepository
from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.shared.domain.enums import (
    InteractionSource,
    OpportunityStage,
    TransitionTrigger,
)
from talent_inbound.shared.infrastructure.event_bus import InProcessEventBus


@dataclass
class SubmitMessageCommand:
    candidate_id: str
    raw_content: str
    source: str  # Will be converted to InteractionSource enum


@dataclass
class SubmitMessageResult:
    interaction: Interaction
    opportunity: Opportunity


class SubmitMessage:
    """Validates input, checks duplicates, creates Interaction + Opportunity,
    publishes InteractionCreated event."""

    def __init__(
        self,
        interaction_repo: InteractionRepository,
        opportunity_repo: OpportunityRepository,
        event_bus: InProcessEventBus,
        max_message_length: int,
    ) -> None:
        self._interaction_repo = interaction_repo
        self._opportunity_repo = opportunity_repo
        self._event_bus = event_bus
        self._max_message_length = max_message_length

    async def execute(self, command: SubmitMessageCommand) -> SubmitMessageResult:
        # Validate content
        stripped = command.raw_content.strip()
        if not stripped:
            raise EmptyContentError()
        if len(stripped) > self._max_message_length:
            raise ContentTooLongError(len(stripped), self._max_message_length)

        source = InteractionSource(command.source)

        # Build a temporary interaction to compute the content hash
        interaction = Interaction(
            candidate_id=command.candidate_id,
            raw_content=stripped,
            source=source,
        )

        # Phase 1: Exact hash check (fast path — catches identical copy-pastes)
        existing = await self._interaction_repo.find_duplicate(
            interaction.content_hash, command.candidate_id
        )
        if existing and existing.opportunity_id:
            raise DuplicateInteractionError(existing.opportunity_id)

        # Phase 2: Field-based check (catches near-duplicates — same offer, different wording)
        similar_id = await self._find_field_based_duplicate(stripped, command.candidate_id)
        if similar_id:
            raise DuplicateInteractionError(similar_id)

        # Create the Opportunity (starts in DISCOVERY stage)
        opportunity = Opportunity(candidate_id=command.candidate_id)
        opportunity.change_stage(
            OpportunityStage.DISCOVERY,
            triggered_by=TransitionTrigger.SYSTEM,
            note="Auto-created from submitted message",
        )
        saved_opportunity = await self._opportunity_repo.save(opportunity)

        # Link interaction to opportunity and save
        interaction.opportunity_id = saved_opportunity.id
        saved_interaction = await self._interaction_repo.save(interaction)

        # Publish domain event
        event = InteractionCreated(
            interaction_id=saved_interaction.id,
            opportunity_id=saved_opportunity.id,
            candidate_id=command.candidate_id,
        )
        await self._event_bus.publish(event)

        return SubmitMessageResult(
            interaction=saved_interaction,
            opportunity=saved_opportunity,
        )

    async def _find_field_based_duplicate(
        self, raw_content: str, candidate_id: str
    ) -> str | None:
        """Detect near-duplicate offers by comparing extracted fields from existing
        opportunities against the new raw content.

        Matches when company_name AND role_title from a previous opportunity both
        appear in the new message (case-insensitive). This catches the same offer
        pasted again with minor wording changes that would defeat the hash check.
        """
        content_lower = raw_content.lower()
        existing = await self._opportunity_repo.list_by_candidate(candidate_id)

        for opp in existing:
            company = (opp.company_name or "").strip().lower()
            role = (opp.role_title or "").strip().lower()

            # Skip if we don't have extracted data yet (pipeline may not have run)
            if not company or not role:
                continue

            company_match = company in content_lower
            role_match = role in content_lower

            if company_match and role_match:
                return opp.id

        return None
