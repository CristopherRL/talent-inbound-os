"""LoginUser use case — authenticates credentials and generates JWT tokens."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from jose import jwt

from talent_inbound.modules.auth.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)
from talent_inbound.modules.auth.domain.repositories import UserRepository
from talent_inbound.modules.auth.infrastructure.password import BcryptPasswordHasher


@dataclass
class LoginUserCommand:
    email: str
    password: str


@dataclass
class TokenPair:
    """JWT access + refresh tokens."""

    access_token: str
    refresh_token: str


class LoginUser:
    """Verifies credentials and issues JWT access + refresh tokens.

    JWT (JSON Web Token) is a compact, self-contained token that carries
    claims (user_id, expiration). The server signs it with a secret key
    so it can verify authenticity without a database lookup on every request.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        password_hasher: BcryptPasswordHasher,
        jwt_secret: str,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._jwt_secret = jwt_secret
        self._access_expire_minutes = access_token_expire_minutes
        self._refresh_expire_days = refresh_token_expire_days

    async def execute(self, command: LoginUserCommand) -> TokenPair:
        user = await self._user_repo.find_by_email(command.email)
        if not user:
            raise InvalidCredentialsError()

        if not self._password_hasher.verify(command.password, user.hashed_password):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        now = datetime.now(timezone.utc)

        access_token = jwt.encode(
            {
                "sub": user.id,
                "email": user.email,
                "type": "access",
                "exp": now + timedelta(minutes=self._access_expire_minutes),
                "iat": now,
            },
            self._jwt_secret,
            algorithm="HS256",
        )

        refresh_token = jwt.encode(
            {
                "sub": user.id,
                "type": "refresh",
                "exp": now + timedelta(days=self._refresh_expire_days),
                "iat": now,
            },
            self._jwt_secret,
            algorithm="HS256",
        )

        return TokenPair(access_token=access_token, refresh_token=refresh_token)
