"""FastAPI dependencies for auth — extracts and validates JWT from cookies."""

from dependency_injector.wiring import Provide, inject
from fastapi import Cookie, Depends, HTTPException, status

from talent_inbound.container import Container
from talent_inbound.modules.auth.application.get_current_user import GetCurrentUser
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.exceptions import InvalidCredentialsError


@inject
async def get_current_user(
    access_token: str | None = Cookie(default=None),
    get_current_user_uc: GetCurrentUser = Depends(
        Provide[Container.get_current_user_uc]
    ),
) -> User:
    """FastAPI dependency that extracts the JWT from the access_token cookie.

    This is used by adding `current_user: User = Depends(get_current_user)`
    to any route that requires authentication.
    """
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        return await get_current_user_uc.execute(access_token)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
