"""SQLAlchemy ORM model for the CandidateProfile entity."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.shared.infrastructure.database import Base


class CandidateProfileModel(Base):
    """candidate_profiles table — maps to the CandidateProfile domain entity."""

    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    professional_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    min_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    work_model: Mapped[str | None] = mapped_column(String(20), nullable=True)
    preferred_locations: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    industries: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    cv_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cv_storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cv_extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    ghosting_days: Mapped[int] = mapped_column(Integer, nullable=False, default=14)
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

    def to_domain(self) -> CandidateProfile:
        """Convert ORM model to domain entity."""
        return CandidateProfile(
            id=self.id,
            candidate_id=self.candidate_id,
            display_name=self.display_name,
            professional_title=self.professional_title,
            skills=self.skills or [],
            min_salary=self.min_salary,
            preferred_currency=self.preferred_currency,
            work_model=self.work_model,
            preferred_locations=self.preferred_locations or [],
            industries=self.industries or [],
            cv_filename=self.cv_filename,
            cv_storage_path=self.cv_storage_path,
            cv_extracted_text=self.cv_extracted_text,
            follow_up_days=self.follow_up_days,
            ghosting_days=self.ghosting_days,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_domain(profile: CandidateProfile) -> "CandidateProfileModel":
        """Create ORM model from domain entity."""
        return CandidateProfileModel(
            id=profile.id,
            candidate_id=profile.candidate_id,
            display_name=profile.display_name,
            professional_title=profile.professional_title,
            skills=profile.skills,
            min_salary=profile.min_salary,
            preferred_currency=profile.preferred_currency,
            work_model=profile.work_model.value if profile.work_model else None,
            preferred_locations=profile.preferred_locations,
            industries=profile.industries,
            cv_filename=profile.cv_filename,
            cv_storage_path=profile.cv_storage_path,
            cv_extracted_text=profile.cv_extracted_text,
            follow_up_days=profile.follow_up_days,
            ghosting_days=profile.ghosting_days,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
