"""Integration test for the full pipeline graph with mock LLM.

Tests the complete LangGraph flow using the heuristic/mock fallbacks
(no real LLM calls). Pipeline steps read from config.
"""

import pytest

from talent_inbound.config import get_settings
from talent_inbound.modules.pipeline.domain.state import PipelineState
from talent_inbound.modules.pipeline.infrastructure.graphs import build_main_pipeline

PIPELINE_STEPS = get_settings().pipeline_steps


@pytest.mark.integration
class TestPipelineGraph:
    """Tests for the compiled LangGraph pipeline."""

    @pytest.fixture
    def graph(self):
        return build_main_pipeline(model_router=None)

    async def test_real_offer_flows_through_all_nodes(self, graph):
        initial: PipelineState = {
            "raw_input": (
                "Hi, I'm a recruiter at Acme Corp. We have a Senior Backend Engineer "
                "role, fully remote, $150-180K. Stack: Python, FastAPI, PostgreSQL. "
                "Looking for someone to join our team."
            ),
            "interaction_id": "test-int-1",
            "opportunity_id": "test-opp-1",
            "candidate_id": "test-user",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        # All pipeline steps should have executed
        steps = [log["step"] for log in result["pipeline_log"]]
        assert steps == PIPELINE_STEPS

        # Classification
        assert result["classification"] == "REAL_OFFER"

        # Extraction
        extracted = result["extracted_data"]
        assert extracted["company_name"] is not None
        assert extracted["work_model"] == "REMOTE"
        assert "Python" in extracted["tech_stack"]

    async def test_spam_skips_extractor(self, graph):
        initial: PipelineState = {
            "raw_input": (
                "Click here to claim your FREE bitcoin prize! "
                "Limited time investment guaranteed returns!"
            ),
            "interaction_id": "test-int-2",
            "opportunity_id": "test-opp-2",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        steps = [log["step"] for log in result["pipeline_log"]]
        assert "guardrail" in steps
        assert "gatekeeper" in steps
        assert "extractor" not in steps
        assert result["classification"] == "SPAM"

    async def test_pii_is_sanitized_before_classification(self, graph):
        initial: PipelineState = {
            "raw_input": (
                "Call me at +1-555-123-4567 or email recruiter@acme.com. "
                "We have a Senior Engineer role at Acme Corp, remote, Python stack."
            ),
            "interaction_id": "test-int-3",
            "opportunity_id": "test-opp-3",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        assert result["pii_items_found"] >= 2
        assert "+1-555-123-4567" not in result["sanitized_text"]
        assert "recruiter@acme.com" not in result["sanitized_text"]
        # Still classified as real offer
        assert result["classification"] == "REAL_OFFER"

    async def test_pipeline_log_has_timestamps(self, graph):
        initial: PipelineState = {
            "raw_input": "Senior Developer role at TechCo, remote, hiring now",
            "interaction_id": "test-int-4",
            "opportunity_id": "test-opp-4",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        for log in result["pipeline_log"]:
            assert "timestamp" in log
            assert "latency_ms" in log
            assert log["latency_ms"] >= 0

    async def test_not_an_offer_skips_extractor(self, graph):
        initial: PipelineState = {
            "raw_input": "Thanks for connecting! Hope we can catch up sometime.",
            "interaction_id": "test-int-5",
            "opportunity_id": "test-opp-5",
            "pipeline_log": [],
        }
        result = await graph.ainvoke(initial)

        steps = [log["step"] for log in result["pipeline_log"]]
        assert "extractor" not in steps
        assert result["classification"] == "NOT_AN_OFFER"
