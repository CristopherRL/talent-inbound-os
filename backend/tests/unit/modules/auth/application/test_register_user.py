"""Unit tests for the RegisterUser use case."""

from unittest.mock import AsyncMock

import pytest

from talent_inbound.modules.auth.application.register_user import (
    RegisterUser,
    RegisterUserCommand,
)
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.exceptions import DuplicateEmailError
from talent_inbound.modules.auth.infrastructure.password import BcryptPasswordHasher


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_email = AsyncMock(return_value=None)
    repo.save = AsyncMock(side_effect=lambda user: user)
    return repo


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    bus.publish_all = AsyncMock()
    return bus


@pytest.fixture
def password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


@pytest.fixture
def register_uc(
    mock_user_repo: AsyncMock,
    password_hasher: BcryptPasswordHasher,
    mock_event_bus: AsyncMock,
) -> RegisterUser:
    return RegisterUser(
        user_repo=mock_user_repo,
        password_hasher=password_hasher,
        event_bus=mock_event_bus,
    )


class TestRegisterUser:

    @pytest.mark.asyncio
    async def test_register_new_user_success(
        self, register_uc: RegisterUser, mock_user_repo: AsyncMock
    ) -> None:
        cmd = RegisterUserCommand(email="new@example.com", password="Str0ngPass1")
        user = await register_uc.execute(cmd)

        assert user.email == "new@example.com"
        assert user.hashed_password != "Str0ngPass1"  # Must be hashed
        mock_user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_publishes_user_registered_event(
        self, register_uc: RegisterUser, mock_event_bus: AsyncMock
    ) -> None:
        cmd = RegisterUserCommand(email="event@example.com", password="Str0ngPass1")
        await register_uc.execute(cmd)

        mock_event_bus.publish_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(
        self,
        register_uc: RegisterUser,
        mock_user_repo: AsyncMock,
    ) -> None:
        existing_user = User(email="dupe@example.com", hashed_password="hash")
        mock_user_repo.find_by_email.return_value = existing_user

        cmd = RegisterUserCommand(email="dupe@example.com", password="Str0ngPass1")
        with pytest.raises(DuplicateEmailError):
            await register_uc.execute(cmd)

    @pytest.mark.asyncio
    async def test_register_hashes_password(
        self,
        register_uc: RegisterUser,
        password_hasher: BcryptPasswordHasher,
        mock_user_repo: AsyncMock,
    ) -> None:
        cmd = RegisterUserCommand(email="hash@example.com", password="Str0ngPass1")
        user = await register_uc.execute(cmd)

        assert password_hasher.verify("Str0ngPass1", user.hashed_password)
