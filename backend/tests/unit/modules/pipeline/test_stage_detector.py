"""Unit tests for Stage Detector heuristic detection."""

import pytest

from talent_inbound.modules.pipeline.infrastructure.agents.stage_detector import (
    _heuristic_detect,
    _is_forward_move,
)


class TestIsForwardMove:
    def test_discovery_to_engaging(self):
        assert _is_forward_move("DISCOVERY", "ENGAGING") is True

    def test_engaging_to_interviewing(self):
        assert _is_forward_move("ENGAGING", "INTERVIEWING") is True

    def test_interviewing_to_negotiating(self):
        assert _is_forward_move("INTERVIEWING", "NEGOTIATING") is True

    def test_backward_move(self):
        assert _is_forward_move("INTERVIEWING", "DISCOVERY") is False

    def test_same_stage(self):
        assert _is_forward_move("ENGAGING", "ENGAGING") is False

    def test_invalid_stage(self):
        assert _is_forward_move("INVALID", "ENGAGING") is False

    def test_terminal_stage(self):
        assert _is_forward_move("OFFER", "ENGAGING") is False


class TestHeuristicDetect:
    def test_interview_signal(self):
        text = "We'd like to schedule a technical interview for next week."
        stage, reason = _heuristic_detect(text, "ENGAGING")
        assert stage == "INTERVIEWING"
        assert reason is not None

    def test_negotiating_signal(self):
        text = "Here's our compensation package: base salary 120K plus equity."
        stage, reason = _heuristic_detect(text, "INTERVIEWING")
        assert stage == "NEGOTIATING"
        assert reason is not None

    def test_no_signal(self):
        text = "Thanks for your interest. We'll get back to you soon."
        stage, reason = _heuristic_detect(text, "DISCOVERY")
        assert stage is None
        assert reason is None

    def test_no_backward_suggestion(self):
        text = "We'd like to schedule an interview."
        # Already at INTERVIEWING — should not suggest INTERVIEWING again
        stage, reason = _heuristic_detect(text, "INTERVIEWING")
        assert stage is None

    def test_negotiating_from_discovery_suggests_negotiating(self):
        text = "We want to discuss the offer letter and start date."
        stage, reason = _heuristic_detect(text, "DISCOVERY")
        assert stage == "NEGOTIATING"

    def test_phone_screen_suggests_interviewing(self):
        text = "Let's schedule a phone screen to discuss the role further."
        stage, reason = _heuristic_detect(text, "ENGAGING")
        assert stage == "INTERVIEWING"

    def test_coding_challenge_suggests_interviewing(self):
        text = "Please complete this coding challenge before our next meeting."
        stage, reason = _heuristic_detect(text, "ENGAGING")
        assert stage == "INTERVIEWING"
