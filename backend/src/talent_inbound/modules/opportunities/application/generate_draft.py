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
from talent_inbound.modules.pipeline.infrastructure.agents.guardrail import (
    check_guardrail,
)
from talent_inbound.shared.domain.enums import ResponseType

logger = structlog.get_logger()


def _build_extracted_data(opp) -> dict:
    """Build extracted data dict from opportunity fields."""
    return {
        "company_name": opp.company_name,
        "role_title": opp.role_title,
        "salary_range": opp.salary_range,
        "tech_stack": opp.tech_stack or [],
        "work_model": opp.work_model.value
        if hasattr(opp.work_model, "value")
        else opp.work_model,
        "recruiter_name": opp.recruiter_name,
        "recruiter_company": opp.recruiter_company,
        "missing_fields": opp.missing_fields or [],
    }


async def _check_additional_context(
    text: str, model_router, opportunity_id: str
) -> str:
    """Run guardrail on additional_context, raise on injection, return sanitized text."""
    guardrail_model = model_router.get_model("guardrail") if model_router else None
    gr = await check_guardrail(text, model=guardrail_model)
    if gr.prompt_injection_detected:
        logger.warning(
            "draft_additional_context_injection",
            opportunity_id=opportunity_id,
            source=gr.detection_source,
        )
        raise ValueError(
            "The additional instructions were flagged as potentially unsafe. "
            "Please rephrase and try again."
        )
    return gr.sanitized_text


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

    async def _load_profile(self, candidate_id: str):
        """Load candidate profile, returning None on failure."""
        if not self._profile_repo:
            return None
        try:
            return await self._profile_repo.find_by_candidate_id(candidate_id)
        except Exception:
            return None

    async def execute(
        self,
        opportunity_id: str,
        response_type: str,
        additional_context: str | None = None,
        language: str | None = None,
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

        extracted_data = _build_extracted_data(opp)
        profile = await self._load_profile(opp.candidate_id)
        model = self._model_router.get_model("communicator") if self._model_router else None
        generation_mode = "llm" if model is not None else "mock"

        logger.info(
            "draft_generation_started",
            opportunity_id=opportunity_id,
            response_type=rt.value,
            mode=generation_mode,
            company=opp.company_name,
        )

        # Guardrail: check additional_context for prompt injection
        if additional_context:
            additional_context = await _check_additional_context(
                additional_context, self._model_router, opportunity_id
            )

        # Resolve effective language: explicit override > pipeline-detected > None
        effective_language = language or opp.detected_language
        if not effective_language:
            logger.warning(
                "draft_language_unknown",
                opportunity_id=opportunity_id,
                hint="detected_language is NULL — LLM will infer from context",
            )

        # Generate draft
        draft_text = await generate_draft_standalone(
            response_type=rt.value,
            extracted_data=extracted_data,
            profile=profile,
            model=model,
            additional_context=additional_context,
            language=effective_language,
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
            "is_sent": draft_model.is_sent,
            "sent_at": draft_model.sent_at,
            "created_at": draft_model.created_at,
        }
