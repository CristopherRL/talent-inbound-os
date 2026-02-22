"""Language Detector agent — identifies the language of the recruiter message.

Uses FAST-tier LLM when available, falls back to keyword-based heuristic
for mock-first development and testing. Returns an ISO 639-1 code
("en", "es") that downstream agents (Communicator) use to draft responses
in the correct language.
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

logger = structlog.get_logger()

_ALLOWED_LANGUAGES = {"en", "es"}

# Spanish markers for the mock/heuristic detector
_SPANISH_MARKERS = [
    r"\b(hola|estimado|estimada|somos|tenemos|posición|posicion)\b",
    r"\b(salario|remoto|empresa|equipo|interesa|buscamos)\b",
    r"\b(oferta|puesto|trabajar|experiencia en)\b",
    r"\b(te gustaría|nos gustaría|estaríamos|podríamos)\b",
    r"[áéíóúñ¿¡]",
]

# Regex to extract JSON from LLM response (handles markdown code blocks, extra text)
_JSON_RE = re.compile(r'\{[^{}]*"language"\s*:\s*"[^"]+"\s*[^{}]*\}')


def _mock_detect(text: str) -> str:
    """Keyword heuristic: count Spanish markers, default to English."""
    lower = text.lower()
    score = sum(1 for pattern in _SPANISH_MARKERS if re.search(pattern, lower))
    return "es" if score >= 2 else "en"


def _parse_llm_response(raw: str) -> str | None:
    """Extract language code from LLM response, handling various formats.

    The LLM may return:
    - Clean JSON: {"language": "es"}
    - Markdown-wrapped: ```json\n{"language": "es"}\n```
    - With extra text: "The language is Spanish.\n{"language": "es"}"
    """
    # Try direct parse first
    try:
        parsed = json.loads(raw.strip())
        lang = parsed.get("language")
        if lang and lang in _ALLOWED_LANGUAGES:
            return lang
    except (json.JSONDecodeError, AttributeError):
        pass

    # Try extracting JSON from within the response
    match = _JSON_RE.search(raw)
    if match:
        try:
            parsed = json.loads(match.group())
            lang = parsed.get("language")
            if lang and lang in _ALLOWED_LANGUAGES:
                return lang
        except (json.JSONDecodeError, AttributeError):
            pass

    # Try finding bare language codes in the response
    lower = raw.lower().strip()
    if '"es"' in lower or "'es'" in lower or lower.endswith("es"):
        return "es"

    return None


async def _llm_detect(model: BaseChatModel, text: str) -> str:
    """Use FAST-tier LLM to detect language, with heuristic fallback."""
    prompt_template = load_prompt("language_detector")
    messages = [
        SystemMessage(content=prompt_template),
        HumanMessage(content=text),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    raw = content if isinstance(content, str) else str(content)

    lang = _parse_llm_response(raw)
    if lang:
        logger.debug("language_detector_llm", detected=lang, raw_response=raw[:200])
        return lang

    # LLM response unparseable — fall back to heuristic instead of defaulting to "en"
    heuristic_lang = _mock_detect(text)
    logger.warning(
        "language_detector_llm_parse_failed",
        raw_response=raw[:200],
        heuristic_fallback=heuristic_lang,
    )
    return heuristic_lang


def create_language_detector_node(model: BaseChatModel | None = None):
    """Factory: returns a language detector node function for the pipeline graph."""

    async def language_detector_node(state: PipelineState) -> dict:
        start = time.perf_counter()

        text = state.get("sanitized_text") or state.get("raw_input", "")

        if model is not None:
            lang = await _llm_detect(model, text)
            source = "llm"
        else:
            lang = _mock_detect(text)
            source = "heuristic"

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        log_entry: StepLog = {
            "step": "language_detector",
            "status": "completed",
            "latency_ms": elapsed_ms,
            "tokens": 0,
            "timestamp": datetime.now(UTC).isoformat(),
            "detail": f"Detected language: {lang} via {source}",
        }

        return {
            "detected_language": lang,
            "current_step": "language_detector",
            "pipeline_log": [log_entry],
        }

    return language_detector_node
