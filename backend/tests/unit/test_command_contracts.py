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


# ---------------------------------------------------------------------------
# 8. Navigation sections (F1-T1, F1-T2, F1-T3)
# ---------------------------------------------------------------------------

class TestNavigationSections:
    """CLAUDE.md must have navigation sections that guide bots to the right docs."""

    # --- F1-T1: Project Identification Step ---

    def test_has_project_identification_step(self):
        """CLAUDE.md must instruct bots to ask which project the user is working on."""
        content = read_file(CLAUDE_MD)
        has_project_id = (
            "which project" in content.lower()
            or "project identification" in content.lower()
        )
        assert has_project_id, \
            "CLAUDE.md must contain project identification instruction ('Which project' or 'Project Identification')"

    # --- F1-T2: Core Documentation Reference table ---

    def test_has_core_docs_reference_section(self):
        """CLAUDE.md must have a Core Documentation Reference section."""
        content = read_file(CLAUDE_MD)
        assert "Core Documentation Reference" in content, \
            "CLAUDE.md must have a 'Core Documentation Reference' section"

    def test_core_docs_references_testing_guide(self):
        """Core docs table must reference TESTING_GUIDE.md."""
        content = read_file(CLAUDE_MD)
        assert "TESTING_GUIDE.md" in content, \
            "CLAUDE.md must reference TESTING_GUIDE.md in core docs"

    def test_core_docs_references_tests_readme(self):
        """Core docs table must reference tests/README.md."""
        content = read_file(CLAUDE_MD)
        assert "tests/README.md" in content or "tests\\README.md" in content, \
            "CLAUDE.md must reference tests/README.md in core docs"

    def test_core_docs_references_models_reference(self):
        """Core docs table must reference MODELS_REFERENCE.md."""
        content = read_file(CLAUDE_MD)
        assert "MODELS_REFERENCE.md" in content, \
            "CLAUDE.md must reference MODELS_REFERENCE.md"

    def test_core_docs_references_style_guide(self):
        """Core docs table must reference STYLE_GUIDE.md."""
        content = read_file(CLAUDE_MD)
        assert "STYLE_GUIDE.md" in content, \
            "CLAUDE.md must reference STYLE_GUIDE.md"

    def test_core_docs_references_ui_element_catalog(self):
        """Core docs table must reference UI_ELEMENT_CATALOG.md."""
        content = read_file(CLAUDE_MD)
        assert "UI_ELEMENT_CATALOG.md" in content, \
            "CLAUDE.md must reference UI_ELEMENT_CATALOG.md"

    def test_core_docs_references_investor_journey_concept(self):
        """Core docs table must reference INVESTOR_JOURNEY_CONCEPT.md."""
        content = read_file(CLAUDE_MD)
        assert "INVESTOR_JOURNEY_CONCEPT.md" in content, \
            "CLAUDE.md must reference INVESTOR_JOURNEY_CONCEPT.md"

    def test_core_docs_references_technical_brief(self):
        """Core docs table must reference TECHNICAL_BRIEF.md."""
        content = read_file(CLAUDE_MD)
        assert "TECHNICAL_BRIEF.md" in content, \
            "CLAUDE.md must reference TECHNICAL_BRIEF.md"

    def test_core_docs_references_participe_source_of_truth(self):
        """Core docs table must reference PARTICIPE_V4_SOURCE_OF_TRUTH.md."""
        content = read_file(CLAUDE_MD)
        assert "PARTICIPE_V4_SOURCE_OF_TRUTH.md" in content, \
            "CLAUDE.md must reference PARTICIPE_V4_SOURCE_OF_TRUTH.md"

    def test_core_docs_references_wix_injection_guide(self):
        """Core docs table must reference WIX_INJECTION_GUIDE.md."""
        content = read_file(CLAUDE_MD)
        assert "WIX_INJECTION_GUIDE.md" in content, \
            "CLAUDE.md must reference WIX_INJECTION_GUIDE.md"

    def test_core_docs_has_open_when_guidance(self):
        """Core docs table must include 'open when' guidance for each doc."""
        content = read_file(CLAUDE_MD)
        # The table should have an 'Open When' or 'When to Read' column
        has_guidance = (
            "Open When" in content
            or "When to Read" in content
            or "open when" in content.lower()
        )
        assert has_guidance, \
            "Core docs reference must include 'Open When' guidance column"

    # --- F1-T3: Shared Tools & Cross-Project Resources ---

    def test_has_shared_tools_section(self):
        """CLAUDE.md must have a Shared Tools section."""
        content = read_file(CLAUDE_MD)
        assert "Shared Tools" in content, \
            "CLAUDE.md must have a 'Shared Tools' section"

    def test_shared_tools_mentions_journey_agent(self):
        """Shared Tools must mention the journey agent."""
        content = read_file(CLAUDE_MD)
        has_journey = (
            "journey agent" in content.lower()
            or "investor journey" in content.lower()
            or "investor-journey" in content.lower()
        )
        assert has_journey, \
            "Shared Tools section must mention the journey agent"

    def test_shared_tools_mentions_copilot_browser(self):
        """Shared Tools must mention COPILOT BROWSER."""
        content = read_file(CLAUDE_MD)
        assert "COPILOT BROWSER" in content or "copilot browser" in content.lower(), \
            "Shared Tools section must mention COPILOT BROWSER"

    def test_shared_tools_mentions_browser_scripts(self):
        """Shared Tools must mention browser automation scripts."""
        content = read_file(CLAUDE_MD)
        has_scripts = (
            "browser automation" in content.lower()
            or "browser scripts" in content.lower()
            or "root-level" in content.lower() and ".py" in content
        )
        assert has_scripts, \
            "Shared Tools section must mention browser automation scripts"

    # --- F1-T4: Workspace Assets Reference ---

    def test_has_workspace_assets_section(self):
        """CLAUDE.md must have a Workspace Assets section."""
        content = read_file(CLAUDE_MD)
        has_section = (
            "Workspace Assets" in content
            or "Root Assets" in content
        )
        assert has_section, \
            "CLAUDE.md must have a 'Workspace Assets' or 'Root Assets' section"

    def test_workspace_assets_mentions_crash_logs(self):
        """Workspace Assets must reference crash_logs/ directory."""
        content = read_file(CLAUDE_MD)
        assert "crash_logs" in content, \
            "CLAUDE.md must reference crash_logs/ in workspace assets"

    def test_workspace_assets_mentions_data_dir(self):
        """Workspace Assets must reference data/ directory."""
        content = read_file(CLAUDE_MD)
        # Must mention 'data/' as a workspace asset (not just any 'data' word)
        assert "data/" in content or "`data`" in content or "data |" in content, \
            "CLAUDE.md must reference data/ directory in workspace assets"

    def test_workspace_assets_mentions_temp_ipc(self):
        """Workspace Assets must reference temp_ipc/ directory."""
        content = read_file(CLAUDE_MD)
        assert "temp_ipc" in content, \
            "CLAUDE.md must reference temp_ipc/ in workspace assets"

    # --- F1-T5: FlavioValle Ecosystem ---

    def test_has_flaviovalle_ecosystem_section(self):
        """CLAUDE.md must document the FlavioValle ecosystem."""
        content = read_file(CLAUDE_MD)
        has_ecosystem = (
            "FlavioValle Ecosystem" in content
            or "FlavioValle ecosystem" in content
        )
        assert has_ecosystem, \
            "CLAUDE.md must have a 'FlavioValle Ecosystem' section or entry"

    def test_flaviovalle_mentions_live_repo(self):
        """CLAUDE.md must mention flavio-valle/ as the live site repo."""
        content = read_file(CLAUDE_MD)
        assert "flavio-valle" in content.lower(), \
            "CLAUDE.md must reference flavio-valle/ (live Wix site repo)"

    def test_flaviovalle_mentions_updating_repo(self):
        """CLAUDE.md must mention Updating-FlavioValle/ as the dev/planning repo."""
        content = read_file(CLAUDE_MD)
        assert "Updating-FlavioValle" in content, \
            "CLAUDE.md must reference Updating-FlavioValle/ (dev/planning repo)"

    def test_flaviovalle_mentions_snapshot_repo(self):
        """CLAUDE.md must mention flavio-vale/ as the snapshot."""
        content = read_file(CLAUDE_MD)
        # flavio-vale (without double-l) is the snapshot
        has_snapshot = (
            "flavio-vale/" in content
            or "flavio-vale`" in content
            or "`flavio-vale" in content
        )
        assert has_snapshot, \
            "CLAUDE.md must reference flavio-vale/ (partial snapshot)"

    # --- F1-T6: Projects Table Update ---

    def test_projects_table_has_six_or_more_entries(self):
        """Projects table must have at least 6 project entries."""
        content = read_file(CLAUDE_MD)
        # Count data rows in the Projects table (between ## Projects and next ##)
        lines = content.split('\n')
        in_projects = False
        data_rows = 0
        for line in lines:
            if line.strip() == '## Projects':
                in_projects = True
                continue
            if in_projects and line.strip().startswith('## '):
                break
            if in_projects and line.startswith('|') and '---' not in line:
                # Skip the header row
                if 'Project' in line and 'Description' in line:
                    continue
                if '`' in line:  # Data rows have backtick-wrapped names
                    data_rows += 1
        assert data_rows >= 6, \
            f"Projects table must have ≥6 entries, found {data_rows}"

    def test_projects_table_lists_flavio_valle_repo(self):
        """Projects table must include flavio-valle/ as a separate project entry."""
        content = read_file(CLAUDE_MD)
        # Look specifically in the Projects table section (not FlavioValle Ecosystem)
        lines = content.split('\n')
        in_projects = False
        found = False
        for line in lines:
            if line.strip() == '## Projects':
                in_projects = True
                continue
            if in_projects and line.strip().startswith('## '):
                break
            if in_projects and '|' in line and 'flavio-valle' in line and '---' not in line:
                found = True
                break
        assert found, \
            "Projects table must include flavio-valle/ as a project entry"

    # --- F2-T1: Decision Tree Navigation ---

    def test_has_decision_tree_navigation_section(self):
        """CLAUDE.md must have a Decision Tree Navigation section."""
        content = read_file(CLAUDE_MD)
        assert "Decision Tree Navigation" in content, \
            "CLAUDE.md must have a 'Decision Tree Navigation' section"

    def test_decision_tree_mentions_ia_educacao(self):
        """Decision tree must have an entry for IA_Educacao_V2."""
        content = read_file(CLAUDE_MD)
        # Extract the Decision Tree Navigation section
        lines = content.split('\n')
        in_tree = False
        tree_content = []
        for line in lines:
            if 'Decision Tree Navigation' in line and line.strip().startswith('#'):
                in_tree = True
                continue
            if in_tree and line.strip().startswith('## '):
                break
            if in_tree:
                tree_content.append(line)
        tree_text = '\n'.join(tree_content)
        assert 'IA_Educacao_V2' in tree_text, \
            "Decision tree must mention IA_Educacao_V2"

    def test_decision_tree_mentions_general_scraper(self):
        """Decision tree must have an entry for general_scraper."""
        content = read_file(CLAUDE_MD)
        lines = content.split('\n')
        in_tree = False
        tree_content = []
        for line in lines:
            if 'Decision Tree Navigation' in line and line.strip().startswith('#'):
                in_tree = True
                continue
            if in_tree and line.strip().startswith('## '):
                break
            if in_tree:
                tree_content.append(line)
        tree_text = '\n'.join(tree_content)
        assert 'general_scraper' in tree_text, \
            "Decision tree must mention general_scraper"

    def test_decision_tree_mentions_flaviovalle(self):
        """Decision tree must have an entry for FlavioValle."""
        content = read_file(CLAUDE_MD)
        lines = content.split('\n')
        in_tree = False
        tree_content = []
        for line in lines:
            if 'Decision Tree Navigation' in line and line.strip().startswith('#'):
                in_tree = True
                continue
            if in_tree and line.strip().startswith('## '):
                break
            if in_tree:
                tree_content.append(line)
        tree_text = '\n'.join(tree_content)
        assert 'FlavioValle' in tree_text, \
            "Decision tree must mention FlavioValle"

    def test_decision_tree_mentions_cross_project(self):
        """Decision tree must have a Cross-project / Multiple option."""
        content = read_file(CLAUDE_MD)
        lines = content.split('\n')
        in_tree = False
        tree_content = []
        for line in lines:
            if 'Decision Tree Navigation' in line and line.strip().startswith('#'):
                in_tree = True
                continue
            if in_tree and line.strip().startswith('## '):
                break
            if in_tree:
                tree_content.append(line)
        tree_text = '\n'.join(tree_content)
        has_cross = (
            'cross-project' in tree_text.lower()
            or 'cross project' in tree_text.lower()
            or 'multiple' in tree_text.lower()
        )
        assert has_cross, \
            "Decision tree must have a Cross-project or Multiple option"

    # --- F2-T2: Notes & Warnings ---

    def test_notes_mentions_legacy_agent_dirs(self):
        """CLAUDE.md must warn about legacy agent directories."""
        content = read_file(CLAUDE_MD)
        has_legacy = (
            ".agent/" in content
            or ".agents/" in content
            or "legacy agent" in content.lower()
        )
        assert has_legacy, \
            "CLAUDE.md must mention legacy agent directories (.agent/, .agents/, etc.)"

    def test_notes_mentions_codex_branches(self):
        """CLAUDE.md must note the codex/* experiment branches."""
        content = read_file(CLAUDE_MD)
        assert "codex" in content.lower(), \
            "CLAUDE.md must mention codex/* experiment branches"

    def test_notes_mentions_git_remote_quirk(self):
        """CLAUDE.md must note the general_scraper nested git quirk."""
        content = read_file(CLAUDE_MD)
        content_lower = content.lower()
        # The quirk: general_scraper remote actually points to general-ai-workflows
        # Must be explicitly warned about, not just mentioned in passing
        has_note = (
            "nested git" in content_lower
            or ("general_scraper" in content and "not independent" in content_lower)
            or ("general_scraper" in content and "points to general-ai-workflows" in content_lower)
        )
        assert has_note, \
            "CLAUDE.md must warn about general_scraper nested git relationship"
