"""
Progress Narrator - Periodic summaries during agent journey runs.

Provides concise progress updates at configurable intervals,
showing step count, frustration trend, and success rate.
"""

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .llm_brain import JourneyStep


class ProgressNarrator:
    """
    Produces periodic progress summaries during journey execution.

    Feed each step via on_step(). Returns a summary string every
    `interval` steps, or None if not at an interval boundary.
    """

    def __init__(self, interval: int = 3):
        self.interval = interval
        self._steps: List["JourneyStep"] = []

    def on_step(self, step: "JourneyStep") -> Optional[str]:
        """
        Record a step and return a summary if at interval boundary.

        Args:
            step: The completed JourneyStep.

        Returns:
            Summary string at interval, None otherwise.
        """
        self._steps.append(step)

        if len(self._steps) % self.interval == 0:
            return self._build_summary()
        return None

    def final_summary(self) -> str:
        """Produce a final summary regardless of interval."""
        return self._build_summary()

    def _build_summary(self) -> str:
        """Build a progress summary from recorded steps."""
        total = len(self._steps)
        successes = sum(1 for s in self._steps if s.success)
        failures = total - successes
        success_rate = successes / total if total > 0 else 0

        # Frustration trend
        recent = self._steps[-min(3, total):]
        avg_frustration = sum(s.action.frustration_level for s in recent) / len(recent)
        latest_frustration = self._steps[-1].action.frustration_level

        # Latest action info
        latest = self._steps[-1]
        action_desc = f"{latest.action.action_type.value} on {latest.action.target}"
        status = "OK" if latest.success else "FAILED"

        lines = [
            f"--- Progress: Step {total} ---",
            f"  Success rate: {successes}/{total} ({success_rate:.0%})",
            f"  Latest: {action_desc} [{status}]",
            f"  Frustration: {latest_frustration:.0%} (avg recent: {avg_frustration:.0%})",
        ]

        if failures > 0:
            lines.append(f"  Failures: {failures}")

        return "\n".join(lines)
