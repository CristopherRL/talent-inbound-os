"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from talent_inbound.config import get_settings
from talent_inbound.container import Container
from talent_inbound.shared.infrastructure.database import DBSessionMiddleware
from talent_inbound.shared.infrastructure.logging import configure_logging, get_logger
from talent_inbound.shared.infrastructure.middleware import RequestLoggingMiddleware

logger = get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()

    configure_logging(
        log_level=settings.log_level,
        json_output=not settings.is_development,
    )

    app = FastAPI(
        title="Talent Inbound OS",
        description="AI-assisted inbound recruiting management for Senior Engineers",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # DI container
    container = Container()
    app.container = container  # type: ignore[attr-defined]

    # CORS — allow frontend origin (both localhost and 127.0.0.1 for Windows IPv6 compat)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # API routes (must be registered on FastAPI app BEFORE ASGI wrapping)
    from talent_inbound.api.v1.router import v1_router

    app.include_router(v1_router, prefix="/api/v1")

    # Global handler: database connection errors → 503
    async def _db_unavailable_response(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("database_connection_failed", error=type(exc).__name__, detail=str(exc))
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database is unavailable. Please ensure PostgreSQL is running.",
            },
        )

    app.exception_handler(OperationalError)(_db_unavailable_response)
    app.exception_handler(ConnectionRefusedError)(_db_unavailable_response)

    # Health check (unversioned) — pings DB to verify connectivity
    @app.get("/health")
    async def health():
        from sqlalchemy import text

        from talent_inbound.shared.infrastructure.database import get_current_session

        try:
            session = get_current_session()
            await session.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "unavailable"

        status = "ok" if db_status == "ok" else "degraded"
        return {"status": status, "database": db_status}

    # Log startup configuration
    _log_startup_banner(settings, container)

    # DB session per request (commit on success, rollback on error).
    # Wraps the entire FastAPI ASGI app as the outermost middleware so
    # every HTTP request gets its own AsyncSession via ContextVar.
    session_factory = container.db_session_factory()
    wrapped = DBSessionMiddleware(app, session_factory=session_factory)

    return wrapped  # type: ignore[return-value]


def _log_startup_banner(settings, container) -> None:
    """Log application configuration at startup for observability."""
    model_router = container.model_router()
    llm_configured = model_router.is_configured
    mode = "LLM" if llm_configured else "MOCK"

    logger.info(
        "app_startup",
        mode=mode,
        llm_provider=settings.llm_provider if llm_configured else "none",
        llm_fast_model=settings.llm_fast_model if llm_configured else "n/a",
        llm_smart_model=settings.llm_smart_model if llm_configured else "n/a",
        environment=settings.environment,
        pipeline_steps=settings.pipeline_steps,
    )


app = create_app()
