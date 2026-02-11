"""Auth domain events."""

from talent_inbound.shared.domain.events import DomainEvent


class UserRegistered(DomainEvent):
    """Published when a new user account is created."""

    user_id: str
    email: str
