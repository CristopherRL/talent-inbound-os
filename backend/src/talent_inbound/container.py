"""Dependency injection container using dependency-injector."""

from dependency_injector import containers, providers

from talent_inbound.config import Settings
from talent_inbound.modules.auth.application.get_current_user import GetCurrentUser
from talent_inbound.modules.auth.application.login_user import LoginUser
from talent_inbound.modules.auth.application.register_user import RegisterUser
from talent_inbound.modules.auth.infrastructure.password import BcryptPasswordHasher
from talent_inbound.modules.auth.infrastructure.repositories import (
    SqlAlchemyUserRepository,
)
from talent_inbound.modules.ingestion.application.submit_message import SubmitMessage
from talent_inbound.modules.ingestion.infrastructure.repositories import (
    SqlAlchemyInteractionRepository,
)
from talent_inbound.modules.opportunities.application.archive import (
    ArchiveOpportunity,
    UnarchiveOpportunity,
)
from talent_inbound.modules.opportunities.application.change_status import ChangeStatus
from talent_inbound.modules.opportunities.application.edit_draft import EditDraft
from talent_inbound.modules.opportunities.application.generate_draft import (
    GenerateDraft,
)
from talent_inbound.modules.opportunities.application.get_stale import (
    GetStaleOpportunities,
)
from talent_inbound.modules.pipeline.infrastructure.model_router import ModelRouter
from talent_inbound.modules.pipeline.infrastructure.sse import SSEEmitter
from talent_inbound.modules.opportunities.infrastructure.repositories import (
    SqlAlchemyOpportunityRepository,
)
from talent_inbound.modules.profile.application.get_profile import GetProfile
from talent_inbound.modules.profile.application.update_profile import UpdateProfile
from talent_inbound.modules.profile.application.upload_cv import UploadCV
from talent_inbound.modules.profile.infrastructure.cv_parser import CVParser
from talent_inbound.modules.profile.infrastructure.repositories import (
    SqlAlchemyProfileRepository,
)
from talent_inbound.modules.profile.infrastructure.storage import LocalStorageBackend
from talent_inbound.shared.infrastructure.database import (
    create_engine,
    create_session_factory,
    get_current_session,
)
from talent_inbound.shared.infrastructure.event_bus import InProcessEventBus


class Container(containers.DeclarativeContainer):
    """Root DI container. Module-specific providers are added per user story."""

    wiring_config = containers.WiringConfiguration(
        modules=[
            "talent_inbound.modules.auth.presentation.router",
            "talent_inbound.modules.auth.presentation.dependencies",
            "talent_inbound.modules.profile.presentation.router",
            "talent_inbound.modules.ingestion.presentation.router",
            "talent_inbound.modules.opportunities.presentation.router",
            "talent_inbound.modules.pipeline.presentation.router",
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

    db_session = providers.Callable(get_current_session)

    event_bus = providers.Singleton(InProcessEventBus)

    # --- Auth module ---
    password_hasher = providers.Singleton(BcryptPasswordHasher)

    user_repo = providers.Factory(
        SqlAlchemyUserRepository,
        session=db_session,
    )

    register_user_uc = providers.Factory(
        RegisterUser,
        user_repo=user_repo,
        password_hasher=password_hasher,
        event_bus=event_bus,
    )

    login_user_uc = providers.Factory(
        LoginUser,
        user_repo=user_repo,
        password_hasher=password_hasher,
        jwt_secret=config.provided.jwt_secret_key,
        access_token_expire_minutes=config.provided.jwt_access_token_expire_minutes,
        refresh_token_expire_days=config.provided.jwt_refresh_token_expire_days,
    )

    get_current_user_uc = providers.Factory(
        GetCurrentUser,
        user_repo=user_repo,
        jwt_secret=config.provided.jwt_secret_key,
    )

    # --- Profile module ---
    storage_backend = providers.Singleton(
        LocalStorageBackend,
        upload_dir=config.provided.upload_dir,
    )

    cv_parser = providers.Singleton(CVParser)

    profile_repo = providers.Factory(
        SqlAlchemyProfileRepository,
        session=db_session,
    )

    update_profile_uc = providers.Factory(
        UpdateProfile,
        profile_repo=profile_repo,
    )

    upload_cv_uc = providers.Factory(
        UploadCV,
        profile_repo=profile_repo,
        storage_backend=storage_backend,
        cv_parser=cv_parser,
    )

    get_profile_uc = providers.Factory(
        GetProfile,
        profile_repo=profile_repo,
    )

    # --- Ingestion module ---
    interaction_repo = providers.Factory(
        SqlAlchemyInteractionRepository,
        session=db_session,
    )

    # --- Opportunities module ---
    opportunity_repo = providers.Factory(
        SqlAlchemyOpportunityRepository,
        session=db_session,
    )

    # --- Ingestion use cases ---
    submit_message_uc = providers.Factory(
        SubmitMessage,
        interaction_repo=interaction_repo,
        opportunity_repo=opportunity_repo,
        event_bus=event_bus,
        max_message_length=config.provided.max_message_length,
    )

    # --- Opportunities use cases ---
    change_status_uc = providers.Factory(
        ChangeStatus,
        opportunity_repo=opportunity_repo,
    )

    archive_uc = providers.Factory(
        ArchiveOpportunity,
        opportunity_repo=opportunity_repo,
    )

    unarchive_uc = providers.Factory(
        UnarchiveOpportunity,
        opportunity_repo=opportunity_repo,
    )

    get_stale_uc = providers.Factory(
        GetStaleOpportunities,
        opportunity_repo=opportunity_repo,
        profile_repo=profile_repo,
    )

    edit_draft_uc = providers.Factory(EditDraft)

    # --- Pipeline module ---
    model_router = providers.Singleton(
        ModelRouter,
        openai_api_key=config.provided.openai_api_key,
        anthropic_api_key=config.provided.anthropic_api_key,
        provider=config.provided.llm_provider,
        fast_model=config.provided.llm_fast_model,
        smart_model=config.provided.llm_smart_model,
    )

    sse_emitter = providers.Singleton(SSEEmitter)

    # GenerateDraft uses model_router to stay consistent with the pipeline mode
    generate_draft_uc = providers.Factory(
        GenerateDraft,
        opportunity_repo=opportunity_repo,
        profile_repo=profile_repo,
        model_router=model_router,
    )
