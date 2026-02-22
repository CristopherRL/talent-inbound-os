"""Guardrail agent — PII detection/sanitization and prompt injection detection.

Two-layer defence:
  1. Regex-based heuristics (fast, zero-cost, catches obvious patterns).
  2. FAST-tier LLM analysis (deeper, catches sophisticated attempts).

Used in:
  - Pipeline nodes (ingestion + follow-ups) via ``create_guardrail_node()``.
  - On-demand checks (draft additional_context, CV extraction) via ``check_guardrail()``.
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog
from talent_inbound.modules.pipeline.prompts import load_prompt

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# PII patterns
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("phone", re.compile(r"\+?\d[\d\-\s]{8,}\d")),
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    (
        "address",
        re.compile(
            r"\b\d{1,5}\s+[\w\s]{2,30}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b",
            re.IGNORECASE,
        ),
    ),
]

# ---------------------------------------------------------------------------
# Prompt injection — regex patterns (layer 1)
# ---------------------------------------------------------------------------

_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions", re.IGNORECASE
    ),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)", re.IGNORECASE),
    re.compile(r"system\s*:\s*", re.IGNORECASE),
    re.compile(r"<\|(?:im_start|system|endoftext)\|>", re.IGNORECASE),
    re.compile(r"(?:disregard|forget)\s+(?:everything|all)", re.IGNORECASE),
    re.compile(
        r"do\s+not\s+follow\s+(?:your|the)\s+(?:rules|instructions)", re.IGNORECASE
    ),
]

# Regex to extract JSON from LLM response (handles markdown code blocks)
_JSON_RE = re.compile(r'\{[^{}]*"is_injection"\s*:\s*(?:true|false)\s*[^{}]*\}')


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitize_pii(text: str) -> tuple[str, int]:
    """Replace PII patterns with redacted placeholders. Returns (sanitized, count)."""
    count = 0
    sanitized = text
    for pii_type, pattern in _PII_PATTERNS:
        matches = pattern.findall(sanitized)
        count += len(matches)
        sanitized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", sanitized)
    return sanitized, count


def _detect_prompt_injection_regex(text: str) -> bool:
    """Layer 1: Return True if any regex injection pattern matches."""
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


async def _detect_prompt_injection_llm(model: BaseChatModel, text: str) -> bool:
    """Layer 2: Use FAST-tier LLM to detect sophisticated prompt injection."""
    prompt_template = load_prompt("guardrail")
    messages = [
        SystemMessage(content=prompt_template),
        HumanMessage(content=text[:4000]),  # limit to avoid excessive token use
    ]
    try:
        response = await model.ainvoke(messages)
        raw = response.content if isinstance(response.content, str) else str(response.content)
        return _parse_llm_injection_response(raw)
    except Exception:
        logger.exception("guardrail_llm_failed")
        return False  # fail open — regex layer already ran


def _parse_llm_injection_response(raw: str) -> bool:
    """Parse the guardrail LLM response to extract is_injection flag."""
    # Try direct JSON parse
    try:
        parsed = json.loads(raw.strip())
        return bool(parsed.get("is_injection", False))
    except (json.JSONDecodeError, AttributeError):
        pass

    # Try extracting JSON from within the response
    match = _JSON_RE.search(raw)
    if match:
        try:
            parsed = json.loads(match.group())
            return bool(parsed.get("is_injection", False))
        except (json.JSONDecodeError, AttributeError):
            pass

    logger.warning("guardrail_llm_parse_failed", raw_response=raw[:200])
    return False


# ---------------------------------------------------------------------------
# Standalone guardrail check (for use outside the pipeline)
# ---------------------------------------------------------------------------


@dataclass
class GuardrailResult:
    """Result of a guardrail check on arbitrary user text."""

    sanitized_text: str
    pii_items_found: int
    prompt_injection_detected: bool
    detection_source: str  # "regex", "llm", or "none"


async def check_guardrail(
    text: str,
    model: BaseChatModel | None = None,
) -> GuardrailResult:
    """Run guardrail checks on arbitrary user text.

    Used by use cases that accept free-text from users (additional_context,
    CV text, etc.) before passing it to an LLM prompt.

    Args:
        text: The user-supplied text to check.
        model: Optional FAST-tier LLM for deeper injection detection.

    Returns:
        GuardrailResult with sanitized text and detection flags.
    """
    sanitized, pii_count = _sanitize_pii(text)

    # Layer 1: regex (fast, synchronous)
    if _detect_prompt_injection_regex(text):
        logger.warning("guardrail_injection_regex", text_preview=text[:100])
        return GuardrailResult(
            sanitized_text=sanitized,
            pii_items_found=pii_count,
            prompt_injection_detected=True,
            detection_source="regex",
        )

    # Layer 2: LLM (deeper analysis)
    if model is not None:
        llm_detected = await _detect_prompt_injection_llm(model, text)
        if llm_detected:
            logger.warning("guardrail_injection_llm", text_preview=text[:100])
            return GuardrailResult(
                sanitized_text=sanitized,
                pii_items_found=pii_count,
                prompt_injection_detected=True,
                detection_source="llm",
            )

    return GuardrailResult(
        sanitized_text=sanitized,
        pii_items_found=pii_count,
        prompt_injection_detected=False,
        detection_source="none",
    )


# ---------------------------------------------------------------------------
# Pipeline node (factory pattern — like other agents)
# ---------------------------------------------------------------------------


def create_guardrail_node(model: BaseChatModel | None = None):
    """Factory: returns a guardrail node function for the pipeline graph.

    Args:
        model: Optional FAST-tier LLM for deeper prompt injection detection.
    """

    async def guardrail_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        raw = state["raw_input"]
        result = await check_guardrail(raw, model=model)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        detail = f"PII items redacted: {result.pii_items_found}"
        source = "regex+llm" if model is not None else "regex"
        if result.prompt_injection_detected:
            detail += f" | PROMPT INJECTION DETECTED (via {result.detection_source})"

        log_entry: StepLog = {
            "step": "guardrail",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(UTC).isoformat(),
            "detail": f"{detail} [{source}]",
        }

        return {
            "sanitized_text": result.sanitized_text,
            "pii_items_found": result.pii_items_found,
            "prompt_injection_detected": result.prompt_injection_detected,
            "current_step": "guardrail",
            "pipeline_log": [log_entry],
        }

    return guardrail_node
