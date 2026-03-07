"""
Tests for F5-T5: Graceful Budget Exhaustion.

- InvestorJourneyAgent must have a `_check_budget(current_step)` sync method
  that returns a dict with keys: `remaining` (int), `total` (int), `is_low` (bool).
  - remaining = config.max_steps - current_step
  - is_low = True when remaining < 10% of max_steps
- InvestorJourneyAgent must have an `_on_budget_exhaustion()` sync method
  that calls `_write_verification_entry()` with status="PARTIAL" and details
  containing "budget exhausted", then returns the Path to the verification report.
"""

import tempfile
import unittest
from pathlib import Path

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# _check_budget: method existence and callability
# ============================================================


class TestCheckBudgetExists(unittest.TestCase):
    """F5-T5: InvestorJourneyAgent must have a _check_budget() method."""

    def test_agent_has_check_budget_method(self):
        """_check_budget() method must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_check_budget"),
            "InvestorJourneyAgent is missing `_check_budget` method. "
            "Add `def _check_budget(self, current_step: int) -> dict` to agent.py.",
        )

    def test_check_budget_is_callable(self):
        """_check_budget must be callable (not a property or plain attribute)."""
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        self.assertTrue(
            callable(method),
            "_check_budget must be a callable method on InvestorJourneyAgent, "
            "not a plain attribute or property.",
        )


# ============================================================
# _check_budget: return type and dict keys
# ============================================================


class TestCheckBudgetReturnType(unittest.TestCase):
    """F5-T5: _check_budget() must return a dict with the expected keys."""

    def _make_agent(self, tmp):
        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)
        agent.config = AgentConfig(output_dir=Path(tmp))
        return agent

    def test_check_budget_returns_dict(self):
        """_check_budget must return a dict."""
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            result = agent._check_budget(100)
            self.assertIsInstance(
                result,
                dict,
                "_check_budget must return a dict. "
                f"Got type: {type(result).__name__!r}.",
            )

    def test_check_budget_has_remaining_key(self):
        """The dict returned by _check_budget must have a 'remaining' key."""
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            result = agent._check_budget(100)
            self.assertIn(
                "remaining",
                result,
                "_check_budget must return a dict with a 'remaining' key. "
                f"Got keys: {list(result.keys())}",
            )

    def test_check_budget_has_total_key(self):
        """The dict returned by _check_budget must have a 'total' key."""
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            result = agent._check_budget(100)
            self.assertIn(
                "total",
                result,
                "_check_budget must return a dict with a 'total' key. "
                f"Got keys: {list(result.keys())}",
            )

    def test_check_budget_has_is_low_key(self):
        """The dict returned by _check_budget must have an 'is_low' key."""
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            result = agent._check_budget(100)
            self.assertIn(
                "is_low",
                result,
                "_check_budget must return a dict with an 'is_low' key. "
                f"Got keys: {list(result.keys())}",
            )


# ============================================================
# _check_budget: arithmetic correctness
# ============================================================


class TestCheckBudgetArithmetic(unittest.TestCase):
    """F5-T5: _check_budget() must compute remaining and is_low correctly."""

    def _make_agent(self, tmp):
        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)
        agent.config = AgentConfig(output_dir=Path(tmp))
        return agent

    def test_check_budget_remaining_correct(self):
        """remaining must equal config.max_steps - current_step.

        With default max_steps=400 and current_step=350, remaining must be 50.
        """
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            # max_steps defaults to 400
            result = agent._check_budget(350)
            self.assertEqual(
                result["remaining"],
                50,
                "remaining must equal config.max_steps - current_step. "
                "With max_steps=400 and current_step=350, expected remaining=50. "
                f"Got: {result.get('remaining')!r}",
            )

    def test_check_budget_is_low_when_under_10_percent(self):
        """is_low must be True when remaining < 10% of max_steps.

        With max_steps=400 and current_step=365, remaining=35 which is < 40 (10% of 400).
        is_low must be True.
        """
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            # max_steps=400, current_step=365 → remaining=35 → 35 < 40 → is_low=True
            result = agent._check_budget(365)
            self.assertTrue(
                result["is_low"],
                "is_low must be True when remaining < 10% of max_steps. "
                "With max_steps=400 and current_step=365, remaining=35 which is less than "
                "40 (10% of 400), so is_low must be True. "
                f"Got is_low={result.get('is_low')!r}",
            )

    def test_check_budget_is_not_low_when_above_10_percent(self):
        """is_low must be False when remaining >= 10% of max_steps.

        With max_steps=400 and current_step=100, remaining=300 which is >= 40 (10% of 400).
        is_low must be False.
        """
        method = getattr(InvestorJourneyAgent, "_check_budget", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_check_budget` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            # max_steps=400, current_step=100 → remaining=300 → 300 >= 40 → is_low=False
            result = agent._check_budget(100)
            self.assertFalse(
                result["is_low"],
                "is_low must be False when remaining >= 10% of max_steps. "
                "With max_steps=400 and current_step=100, remaining=300 which is not less than "
                "40 (10% of 400), so is_low must be False. "
                f"Got is_low={result.get('is_low')!r}",
            )


# ============================================================
# _on_budget_exhaustion: method existence and callability
# ============================================================


class TestOnBudgetExhaustionExists(unittest.TestCase):
    """F5-T5: InvestorJourneyAgent must have a _on_budget_exhaustion() method."""

    def test_agent_has_on_budget_exhaustion_method(self):
        """_on_budget_exhaustion() method must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_on_budget_exhaustion"),
            "InvestorJourneyAgent is missing `_on_budget_exhaustion` method. "
            "Add `def _on_budget_exhaustion(self) -> Path` to agent.py.",
        )

    def test_on_budget_exhaustion_is_callable(self):
        """_on_budget_exhaustion must be callable (not a property or plain attribute)."""
        method = getattr(InvestorJourneyAgent, "_on_budget_exhaustion", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_on_budget_exhaustion` before this test can run.",
        )
        self.assertTrue(
            callable(method),
            "_on_budget_exhaustion must be a callable method on InvestorJourneyAgent, "
            "not a plain attribute or property.",
        )


# ============================================================
# _on_budget_exhaustion: return type and file content
# ============================================================


class TestOnBudgetExhaustionBehavior(unittest.TestCase):
    """F5-T5: _on_budget_exhaustion() must write PARTIAL status and return a Path."""

    def _make_agent(self, tmp):
        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)
        agent.config = AgentConfig(output_dir=Path(tmp))
        return agent

    def test_on_budget_exhaustion_returns_path(self):
        """_on_budget_exhaustion must return a Path instance."""
        method = getattr(InvestorJourneyAgent, "_on_budget_exhaustion", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_on_budget_exhaustion` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            result = agent._on_budget_exhaustion()
            self.assertIsInstance(
                result,
                Path,
                "_on_budget_exhaustion must return a Path instance. "
                f"Got type: {type(result).__name__!r}. "
                "Return the Path from _write_verification_entry().",
            )

    def test_on_budget_exhaustion_writes_partial_status(self):
        """verification_report.md must contain 'PARTIAL' after calling _on_budget_exhaustion."""
        method = getattr(InvestorJourneyAgent, "_on_budget_exhaustion", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_on_budget_exhaustion` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            report_path = agent._on_budget_exhaustion()

            self.assertTrue(
                report_path.exists(),
                f"_on_budget_exhaustion must create the verification report at {report_path}.",
            )
            content = report_path.read_text(encoding="utf-8")
            self.assertIn(
                "PARTIAL",
                content,
                "_on_budget_exhaustion must call _write_verification_entry() with "
                "status='PARTIAL'. The string 'PARTIAL' must appear in "
                f"verification_report.md. Got content:\n{content}",
            )

    def test_on_budget_exhaustion_mentions_budget(self):
        """verification_report.md must mention 'budget' (case-insensitive) after calling _on_budget_exhaustion."""
        method = getattr(InvestorJourneyAgent, "_on_budget_exhaustion", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_on_budget_exhaustion` before this test can run.",
        )
        with tempfile.TemporaryDirectory() as tmp:
            agent = self._make_agent(tmp)
            report_path = agent._on_budget_exhaustion()

            self.assertTrue(
                report_path.exists(),
                f"_on_budget_exhaustion must create the verification report at {report_path}.",
            )
            content = report_path.read_text(encoding="utf-8")
            self.assertIn(
                "budget",
                content.lower(),
                "_on_budget_exhaustion must call _write_verification_entry() with details "
                "containing 'budget exhausted' (or at minimum the word 'budget'). "
                "The word 'budget' (case-insensitive) must appear in verification_report.md. "
                f"Got content:\n{content}",
            )


if __name__ == "__main__":
    unittest.main()
