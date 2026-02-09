"""
Tests for JourneyState - save/resume state serialization,
and the --interactive CLI flag that wires IPC components together.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone

from tests.ui.investor_journey_agent.llm_brain import Action, ActionType, JourneyStep
from tests.ui.investor_journey_agent.journey_state import JourneyState


def _make_step(step_number=1, frustration=0.3, success=True):
    """Helper to create a JourneyStep."""
    action = Action(
        action_type=ActionType.CLICK,
        target="#btn",
        thought="Clicking button",
        frustration_level=frustration,
        confidence=0.8,
    )
    return JourneyStep(
        step_number=step_number,
        url="https://example.com",
        screenshot_path=f"screenshots/step_{step_number:02d}.png",
        action=action,
        success=success,
    )


class TestJourneyStateCreation:
    """Tests for JourneyState dataclass."""

    def test_journey_state_creation(self):
        """JourneyState can be created with required fields."""
        state = JourneyState(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test the app",
            url="https://example.com",
            current_step=5,
            max_steps=50,
        )
        assert state.persona_name == "investor"
        assert state.current_step == 5

    def test_journey_state_has_steps_data(self):
        """JourneyState stores serialized step data."""
        steps = [_make_step(1), _make_step(2)]
        state = JourneyState(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test",
            url="https://example.com",
            current_step=2,
            max_steps=50,
            steps_data=[
                {"step": 1, "action": "click", "success": True, "frustration": 0.3},
                {"step": 2, "action": "click", "success": True, "frustration": 0.3},
            ],
        )
        assert len(state.steps_data) == 2


class TestJourneyStateSaveLoad:
    """Tests for save/load round-trip."""

    def test_save_creates_file(self, tmp_path):
        """save() creates state.json in the given directory."""
        state = JourneyState(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test",
            url="https://example.com",
            current_step=5,
            max_steps=50,
        )

        state.save(tmp_path)

        assert (tmp_path / "state.json").exists()

    def test_save_writes_valid_json(self, tmp_path):
        """state.json contains valid JSON."""
        state = JourneyState(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test",
            url="https://example.com",
            current_step=5,
            max_steps=50,
        )

        state.save(tmp_path)

        data = json.loads((tmp_path / "state.json").read_text())
        assert data["persona_name"] == "investor"
        assert data["current_step"] == 5

    def test_load_from_file(self, tmp_path):
        """load() reads state from state.json."""
        state = JourneyState(
            persona_name="student",
            viewport_name="desktop",
            goal="Find grades",
            url="https://example.com",
            current_step=10,
            max_steps=30,
        )
        state.save(tmp_path)

        loaded = JourneyState.load(tmp_path)

        assert loaded.persona_name == "student"
        assert loaded.viewport_name == "desktop"
        assert loaded.goal == "Find grades"
        assert loaded.current_step == 10
        assert loaded.max_steps == 30

    def test_round_trip_with_steps(self, tmp_path):
        """Save then load preserves steps data."""
        steps_data = [
            {"step": 1, "action": "click", "target": "#btn", "success": True, "frustration": 0.2, "thought": "First"},
            {"step": 2, "action": "type", "target": "#input", "success": True, "frustration": 0.4, "thought": "Second"},
        ]
        state = JourneyState(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test",
            url="https://example.com",
            current_step=2,
            max_steps=50,
            steps_data=steps_data,
        )
        state.save(tmp_path)

        loaded = JourneyState.load(tmp_path)

        assert len(loaded.steps_data) == 2
        assert loaded.steps_data[0]["thought"] == "First"
        assert loaded.steps_data[1]["frustration"] == 0.4

    def test_round_trip_preserves_output_dir(self, tmp_path):
        """Save then load preserves output_dir path."""
        state = JourneyState(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test",
            url="https://example.com",
            current_step=5,
            max_steps=50,
            output_dir=str(tmp_path / "reports" / "run1"),
        )
        state.save(tmp_path)

        loaded = JourneyState.load(tmp_path)

        assert loaded.output_dir == str(tmp_path / "reports" / "run1")


class TestJourneyStateFromSteps:
    """Tests for creating state from live JourneyStep objects."""

    def test_from_steps(self):
        """from_steps() creates a JourneyState from live step objects."""
        steps = [_make_step(1, frustration=0.2), _make_step(2, frustration=0.5)]

        state = JourneyState.from_steps(
            persona_name="investor",
            viewport_name="iphone_14",
            goal="Test",
            url="https://example.com",
            max_steps=50,
            steps=steps,
        )

        assert state.current_step == 2
        assert len(state.steps_data) == 2
        assert state.steps_data[0]["frustration"] == 0.2
        assert state.steps_data[1]["frustration"] == 0.5


class TestInteractiveCLIFlag:
    """Tests for --interactive CLI flag in __main__.py."""

    def test_parse_args_has_interactive_flag(self):
        """--interactive flag exists in argparse."""
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['prog', '--interactive', '--persona', 'investor']):
            from tests.ui.investor_journey_agent.__main__ import build_parser
            parser = build_parser()
            args = parser.parse_args(['--interactive', '--persona', 'investor'])
            assert args.interactive is True

    def test_parse_args_interactive_defaults_false(self):
        """--interactive defaults to False."""
        from tests.ui.investor_journey_agent.__main__ import build_parser
        parser = build_parser()
        args = parser.parse_args(['--persona', 'investor'])
        assert args.interactive is False

    def test_parse_args_has_resume_flag(self):
        """--resume flag exists in argparse."""
        from tests.ui.investor_journey_agent.__main__ import build_parser
        parser = build_parser()
        args = parser.parse_args(['--resume', '/some/path', '--persona', 'investor'])
        assert args.resume == '/some/path'
