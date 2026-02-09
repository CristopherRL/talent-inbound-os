"""Base domain entities for the Talent Inbound OS shared kernel."""

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Entity(BaseModel):
    """Base entity with identity and timestamps."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def touch(self) -> None:
        self.updated_at = _utcnow()


class AggregateRoot(Entity):
    """Base aggregate root. Collects domain events for publishing."""

    _events: list = []

    def model_post_init(self, __context: object) -> None:
        self._events = []

    def add_event(self, event: object) -> None:
        self._events.append(event)

    def collect_events(self) -> list:
        events = list(self._events)
        self._events.clear()
        return events
