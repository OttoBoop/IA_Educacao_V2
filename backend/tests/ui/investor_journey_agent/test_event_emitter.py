"""
Tests for EventEmitter - structured JSONL event output for IPC.

The EventEmitter writes machine-readable events to events.jsonl
and a quick-poll status summary to status.json, enabling Claude Code
to monitor journey progress in real time.
"""

import json
import pytest
from pathlib import Path

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.llm_brain import Action, ActionType, JourneyStep
from tests.ui.investor_journey_agent.event_emitter import EventEmitter


def _make_step(step_number=1, frustration=0.3, success=True, error=None):
    """Helper to create a JourneyStep with sensible defaults."""
    action = Action(
        action_type=ActionType.CLICK,
        target="#some-button",
        thought="I see a button, let me click it",
        frustration_level=frustration,
        confidence=0.8,
    )
    return JourneyStep(
        step_number=step_number,
        url="https://example.com/page",
        screenshot_path=f"screenshots/step_{step_number:02d}.png",
        action=action,
        success=success,
        error_message=error,
    )


class TestEventEmitterCreation:
    """Tests for EventEmitter initialization."""

    def test_emitter_creates_events_file_on_first_emit(self, tmp_path):
        """events.jsonl is created in output_dir after first emit_step()."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step()

        emitter.emit_step(step)

        assert (tmp_path / "events.jsonl").exists()

    def test_events_file_not_created_before_emit(self, tmp_path):
        """events.jsonl does NOT exist until something is emitted."""
        EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")

        assert not (tmp_path / "events.jsonl").exists()


class TestEmitStep:
    """Tests for emit_step() writing step events."""

    def test_emit_step_writes_valid_json_line(self, tmp_path):
        """Each line in events.jsonl is valid JSON."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step()

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(lines[0])
        assert isinstance(event, dict)

    def test_emit_step_includes_all_required_fields(self, tmp_path):
        """Step event contains all required fields."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(step_number=3, frustration=0.4)

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(lines[0])

        assert event["event_type"] == "step_completed"
        assert "timestamp" in event
        assert event["step"] == 3
        assert event["max_steps"] == 50
        assert event["action"] == "click"
        assert event["target"] == "#some-button"
        assert event["thought"] == "I see a button, let me click it"
        assert event["frustration"] == 0.4
        assert event["confidence"] == 0.8
        assert event["success"] is True
        assert event["url"] == "https://example.com/page"
        assert event["error"] is None

    def test_emit_step_with_error(self, tmp_path):
        """Step event includes error message when step failed."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(success=False, error="Element not found")

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(lines[0])
        assert event["success"] is False
        assert event["error"] == "Element not found"

    def test_multiple_emits_append(self, tmp_path):
        """Multiple emit_step() calls produce multiple lines (append, not overwrite)."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")

        for i in range(1, 4):
            emitter.emit_step(_make_step(step_number=i))

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        assert len(lines) == 3

        for i, line in enumerate(lines):
            event = json.loads(line)
            assert event["step"] == i + 1


class TestFrustrationSpike:
    """Tests for automatic frustration_spike events."""

    def test_spike_emitted_at_threshold(self, tmp_path):
        """When frustration >= 0.7, an additional frustration_spike event is emitted."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(frustration=0.7)

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2  # step_completed + frustration_spike

        events = [json.loads(line) for line in lines]
        assert events[0]["event_type"] == "step_completed"
        assert events[1]["event_type"] == "frustration_spike"
        assert events[1]["frustration"] == 0.7

    def test_spike_emitted_above_threshold(self, tmp_path):
        """Frustration 0.9 also triggers spike event."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(frustration=0.9)

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        events = [json.loads(line) for line in lines]
        assert any(e["event_type"] == "frustration_spike" for e in events)

    def test_no_spike_below_threshold(self, tmp_path):
        """Frustration 0.5 does NOT trigger a spike event."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(frustration=0.5)

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        assert len(lines) == 1  # Only step_completed, no spike

    def test_spike_includes_step_context(self, tmp_path):
        """Frustration spike includes step number and thought for context."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(step_number=7, frustration=0.85)

        emitter.emit_step(step)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        spike = json.loads(lines[1])
        assert spike["step"] == 7
        assert "thought" in spike


class TestSpecialEvents:
    """Tests for error, complete, and stopped events."""

    def test_emit_error_event(self, tmp_path):
        """emit_error() writes an error event with error and traceback fields."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")

        emitter.emit_error(error="Browser crashed", traceback_str="Traceback (most recent)...")

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(lines[0])
        assert event["event_type"] == "error"
        assert event["error"] == "Browser crashed"
        assert event["traceback"] == "Traceback (most recent)..."
        assert "timestamp" in event

    def test_emit_complete_event(self, tmp_path):
        """emit_complete() writes a journey_complete event with summary data."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")

        emitter.emit_complete(
            success_rate=0.85,
            total_steps=20,
            gave_up=False,
        )

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(lines[0])
        assert event["event_type"] == "journey_complete"
        assert event["success_rate"] == 0.85
        assert event["total_steps"] == 20
        assert event["gave_up"] is False
        assert "timestamp" in event

    def test_emit_stopped_event(self, tmp_path):
        """emit_stopped() writes a journey_stopped event with reason."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")

        emitter.emit_stopped(reason="User requested report", steps_completed=15)

        lines = (tmp_path / "events.jsonl").read_text().strip().split("\n")
        event = json.loads(lines[0])
        assert event["event_type"] == "journey_stopped"
        assert event["reason"] == "User requested report"
        assert event["steps_completed"] == 15
        assert "timestamp" in event


class TestStatusFile:
    """Tests for status.json quick-poll summary."""

    def test_status_json_created_after_emit(self, tmp_path):
        """status.json exists after emit_step()."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step()

        emitter.emit_step(step)

        assert (tmp_path / "status.json").exists()

    def test_status_json_has_required_fields(self, tmp_path):
        """status.json has step, max_steps, frustration, running, persona."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        step = _make_step(step_number=5, frustration=0.4)

        emitter.emit_step(step)

        status = json.loads((tmp_path / "status.json").read_text())
        assert status["step"] == 5
        assert status["max_steps"] == 50
        assert status["frustration"] == 0.4
        assert status["running"] is True
        assert status["persona"] == "investor"

    def test_status_json_updated_on_each_step(self, tmp_path):
        """status.json reflects the latest step after each emit."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")

        emitter.emit_step(_make_step(step_number=1, frustration=0.1))
        status1 = json.loads((tmp_path / "status.json").read_text())
        assert status1["step"] == 1

        emitter.emit_step(_make_step(step_number=2, frustration=0.5))
        status2 = json.loads((tmp_path / "status.json").read_text())
        assert status2["step"] == 2
        assert status2["frustration"] == 0.5

    def test_status_running_false_after_complete(self, tmp_path):
        """status.json shows running=false after emit_complete()."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        emitter.emit_step(_make_step())  # Create status first

        emitter.emit_complete(success_rate=0.9, total_steps=10, gave_up=False)

        status = json.loads((tmp_path / "status.json").read_text())
        assert status["running"] is False

    def test_status_running_false_after_stopped(self, tmp_path):
        """status.json shows running=false after emit_stopped()."""
        emitter = EventEmitter(output_dir=tmp_path, max_steps=50, persona="investor")
        emitter.emit_step(_make_step())  # Create status first

        emitter.emit_stopped(reason="User stop", steps_completed=5)

        status = json.loads((tmp_path / "status.json").read_text())
        assert status["running"] is False


class TestAgentEventEmitterIntegration:
    """Tests that InvestorJourneyAgent accepts and uses EventEmitter."""

    def test_agent_constructor_accepts_event_emitter(self):
        """InvestorJourneyAgent accepts optional event_emitter param."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from unittest.mock import MagicMock

        emitter = MagicMock(spec=EventEmitter)
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
            event_emitter=emitter,
        )

        assert agent.event_emitter is emitter

    def test_agent_constructor_defaults_to_no_emitter(self):
        """InvestorJourneyAgent defaults to event_emitter=None."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
        )

        assert agent.event_emitter is None
