"""In-process event bus for domain event publishing."""

from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from talent_inbound.shared.domain.events import DomainEvent

EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class InProcessEventBus:
    """Simple in-process async event bus. Sufficient for single-process MVP."""

    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers[type(event)]:
            await handler(event)

    async def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.publish(event)
