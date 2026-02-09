"""Dependency injection container using dependency-injector."""

from dependency_injector import containers, providers

from talent_inbound.config import Settings
from talent_inbound.shared.infrastructure.database import (
    create_engine,
    create_session_factory,
)
from talent_inbound.shared.infrastructure.event_bus import InProcessEventBus


class Container(containers.DeclarativeContainer):
    """Root DI container. Module-specific providers are added per user story."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            # Module routers will be added here as they are implemented
        ]
    )

    config = providers.Singleton(Settings)

    # Shared infrastructure
    db_engine = providers.Singleton(
        create_engine,
        database_url=config.provided.database_url,
        echo=False,
    )

    db_session_factory = providers.Singleton(
        create_session_factory,
        engine=db_engine,
    )

    event_bus = providers.Singleton(InProcessEventBus)
