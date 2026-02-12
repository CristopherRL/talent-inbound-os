"""Profile repository abstract base class."""

from abc import ABC, abstractmethod

from talent_inbound.modules.profile.domain.entities import CandidateProfile


class ProfileRepository(ABC):
    """Port for CandidateProfile persistence."""

    @abstractmethod
    async def save(self, profile: CandidateProfile) -> CandidateProfile:
        """Persist a new profile."""

    @abstractmethod
    async def find_by_candidate_id(self, candidate_id: str) -> CandidateProfile | None:
        """Find profile by candidate (user) ID. Returns None if not found."""

    @abstractmethod
    async def update(self, profile: CandidateProfile) -> CandidateProfile:
        """Update an existing profile."""
