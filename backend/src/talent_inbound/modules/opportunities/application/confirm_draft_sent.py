"""ConfirmDraftSent use case — marks a final draft as sent and creates
a CANDIDATE_RESPONSE interaction to record it in the timeline."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.ingestion.infrastructure.orm_models import InteractionModel
from talent_inbound.modules.opportunities.infrastructure.orm_models import (
    DraftResponseModel,
    OpportunityModel,
)
from talent_inbound.shared.domain.enums import (
    InteractionType,
    ProcessingStatus,
)
from talent_inbound.shared.infrastructure.database import get_current_session


class ConfirmDraftSent:
    """Mark a finalized draft as sent and record it as a CANDIDATE_RESPONSE interaction."""

    async def execute(
        self,
        opportunity_id: str,
        draft_id: str,
        candidate_id: str,
    ) -> dict:
        session: AsyncSession = get_current_session()

        # Load draft
        stmt = select(DraftResponseModel).where(
            DraftResponseModel.id == draft_id,
            DraftResponseModel.opportunity_id == opportunity_id,
        )
        result = await session.execute(stmt)
        draft = result.scalar_one_or_none()

        if draft is None:
            raise ValueError("Draft not found")
        if not draft.is_final:
            raise ValueError("Draft must be marked as final before confirming sent")
        if draft.is_sent:
            raise ValueError("Draft has already been confirmed as sent")

        # Mark draft as sent
        now = datetime.now(timezone.utc)
        draft.is_sent = True
        draft.sent_at = now

        # Create CANDIDATE_RESPONSE interaction
        import uuid
        import hashlib

        sent_text = draft.edited_content or draft.generated_content
        content_hash = hashlib.sha256(
            f"{sent_text}|CANDIDATE_RESPONSE".encode("utf-8")
        ).hexdigest()

        interaction = InteractionModel(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            opportunity_id=opportunity_id,
            raw_content=sent_text,
            source="OTHER",
            interaction_type=InteractionType.CANDIDATE_RESPONSE.value,
            processing_status=ProcessingStatus.COMPLETED.value,
            content_hash=content_hash,
            created_at=now,
            updated_at=now,
        )
        session.add(interaction)

        # Update opportunity.last_interaction_at
        opp_stmt = select(OpportunityModel).where(
            OpportunityModel.id == opportunity_id
        )
        opp_result = await session.execute(opp_stmt)
        opp = opp_result.scalar_one_or_none()
        if opp:
            opp.last_interaction_at = now

        await session.flush()

        return {
            "draft_id": draft_id,
            "interaction_id": interaction.id,
        }
