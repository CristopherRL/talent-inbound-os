"""Unit tests for the Gatekeeper agent (spam classification)."""

import pytest

from talent_inbound.modules.pipeline.infrastructure.agents.gatekeeper import (
    create_gatekeeper_node,
)


class TestGatekeeperAgent:
    """Tests for the mock/heuristic classifier (no LLM)."""

    @pytest.fixture
    def node(self):
        return create_gatekeeper_node(model=None)

    async def test_real_offer_detected(self, node):
        state = {
            "sanitized_text": (
                "Hi, I'm a recruiter looking for a Senior Backend Engineer. "
                "The role is remote, salary $150K, Python stack. "
                "Our company is hiring for a client opportunity."
            ),
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["classification"] == "REAL_OFFER"
        assert result["classification_confidence"] > 0.5

    async def test_spam_detected(self, node):
        state = {
            "sanitized_text": (
                "Click here to claim your FREE prize! "
                "You are the winner of our bitcoin giveaway. "
                "Limited time investment opportunity!"
            ),
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["classification"] == "SPAM"

    async def test_not_an_offer(self, node):
        state = {
            "sanitized_text": "Thanks for connecting on LinkedIn! Let's stay in touch.",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["classification"] == "NOT_AN_OFFER"

    async def test_logs_step_metadata(self, node):
        state = {
            "sanitized_text": "Some text about a role",
            "raw_input": "",
            "pipeline_log": [],
        }
        result = await node(state)
        assert len(result["pipeline_log"]) == 1
        log = result["pipeline_log"][0]
        assert log["step"] == "gatekeeper"
        assert log["status"] == "completed"
        assert "heuristic" in log["detail"]

    async def test_uses_sanitized_text(self, node):
        state = {
            "sanitized_text": "This is a recruiter hiring for a developer role at our company",
            "raw_input": "should not be used",
            "pipeline_log": [],
        }
        result = await node(state)
        assert result["classification"] == "REAL_OFFER"
