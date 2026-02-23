"""Unit tests for the Language Detector agent.

Verifies:
1. Mock mode detects English by default.
2. Mock mode detects Spanish from keyword markers.
3. LLM mode parses JSON response correctly (clean, markdown-wrapped, extra text).
4. LLM mode falls back to heuristic on unparseable response.
5. LLM mode falls back to English on unsupported language code.
6. Pipeline node returns correct state shape.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.agents.language_detector import (
    _mock_detect,
    _parse_llm_response,
    create_language_detector_node,
)


class TestMockDetect:
    """Tests for the keyword-based heuristic detector."""

    def test_english_text_returns_en(self):
        text = (
            "Hi, I'm a recruiter at Acme Corp. We have a Senior Backend Engineer "
            "role, fully remote, $150-180K. Stack: Python, FastAPI, AWS."
        )
        assert _mock_detect(text) == "en"

    def test_spanish_text_returns_es(self):
        text = (
            "Hola, soy reclutador en TechCorp. Tenemos una posición de Senior "
            "Backend Engineer, totalmente remoto, salario 90-120K EUR."
        )
        assert _mock_detect(text) == "es"

    def test_ambiguous_text_defaults_to_en(self):
        text = "Alejandro, Python, FastAPI, PostgreSQL, ACME Corp"
        assert _mock_detect(text) == "en"

    def test_spanish_accented_chars_count(self):
        text = "Podríamos hablar sobre la posición?"
        assert _mock_detect(text) == "es"

    def test_empty_text_returns_en(self):
        assert _mock_detect("") == "en"


class TestParseLlmResponse:
    """Tests for _parse_llm_response — robust JSON extraction from LLM output."""

    def test_clean_json(self):
        assert _parse_llm_response('{"language": "es"}') == "es"

    def test_json_with_whitespace(self):
        assert _parse_llm_response('  {"language": "en"}  \n') == "en"

    def test_markdown_code_block(self):
        raw = '```json\n{"language": "es"}\n```'
        assert _parse_llm_response(raw) == "es"

    def test_extra_text_before_json(self):
        raw = 'The text is in Spanish.\n{"language": "es"}'
        assert _parse_llm_response(raw) == "es"

    def test_extra_text_after_json(self):
        raw = '{"language": "es"}\nConfidence: high'
        assert _parse_llm_response(raw) == "es"

    def test_unsupported_language_returns_none(self):
        assert _parse_llm_response('{"language": "fr"}') is None

    def test_completely_unparseable(self):
        assert _parse_llm_response("I think it's Spanish") is None

    def test_bare_es_code_in_response(self):
        assert _parse_llm_response('language: "es"') == "es"

    def test_empty_response(self):
        assert _parse_llm_response("") is None


class TestLanguageDetectorNode:
    """Tests for the pipeline node function."""

    async def test_mock_mode_english(self):
        """Node without LLM returns 'en' for English text."""
        state: PipelineState = {
            "raw_input": "Hi, we have a position for you.",
            "sanitized_text": "Hi, we have a position for you.",
            "interaction_id": "test-1",
            "opportunity_id": "opp-1",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=None)
        result = await node(state)

        assert result["detected_language"] == "en"
        assert result["current_step"] == "language_detector"
        assert len(result["pipeline_log"]) == 1
        assert result["pipeline_log"][0]["step"] == "language_detector"
        assert result["pipeline_log"][0]["status"] == "completed"

    async def test_mock_mode_spanish(self):
        """Node without LLM returns 'es' for Spanish text."""
        state: PipelineState = {
            "raw_input": "Hola, tenemos una posición de Senior Engineer. ¿Te interesa?",
            "sanitized_text": "Hola, tenemos una posición de Senior Engineer. ¿Te interesa?",
            "interaction_id": "test-2",
            "opportunity_id": "opp-2",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=None)
        result = await node(state)

        assert result["detected_language"] == "es"

    async def test_llm_mode_parses_json(self):
        """Node with LLM parses valid JSON response."""
        mock_response = MagicMock()
        mock_response.content = '{"language": "es"}'
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=mock_response)

        state: PipelineState = {
            "raw_input": "Hola",
            "sanitized_text": "Hola",
            "interaction_id": "test-3",
            "opportunity_id": "opp-3",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=model)
        result = await node(state)

        assert result["detected_language"] == "es"
        assert model.ainvoke.called

    async def test_llm_mode_invalid_json_falls_back_to_heuristic(self):
        """Node with LLM falls back to heuristic on unparseable response."""
        mock_response = MagicMock()
        mock_response.content = "I cannot determine the language"
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=mock_response)

        # Spanish text → heuristic should detect "es"
        state: PipelineState = {
            "raw_input": "Hola, tenemos una posición para ti. ¿Te interesa?",
            "sanitized_text": "Hola, tenemos una posición para ti. ¿Te interesa?",
            "interaction_id": "test-4",
            "opportunity_id": "opp-4",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=model)
        result = await node(state)

        assert result["detected_language"] == "es"

    async def test_llm_mode_invalid_json_english_text_falls_back_to_en(self):
        """Node with LLM falls back to heuristic → 'en' for English text."""
        mock_response = MagicMock()
        mock_response.content = "I cannot determine the language"
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=mock_response)

        state: PipelineState = {
            "raw_input": "Hi, we have a great position for you.",
            "sanitized_text": "Hi, we have a great position for you.",
            "interaction_id": "test-4b",
            "opportunity_id": "opp-4b",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=model)
        result = await node(state)

        assert result["detected_language"] == "en"

    async def test_llm_mode_markdown_code_block(self):
        """Node with LLM correctly parses markdown-wrapped JSON."""
        mock_response = MagicMock()
        mock_response.content = '```json\n{"language": "es"}\n```'
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=mock_response)

        state: PipelineState = {
            "raw_input": "Hola",
            "sanitized_text": "Hola",
            "interaction_id": "test-4c",
            "opportunity_id": "opp-4c",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=model)
        result = await node(state)

        assert result["detected_language"] == "es"

    async def test_llm_mode_unsupported_language_falls_back_to_heuristic(self):
        """Node with LLM falls back to heuristic for unsupported language codes."""
        mock_response = MagicMock()
        mock_response.content = '{"language": "fr"}'
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=mock_response)

        state: PipelineState = {
            "raw_input": "Bonjour",
            "sanitized_text": "Bonjour",
            "interaction_id": "test-5",
            "opportunity_id": "opp-5",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=model)
        result = await node(state)

        # "Bonjour" has no Spanish markers → heuristic returns "en"
        assert result["detected_language"] == "en"

    async def test_uses_sanitized_text_over_raw_input(self):
        """Node prefers sanitized_text when available."""
        mock_response = MagicMock()
        mock_response.content = '{"language": "es"}'
        model = AsyncMock()
        model.ainvoke = AsyncMock(return_value=mock_response)

        state: PipelineState = {
            "raw_input": "Original with PII",
            "sanitized_text": "Hola, tenemos una posición",
            "interaction_id": "test-6",
            "opportunity_id": "opp-6",
            "candidate_id": "user-1",
            "pipeline_log": [],
        }
        node = create_language_detector_node(model=model)
        await node(state)

        # Verify the LLM received sanitized_text, not raw_input
        call_args = model.ainvoke.call_args[0][0]
        user_message = call_args[1].content
        assert user_message == "Hola, tenemos una posición"
