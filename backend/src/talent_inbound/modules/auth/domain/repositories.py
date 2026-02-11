"""User repository abstract base class."""

from abc import ABC, abstractmethod

from talent_inbound.modules.auth.domain.entities import User


class UserRepository(ABC):
    """Port for User persistence. Infrastructure provides the adapter."""

    @abstractmethod
    async def save(self, user: User) -> User:
        """Persist a new user."""

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Find a user by email. Returns None if not found."""

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None:
        """Find a user by ID. Returns None if not found."""
