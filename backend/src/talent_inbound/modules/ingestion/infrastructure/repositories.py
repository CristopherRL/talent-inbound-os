"""SQLAlchemy implementation of the InteractionRepository."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from talent_inbound.modules.ingestion.domain.entities import Interaction
from talent_inbound.modules.ingestion.domain.repositories import InteractionRepository
from talent_inbound.modules.ingestion.infrastructure.orm_models import InteractionModel


class SqlAlchemyInteractionRepository(InteractionRepository):
    """Adapter: persists Interaction entities via SQLAlchemy async sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, interaction: Interaction) -> Interaction:
        model = InteractionModel.from_domain(interaction)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()

    async def find_by_id(self, interaction_id: str) -> Interaction | None:
        stmt = select(InteractionModel).where(InteractionModel.id == interaction_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def find_duplicate(self, content_hash: str) -> Interaction | None:
        stmt = select(InteractionModel).where(
            InteractionModel.content_hash == content_hash
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return model.to_domain() if model else None

    async def update(self, interaction: Interaction) -> Interaction:
        stmt = select(InteractionModel).where(
            InteractionModel.id == interaction.id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Interaction not found: {interaction.id}")

        model.opportunity_id = interaction.opportunity_id
        model.sanitized_content = interaction.sanitized_content
        model.processing_status = interaction.processing_status.value
        model.classification = (
            interaction.classification.value if interaction.classification else None
        )
        model.pipeline_log = interaction.pipeline_log
        await self._session.flush()
        await self._session.refresh(model)
        return model.to_domain()
