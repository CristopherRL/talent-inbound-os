"""GetCurrentUser use case — validates a JWT and returns the user."""

from jose import JWTError, jwt

from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.exceptions import InvalidCredentialsError
from talent_inbound.modules.auth.domain.repositories import UserRepository


class GetCurrentUser:
    """Extracts user_id from a JWT access token and loads the User.

    This is called on every authenticated request to resolve
    the current user from the token stored in the HTTP-only cookie.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        jwt_secret: str,
    ) -> None:
        self._user_repo = user_repo
        self._jwt_secret = jwt_secret

    async def execute(self, token: str) -> User:
        try:
            payload = jwt.decode(token, self._jwt_secret, algorithms=["HS256"])
        except JWTError:
            raise InvalidCredentialsError()

        if payload.get("type") != "access":
            raise InvalidCredentialsError()

        user_id: str | None = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsError()

        user = await self._user_repo.find_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidCredentialsError()

        return user
