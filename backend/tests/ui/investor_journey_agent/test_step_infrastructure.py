"""
Tests for journey agent infrastructure improvements.

- F2-T1: AgentConfig max_steps default = 400 (updated from 200 for F5-T1)
- F2-T2: CLI --max-steps default = 400 (updated from 200 for F5-T1)
- F3-T1: _do_step() helper method exists on InvestorJourneyAgent
"""

import inspect
import unittest

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.__main__ import build_parser
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# F5-T1: AgentConfig default max_steps = 400
# ============================================================


class TestAgentConfigDefaultSteps(unittest.TestCase):
    """F5-T1: Default max_steps in AgentConfig should be 400."""

    def test_default_max_steps_is_400(self):
        """AgentConfig().max_steps must default to 400 for full pipeline verification."""
        config = AgentConfig()
        self.assertEqual(
            config.max_steps,
            400,
            f"Expected AgentConfig().max_steps == 400 but got {config.max_steps}. "
            "Change `max_steps: int = 200` to `max_steps: int = 400` in config.py.",
        )


# ============================================================
# F5-T1: CLI --max-steps default = 400
# ============================================================


class TestCLIDefaultMaxSteps(unittest.TestCase):
    """F5-T1: CLI --max-steps flag should default to 400."""

    def test_cli_max_steps_default_is_400(self):
        """build_parser() --max-steps default must be 400."""
        parser = build_parser()
        default = parser.get_default("max_steps")
        self.assertEqual(
            default,
            400,
            f"Expected --max-steps CLI default == 400 but got {default}. "
            "Change `default=200` to `default=400` in __main__.py --max-steps argument.",
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
