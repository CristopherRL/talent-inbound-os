"""GenerateDraft use case — invoke Communicator agent for on-demand draft generation."""

import structlog

from talent_inbound.modules.opportunities.domain.exceptions import (
    OpportunityNotFoundError,
)
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.pipeline.infrastructure.agents.communicator import (
    generate_draft_standalone,
)
from talent_inbound.shared.domain.enums import ResponseType

logger = structlog.get_logger()


class GenerateDraft:
    """Generate a draft response for a specific opportunity + response type."""

    def __init__(
        self,
        opportunity_repo: OpportunityRepository,
        profile_repo=None,
        model_router=None,
    ) -> None:
        self._opportunity_repo = opportunity_repo
        self._profile_repo = profile_repo
        self._model_router = model_router

    async def execute(
        self,
        opportunity_id: str,
        response_type: str,
        additional_context: str | None = None,
    ) -> dict:
        """Generate a draft and persist it.

        Returns:
            Dict with draft fields (id, response_type, generated_content, etc.)
        """
        # Validate response type
        try:
            rt = ResponseType(response_type)
        except ValueError:
            raise ValueError(
                f"Invalid response_type: {response_type}. "
                f"Must be one of: {', '.join(r.value for r in ResponseType)}"
            )

        # Load opportunity
        opp = await self._opportunity_repo.find_by_id(opportunity_id)
        if opp is None:
            raise OpportunityNotFoundError(opportunity_id)

        # Build extracted data dict from opportunity fields
        extracted_data = {
            "company_name": opp.company_name,
            "role_title": opp.role_title,
            "salary_range": opp.salary_range,
            "tech_stack": opp.tech_stack or [],
            "work_model": opp.work_model.value if hasattr(opp.work_model, "value") else opp.work_model,
            "recruiter_name": opp.recruiter_name,
            "recruiter_company": opp.recruiter_company,
            "missing_fields": opp.missing_fields or [],
        }

        # Load profile
        profile = None
        if self._profile_repo:
            try:
                profile = await self._profile_repo.find_by_candidate_id(opp.candidate_id)
            except Exception:
                pass

        # Resolve LLM model
        model = None
        if self._model_router:
            model = self._model_router.get_model("communicator")

        generation_mode = "llm" if model is not None else "mock"

        log_ctx = {
            "opportunity_id": opportunity_id,
            "response_type": rt.value,
            "mode": generation_mode,
            "company": opp.company_name,
        }
        if additional_context:
            # Log a preview (first 100 chars) — not the full text for privacy
            log_ctx["additional_context_preview"] = additional_context[:100]

        logger.info("draft_generation_started", **log_ctx)

        if additional_context and model is None:
            logger.warning(
                "additional_context_ignored",
                reason="Mock mode cannot process additional instructions. "
                       "Configure an LLM API key to enable this feature.",
                opportunity_id=opportunity_id,
            )

        # Generate draft
        draft_text = await generate_draft_standalone(
            response_type=rt.value,
            extracted_data=extracted_data,
            profile=profile,
            model=model,
            additional_context=additional_context,
        )

        logger.info(
            "draft_generation_completed",
            opportunity_id=opportunity_id,
            response_type=rt.value,
            mode=generation_mode,
            draft_length=len(draft_text),
        )

        # Persist
        from talent_inbound.modules.opportunities.infrastructure.orm_models import (
            DraftResponseModel,
        )
        from talent_inbound.shared.infrastructure.database import get_current_session

        session = get_current_session()
        draft_model = DraftResponseModel(
            opportunity_id=opportunity_id,
            response_type=rt.value,
            generated_content=draft_text,
        )
        session.add(draft_model)
        await session.flush()
        await session.refresh(draft_model)

        return {
            "id": draft_model.id,
            "response_type": draft_model.response_type,
            "generated_content": draft_model.generated_content,
            "edited_content": draft_model.edited_content,
            "is_final": draft_model.is_final,
            "created_at": draft_model.created_at,
        }
