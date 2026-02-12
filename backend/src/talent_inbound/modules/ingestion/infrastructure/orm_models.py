"""SQLAlchemy ORM model for the Interaction entity."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from talent_inbound.modules.ingestion.domain.entities import Interaction
from talent_inbound.shared.infrastructure.database import Base


class InteractionModel(Base):
    """interactions table — maps to the Interaction domain entity."""

    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    opportunity_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("opportunities.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    sanitized_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    interaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="INITIAL"
    )
    processing_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )
    classification: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    pipeline_log: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_domain(self) -> Interaction:
        """Convert ORM model to domain entity."""
        return Interaction(
            id=self.id,
            candidate_id=self.candidate_id,
            opportunity_id=self.opportunity_id,
            raw_content=self.raw_content,
            sanitized_content=self.sanitized_content,
            source=self.source,
            interaction_type=self.interaction_type,
            processing_status=self.processing_status,
            classification=self.classification,
            pipeline_log=self.pipeline_log or [],
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(interaction: Interaction) -> "InteractionModel":
        """Create ORM model from domain entity."""
        return InteractionModel(
            id=interaction.id,
            candidate_id=interaction.candidate_id,
            opportunity_id=interaction.opportunity_id,
            raw_content=interaction.raw_content,
            sanitized_content=interaction.sanitized_content,
            source=interaction.source.value,
            interaction_type=interaction.interaction_type.value,
            processing_status=interaction.processing_status.value,
            classification=(
                interaction.classification.value if interaction.classification else None
            ),
            content_hash=interaction.content_hash,
            pipeline_log=interaction.pipeline_log,
            created_at=interaction.created_at,
            updated_at=interaction.updated_at,
        )
