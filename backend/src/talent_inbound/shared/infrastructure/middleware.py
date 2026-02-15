"""Request logging middleware for FastAPI."""

import time
import uuid

from jose import jwt as jose_jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars

from talent_inbound.shared.infrastructure.logging import get_logger

logger = get_logger(__name__)


def _extract_user_email(request: Request) -> str | None:
    """Try to extract user email from the JWT access_token cookie.

    This is a best-effort extraction for logging — never blocks the request.
    Returns None if no cookie or invalid token.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        # Decode without verification — we only need the email for logging.
        # Auth verification happens in the dependency layer.
        payload = jose_jwt.get_unverified_claims(token)
        return payload.get("email")
    except Exception:
        return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with request_id, method, path, user, duration, and status."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        clear_contextvars()
        request_id = str(uuid.uuid4())

        # Build log context
        ctx: dict = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        }

        # Add user email if authenticated (best-effort, no DB lookup)
        user_email = _extract_user_email(request)
        if user_email:
            ctx["user"] = user_email

        bind_contextvars(**ctx)

        start = time.perf_counter()
        logger.info("request_started")

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed")
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        response.headers["X-Request-ID"] = request_id
        return response
