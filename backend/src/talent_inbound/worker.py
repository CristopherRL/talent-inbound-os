"""Arq worker settings for background job processing."""

from arq.connections import RedisSettings

from talent_inbound.config import get_settings


async def startup(ctx: dict) -> None:
    """Called once when the worker starts."""
    settings = get_settings()
    ctx["settings"] = settings


async def shutdown(ctx: dict) -> None:
    """Called once when the worker shuts down."""


# Pipeline job stubs — real implementations added in US3/US4
# async def process_pipeline(ctx: dict, interaction_id: str) -> None:
#     pass


class WorkerSettings:
    """Arq worker configuration."""

    functions: list = [
        # process_pipeline,  # Added in US3
    ]
    on_startup = startup
    on_shutdown = shutdown

    @staticmethod
    def redis_settings() -> RedisSettings:
        settings = get_settings()
        return RedisSettings.from_dsn(settings.redis_url)
