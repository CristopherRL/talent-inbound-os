"""Arq worker settings for background job processing."""

import structlog
from arq.connections import RedisSettings

from talent_inbound.config import get_settings

logger = structlog.get_logger()


async def process_pipeline(ctx: dict, interaction_id: str) -> None:
    """Stub pipeline job — actual AI pipeline logic added in US4 (Phase 6)."""
    logger.info(
        "pipeline_job_received",
        interaction_id=interaction_id,
        status="stub",
    )


async def startup(ctx: dict) -> None:
    """Called once when the worker starts."""
    settings = get_settings()
    ctx["settings"] = settings


async def shutdown(ctx: dict) -> None:
    """Called once when the worker shuts down."""


class WorkerSettings:
    """Arq worker configuration."""

    functions = [process_pipeline]
    on_startup = startup
    on_shutdown = shutdown

    @staticmethod
    def redis_settings() -> RedisSettings:
        settings = get_settings()
        return RedisSettings.from_dsn(settings.redis_url)
