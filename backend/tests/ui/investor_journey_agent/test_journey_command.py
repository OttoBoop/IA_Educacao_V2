"""
Tests for /journey slash command (Feature 1: Seamless Journey Command).

Tests cover:
- F1-T1: Command file exists with menu flow and execution logic
- F1-T2: Multi-persona sequential execution instructions
- F1-T3: Post-run analysis instructions
- F2-T1: Pre-flight check instructions
- F2-T4: Permission mode fallback instructions
- F3-T1: CLAUDE.md references /journey
"""

import pytest
from pathlib import Path


# Project root (prova-ai/)
# __file__ is at IA_Educacao_V2/backend/tests/ui/investor_journey_agent/test_journey_command.py
# parents: [0]=investor_journey_agent, [1]=ui, [2]=tests, [3]=backend, [4]=IA_Educacao_V2, [5]=prova-ai
PROJECT_ROOT = Path(__file__).resolve().parents[5]
COMMANDS_DIR = PROJECT_ROOT / ".claude" / "commands"
JOURNEY_CMD = COMMANDS_DIR / "journey.md"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"
AGENT_MD = PROJECT_ROOT / ".claude" / "agents" / "investor-journey.md"


# ============================================================
# F1-T1: Command File Exists & Core Structure
# ============================================================


class TestJourneyCommandExists:
    """F1-T1: journey.md must exist and have valid structure."""

    def test_journey_command_file_exists(self):
        """journey.md should exist in .claude/commands/."""
        assert JOURNEY_CMD.exists(), (
            f"Expected {JOURNEY_CMD} to exist. "
            f"Create .claude/commands/journey.md"
        )

    def test_journey_command_has_description_frontmatter(self):
        """Command file should have a description in YAML frontmatter."""
        content = JOURNEY_CMD.read_text(encoding="utf-8")
        assert "---" in content, "Missing YAML frontmatter"
        assert "description:" in content.lower(), "Missing description in frontmatter"

    def test_journey_command_has_persona_picker(self):
        """Command should instruct Claude to ask user to pick personas."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        assert "persona" in content, "Should mention persona selection"
        # Must support multi-select
        has_multi = "multi" in content or "all personas" in content or "all of them" in content
        assert has_multi, "Should support selecting multiple personas or 'all'"

    def test_journey_command_has_target_picker(self):
        """Command should instruct Claude to ask about target URL."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        has_target = (
            "production" in content
            or "local" in content
            or "localhost" in content
            or "url" in content
        )
        assert has_target, "Should mention target URL selection (production/local)"

    def test_journey_command_has_cli_command(self):
        """Command should contain the actual CLI command to run."""
        content = JOURNEY_CMD.read_text(encoding="utf-8")
        assert "python -m tests.ui.investor_journey_agent" in content, (
            "Should contain the CLI command to run the journey agent"
        )

    def test_journey_command_runs_from_backend_dir(self):
        """Command should instruct running from the backend directory."""
        content = JOURNEY_CMD.read_text(encoding="utf-8")
        has_backend = (
            "IA_Educacao_V2/backend" in content
            or "backend" in content.lower()
        )
        assert has_backend, "Should specify running from the backend directory"


# ============================================================
# F1-T2: Multi-Persona Sequential Execution
# ============================================================


class TestMultiPersonaExecution:
    """F1-T2: Command supports running multiple personas."""

    def test_command_mentions_sequential_runs(self):
        """Command should describe running personas one after another."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        has_sequential = (
            "each persona" in content
            or "for each" in content
            or "sequen" in content
            or "one by one" in content
            or "loop" in content
        )
        assert has_sequential, "Should describe sequential persona execution"

    def test_command_lists_available_personas(self):
        """Command should list the available persona options."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        assert "investor" in content
        assert "student" in content
        assert "confused_teacher" in content


# ============================================================
# F1-T3: Post-Run Analysis
# ============================================================


class TestPostRunAnalysis:
    """F1-T3: Command includes post-run analysis instructions."""

    def test_command_reads_summary_json(self):
        """Command should instruct reading summary.json after the run."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        assert "summary.json" in content or "summary" in content, (
            "Should instruct reading summary.json for quick metrics"
        )

    def test_command_reads_journey_log(self):
        """Command should instruct reading journey_log.md for analysis."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        assert "journey_log" in content or "journey log" in content, (
            "Should instruct reading journey_log.md for detailed analysis"
        )

    def test_command_provides_analysis_recommendations(self):
        """Command should instruct providing actionable recommendations."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        has_analysis = (
            "analy" in content  # analysis/analyze
            or "recommend" in content
            or "pain point" in content
            or "frustration" in content
        )
        assert has_analysis, "Should instruct providing analysis and recommendations"

    def test_command_mentions_html_report(self):
        """Command should reference the HTML report output."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        assert "html" in content, "Should mention the HTML report"


# ============================================================
# F2-T1/T4: Pre-flight & Permission Fallback
# ============================================================


class TestPreflightAndPermissions:
    """F2-T1/T4: Pre-flight checks and permission mode handling."""

    def test_command_checks_playwright(self):
        """Command should mention checking/installing Playwright."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        assert "playwright" in content, "Should mention Playwright dependency"

    def test_command_checks_api_key(self):
        """Command should mention checking for ANTHROPIC_API_KEY."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        has_key = "anthropic" in content or "api_key" in content or "api key" in content
        assert has_key, "Should mention checking for Anthropic API key"

    def test_command_has_permission_fallback(self):
        """Command should handle when Bash tool is blocked."""
        content = JOURNEY_CMD.read_text(encoding="utf-8").lower()
        has_fallback = (
            "permission" in content
            or "blocked" in content
            or "denied" in content
            or "allow" in content
        )
        assert has_fallback, "Should include permission mode fallback instructions"


# ============================================================
# F3-T1/T3: CLAUDE.md Discoverability
# ============================================================


class TestCLAUDEMDDiscoverability:
    """F3: CLAUDE.md should reference /journey for discoverability."""

    def test_claude_md_has_journey_in_commands_table(self):
        """CLAUDE.md commands table should include /journey."""
        content = CLAUDE_MD.read_text(encoding="utf-8")
        assert "/journey" in content, "CLAUDE.md should reference /journey command"

    def test_claude_md_has_natural_language_trigger(self):
        """CLAUDE.md should instruct Claude to recognize journey requests."""
        content = CLAUDE_MD.read_text(encoding="utf-8").lower()
        has_trigger = (
            "run the journey" in content
            or "journey agent" in content
            or "simulate" in content
        )
        assert has_trigger, "CLAUDE.md should describe natural language triggers for journey runs"

    def test_investor_journey_agent_md_references_journey_command(self):
        """investor-journey.md should mention /journey as entry point."""
        content = AGENT_MD.read_text(encoding="utf-8")
        assert "/journey" in content, "investor-journey.md should reference /journey command"
