"""
EventEmitter - Structured JSONL event output for IPC with Claude Code.

Writes machine-readable events to events.jsonl and a quick-poll
status summary to status.json, enabling external processes to
monitor journey progress in real time.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .llm_brain import JourneyStep


class EventEmitter:
    """Emits structured JSON events to files for IPC."""

    def __init__(self, output_dir: Path, max_steps: int, persona: str):
        self._output_dir = Path(output_dir)
        self._max_steps = max_steps
        self._persona = persona
        self._events_path = self._output_dir / "events.jsonl"
        self._status_path = self._output_dir / "status.json"
        self._last_step = 0
        self._last_frustration = 0.0
        self._running = True

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _append_event(self, event: dict) -> None:
        """Append a single JSON line to events.jsonl."""
        with open(self._events_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _write_status(self) -> None:
        """Atomically overwrite status.json with current state."""
        status = {
            "step": self._last_step,
            "max_steps": self._max_steps,
            "frustration": self._last_frustration,
            "running": self._running,
            "persona": self._persona,
        }
        # Atomic write: write to temp file, then rename
        fd, tmp_path = tempfile.mkstemp(
            dir=self._output_dir, suffix=".tmp", prefix="status_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(status, f, ensure_ascii=False)
            os.replace(tmp_path, self._status_path)
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def emit_step(self, step: JourneyStep) -> None:
        """Emit a step_completed event. Auto-emits frustration_spike if >= 0.7."""
        self._last_step = step.step_number
        self._last_frustration = step.action.frustration_level

        event = {
            "event_type": "step_completed",
            "timestamp": self._timestamp(),
            "step": step.step_number,
            "max_steps": self._max_steps,
            "action": step.action.action_type.value,
            "target": step.action.target,
            "thought": step.action.thought,
            "frustration": step.action.frustration_level,
            "confidence": step.action.confidence,
            "success": step.success,
            "url": step.url,
            "error": step.error_message,
        }
        self._append_event(event)

        # Auto-emit frustration spike
        if step.action.frustration_level >= 0.7:
            spike = {
                "event_type": "frustration_spike",
                "timestamp": self._timestamp(),
                "step": step.step_number,
                "frustration": step.action.frustration_level,
                "thought": step.action.thought,
            }
            self._append_event(spike)

        self._write_status()

    def emit_error(self, error: str, traceback_str: str) -> None:
        """Emit an error event."""
        event = {
            "event_type": "error",
            "timestamp": self._timestamp(),
            "error": error,
            "traceback": traceback_str,
        }
        self._append_event(event)
        self._running = False
        self._write_status()

    def emit_complete(self, success_rate: float, total_steps: int, gave_up: bool) -> None:
        """Emit a journey_complete event."""
        event = {
            "event_type": "journey_complete",
            "timestamp": self._timestamp(),
            "success_rate": success_rate,
            "total_steps": total_steps,
            "gave_up": gave_up,
        }
        self._append_event(event)
        self._running = False
        self._write_status()

    def emit_stopped(self, reason: str, steps_completed: int) -> None:
        """Emit a journey_stopped event."""
        event = {
            "event_type": "journey_stopped",
            "timestamp": self._timestamp(),
            "reason": reason,
            "steps_completed": steps_completed,
        }
        self._append_event(event)
        self._running = False
        self._write_status()
