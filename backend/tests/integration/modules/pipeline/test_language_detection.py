"""Integration test for language detection in the pipeline.

Verifies that:
1. The Language Detector agent produces detected_language in pipeline state.
2. The Communicator agent reads detected_language and uses it in the LLM prompt.
3. generate_draft_standalone correctly uses the language parameter.
4. Explicit language override appears in the prompt.

Note: These tests mock the LLM — no real API key is required.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.agents.communicator import (
    create_communicator_node,
    generate_draft_standalone,
)
from talent_inbound.modules.pipeline.infrastructure.agents.language_detector import (
    create_language_detector_node,
)
from talent_inbound.modules.profile.domain.entities import CandidateProfile
from talent_inbound.shared.domain.enums import WorkModel


def _make_profile() -> CandidateProfile:
    return CandidateProfile(
        candidate_id="test-user",
        display_name="Test User",
        skills=["Python", "FastAPI", "PostgreSQL"],
        min_salary=80000,
        preferred_currency="EUR",
        work_model=WorkModel.REMOTE,
        preferred_locations=["Spain"],
        industries=["FinTech"],
    )


def _make_mock_model(response_text: str = "Draft response.") -> AsyncMock:
    """Return a mock LLM model that records calls and returns a fixed response."""
    mock_response = MagicMock()
    mock_response.content = response_text
    model = AsyncMock()
    model.ainvoke = AsyncMock(return_value=mock_response)
    return model


def _get_system_prompt(model: AsyncMock) -> str:
    """Extract the system prompt content from the first LLM call."""
    call_args = model.ainvoke.call_args
    messages = call_args[0][0]  # first positional arg: list of messages
    return messages[0].content


@pytest.mark.integration
class TestLanguageDetectionPipeline:
    """Verify language detection flows through the pipeline correctly."""

    async def test_language_detector_detects_spanish(self):
        """Language Detector with mock LLM returns 'es' for Spanish JSON."""
        lang_model = _make_mock_model('{"language": "es"}')

        state: PipelineState = {
            "raw_input": "Hola, tenemos una posición de Senior Engineer.",
            "sanitized_text": "Hola, tenemos una posición de Senior Engineer.",
            "interaction_id": "lang-es-1",
            "opportunity_id": "opp-lang-1",
            "candidate_id": "test-user",
            "pipeline_log": [],
        }

        node = create_language_detector_node(model=lang_model)
        result = await node(state)

        assert result["detected_language"] == "es"
        assert lang_model.ainvoke.called

    async def test_communicator_uses_detected_language(self):
        """Communicator reads detected_language from state and includes it in prompt."""
        comm_model = _make_mock_model("Gracias por contactarme.")
        profile_repo = AsyncMock()
        profile_repo.find_by_candidate_id.return_value = _make_profile()

        state: PipelineState = {
            "raw_input": "Hola, tenemos una posición.",
            "interaction_id": "lang-es-2",
            "opportunity_id": "opp-lang-2",
            "candidate_id": "test-user",
            "pipeline_log": [],
            "detected_language": "es",
            "extracted_data": {
                "company_name": "TechCorp",
                "role_title": "Senior Backend Engineer",
                "salary_range": "90-120K EUR",
                "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                "work_model": "REMOTE",
                "missing_fields": [],
            },
        }

        node = create_communicator_node(
            model=comm_model,
            profile_repo=profile_repo,
            response_type="EXPRESS_INTEREST",
        )
        result = await node(state)

        assert "draft_response" in result
        assert result["draft_response"], "Draft must be non-empty"
        assert comm_model.ainvoke.called

        system_prompt = _get_system_prompt(comm_model)
        assert "Spanish" in system_prompt, (
            "Communicator should include Spanish language instruction "
            "when detected_language is 'es'."
        )

    async def test_communicator_defaults_to_english_without_detected_language(self):
        """When no detected_language in state, communicator defaults to English."""
        comm_model = _make_mock_model("Thank you for reaching out.")
        profile_repo = AsyncMock()
        profile_repo.find_by_candidate_id.return_value = _make_profile()

        state: PipelineState = {
            "raw_input": "Hi, we have a position.",
            "interaction_id": "lang-en-1",
            "opportunity_id": "opp-lang-3",
            "candidate_id": "test-user",
            "pipeline_log": [],
            # detected_language intentionally omitted
            "extracted_data": {
                "company_name": "Acme Corp",
                "role_title": "Senior Backend Engineer",
                "tech_stack": [],
                "missing_fields": [],
            },
        }

        node = create_communicator_node(model=comm_model, profile_repo=profile_repo)
        result = await node(state)

        assert "draft_response" in result
        assert comm_model.ainvoke.called
        system_prompt = _get_system_prompt(comm_model)
        assert "English" in system_prompt

    async def test_standalone_draft_with_language_parameter(self):
        """generate_draft_standalone passes language to the LLM prompt."""
        model = _make_mock_model()

        await generate_draft_standalone(
            response_type="EXPRESS_INTEREST",
            extracted_data={
                "company_name": "Corp",
                "tech_stack": [],
                "missing_fields": [],
            },
            profile=_make_profile(),
            model=model,
            language="es",
        )

        assert model.ainvoke.called
        system_prompt = _get_system_prompt(model)
        assert "Spanish" in system_prompt

    async def test_standalone_draft_without_language_defaults_to_english(self):
        """generate_draft_standalone defaults to English when language is None."""
        model = _make_mock_model()

        await generate_draft_standalone(
            response_type="DECLINE",
            extracted_data={"company_name": "Corp", "tech_stack": [], "missing_fields": []},
            profile=_make_profile(),
            model=model,
            language=None,
        )

        assert model.ainvoke.called
        system_prompt = _get_system_prompt(model)
        assert "English" in system_prompt

    async def test_explicit_language_override_in_standalone(self):
        """When language is explicitly set, the instruction appears in the prompt."""
        model = _make_mock_model()

        await generate_draft_standalone(
            response_type="EXPRESS_INTEREST",
            extracted_data={
                "company_name": "Corp",
                "tech_stack": [],
                "missing_fields": [],
            },
            profile=_make_profile(),
            model=model,
            language="en",
        )

        assert model.ainvoke.called
        system_prompt = _get_system_prompt(model)
        assert "English" in system_prompt
