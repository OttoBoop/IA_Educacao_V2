"""
Structural contract tests for Claude Code command files and CLAUDE.md.

These tests verify that command files (.claude/commands/*.md) and CLAUDE.md
have the required structure, instructions, and cross-references. They enforce
that prompt engineering changes don't break the workflow contract.

No API calls — pure file content validation. Fast and free.
"""
import os
from pathlib import Path
import pytest

# Project root (prova-ai/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent

COMMANDS_DIR = PROJECT_ROOT / ".claude" / "commands"
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"
GITHUB_AGENTS_DIR = PROJECT_ROOT / ".github" / "agents"
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_file(path: Path) -> str:
    """Read a file with UTF-8 encoding, skip test if file missing."""
    if not path.exists():
        pytest.skip(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def collect_md_files(directory: Path):
    """Collect all .md files in a directory (non-recursive)."""
    if not directory.exists():
        return []
    return list(directory.glob("*.md"))


# ---------------------------------------------------------------------------
# 1. Command files exist
# ---------------------------------------------------------------------------

class TestCommandFilesExist:
    """Each expected command file must exist in .claude/commands/."""

    @pytest.mark.parametrize("filename", ["discover.md", "plan.md", "tdd.md"])
    def test_command_file_exists(self, filename):
        path = COMMANDS_DIR / filename
        assert path.exists(), f"Command file missing: {path}"


# ---------------------------------------------------------------------------
# 2. Command file structure
# ---------------------------------------------------------------------------

class TestCommandFileStructure:
    """Each command file must have valid frontmatter and required sections."""

    @pytest.mark.parametrize("filename", ["discover.md", "plan.md", "tdd.md"])
    def test_has_frontmatter(self, filename):
        content = read_file(COMMANDS_DIR / filename)
        assert content.startswith("---\n"), \
            f"{filename} must start with YAML frontmatter (---)"

    @pytest.mark.parametrize("filename", ["discover.md", "plan.md", "tdd.md"])
    def test_has_description_field(self, filename):
        content = read_file(COMMANDS_DIR / filename)
        assert "description:" in content[:500], \
            f"{filename} must have a description: field in frontmatter"

    @pytest.mark.parametrize("filename", ["discover.md", "plan.md", "tdd.md"])
    def test_has_visual_activation_banner(self, filename):
        content = read_file(COMMANDS_DIR / filename)
        # Each command should have a blockquote banner with bold mode indicator
        assert "> " in content and "**" in content[:500], \
            f"{filename} must have a visual activation banner (> ... **MODE**)"

    @pytest.mark.parametrize("filename", ["discover.md", "plan.md", "tdd.md"])
    def test_uses_arguments_variable(self, filename):
        content = read_file(COMMANDS_DIR / filename)
        assert "$ARGUMENTS" in content, \
            f"{filename} must use $ARGUMENTS for parameterization"

    @pytest.mark.parametrize("filename", ["discover.md", "plan.md", "tdd.md"])
    def test_has_completion_section(self, filename):
        content = read_file(COMMANDS_DIR / filename)
        has_completion = (
            "Completion" in content
            or "completion" in content
            or "Complete" in content
            or "complete" in content
        )
        assert has_completion, \
            f"{filename} must have a completion/handoff section"


# ---------------------------------------------------------------------------
# 3. No stale references
# ---------------------------------------------------------------------------

class TestNoStaleReferences:
    """No /project:* references should exist in .claude/ or .github/."""

    def test_no_stale_refs_in_commands(self):
        stale = []
        for md_file in collect_md_files(COMMANDS_DIR):
            content = md_file.read_text(encoding="utf-8")
            if "/project:" in content:
                stale.append(md_file.name)
        assert not stale, f"Stale /project:* refs found in commands: {stale}"

    def test_no_stale_refs_in_agents(self):
        stale = []
        for md_file in collect_md_files(AGENTS_DIR):
            content = md_file.read_text(encoding="utf-8")
            if "/project:" in content:
                stale.append(md_file.name)
        assert not stale, f"Stale /project:* refs found in agents: {stale}"

    def test_no_stale_refs_in_github_agents(self):
        stale = []
        for md_file in collect_md_files(GITHUB_AGENTS_DIR):
            content = md_file.read_text(encoding="utf-8")
            if "/project:" in content:
                stale.append(md_file.name)
        assert not stale, f"Stale /project:* refs found in .github/agents: {stale}"

    def test_no_stale_refs_in_claude_md(self):
        content = read_file(CLAUDE_MD)
        assert "/project:" not in content, \
            "CLAUDE.md still has stale /project:* references"


# ---------------------------------------------------------------------------
# 4. Auto-trigger instructions
# ---------------------------------------------------------------------------

class TestAutoTriggerInstructions:
    """CLAUDE.md must instruct Claude to proactively invoke workflow commands."""

    def test_has_auto_trigger_section(self):
        content = read_file(CLAUDE_MD)
        assert "Auto-Trigger" in content or "auto-trigger" in content, \
            "CLAUDE.md must have an auto-trigger workflow section"

    def test_mentions_skill_tool(self):
        content = read_file(CLAUDE_MD)
        assert "Skill tool" in content or "Skill" in content, \
            "CLAUDE.md must reference the Skill tool for invoking commands"

    def test_auto_trigger_before_plan_mode(self):
        content = read_file(CLAUDE_MD)
        has_plan_mode_override = (
            "before plan mode" in content.lower()
            or "before entering plan" in content.lower()
            or "do not use enterplanmode" in content.lower()
        )
        assert has_plan_mode_override, \
            "CLAUDE.md must instruct Claude to invoke skills BEFORE entering plan mode"

    def test_auto_trigger_covers_discover(self):
        content = read_file(CLAUDE_MD)
        # Must mention auto-invoking discover for new features
        has_discover_trigger = (
            "discover" in content.lower()
            and ("new feature" in content.lower() or "significant change" in content.lower())
            and ("proactiv" in content.lower() or "auto" in content.lower())
        )
        assert has_discover_trigger, \
            "CLAUDE.md must instruct auto-invoking /discover for new features"

    def test_auto_trigger_covers_plan(self):
        content = read_file(CLAUDE_MD)
        has_plan_trigger = (
            "/plan" in content
            and ("discovery" in content.lower() or "discover" in content.lower())
        )
        assert has_plan_trigger, \
            "CLAUDE.md must instruct auto-invoking /plan after discovery"

    def test_auto_trigger_covers_tdd(self):
        content = read_file(CLAUDE_MD)
        has_tdd_trigger = (
            "/tdd" in content
            and ("approved" in content.lower() or "implement" in content.lower())
        )
        assert has_tdd_trigger, \
            "CLAUDE.md must instruct auto-invoking /tdd after plan approval"

    def test_plan_mode_escape_instruction(self):
        content = read_file(CLAUDE_MD)
        has_escape = (
            "plan mode" in content.lower()
            and ("exitplanmode" in content.lower() or "exit plan mode" in content.lower())
            and ("discover" in content.lower())
        )
        assert has_escape, \
            "CLAUDE.md must instruct Claude to ExitPlanMode and invoke /discover if stuck in plan mode"


# ---------------------------------------------------------------------------
# 5. Command handoff chain
# ---------------------------------------------------------------------------

class TestCommandHandoff:
    """Each command's completion must reference the next command in the chain."""

    def test_discover_hands_off_to_plan(self):
        content = read_file(COMMANDS_DIR / "discover.md")
        assert "/plan" in content, \
            "discover.md completion must reference /plan as next step"

    def test_plan_hands_off_to_tdd(self):
        content = read_file(COMMANDS_DIR / "plan.md")
        assert "/tdd" in content, \
            "plan.md completion must reference /tdd as next step"

    def test_tdd_hands_off_to_next_task(self):
        content = read_file(COMMANDS_DIR / "tdd.md")
        assert "/tdd" in content and "next" in content.lower(), \
            "tdd.md completion must reference /tdd for the next task"


# ---------------------------------------------------------------------------
# 6. Testing guide references
# ---------------------------------------------------------------------------

class TestTestingGuideReferences:
    """CLAUDE.md must prominently reference testing guides."""

    def test_has_check_testing_guides_instruction(self):
        content = read_file(CLAUDE_MD)
        has_instruction = (
            "Check Testing Guide" in content
            or "check testing guide" in content.lower()
            or "ALWAYS read" in content
        )
        assert has_instruction, \
            "CLAUDE.md must have a prominent 'check testing guides first' instruction"

    def test_references_tests_readme(self):
        content = read_file(CLAUDE_MD)
        assert "tests/README.md" in content or "tests\\README.md" in content, \
            "CLAUDE.md must reference tests/README.md"

    def test_references_testing_guide(self):
        content = read_file(CLAUDE_MD)
        assert "TESTING_GUIDE.md" in content, \
            "CLAUDE.md must reference TESTING_GUIDE.md"


# ---------------------------------------------------------------------------
# 7. Multi-step operations
# ---------------------------------------------------------------------------

class TestMultiStepOperations:
    """CLAUDE.md must have multi-step operation guidance."""

    def test_has_multi_step_section(self):
        content = read_file(CLAUDE_MD)
        assert "Multi-Step" in content or "multi-step" in content, \
            "CLAUDE.md must have a multi-step operations section"

    def test_mentions_batch_operations(self):
        content = read_file(CLAUDE_MD)
        assert "batch" in content.lower() or "parallel" in content.lower(), \
            "Multi-step section must mention batching/parallel operations"

    def test_mentions_progress_reporting(self):
        content = read_file(CLAUDE_MD)
        assert "progress" in content.lower() or "report" in content.lower(), \
            "Multi-step section must mention progress reporting"

    def test_mentions_failure_handling(self):
        content = read_file(CLAUDE_MD)
        assert "failure" in content.lower() or "interruption" in content.lower(), \
            "Multi-step section must mention failure/interruption handling"
