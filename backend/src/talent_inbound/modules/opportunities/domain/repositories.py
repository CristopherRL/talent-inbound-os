"""Opportunity repository abstract base class."""

from abc import ABC, abstractmethod

from talent_inbound.modules.opportunities.domain.entities import Opportunity


class OpportunityRepository(ABC):
    """Port for Opportunity persistence."""

    @abstractmethod
    async def save(self, opportunity: Opportunity) -> Opportunity:
        """Persist a new opportunity."""

    @abstractmethod
    async def find_by_id(self, opportunity_id: str) -> Opportunity | None:
        """Find opportunity by ID."""

    @abstractmethod
    async def list_by_candidate(
        self, candidate_id: str, include_archived: bool = False
    ) -> list[Opportunity]:
        """List opportunities for a candidate, optionally including archived."""

    @abstractmethod
    async def update(self, opportunity: Opportunity) -> Opportunity:
        """Update an existing opportunity."""
