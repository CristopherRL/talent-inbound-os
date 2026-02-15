"""EditDraft use case — update edited_content and optionally mark as final."""

from sqlalchemy import select

from talent_inbound.modules.opportunities.infrastructure.orm_models import (
    DraftResponseModel,
)
from talent_inbound.shared.infrastructure.database import get_current_session


class EditDraft:
    """Edit a draft response's content and/or mark it as final."""

    async def execute(
        self,
        opportunity_id: str,
        draft_id: str,
        edited_content: str | None = None,
        is_final: bool | None = None,
    ) -> dict:
        """Update draft and return updated fields.

        Raises:
            ValueError: If draft not found or doesn't belong to the opportunity.
        """
        session = get_current_session()

        stmt = select(DraftResponseModel).where(
            DraftResponseModel.id == draft_id,
            DraftResponseModel.opportunity_id == opportunity_id,
        )
        result = await session.execute(stmt)
        draft = result.scalar_one_or_none()

        if draft is None:
            raise ValueError("Draft not found")

        if edited_content is not None:
            draft.edited_content = edited_content
        if is_final is not None:
            draft.is_final = is_final

        await session.flush()
        await session.refresh(draft)

        return {
            "id": draft.id,
            "response_type": draft.response_type,
            "generated_content": draft.generated_content,
            "edited_content": draft.edited_content,
            "is_final": draft.is_final,
            "is_sent": draft.is_sent,
            "sent_at": draft.sent_at,
            "created_at": draft.created_at,
        }
