"""Unit tests for the User domain entity and password validation."""

import pytest
from pydantic import ValidationError

from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.events import UserRegistered
from talent_inbound.modules.auth.domain.exceptions import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
)


class TestUserEntity:
    """Tests for the User aggregate root."""

    def test_create_user_with_valid_data(self) -> None:
        user = User(email="test@example.com", hashed_password="hashed123")
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed123"
        assert user.is_active is True
        assert user.id  # UUID auto-generated
        assert user.created_at
        assert user.updated_at

    def test_create_user_default_active(self) -> None:
        user = User(email="active@example.com", hashed_password="hash")
        assert user.is_active is True

    def test_create_user_inactive(self) -> None:
        user = User(email="inactive@example.com", hashed_password="hash", is_active=False)
        assert user.is_active is False

    def test_user_invalid_email_rejected(self) -> None:
        with pytest.raises(ValidationError):
            User(email="not-an-email", hashed_password="hash")

    def test_user_empty_email_rejected(self) -> None:
        with pytest.raises(ValidationError):
            User(email="", hashed_password="hash")

    def test_user_touch_updates_timestamp(self) -> None:
        user = User(email="test@example.com", hashed_password="hash")
        original = user.updated_at
        user.touch()
        assert user.updated_at >= original

    def test_user_aggregate_root_events(self) -> None:
        user = User(email="test@example.com", hashed_password="hash")
        event = UserRegistered(user_id=user.id, email=user.email)
        user.add_event(event)
        collected = user.collect_events()
        assert len(collected) == 1
        assert isinstance(collected[0], UserRegistered)
        assert collected[0].email == "test@example.com"
        # Events should be cleared after collection
        assert len(user.collect_events()) == 0

    def test_user_from_attributes(self) -> None:
        """Test that from_attributes config works (needed for ORM mapping)."""
        user = User(email="orm@example.com", hashed_password="hash")
        data = user.model_dump()
        reconstructed = User.model_validate(data)
        assert reconstructed.email == user.email
        assert reconstructed.id == user.id


class TestAuthExceptions:
    """Tests for auth domain exceptions."""

    def test_duplicate_email_message(self) -> None:
        exc = DuplicateEmailError("test@example.com")
        assert "test@example.com" in str(exc)
        assert exc.email == "test@example.com"

    def test_invalid_credentials_generic_message(self) -> None:
        exc = InvalidCredentialsError()
        assert "email" in str(exc).lower() or "password" in str(exc).lower()

    def test_inactive_user_message(self) -> None:
        exc = InactiveUserError()
        assert "inactive" in str(exc).lower()
