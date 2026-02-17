"""Auth API router — register, login, logout, refresh."""

from datetime import UTC

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import JWTError, jwt

from talent_inbound.config import Settings
from talent_inbound.container import Container
from talent_inbound.modules.auth.application.login_user import (
    LoginUser,
    LoginUserCommand,
)
from talent_inbound.modules.auth.application.register_user import (
    RegisterUser,
    RegisterUserCommand,
)
from talent_inbound.modules.auth.domain.entities import User
from talent_inbound.modules.auth.domain.exceptions import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
)
from talent_inbound.modules.auth.presentation.dependencies import get_current_user
from talent_inbound.modules.auth.presentation.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookies(
    response: Response, access_token: str, refresh_token: str
) -> None:
    """Set JWT tokens as HTTP-only, secure cookies.

    HTTP-only means JavaScript cannot read these cookies (XSS protection).
    In production (HTTPS), uses secure=True and samesite="none" for
    cross-origin cookies (backend and frontend on different domains).
    In development, uses secure=False and samesite="lax".
    """
    from talent_inbound.config import get_settings

    is_prod = not get_settings().is_development
    samesite_value: str = "none" if is_prod else "lax"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite=samesite_value,
        secure=is_prod,
        max_age=30 * 60,  # 30 minutes
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite=samesite_value,
        secure=is_prod,
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/api/v1/auth/refresh",  # Only sent to refresh endpoint
    )


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def register(
    body: RegisterRequest,
    register_uc: RegisterUser = Depends(Provide[Container.register_user_uc]),
) -> UserResponse:
    try:
        user = await register_uc.execute(
            RegisterUserCommand(email=body.email, password=body.password)
        )
    except DuplicateEmailError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    return UserResponse(user_id=user.id, email=user.email)


@router.post("/login", response_model=MessageResponse)
@inject
async def login(
    body: LoginRequest,
    response: Response,
    login_uc: LoginUser = Depends(Provide[Container.login_user_uc]),
) -> MessageResponse:
    try:
        tokens = await login_uc.execute(
            LoginUserCommand(email=body.email, password=body.password)
        )
    except (InvalidCredentialsError, InactiveUserError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    _set_auth_cookies(response, tokens.access_token, tokens.refresh_token)
    return MessageResponse(message="Login successful")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")
    return MessageResponse(message="Logged out")


@router.post("/refresh", response_model=MessageResponse)
@inject
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    login_uc: LoginUser = Depends(Provide[Container.login_user_uc]),
    settings: Settings = Depends(Provide[Container.config]),
) -> MessageResponse:
    """Use the refresh token to issue a new access token.

    The refresh token has a longer lifespan (7 days) and is only sent
    to this specific endpoint (via cookie path restriction).
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    try:
        payload = jwt.decode(
            refresh_token, settings.jwt_secret_key, algorithms=["HS256"]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Re-issue tokens via a minimal login flow using user_id lookup
    from talent_inbound.modules.auth.domain.repositories import UserRepository

    user_repo: UserRepository = login_uc._user_repo
    user = await user_repo.find_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    from datetime import datetime, timedelta

    now = datetime.now(UTC)
    new_access = jwt.encode(
        {
            "sub": user.id,
            "email": user.email,
            "type": "access",
            "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
            "iat": now,
        },
        settings.jwt_secret_key,
        algorithm="HS256",
    )

    is_prod = not settings.is_development
    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        samesite="none" if is_prod else "lax",
        secure=is_prod,
        max_age=settings.jwt_access_token_expire_minutes * 60,
        path="/",
    )
    return MessageResponse(message="Token refreshed")


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Return the currently authenticated user's basic info."""
    return UserResponse(user_id=current_user.id, email=current_user.email)
