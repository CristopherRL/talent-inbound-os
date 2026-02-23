"""Stage Detector agent — suggests hiring process stage transitions.

Analyzes the conversation context and suggests forward stage transitions
based on heuristics (always) and LLM analysis (when available).
Runs after the communicator as the last pipeline node.
"""

import json
import re
import time
from datetime import UTC, datetime

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog
from talent_inbound.modules.pipeline.prompts import load_prompt
from talent_inbound.shared.domain.enums import STAGE_FLOW, OpportunityStage

logger = structlog.get_logger()

# Heuristic keyword patterns for stage detection (English + Spanish)
_INTERVIEWING_PATTERNS = re.compile(
    r"\b(interview|technical\s+test|coding\s+challenge|call\s+scheduled|"
    r"meet\s+the\s+team|screening\s+call|phone\s+screen|video\s+call|"
    r"on-?site\s+visit|assessment|"
    # Spanish equivalents
    r"entrevista|prueba\s+t[eé]cnica|llamada|videollamada|"
    r"agendar|agendemos|agendamos|programar\s+una|"
    r"conocer\s+al\s+equipo|visita\s+presencial)\b",
    re.IGNORECASE,
)
_NEGOTIATING_PATTERNS = re.compile(
    r"\b(offer\s+letter|compensation|package|start\s+date|salary\s+proposal|"
    r"benefits|stock\s+options|equity|signing\s+bonus|notice\s+period|"
    r"contract\s+terms|terms\s+of\s+employment|"
    # Spanish equivalents
    r"carta\s+de\s+oferta|compensaci[oó]n|paquete\s+salarial|"
    r"fecha\s+de\s+inicio|propuesta\s+salarial|beneficios|"
    r"opciones\s+sobre\s+acciones|periodo\s+de\s+prueba|"
    r"condiciones\s+del\s+contrato|t[eé]rminos\s+de\s+empleo)\b",
    re.IGNORECASE,
)


def _is_forward_move(current_stage: str, suggested_stage: str) -> bool:
    """Check if the suggested stage is a forward move from the current stage."""
    try:
        current = OpportunityStage(current_stage)
        suggested = OpportunityStage(suggested_stage)
    except ValueError:
        return False

    if current not in STAGE_FLOW or suggested not in STAGE_FLOW:
        return False

    return STAGE_FLOW.index(suggested) > STAGE_FLOW.index(current)


def _heuristic_detect(text: str, current_stage: str) -> tuple[str | None, str | None]:
    """Detect stage suggestion using keyword heuristics.

    Returns (suggested_stage, reason) or (None, None).
    """
    # Check for negotiating signals first (higher priority)
    if _NEGOTIATING_PATTERNS.search(text) and _is_forward_move(
        current_stage, "NEGOTIATING"
    ):
        return (
            "NEGOTIATING",
            "Message contains compensation/offer discussion signals",
        )

    # Check for interviewing signals
    if _INTERVIEWING_PATTERNS.search(text) and _is_forward_move(
        current_stage, "INTERVIEWING"
    ):
        return "INTERVIEWING", "Message contains interview scheduling signals"

    return None, None


async def _load_current_stage(opportunity_repo, opportunity_id: str) -> str:
    """Load the current stage from the opportunity, defaulting to DISCOVERY."""
    if not opportunity_repo or not opportunity_id:
        return "DISCOVERY"
    try:
        opp = await opportunity_repo.find_by_id(opportunity_id)
        if opp:
            return opp.stage.value if hasattr(opp.stage, "value") else str(opp.stage)
    except Exception:
        pass
    return "DISCOVERY"


async def _llm_detect(
    model: BaseChatModel, text: str, current_stage: str
) -> tuple[str | None, str | None]:
    """Use LLM for nuanced stage detection. Returns (stage, reason) or (None, None)."""
    try:
        prompt_template = load_prompt("stage_detector")
        prompt = prompt_template.format(
            current_stage=current_stage,
            stage_flow="DISCOVERY → ENGAGING → INTERVIEWING → NEGOTIATING",
        )
        messages = [
            SystemMessage(content=prompt),
            HumanMessage(content=f"Analyze this conversation:\n\n{text}"),
        ]
        response = await model.ainvoke(messages)
        content = (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )

        logger.debug(
            "stage_detector_llm_response",
            raw_response=content[:300],
            current_stage=current_stage,
        )

        json_match = re.search(r"\{[^}]+\}", content)
        if not json_match:
            logger.warning(
                "stage_detector_llm_no_json", raw_response=content[:300]
            )
            return None, None

        parsed = json.loads(json_match.group())
        llm_stage = parsed.get("suggested_stage")
        llm_reason = parsed.get("reason")

        logger.debug(
            "stage_detector_llm_parsed",
            llm_stage=llm_stage,
            llm_reason=llm_reason,
            is_forward=_is_forward_move(current_stage, llm_stage)
            if llm_stage
            else False,
        )

        if llm_stage and _is_forward_move(current_stage, llm_stage):
            return llm_stage, llm_reason
    except Exception:
        logger.exception("stage_detector_llm_failed")

    return None, None


def create_stage_detector_node(
    model: BaseChatModel | None = None,
    opportunity_repo=None,
):
    """Factory: returns a stage detector node function."""

    async def stage_detector_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        opportunity_id = state.get("opportunity_id", "")
        sanitized_text = state.get("sanitized_text", state.get("raw_input", ""))

        current_stage = await _load_current_stage(opportunity_repo, opportunity_id)

        # Try heuristic first (always runs, used as fallback)
        h_stage, h_reason = _heuristic_detect(sanitized_text, current_stage)

        # Try LLM detection (preferred when available)
        suggested_stage = None
        suggested_reason = None
        source = "none"

        if model is not None:
            suggested_stage, suggested_reason = await _llm_detect(
                model, sanitized_text, current_stage
            )
            if suggested_stage:
                source = "llm"

        # Fall back to heuristic if LLM didn't suggest anything
        if suggested_stage is None and h_stage is not None:
            suggested_stage = h_stage
            suggested_reason = h_reason
            source = "heuristic"

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        detail = (
            "No stage change suggested"
            if not suggested_stage
            else f"Suggested {suggested_stage} via {source}"
        )
        log_entry: StepLog = {
            "step": "stage_detector",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(UTC).isoformat(),
            "detail": detail,
        }

        return {
            "suggested_stage": suggested_stage,
            "suggested_stage_reason": suggested_reason,
            "current_step": "stage_detector",
            "pipeline_log": [log_entry],
        }

    return stage_detector_node
