"""
Tests for F4-T1/F4-T2/F4-T3: Timed WAIT Action.

- F4-T1: Action dataclass must have `wait_duration_seconds: Optional[int] = None`
- F4-T2: _parse_action_response parses wait_duration_seconds from JSON dict
         _build_decision_system_prompt schema includes wait_duration_seconds
- F4-T3: _execute_action WAIT handler calls asyncio.sleep(wait_duration_seconds or 1)
"""

import asyncio
import unittest
from unittest.mock import patch, AsyncMock

from tests.ui.investor_journey_agent.llm_brain import Action, ActionType, LLMBrain
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
from tests.ui.investor_journey_agent.personas import get_persona


def _make_wait_action(**kwargs):
    """Helper: create a minimal WAIT Action with extra kwargs."""
    return Action(
        action_type=ActionType.WAIT,
        target="",
        thought="",
        frustration_level=0.0,
        confidence=1.0,
        **kwargs,
    )


# ============================================================
# F4-T1: Action.wait_duration_seconds field
# ============================================================


class TestActionWaitDurationField(unittest.TestCase):
    """F4-T1: Action dataclass must have wait_duration_seconds Optional[int] field."""

    def test_action_has_wait_duration_seconds_field(self):
        """Action dataclass must expose a wait_duration_seconds attribute."""
        action = _make_wait_action()
        self.assertTrue(
            hasattr(action, "wait_duration_seconds"),
            "Action dataclass is missing `wait_duration_seconds` field. "
            "Add `wait_duration_seconds: Optional[int] = None` to the Action dataclass in llm_brain.py.",
        )

    def test_wait_duration_seconds_defaults_to_none(self):
        """wait_duration_seconds must default to None when not provided."""
        action = _make_wait_action()
        self.assertIsNone(
            action.wait_duration_seconds,
            "Action.wait_duration_seconds should default to None when not specified.",
        )

    def test_action_accepts_wait_duration_seconds_value(self):
        """Action should store wait_duration_seconds=45 when explicitly provided."""
        action = _make_wait_action(wait_duration_seconds=45)
        self.assertEqual(
            action.wait_duration_seconds,
            45,
            "Action should store wait_duration_seconds=45 when provided.",
        )

    def test_action_accepts_wait_duration_seconds_one(self):
        """Action should handle wait_duration_seconds=1 (minimum meaningful value)."""
        action = _make_wait_action(wait_duration_seconds=1)
        self.assertEqual(
            action.wait_duration_seconds,
            1,
            "Action should store wait_duration_seconds=1 when provided.",
        )


# ============================================================
# F4-T2: LLM JSON schema and _parse_action_response
# ============================================================


class TestParseActionResponseWaitDuration(unittest.TestCase):
    """F4-T2: _parse_action_response must extract wait_duration_seconds from JSON dict."""

    def _make_brain(self):
        """Create LLMBrain bypassing __init__ (no API key needed)."""
        return LLMBrain.__new__(LLMBrain)

    def test_parse_action_response_extracts_wait_duration_seconds(self):
        """_parse_action_response must set wait_duration_seconds from the JSON dict."""
        brain = self._make_brain()
        data = {
            "action_type": "wait",
            "target": "",
            "thought": "waiting for pipeline",
            "frustration_level": 0.0,
            "confidence": 1.0,
            "wait_duration_seconds": 45,
        }
        action = brain._parse_action_response(data)
        self.assertEqual(
            action.wait_duration_seconds,
            45,
            "_parse_action_response must extract wait_duration_seconds=45 from the JSON dict. "
            "Add `wait_duration_seconds=data.get('wait_duration_seconds')` to the Action(...) "
            "call in _parse_action_response() in llm_brain.py.",
        )

    def test_parse_action_response_defaults_wait_duration_to_none(self):
        """_parse_action_response must default wait_duration_seconds to None when absent."""
        brain = self._make_brain()
        data = {
            "action_type": "wait",
            "target": "",
            "thought": "waiting",
            "frustration_level": 0.0,
            "confidence": 1.0,
        }
        action = brain._parse_action_response(data)
        self.assertIsNone(
            action.wait_duration_seconds,
            "wait_duration_seconds must be None when not present in the JSON dict.",
        )


class TestDecisionPromptIncludesWaitDuration(unittest.TestCase):
    """F4-T2: _build_decision_system_prompt must include wait_duration_seconds in schema."""

    def _make_brain(self):
        """Create LLMBrain bypassing __init__ (no API key needed)."""
        return LLMBrain.__new__(LLMBrain)

    def test_decision_prompt_schema_includes_wait_duration_seconds(self):
        """_build_decision_system_prompt must include 'wait_duration_seconds' in JSON schema."""
        brain = self._make_brain()
        persona = get_persona("investor")
        prompt = brain._build_decision_system_prompt(persona, "explore the app")
        self.assertIn(
            "wait_duration_seconds",
            prompt,
            "The LLM decision prompt JSON schema must include 'wait_duration_seconds'. "
            "Add `\"wait_duration_seconds\": <optional integer>` to the JSON schema block "
            "in _build_decision_system_prompt() in llm_brain.py.",
        )


# ============================================================
# F4-T3: Agent WAIT handler uses wait_duration_seconds
# ============================================================


class TestWaitHandlerUsesDuration(unittest.IsolatedAsyncioTestCase):
    """F4-T3: _execute_action WAIT handler must use action.wait_duration_seconds."""

    def _make_agent(self):
        """Create a bare InvestorJourneyAgent instance (bypasses __init__)."""
        return InvestorJourneyAgent.__new__(InvestorJourneyAgent)

    async def test_wait_action_sleeps_for_wait_duration_seconds(self):
        """WAIT action with wait_duration_seconds=45 must sleep for 45s (not 1s)."""
        agent = self._make_agent()
        action = _make_wait_action(wait_duration_seconds=45)
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await agent._execute_action(action)
        self.assertEqual(
            mock_sleep.call_args[0][0],
            45,
            "WAIT action with wait_duration_seconds=45 must call asyncio.sleep(45), "
            "not asyncio.sleep(1). Change the WAIT handler in _execute_action() to use "
            "`asyncio.sleep(action.wait_duration_seconds or 1)`.",
        )

    async def test_wait_action_defaults_to_1s_when_duration_is_none(self):
        """WAIT action with wait_duration_seconds=None must sleep for 1 second (default)."""
        agent = self._make_agent()
        action = _make_wait_action()  # wait_duration_seconds defaults to None
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await agent._execute_action(action)
        self.assertEqual(
            mock_sleep.call_args[0][0],
            1,
            "WAIT action with wait_duration_seconds=None must call asyncio.sleep(1), "
            "the default. Change the WAIT handler in _execute_action() to use "
            "`asyncio.sleep(action.wait_duration_seconds or 1)`.",
        )


if __name__ == "__main__":
    unittest.main()
