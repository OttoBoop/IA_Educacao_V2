"""
Tests for F4-T1: Timed WAIT Action (wait_duration_seconds field on Action).

- F4-T1: Action dataclass must have `wait_duration_seconds: Optional[int] = None`
  - Field exists on Action instances
  - Defaults to None when not provided
  - Stores the value when provided (e.g., 45 seconds)
"""

import unittest

from tests.ui.investor_journey_agent.llm_brain import Action, ActionType


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


if __name__ == "__main__":
    unittest.main()
