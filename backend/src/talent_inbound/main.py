"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talent_inbound.config import get_settings
from talent_inbound.container import Container
from talent_inbound.shared.infrastructure.logging import configure_logging
from talent_inbound.shared.infrastructure.middleware import RequestLoggingMiddleware


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

    # CORS — allow frontend origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # API routes
    from talent_inbound.api.v1.router import v1_router

    app.include_router(v1_router, prefix="/api/v1")

    # Health check (unversioned)
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
