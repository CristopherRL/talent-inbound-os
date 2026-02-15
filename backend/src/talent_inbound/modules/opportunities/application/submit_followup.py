"""SubmitFollowUp use case — adds a recruiter follow-up message to an existing
opportunity and transitions it back to ANALYZING for re-evaluation."""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.ingestion.infrastructure.orm_models import InteractionModel
from talent_inbound.modules.opportunities.infrastructure.orm_models import (
    OpportunityModel,
    StatusTransitionModel,
)
from talent_inbound.shared.domain.enums import (
    InteractionType,
    OpportunityStatus,
    ProcessingStatus,
    TERMINAL_STATUSES,
    TransitionTrigger,
)
from talent_inbound.shared.infrastructure.database import get_current_session


class SubmitFollowUp:
    """Create a FOLLOW_UP interaction and transition the opportunity back to ANALYZING."""

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

        current_status = OpportunityStatus(opp.status)
        if current_status in TERMINAL_STATUSES:
            raise ValueError(
                f"Cannot add follow-up to an opportunity in terminal status: {opp.status}"
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

        # Transition to ANALYZING
        from_status = opp.status
        opp.status = OpportunityStatus.ANALYZING.value
        opp.last_interaction_at = now

        transition = StatusTransitionModel(
            id=str(uuid.uuid4()),
            opportunity_id=opportunity_id,
            from_status=from_status,
            to_status=OpportunityStatus.ANALYZING.value,
            triggered_by=TransitionTrigger.SYSTEM.value,
            is_unusual=False,
            note="Follow-up message received",
            created_at=now,
            updated_at=now,
        )
        session.add(transition)

        await session.flush()

        return {
            "interaction_id": interaction.id,
            "opportunity_id": opportunity_id,
        }
