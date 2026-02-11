"""User domain entity for the auth module."""

from talent_inbound.shared.domain.base_entity import AggregateRoot
from talent_inbound.shared.domain.value_objects import Email


class User(AggregateRoot):
    """Authenticated user (Candidate). Root identity for all data."""

    email: Email
    hashed_password: str
    is_active: bool = True
