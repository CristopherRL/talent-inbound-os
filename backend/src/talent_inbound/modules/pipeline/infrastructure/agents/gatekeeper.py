"""Gatekeeper agent — classifies messages as REAL_OFFER / SPAM / NOT_AN_OFFER.

Uses FAST-tier LLM when available, falls back to keyword-based heuristic
for mock-first development and testing.
"""

import json
import time
from datetime import UTC, datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog
from talent_inbound.modules.pipeline.prompts import load_prompt

# Keywords for the mock/heuristic classifier
_OFFER_KEYWORDS = [
    "role",
    "position",
    "opportunity",
    "hiring",
    "engineer",
    "developer",
    "salary",
    "remote",
    "onsite",
    "hybrid",
    "stack",
    "looking for",
    "team",
    "company",
    "client",
    "recruiter",
    "vacancy",
    "apply",
]
_SPAM_KEYWORDS = [
    "click here",
    "unsubscribe",
    "free",
    "winner",
    "prize",
    "bitcoin",
    "crypto",
    "investment",
    "guaranteed",
    "limited time",
]


def _mock_classify(text: str) -> tuple[str, float]:
    """Keyword-based heuristic classification for mock-first development."""
    lower = text.lower()
    offer_score = sum(1 for kw in _OFFER_KEYWORDS if kw in lower)
    spam_score = sum(1 for kw in _SPAM_KEYWORDS if kw in lower)

    if spam_score >= 2:
        return "SPAM", min(0.5 + spam_score * 0.1, 0.95)
    if offer_score >= 3:
        return "REAL_OFFER", min(0.5 + offer_score * 0.05, 0.95)
    if offer_score >= 1:
        return "REAL_OFFER", 0.6
    return "NOT_AN_OFFER", 0.7


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from LLM output, handling markdown fences."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        # Remove opening fence (with optional language tag)
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


async def _llm_classify(model: BaseChatModel, text: str) -> tuple[str, float]:
    """Use LLM to classify the message."""
    system_prompt = load_prompt("gatekeeper")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=text),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    if isinstance(content, str):
        parsed = _extract_json(content)
        if parsed and "classification" in parsed:
            return parsed["classification"], parsed.get("confidence", 0.8)
        # Fallback: if LLM returned text but not valid JSON, use mock classifier
        import structlog

        structlog.get_logger().warning(
            "gatekeeper_llm_json_parse_failed",
            content_preview=content[:200],
        )
        return _mock_classify(text)
    return "REAL_OFFER", 0.5


def create_gatekeeper_node(model: BaseChatModel | None = None):
    """Factory: returns a gatekeeper node function with optional LLM model."""

    async def gatekeeper_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        text = state.get("sanitized_text", state["raw_input"])

        if model is not None:
            classification, confidence = await _llm_classify(model, text)
            source = "llm"
        else:
            classification, confidence = _mock_classify(text)
            source = "heuristic"

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        log_entry: StepLog = {
            "step": "gatekeeper",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(UTC).isoformat(),
            "detail": f"{classification} ({confidence:.0%}) via {source}",
        }

        return {
            "classification": classification,
            "classification_confidence": confidence,
            "current_step": "gatekeeper",
            "pipeline_log": [log_entry],
        }

    return gatekeeper_node
