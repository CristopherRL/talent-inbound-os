"""Arq worker settings for background job processing."""

import structlog
from arq.connections import RedisSettings

from talent_inbound.config import get_settings

logger = structlog.get_logger()


async def process_pipeline(ctx: dict, interaction_id: str) -> None:
    """Pipeline job — invokes the ProcessPipeline use case.

    The use case handles: loading the interaction, running the LangGraph
    pipeline, emitting SSE events, and updating the opportunity.
    """
    from talent_inbound.container import Container
    from talent_inbound.modules.pipeline.application.process_pipeline import (
        ProcessPipeline,
    )
    from talent_inbound.modules.pipeline.infrastructure.graphs import (
        build_main_pipeline,
    )
    from talent_inbound.modules.pipeline.infrastructure.model_router import ModelRouter
    from talent_inbound.modules.pipeline.infrastructure.sse import SSEEmitter
    from talent_inbound.shared.infrastructure.database import (
        _current_session,
        create_engine,
        create_session_factory,
    )
    from talent_inbound.modules.ingestion.infrastructure.repositories import (
        SqlAlchemyInteractionRepository,
    )
    from talent_inbound.modules.opportunities.infrastructure.repositories import (
        SqlAlchemyOpportunityRepository,
    )

    settings = ctx["settings"]
    log = logger.bind(interaction_id=interaction_id)
    log.info("pipeline_job_started")

    # Create a dedicated DB session for this job (worker runs outside HTTP context)
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)

    async with factory() as session:
        token = _current_session.set(session)
        try:
            interaction_repo = SqlAlchemyInteractionRepository(session)
            opportunity_repo = SqlAlchemyOpportunityRepository(session)

            model_router = ModelRouter(
                openai_api_key=settings.openai_api_key,
                anthropic_api_key=settings.anthropic_api_key,
            )
            graph = build_main_pipeline(model_router)
            sse_emitter = ctx.get("sse_emitter", SSEEmitter())

            use_case = ProcessPipeline(
                interaction_repo=interaction_repo,
                opportunity_repo=opportunity_repo,
                pipeline_graph=graph,
                sse_emitter=sse_emitter,
            )

            await use_case.execute(interaction_id)
            await session.commit()
            log.info("pipeline_job_completed")
        except Exception:
            await session.rollback()
            log.exception("pipeline_job_failed")
            raise
        finally:
            _current_session.reset(token)

    await engine.dispose()


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
    max_tries = 3

    @staticmethod
    def redis_settings() -> RedisSettings:
        settings = get_settings()
        return RedisSettings.from_dsn(settings.redis_url)
