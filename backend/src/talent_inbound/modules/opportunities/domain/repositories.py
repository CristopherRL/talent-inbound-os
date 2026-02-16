"""Opportunity repository abstract base class."""

from abc import ABC, abstractmethod
from datetime import datetime

from talent_inbound.modules.opportunities.domain.entities import (
    Opportunity,
    StageTransition,
)


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
        self,
        candidate_id: str,
        archived_filter: str | None = None,
        stage_filter: str | None = None,
    ) -> list[Opportunity]:
        """List opportunities for a candidate.

        archived_filter:
            None (default) → non-archived only
            "only" → archived only
            "all" → everything
        """

    @abstractmethod
    async def update(self, opportunity: Opportunity) -> Opportunity:
        """Update an existing opportunity."""

    @abstractmethod
    async def save_transition(self, transition: StageTransition) -> StageTransition:
        """Persist a stage transition audit record."""

    @abstractmethod
    async def list_transitions(self, opportunity_id: str) -> list[StageTransition]:
        """List all stage transitions for an opportunity, ordered by created_at."""

    @abstractmethod
    async def list_stale(
        self, candidate_id: str, before: datetime
    ) -> list[Opportunity]:
        """List non-archived opportunities with last_interaction_at before the given datetime."""
