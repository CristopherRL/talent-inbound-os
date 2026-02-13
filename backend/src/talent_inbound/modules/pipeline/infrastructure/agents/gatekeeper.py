"""Gatekeeper agent — classifies messages as REAL_OFFER / SPAM / NOT_AN_OFFER.

Uses FAST-tier LLM when available, falls back to keyword-based heuristic
for mock-first development and testing.
"""

import json
import time
from datetime import datetime, timezone

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog
from talent_inbound.modules.pipeline.prompts import load_prompt

# Keywords for the mock/heuristic classifier
_OFFER_KEYWORDS = [
    "role", "position", "opportunity", "hiring", "engineer", "developer",
    "salary", "remote", "onsite", "hybrid", "stack", "looking for",
    "team", "company", "client", "recruiter", "vacancy", "apply",
]
_SPAM_KEYWORDS = [
    "click here", "unsubscribe", "free", "winner", "prize", "bitcoin",
    "crypto", "investment", "guaranteed", "limited time",
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


async def _llm_classify(
    model: BaseChatModel, text: str
) -> tuple[str, float]:
    """Use LLM to classify the message."""
    system_prompt = load_prompt("gatekeeper")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=text),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    if isinstance(content, str):
        parsed = json.loads(content)
        return parsed["classification"], parsed.get("confidence", 0.8)
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detail": f"{classification} ({confidence:.0%}) via {source}",
        }

        return {
            "classification": classification,
            "classification_confidence": confidence,
            "current_step": "gatekeeper",
            "pipeline_log": [log_entry],
        }

    return gatekeeper_node
