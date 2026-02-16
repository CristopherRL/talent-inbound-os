"""SubmitFollowUp use case — adds a recruiter follow-up message to an existing
opportunity. No stage change — the pipeline's stage detector will suggest one."""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.ingestion.infrastructure.orm_models import InteractionModel
from talent_inbound.modules.opportunities.infrastructure.orm_models import (
    OpportunityModel,
)
from talent_inbound.shared.domain.enums import (
    InteractionType,
    OpportunityStage,
    ProcessingStatus,
    TERMINAL_STAGES,
)
from talent_inbound.shared.infrastructure.database import get_current_session


class SubmitFollowUp:
    """Create a FOLLOW_UP interaction for an existing opportunity."""

    async def execute(
        self,
        opportunity_id: str,
        candidate_id: str,
        raw_content: str,
        source: str,
    ) -> dict:
        session: AsyncSession = get_current_session()

        # Load opportunity
        opp_stmt = select(OpportunityModel).where(
            OpportunityModel.id == opportunity_id,
        )
        result = await session.execute(opp_stmt)
        opp = result.scalar_one_or_none()

        if opp is None:
            raise ValueError("Opportunity not found")
        if opp.candidate_id != candidate_id:
            raise ValueError("Opportunity not found")
        if opp.is_archived:
            raise ValueError("Cannot add follow-up to an archived opportunity")

        current_stage = OpportunityStage(opp.stage)
        if current_stage in TERMINAL_STAGES:
            raise ValueError(
                f"Cannot add follow-up to an opportunity in terminal stage: {opp.stage}"
            )

        now = datetime.now(timezone.utc)

        # Create FOLLOW_UP interaction
        content_hash = hashlib.sha256(
            f"{raw_content}|{source}".encode("utf-8")
        ).hexdigest()

        interaction = InteractionModel(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            opportunity_id=opportunity_id,
            raw_content=raw_content,
            source=source,
            interaction_type=InteractionType.FOLLOW_UP.value,
            processing_status=ProcessingStatus.PENDING.value,
            content_hash=content_hash,
            created_at=now,
            updated_at=now,
        )
        session.add(interaction)

        # Update last_interaction_at (no stage change — pipeline handles that)
        opp.last_interaction_at = now

        await session.flush()

        return {
            "interaction_id": interaction.id,
            "opportunity_id": opportunity_id,
        }
