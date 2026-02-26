"""
Tests for journey agent infrastructure improvements.

- F2-T1: AgentConfig max_steps default = 200
- F2-T2: CLI --max-steps default = 200
- F3-T1: _do_step() helper method exists on InvestorJourneyAgent
"""

import inspect
import unittest

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.__main__ import build_parser
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# F2-T1: AgentConfig default max_steps = 200
# ============================================================


class TestAgentConfigDefaultSteps(unittest.TestCase):
    """F2-T1: Default max_steps in AgentConfig should be 200."""

    def test_default_max_steps_is_200(self):
        """AgentConfig().max_steps must default to 200, not 50."""
        config = AgentConfig()
        self.assertEqual(
            config.max_steps,
            200,
            f"Expected AgentConfig().max_steps == 200 but got {config.max_steps}. "
            "Change `max_steps: int = 50` to `max_steps: int = 200` in config.py.",
        )


# ============================================================
# F2-T2: CLI --max-steps default = 200
# ============================================================


class TestCLIDefaultMaxSteps(unittest.TestCase):
    """F2-T2: CLI --max-steps flag should default to 200."""

    def test_cli_max_steps_default_is_200(self):
        """build_parser() --max-steps default must be 200, not 20."""
        parser = build_parser()
        default = parser.get_default("max_steps")
        self.assertEqual(
            default,
            200,
            f"Expected --max-steps CLI default == 200 but got {default}. "
            "Change `default=20` to `default=200` in __main__.py --max-steps argument.",
        )


# ============================================================
# F3-T1: _do_step() helper method on InvestorJourneyAgent
# ============================================================


class TestDoStepHelper(unittest.TestCase):
    """F3-T1: InvestorJourneyAgent must have a _do_step() async helper method."""

    def test_agent_has_do_step_method(self):
        """_do_step() method must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_do_step"),
            "InvestorJourneyAgent must have a _do_step() method. "
            "Extract the per-step logic from run_journey() loop into _do_step().",
        )

    def test_do_step_is_async(self):
        """_do_step() must be an async coroutine function."""
        method = getattr(InvestorJourneyAgent, "_do_step", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent must have _do_step()")
        self.assertTrue(
            inspect.iscoroutinefunction(method),
            "_do_step() must be an async method (coroutine function) "
            "so it can be awaited in the async journey loop.",
        )


if __name__ == "__main__":
    unittest.main()
