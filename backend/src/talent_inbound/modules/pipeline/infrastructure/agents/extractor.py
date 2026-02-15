"""Extractor agent — extracts structured data from recruiter messages.

Uses SMART-tier LLM when available, falls back to regex-based heuristic
for mock-first development and testing. Includes hallucination check.
"""

import json
import re
import time
from datetime import datetime, timezone

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from talent_inbound.modules.pipeline.domain.state import (
    ExtractedData,
    PipelineState,
    StepLog,
)
from talent_inbound.modules.pipeline.prompts import load_known_techs, load_prompt

_CRITICAL_FIELDS = ["salary_range", "tech_stack", "role_title"]


def _hallucination_check(
    extracted: ExtractedData, source_text: str
) -> list[str]:
    """Flag fields whose values don't appear in the source text."""
    warnings = []
    lower_source = source_text.lower()

    for field in ("company_name", "role_title"):
        value = extracted.get(field)
        if value and value.lower() not in lower_source:
            warnings.append(f"{field}='{value}' not found in source text")

    return warnings


def _mock_extract(text: str) -> ExtractedData:
    """Regex-based heuristic extraction for mock-first development."""
    lower = text.lower()

    # Company name: look for "at <Company>" or "from <Company>"
    company = None
    m = re.search(
        r"(?:at|from|with)\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\.|,|\s+(?:we|is|are|looking|for|and))",
        text,
    )
    if m:
        company = m.group(1).strip()

    # Role title
    role = None
    m = re.search(
        r"((?:Senior|Staff|Principal|Lead|Junior)?\s*\w+\s*(?:Engineer|Developer|Architect|Manager))",
        text,
        re.IGNORECASE,
    )
    if m:
        role = m.group(1).strip()

    # Salary
    salary = None
    m = re.search(
        r"[\$\u20ac\u00a3]?\s*\d{2,3}[kK,\d]*\s*[-\u2013to]+\s*[\$\u20ac\u00a3]?\s*\d{2,3}[kK,\d]*",
        text,
    )
    if m:
        salary = m.group(0).strip()

    # Tech stack — loaded from external file
    known_techs = load_known_techs()
    stack = [tech for tech in known_techs if tech.lower() in lower]

    # Work model
    work_model = None
    if "remote" in lower and "hybrid" not in lower:
        work_model = "REMOTE"
    elif "hybrid" in lower:
        work_model = "HYBRID"
    elif "onsite" in lower or "on-site" in lower or "in-office" in lower:
        work_model = "ONSITE"

    # Recruiter name (look for "I'm <Name>" or "My name is <Name>")
    recruiter_name = None
    m = re.search(
        r"(?:I'?m|my name is|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text
    )
    if m:
        recruiter_name = m.group(1).strip()

    extracted: ExtractedData = {
        "company_name": company,
        "client_name": None,
        "role_title": role,
        "salary_range": salary,
        "tech_stack": stack,
        "work_model": work_model,
        "recruiter_name": recruiter_name,
        "recruiter_type": None,
        "recruiter_company": None,
        "missing_fields": [],
    }

    missing = [f for f in _CRITICAL_FIELDS if not extracted.get(f)]
    extracted["missing_fields"] = missing

    return extracted


def _parse_llm_json(raw: str) -> dict | None:
    """Try to parse JSON from LLM output, stripping markdown fences if present."""
    text = raw.strip()
    if not text:
        return None
    if text.startswith("```"):
        first_nl = text.index("\n") if "\n" in text else 3
        text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


async def _llm_extract(model: BaseChatModel, text: str) -> ExtractedData:
    """Use LLM to extract structured data."""
    import structlog

    system_prompt = load_prompt("extractor")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=text),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    # Handle list-type content blocks (Anthropic API)
    if isinstance(content, list):
        text_parts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"]
        content = " ".join(text_parts) if text_parts else ""
    if isinstance(content, str):
        parsed = _parse_llm_json(content)
        if parsed:
            missing = [f for f in _CRITICAL_FIELDS if not parsed.get(f)]
            parsed["missing_fields"] = missing
            return ExtractedData(**parsed)
        structlog.get_logger().warning(
            "extractor_llm_json_parse_failed",
            content_preview=str(content)[:200],
        )
    return _mock_extract(text)


def create_extractor_node(model: BaseChatModel | None = None):
    """Factory: returns an extractor node function with optional LLM model."""

    async def extractor_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        text = state.get("sanitized_text", state["raw_input"])

        if model is not None:
            extracted = await _llm_extract(model, text)
            source = "llm"
        else:
            extracted = _mock_extract(text)
            source = "heuristic"

        # Hallucination check
        warnings = _hallucination_check(extracted, text)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        detail_parts = [
            f"Extracted via {source}",
            f"missing: {extracted.get('missing_fields', [])}",
        ]
        if warnings:
            detail_parts.append(f"hallucination warnings: {warnings}")

        log_entry: StepLog = {
            "step": "extractor",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "detail": " | ".join(detail_parts),
        }

        return {
            "extracted_data": extracted,
            "current_step": "extractor",
            "pipeline_log": [log_entry],
        }

    return extractor_node
