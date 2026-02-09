"""Domain event base class."""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
