"""Shared application interfaces (protocols)."""

from typing import Protocol

from talent_inbound.shared.domain.events import DomainEvent


class EventBus(Protocol):
    """Protocol for event bus implementations."""

    async def publish(self, event: DomainEvent) -> None: ...

    async def publish_all(self, events: list[DomainEvent]) -> None: ...
