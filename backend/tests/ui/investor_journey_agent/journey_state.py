"""
JourneyState - Save/resume state serialization for journey interruption.

Allows saving the current journey state to disk and resuming later
in a new browser session with carried context (history, frustration,
step counter).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .llm_brain import JourneyStep


@dataclass
class JourneyState:
    """Serializable snapshot of a journey in progress."""

    persona_name: str
    viewport_name: str
    goal: str
    url: str
    current_step: int
    max_steps: int
    steps_data: List[Dict] = field(default_factory=list)
    output_dir: Optional[str] = None

    def save(self, directory: Path) -> None:
        """Save state to state.json in the given directory."""
        directory = Path(directory)
        data = {
            "persona_name": self.persona_name,
            "viewport_name": self.viewport_name,
            "goal": self.goal,
            "url": self.url,
            "current_step": self.current_step,
            "max_steps": self.max_steps,
            "steps_data": self.steps_data,
            "output_dir": self.output_dir,
        }
        (directory / "state.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, directory: Path) -> "JourneyState":
        """Load state from state.json in the given directory."""
        directory = Path(directory)
        data = json.loads((directory / "state.json").read_text(encoding="utf-8"))
        return cls(
            persona_name=data["persona_name"],
            viewport_name=data["viewport_name"],
            goal=data["goal"],
            url=data["url"],
            current_step=data["current_step"],
            max_steps=data["max_steps"],
            steps_data=data.get("steps_data", []),
            output_dir=data.get("output_dir"),
        )

    @classmethod
    def from_steps(
        cls,
        persona_name: str,
        viewport_name: str,
        goal: str,
        url: str,
        max_steps: int,
        steps: List[JourneyStep],
        output_dir: Optional[str] = None,
    ) -> "JourneyState":
        """Create a JourneyState from live JourneyStep objects."""
        steps_data = []
        for step in steps:
            steps_data.append({
                "step": step.step_number,
                "action": step.action.action_type.value,
                "target": step.action.target,
                "thought": step.action.thought,
                "frustration": step.action.frustration_level,
                "confidence": step.action.confidence,
                "success": step.success,
                "url": step.url,
                "error": step.error_message,
            })
        return cls(
            persona_name=persona_name,
            viewport_name=viewport_name,
            goal=goal,
            url=url,
            current_step=steps[-1].step_number if steps else 0,
            max_steps=max_steps,
            steps_data=steps_data,
            output_dir=output_dir,
        )
