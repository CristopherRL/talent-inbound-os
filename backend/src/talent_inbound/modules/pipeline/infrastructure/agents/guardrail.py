"""Guardrail agent — PII detection/sanitization and prompt injection detection.

This agent uses regex patterns (no LLM call), so it runs on the FAST tier
but doesn't actually need a model. It's the first node in the pipeline.
"""

import re
import time
from datetime import UTC, datetime

from talent_inbound.modules.pipeline.domain.state import PipelineState, StepLog

# PII patterns (phone numbers, email addresses, SSN-like patterns, street addresses)
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

# Prompt injection patterns
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


def _sanitize_pii(text: str) -> tuple[str, int]:
    """Replace PII patterns with redacted placeholders. Returns (sanitized, count)."""
    count = 0
    sanitized = text
    for pii_type, pattern in _PII_PATTERNS:
        matches = pattern.findall(sanitized)
        count += len(matches)
        sanitized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", sanitized)
    return sanitized, count


def _detect_prompt_injection(text: str) -> bool:
    """Return True if any prompt injection pattern is detected."""
    return any(pattern.search(text) for pattern in _INJECTION_PATTERNS)


def guardrail_node(state: PipelineState) -> dict:
    """Guardrail pipeline node: sanitize PII and detect prompt injection."""
    start = time.perf_counter()

    raw = state["raw_input"]
    sanitized, pii_count = _sanitize_pii(raw)
    injection = _detect_prompt_injection(raw)

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    detail = f"PII items redacted: {pii_count}"
    if injection:
        detail += " | PROMPT INJECTION DETECTED"

    log_entry: StepLog = {
        "step": "guardrail",
        "status": "completed",
        "latency_ms": elapsed_ms,
        "tokens": 0,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": detail,
    }

    return {
        "sanitized_text": sanitized,
        "pii_items_found": pii_count,
        "prompt_injection_detected": injection,
        "current_step": "guardrail",
        "pipeline_log": [log_entry],
    }
