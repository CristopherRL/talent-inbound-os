"""Unit tests for the LoginUser use case."""

from unittest.mock import AsyncMock

import pytest
from jose import jwt

from talent_inbound.modules.auth.application.login_user import (
    LoginUser,
    LoginUserCommand,
)
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)
from talent_inbound.modules.auth.infrastructure.password import BcryptPasswordHasher

JWT_SECRET = "test-secret-key-for-unit-tests"


@pytest.fixture
def password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


@pytest.fixture
def active_user(password_hasher: BcryptPasswordHasher) -> User:
    return User(
        email="user@example.com",
        hashed_password=password_hasher.hash("Str0ngPass1"),
        is_active=True,
    )


@pytest.fixture
def inactive_user(password_hasher: BcryptPasswordHasher) -> User:
    return User(
        email="inactive@example.com",
        hashed_password=password_hasher.hash("Str0ngPass1"),
        is_active=False,
    )


@pytest.fixture
def mock_user_repo(active_user: User) -> AsyncMock:
    repo = AsyncMock()
    repo.find_by_email = AsyncMock(return_value=active_user)
    return repo


@pytest.fixture
def login_uc(
    mock_user_repo: AsyncMock, password_hasher: BcryptPasswordHasher
) -> LoginUser:
    return LoginUser(
        user_repo=mock_user_repo,
        password_hasher=password_hasher,
        jwt_secret=JWT_SECRET,
        access_token_expire_minutes=30,
        refresh_token_expire_days=7,
    )


class TestLoginUser:

    @pytest.mark.asyncio
    async def test_login_success_returns_token_pair(
        self, login_uc: LoginUser
    ) -> None:
        cmd = LoginUserCommand(email="user@example.com", password="Str0ngPass1")
        tokens = await login_uc.execute(cmd)

        assert tokens.access_token
        assert tokens.refresh_token

    @pytest.mark.asyncio
    async def test_access_token_contains_correct_claims(
        self, login_uc: LoginUser, active_user: User
    ) -> None:
        cmd = LoginUserCommand(email="user@example.com", password="Str0ngPass1")
        tokens = await login_uc.execute(cmd)

        payload = jwt.decode(tokens.access_token, JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == active_user.id
        assert payload["email"] == active_user.email
        assert payload["type"] == "access"

    @pytest.mark.asyncio
    async def test_refresh_token_is_refresh_type(
        self, login_uc: LoginUser
    ) -> None:
        cmd = LoginUserCommand(email="user@example.com", password="Str0ngPass1")
        tokens = await login_uc.execute(cmd)

        payload = jwt.decode(tokens.refresh_token, JWT_SECRET, algorithms=["HS256"])
        assert payload["type"] == "refresh"

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(
        self, login_uc: LoginUser
    ) -> None:
        cmd = LoginUserCommand(email="user@example.com", password="WrongPass1")
        with pytest.raises(InvalidCredentialsError):
            await login_uc.execute(cmd)

    @pytest.mark.asyncio
    async def test_login_nonexistent_email_raises(
        self, login_uc: LoginUser, mock_user_repo: AsyncMock
    ) -> None:
        mock_user_repo.find_by_email.return_value = None
        cmd = LoginUserCommand(email="nobody@example.com", password="Str0ngPass1")
        with pytest.raises(InvalidCredentialsError):
            await login_uc.execute(cmd)

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(
        self,
        mock_user_repo: AsyncMock,
        password_hasher: BcryptPasswordHasher,
        inactive_user: User,
    ) -> None:
        mock_user_repo.find_by_email.return_value = inactive_user
        login_uc = LoginUser(
            user_repo=mock_user_repo,
            password_hasher=password_hasher,
            jwt_secret=JWT_SECRET,
        )
        cmd = LoginUserCommand(email="inactive@example.com", password="Str0ngPass1")
        with pytest.raises(InactiveUserError):
            await login_uc.execute(cmd)
