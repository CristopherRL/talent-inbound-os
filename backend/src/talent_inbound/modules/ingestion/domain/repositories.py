"""Interaction repository abstract base class."""

from abc import ABC, abstractmethod

from talent_inbound.modules.ingestion.domain.entities import Interaction


class InteractionRepository(ABC):
    """Port for Interaction persistence."""

    @abstractmethod
    async def save(self, interaction: Interaction) -> Interaction:
        """Persist a new interaction."""

    @abstractmethod
    async def find_by_id(self, interaction_id: str) -> Interaction | None:
        """Find interaction by ID."""

    @abstractmethod
    async def find_duplicate(self, content_hash: str) -> Interaction | None:
        """Find an existing interaction with the same content hash."""

    @abstractmethod
    async def update(self, interaction: Interaction) -> Interaction:
        """Update an existing interaction."""
