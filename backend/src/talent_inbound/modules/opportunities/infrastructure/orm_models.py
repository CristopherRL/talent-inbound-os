"""SQLAlchemy ORM models for Opportunity and StatusTransition entities."""

import uuid
from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from talent_inbound.modules.opportunities.domain.entities import (
    Opportunity,
    StatusTransition,
)
from talent_inbound.shared.infrastructure.database import Base


class OpportunityModel(Base):
    """opportunities table — maps to the Opportunity domain entity."""

    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tech_stack: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    work_model: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recruiter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recruiter_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    recruiter_company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    match_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    match_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    missing_fields: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="NEW", index=True
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    last_interaction_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
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

    def to_domain(self) -> Opportunity:
        """Convert ORM model to domain entity."""
        return Opportunity(
            id=self.id,
            candidate_id=self.candidate_id,
            company_name=self.company_name,
            client_name=self.client_name,
            role_title=self.role_title,
            salary_range=self.salary_range,
            tech_stack=self.tech_stack or [],
            work_model=self.work_model,
            recruiter_name=self.recruiter_name,
            recruiter_type=self.recruiter_type,
            recruiter_company=self.recruiter_company,
            match_score=self.match_score,
            match_reasoning=self.match_reasoning,
            missing_fields=self.missing_fields or [],
            status=self.status,
            is_archived=self.is_archived,
            last_interaction_at=self.last_interaction_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(opportunity: Opportunity) -> "OpportunityModel":
        """Create ORM model from domain entity."""
        return OpportunityModel(
            id=opportunity.id,
            candidate_id=opportunity.candidate_id,
            company_name=opportunity.company_name,
            client_name=opportunity.client_name,
            role_title=opportunity.role_title,
            salary_range=opportunity.salary_range,
            tech_stack=opportunity.tech_stack,
            work_model=(
                opportunity.work_model.value
                if isinstance(opportunity.work_model, StrEnum)
                else opportunity.work_model
            ),
            recruiter_name=opportunity.recruiter_name,
            recruiter_type=(
                opportunity.recruiter_type.value
                if isinstance(opportunity.recruiter_type, StrEnum)
                else opportunity.recruiter_type
            ),
            recruiter_company=opportunity.recruiter_company,
            match_score=opportunity.match_score,
            match_reasoning=opportunity.match_reasoning,
            missing_fields=opportunity.missing_fields,
            status=(
                opportunity.status.value
                if isinstance(opportunity.status, StrEnum)
                else opportunity.status
            ),
            is_archived=opportunity.is_archived,
            last_interaction_at=opportunity.last_interaction_at,
            created_at=opportunity.created_at,
            updated_at=opportunity.updated_at,
        )


class StatusTransitionModel(Base):
    """status_transitions table — audit log for opportunity status changes."""

    __tablename__ = "status_transitions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    opportunity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("opportunities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str] = mapped_column(String(30), nullable=False)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    triggered_by: Mapped[str] = mapped_column(String(20), nullable=False)
    is_unusual: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
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

    def to_domain(self) -> StatusTransition:
        """Convert ORM model to domain entity."""
        return StatusTransition(
            id=self.id,
            opportunity_id=self.opportunity_id,
            from_status=self.from_status,
            to_status=self.to_status,
            triggered_by=self.triggered_by,
            is_unusual=self.is_unusual,
            note=self.note,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(transition: StatusTransition) -> "StatusTransitionModel":
        """Create ORM model from domain entity."""
        return StatusTransitionModel(
            id=transition.id,
            opportunity_id=transition.opportunity_id,
            from_status=transition.from_status.value,
            to_status=transition.to_status.value,
            triggered_by=transition.triggered_by.value,
            is_unusual=transition.is_unusual,
            note=transition.note,
            created_at=transition.created_at,
            updated_at=transition.updated_at,
        )
