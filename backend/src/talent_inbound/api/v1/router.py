"""API v1 router aggregator. Includes all module routers under /api/v1."""

from fastapi import APIRouter

from talent_inbound.modules.auth.presentation.router import router as auth_router
from talent_inbound.modules.profile.presentation.router import router as profile_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(profile_router)

# Module routers will be included here as they are implemented:
# from talent_inbound.modules.ingestion.presentation.router import router as ingestion_router
# from talent_inbound.modules.pipeline.presentation.router import router as pipeline_router
# from talent_inbound.modules.opportunities.presentation.router import router as opportunities_router
# from talent_inbound.modules.chat.presentation.router import router as chat_router

# v1_router.include_router(ingestion_router)
# v1_router.include_router(pipeline_router)
# v1_router.include_router(opportunities_router)
# v1_router.include_router(chat_router)
