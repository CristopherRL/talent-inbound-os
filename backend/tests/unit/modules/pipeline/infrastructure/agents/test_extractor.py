"""Unit tests for the Extractor agent (structured data extraction)."""

import pytest

from talent_inbound.modules.pipeline.infrastructure.agents.extractor import (
    create_extractor_node,
)


class TestExtractorAgent:
    """Tests for the mock/heuristic extractor (no LLM)."""

    @pytest.fixture
    def node(self):
        return create_extractor_node(model=None)

    async def test_extracts_company_name(self, node):
        state = {
            "sanitized_text": "We have a role at Acme Corp for a Senior Engineer",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        extracted = result["extracted_data"]
        assert extracted["company_name"] == "Acme Corp"

    async def test_extracts_role_title(self, node):
        state = {
            "sanitized_text": "Looking for a Senior Backend Engineer to join our team",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        extracted = result["extracted_data"]
        assert "Engineer" in (extracted["role_title"] or "")

    async def test_extracts_tech_stack(self, node):
        state = {
            "sanitized_text": "Stack: Python, FastAPI, PostgreSQL, Docker, AWS",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        extracted = result["extracted_data"]
        assert "Python" in extracted["tech_stack"]
        assert "FastAPI" in extracted["tech_stack"]
        assert "PostgreSQL" in extracted["tech_stack"]

    async def test_extracts_work_model_remote(self, node):
        state = {
            "sanitized_text": "Fully remote position for a developer",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["extracted_data"]["work_model"] == "REMOTE"

    async def test_extracts_work_model_hybrid(self, node):
        state = {
            "sanitized_text": "Hybrid role, 2 days in office",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["extracted_data"]["work_model"] == "HYBRID"

    async def test_identifies_missing_critical_fields(self, node):
        state = {
            "sanitized_text": "Interesting opportunity, let me know if you want details",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        missing = result["extracted_data"]["missing_fields"]
        assert len(missing) > 0
        assert "salary_range" in missing

    async def test_extracts_recruiter_name(self, node):
        state = {
            "sanitized_text": "I'm Sarah Johnson from TechRecruit, we have a role for you",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["extracted_data"]["recruiter_name"] == "Sarah Johnson"

    async def test_full_extraction(self, node):
        state = {
            "sanitized_text": (
                "Hi, I'm Alex from Acme Corp. We have a Senior Backend Engineer "
                "role, fully remote, $150-180K salary. Stack: Python, FastAPI, AWS. "
                "Looking for someone to join our team."
            ),
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        extracted = result["extracted_data"]
        assert extracted["company_name"] is not None
        assert extracted["role_title"] is not None
        assert extracted["work_model"] == "REMOTE"
        assert len(extracted["tech_stack"]) > 0

    async def test_logs_step_metadata(self, node):
        state = {
            "sanitized_text": "Some job message",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert len(result["pipeline_log"]) == 1
        log = result["pipeline_log"][0]
        assert log["step"] == "extractor"
        assert log["status"] == "completed"
