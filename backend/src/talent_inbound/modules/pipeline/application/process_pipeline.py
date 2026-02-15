"""ProcessPipeline use case — orchestrates the LangGraph pipeline execution."""

import structlog

from talent_inbound.modules.ingestion.domain.repositories import InteractionRepository
from talent_inbound.modules.opportunities.domain.entities import Opportunity
from talent_inbound.modules.opportunities.domain.repositories import (
    OpportunityRepository,
)
from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.sse import SSEEmitter
from talent_inbound.shared.domain.enums import (
    Classification,
    OpportunityStatus,
    ResponseType,
    TransitionTrigger,
)

logger = structlog.get_logger()


class ProcessPipeline:
    """Load Interaction, invoke the pipeline graph, emit SSE events,
    update Opportunity with extracted data, persist results."""

    def __init__(
        self,
        interaction_repo: InteractionRepository,
        opportunity_repo: OpportunityRepository,
        pipeline_graph,
        sse_emitter: SSEEmitter,
    ) -> None:
        self._interaction_repo = interaction_repo
        self._opportunity_repo = opportunity_repo
        self._graph = pipeline_graph
        self._sse = sse_emitter

    async def execute(self, interaction_id: str) -> None:
        log = logger.bind(interaction_id=interaction_id)

        # Load interaction
        interaction = await self._interaction_repo.find_by_id(interaction_id)
        if interaction is None:
            log.error("interaction_not_found")
            return

        opportunity_id = interaction.opportunity_id or ""
        log = log.bind(opportunity_id=opportunity_id)

        # Mark as processing
        interaction.mark_processing()
        await self._interaction_repo.update(interaction)

        # Emit SSE: pipeline started
        await self._sse.emit_progress(interaction_id, "pipeline", "started")

        # Build initial state
        initial_state: PipelineState = {
            "raw_input": interaction.raw_content,
            "interaction_id": interaction_id,
            "opportunity_id": opportunity_id,
            "candidate_id": interaction.candidate_id,
            "pipeline_log": [],
        }

        try:
            # Invoke the LangGraph pipeline
            result = await self._graph.ainvoke(initial_state)

            # Emit per-step SSE events from the pipeline log
            for step_log in result.get("pipeline_log", []):
                await self._sse.emit_progress(
                    interaction_id,
                    step_log["step"],
                    step_log["status"],
                    step_log.get("detail", ""),
                )

            # Update interaction with classification and pipeline log
            classification_str = result.get("classification")
            if classification_str:
                classification = Classification(classification_str)
                interaction.mark_completed(classification)
            else:
                interaction.mark_completed(Classification.REAL_OFFER)

            interaction.pipeline_log = result.get("pipeline_log", [])
            await self._interaction_repo.update(interaction)

            # Update opportunity with extracted data and status
            if opportunity_id:
                opportunity = await self._opportunity_repo.find_by_id(opportunity_id)
                if opportunity:
                    final_status = self._determine_status(result)
                    self._apply_extracted_data(opportunity, result)
                    self._apply_scoring(opportunity, result)
                    await self._save_draft(opportunity_id, result)
                    opportunity.change_status(
                        final_status,
                        triggered_by=TransitionTrigger.SYSTEM,
                        note=f"Pipeline completed: {classification_str}",
                    )
                    await self._opportunity_repo.update(opportunity)

                    await self._sse.emit_complete(
                        interaction_id, opportunity_id, final_status.value
                    )
                    log.info(
                        "pipeline_completed",
                        classification=classification_str,
                        final_status=final_status.value,
                    )
                    return

            # No opportunity to update — just emit complete
            await self._sse.emit_complete(
                interaction_id, opportunity_id, "ANALYZING"
            )
            log.info("pipeline_completed", classification=classification_str)

        except Exception:
            log.exception("pipeline_failed")
            interaction.mark_failed()
            await self._interaction_repo.update(interaction)
            await self._sse.emit_complete(
                interaction_id, opportunity_id, "ANALYZING"
            )

    def _determine_status(self, result: dict) -> OpportunityStatus:
        """Determine the opportunity status based on pipeline results."""
        classification = result.get("classification", "")

        if classification == "SPAM":
            return OpportunityStatus.REJECTED
        if classification == "NOT_AN_OFFER":
            return OpportunityStatus.REJECTED

        # Real offer — check for missing fields
        extracted = result.get("extracted_data", {})
        missing = extracted.get("missing_fields", [])
        if missing:
            return OpportunityStatus.ACTION_REQUIRED

        return OpportunityStatus.ACTION_REQUIRED

    def _apply_extracted_data(self, opportunity: Opportunity, result: dict) -> None:
        """Apply extracted data fields to the opportunity."""
        extracted = result.get("extracted_data")
        if not extracted:
            return

        if extracted.get("company_name"):
            opportunity.company_name = extracted["company_name"]
        if extracted.get("client_name"):
            opportunity.client_name = extracted["client_name"]
        if extracted.get("role_title"):
            opportunity.role_title = extracted["role_title"]
        if extracted.get("salary_range"):
            opportunity.salary_range = extracted["salary_range"]
        if extracted.get("tech_stack"):
            opportunity.tech_stack = extracted["tech_stack"]
        if extracted.get("work_model"):
            opportunity.work_model = extracted["work_model"]
        if extracted.get("recruiter_name"):
            opportunity.recruiter_name = extracted["recruiter_name"]
        if extracted.get("recruiter_type"):
            opportunity.recruiter_type = extracted["recruiter_type"]
        if extracted.get("recruiter_company"):
            opportunity.recruiter_company = extracted["recruiter_company"]
        opportunity.missing_fields = extracted.get("missing_fields", [])

    def _apply_scoring(self, opportunity: Opportunity, result: dict) -> None:
        """Apply match score and reasoning from the Analyst."""
        if result.get("match_score") is not None:
            opportunity.match_score = result["match_score"]
        if result.get("match_reasoning"):
            opportunity.match_reasoning = result["match_reasoning"]

    async def _save_draft(self, opportunity_id: str, result: dict) -> None:
        """Save the auto-generated draft response from the Communicator."""
        draft_text = result.get("draft_response")
        if not draft_text:
            return

        from talent_inbound.modules.opportunities.infrastructure.orm_models import (
            DraftResponseModel,
        )
        from talent_inbound.shared.infrastructure.database import get_current_session

        session = get_current_session()
        model = DraftResponseModel(
            opportunity_id=opportunity_id,
            response_type=ResponseType.EXPRESS_INTEREST.value,
            generated_content=draft_text,
        )
        session.add(model)
        await session.flush()
