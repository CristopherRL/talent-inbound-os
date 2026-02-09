"""Base use case protocol."""

from typing import Any, Protocol


class UseCase(Protocol):
    """Protocol for all use cases (commands and queries)."""

    async def execute(self, *args: Any, **kwargs: Any) -> Any: ...
