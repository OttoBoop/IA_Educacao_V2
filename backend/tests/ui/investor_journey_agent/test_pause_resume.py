"""
Tests for F3-T2: Interactive Pause/Resume at Step Limit.

- F3-T2: _pause_and_extend() method on InvestorJourneyAgent
  - Exists and is async
  - Returns 0 when user enters "0" (stop signal)
  - Returns N when user enters positive integer N (extension count)
  - Re-prompts on non-integer input until valid
"""

import asyncio
import inspect
import unittest
from unittest.mock import patch

from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# F3-T2: _pause_and_extend() method exists
# ============================================================


class TestPauseAndExtendMethod(unittest.TestCase):
    """F3-T2: InvestorJourneyAgent must have _pause_and_extend() async method."""

    def test_agent_has_pause_and_extend_method(self):
        """_pause_and_extend() must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_pause_and_extend"),
            "InvestorJourneyAgent must have _pause_and_extend() method. "
            "Add outer pause/resume gate to run_journey() that prompts the user when step limit is hit.",
        )

    def test_pause_and_extend_is_async(self):
        """_pause_and_extend() must be an async coroutine function."""
        method = getattr(InvestorJourneyAgent, "_pause_and_extend", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent must have _pause_and_extend()")
        self.assertTrue(
            inspect.iscoroutinefunction(method),
            "_pause_and_extend() must be async (a coroutine function). "
            "Use `async def _pause_and_extend(...)` and `run_in_executor` for the blocking input() call.",
        )


# ============================================================
# F3-T2: _pause_and_extend() behavior with mocked input
# ============================================================


class TestPauseAndExtendBehavior(unittest.IsolatedAsyncioTestCase):
    """F3-T2: _pause_and_extend() prompts and returns the user's choice."""

    def _make_agent(self):
        """Create a bare InvestorJourneyAgent instance (bypasses __init__)."""
        return InvestorJourneyAgent.__new__(InvestorJourneyAgent)

    async def test_returns_zero_when_user_enters_zero(self):
        """Entering '0' should return 0 (stop the journey)."""
        agent = self._make_agent()
        with patch("builtins.input", return_value="0"):
            result = await agent._pause_and_extend(step_number=5)
        self.assertEqual(
            result,
            0,
            "Entering '0' should return 0 to signal 'stop the journey'.",
        )

    async def test_returns_extension_count_when_user_enters_positive_n(self):
        """Entering a positive integer N should return N (extend by N steps)."""
        agent = self._make_agent()
        with patch("builtins.input", return_value="5"):
            result = await agent._pause_and_extend(step_number=5)
        self.assertEqual(
            result,
            5,
            "Entering '5' should return 5, meaning 'extend the journey by 5 more steps'.",
        )

    async def test_reprompts_on_invalid_input_then_returns_valid(self):
        """Non-integer input should be re-prompted until valid integer is given."""
        agent = self._make_agent()
        # First call returns invalid "abc", second call returns "3"
        with patch("builtins.input", side_effect=["abc", "3"]):
            result = await agent._pause_and_extend(step_number=10)
        self.assertEqual(
            result,
            3,
            "Should skip 'abc' and return 3 after re-prompting.",
        )


if __name__ == "__main__":
    unittest.main()
