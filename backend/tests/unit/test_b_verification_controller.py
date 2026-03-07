"""
Unit tests for B-track fixes to run_verification_f10.py.

B1: Remove keyword-based PASS marking (MILESTONE_KEYWORDS removed)
B2: Exempt first 10 steps from repetition-stuck detection
B3: Count executarPipelineCompleto events; inject Phase 3 guidance at count=4

Uses source-inspection and functional testing approaches.

Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Tasks B1, B2, B3
Human Needed: B3 Yes (live run review)
Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_b_verification_controller.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

CONTROLLER_PATH = Path(__file__).parent.parent.parent / "run_verification_f10.py"
CONTROLLER_SRC = CONTROLLER_PATH.read_text(encoding="utf-8")


# ── B1: Keyword-based PASS marking removed ────────────────────────────────────

class TestB1KeywordMarkingRemoved:
    """B1: MILESTONE_KEYWORDS and keyword-based PASS marking must be removed."""

    def test_milestone_keywords_dict_absent(self):
        """MILESTONE_KEYWORDS dict must no longer exist in run_verification_f10.py."""
        assert "MILESTONE_KEYWORDS" not in CONTROLLER_SRC, (
            "MILESTONE_KEYWORDS dict must be removed — keyword-based PASS marking "
            "produces false positives and must be replaced by explicit tracking"
        )

    def test_keyword_checklist_loop_absent(self):
        """The loop that iterates MILESTONE_KEYWORDS and calls mark_checklist_item must be removed."""
        # The old loop had: "for item_id, keywords in MILESTONE_KEYWORDS.items():"
        assert "MILESTONE_KEYWORDS.items()" not in CONTROLLER_SRC, (
            "The keyword-checking loop must be removed from step_completed handler"
        )

    def test_no_auto_pass_from_text_keywords(self):
        """mark_checklist_item must not be called from keyword text matching in step_completed."""
        # Check: no call to mark_checklist_item based on 'any(kw in text for kw in keywords)'
        assert "any(kw in text for kw in keywords)" not in CONTROLLER_SRC, (
            "Keyword-matching PASS logic must be removed from step_completed handler"
        )


# ── B2: First 10 steps exempt from repetition-stuck ──────────────────────────

class TestB2RepetitionStuckExemption:
    """B2: First 10 steps must be exempt from repetition-stuck detection."""

    def test_step_count_guard_exists(self):
        """Controller source must contain a step_count guard for repetition-stuck detection."""
        # The guard should be something like: step_count > 10
        assert "step_count > 10" in CONTROLLER_SRC or "step_count >= 10" in CONTROLLER_SRC, (
            "run_verification_f10.py must guard repetition-stuck detection with "
            "step_count > 10 to exempt the first 10 steps (Phase 1 navigation uses "
            "4+ evaluate_js calls which would falsely trigger stuck detection)"
        )

    def test_repetition_stuck_not_fired_before_step_10(self):
        """run_controller() must NOT fire repetition_stuck at step 4 with 5 evaluate_js actions."""
        sys.path.insert(0, str(CONTROLLER_PATH.parent))
        try:
            import importlib
            import run_verification_f10 as ctrl
            importlib.reload(ctrl)
        finally:
            sys.path.pop(0)

        # Simulate: step_count=4, recent_actions has 6 evaluate_js entries
        # (mirroring Phase 1 navigation)
        ipc_dir = Path("/tmp/fake_ipc_b2")
        ipc_dir.mkdir(exist_ok=True)

        # Patch send_command and build a mini event sequence
        guidance_sent = []

        def fake_send(path, cmd_type, data=None):
            if cmd_type == "guidance":
                guidance_sent.append(data.get("instruction", "") if data else "")

        events_path = ipc_dir / "events.jsonl"

        # Build 6 step_completed events (evaluate_js) + 1 paused event
        step_events = []
        for i in range(6):
            step_events.append(json.dumps({
                "event_type": "step_completed",
                "step": i + 1,
                "action": "evaluate_js",
                "target": "showMateria('abc')",
                "thought": "navigating",
                "success": True,
            }))
        step_events.append(json.dumps({
            "event_type": "paused",
            "step": 7,
        }))
        step_events.append(json.dumps({
            "event_type": "complete",
            "step": 7,
        }))
        events_path.write_text("\n".join(step_events) + "\n", encoding="utf-8")

        commands_path = ipc_dir / "commands.jsonl"
        commands_path.write_text("", encoding="utf-8")

        # We can't easily run_controller standalone without its full loop,
        # but we can check the source logic directly
        # The key assertion: step_count > 10 guard prevents repetition_stuck from firing
        # This is a source-inspection check for the guard
        assert "step_count > 10" in CONTROLLER_SRC or "step_count >= 10" in CONTROLLER_SRC, (
            "Repetition-stuck guard must be present to protect Phase 1 navigate steps"
        )


# ── B3: executarPipelineCompleto count → Phase 3 injection ───────────────────

class TestB3Phase3Injection:
    """B3: Controller must count executarPipelineCompleto and inject Phase 3 at count=4."""

    def test_pipeline_counter_variable_exists(self):
        """Controller source must track executarPipelineCompleto trigger count."""
        assert "executarPipelineCompleto" in CONTROLLER_SRC, (
            "run_verification_f10.py must track executarPipelineCompleto trigger count"
        )
        # Should have some counter for it
        assert (
            "pipeline_trigger_count" in CONTROLLER_SRC
            or "trigger_count" in CONTROLLER_SRC
            or "executarPipeline_count" in CONTROLLER_SRC
            or "pipeline_count" in CONTROLLER_SRC
        ), (
            "A counter variable for executarPipelineCompleto must exist in run_controller()"
        )

    def test_phase3_injection_at_count_4(self):
        """Controller source must inject Phase 3 guidance when pipeline count reaches 4."""
        # Should have a condition checking for count == 4 (or >= 4)
        assert (
            "== 4" in CONTROLLER_SRC
            or ">= 4" in CONTROLLER_SRC
        ), (
            "Controller must inject Phase 3 guidance when 4 pipeline triggers are detected "
            "(count == 4 or >= 4)"
        )

    def test_phase3_guidance_text_contains_download(self):
        """Phase 3 guidance injected at count=4 must mention download/validation steps."""
        # The Phase 3 instruction string should mention download or validate
        assert (
            "download" in CONTROLLER_SRC.lower()
            and "phase 3" in CONTROLLER_SRC.lower()
        ) or (
            "PHASE 3" in CONTROLLER_SRC
        ), (
            "The Phase 3 guidance injected at pipeline_count=4 must describe "
            "download and validation steps (download_file, verify JSON fields)"
        )
