"""
Tests for documentation structure.

These tests verify that the documentation is properly organized
and that the API Unification Guide exists with required sections.
"""
import os
from pathlib import Path
import pytest

# Get project root (prova-ai/)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent


class TestDocumentationStructure:
    """Tests for docs/ folder structure."""

    def test_docs_folder_exists(self):
        """docs/ folder should exist at project root."""
        docs_path = PROJECT_ROOT / "docs"
        assert docs_path.exists(), f"docs/ folder not found at {docs_path}"

    def test_docs_subfolders_exist(self):
        """Required subfolders should exist in docs/."""
        docs_path = PROJECT_ROOT / "docs"
        required_folders = ["plans", "guides", "legacy"]

        for folder in required_folders:
            folder_path = docs_path / folder
            assert folder_path.exists(), f"docs/{folder}/ folder not found"

    def test_api_unification_guide_exists(self):
        """API Unification Guide should exist in docs/guides/."""
        guide_path = PROJECT_ROOT / "docs" / "guides" / "API_UNIFICATION_GUIDE.md"
        assert guide_path.exists(), f"API_UNIFICATION_GUIDE.md not found at {guide_path}"

    def test_api_unification_guide_has_required_sections(self):
        """API Unification Guide should have all required sections."""
        guide_path = PROJECT_ROOT / "docs" / "guides" / "API_UNIFICATION_GUIDE.md"

        if not guide_path.exists():
            pytest.skip("Guide doesn't exist yet - run test_api_unification_guide_exists first")

        content = guide_path.read_text(encoding='utf-8')

        required_sections = [
            "Quick Reference",
            "Quando Usar Este Guia",
            "Quando NÃO Unificar",
            "Workflow de Unificação",
            "Passo 1: Descoberta",
            "Passo 2: Análise",
            "Passo 3: Testes",
            "Passo 4: Implementação",
            "Passo 5: Atualizar Frontend",
            "Passo 6: Depreciação",
            "DO NOT:",
            "ALWAYS:",
            "Troubleshooting",
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        assert not missing_sections, f"Missing sections in guide: {missing_sections}"

    def test_legacy_api_unification_exists(self):
        """Legacy API unification document should be archived."""
        legacy_path = PROJECT_ROOT / "docs" / "legacy" / "API_UNIFICATION_LEGACY.md"
        assert legacy_path.exists(), f"API_UNIFICATION_LEGACY.md not found in docs/legacy/"

    def test_documentation_structure_file_exists(self):
        """DOCUMENTATION_STRUCTURE.md should exist in docs/."""
        structure_path = PROJECT_ROOT / "docs" / "DOCUMENTATION_STRUCTURE.md"
        assert structure_path.exists(), f"DOCUMENTATION_STRUCTURE.md not found at {structure_path}"


class TestAgentsHaveUnificationInstructions:
    """Tests that agents are updated with unification instructions."""

    def test_discover_agent_has_unification_section(self):
        """discover.md agent should have API unification section."""
        agent_path = PROJECT_ROOT / ".claude" / "agents" / "discover.md"

        if not agent_path.exists():
            pytest.skip("Agent file doesn't exist")

        content = agent_path.read_text(encoding='utf-8')
        assert "Unificação" in content or "unificação" in content, \
            "discover.md should have API unification instructions"

    def test_plan_agent_has_unification_section(self):
        """plan.md agent should have API unification section."""
        agent_path = PROJECT_ROOT / ".claude" / "agents" / "plan.md"

        if not agent_path.exists():
            pytest.skip("Agent file doesn't exist")

        content = agent_path.read_text(encoding='utf-8')
        assert "Unificação" in content or "unificação" in content, \
            "plan.md should have API unification instructions"

    def test_tdd_agent_has_unification_section(self):
        """tdd.md agent should have API unification section."""
        agent_path = PROJECT_ROOT / ".claude" / "agents" / "tdd.md"

        if not agent_path.exists():
            pytest.skip("Agent file doesn't exist")

        content = agent_path.read_text(encoding='utf-8')
        assert "Unificação" in content or "unificação" in content, \
            "tdd.md should have API unification instructions"


class TestClaudeMdHasUnificationReference:
    """Tests that CLAUDE.md references the unification guide."""

    def test_claude_md_references_unification_guide(self):
        """CLAUDE.md should reference API_UNIFICATION_GUIDE.md."""
        claude_path = PROJECT_ROOT / "CLAUDE.md"

        assert claude_path.exists(), "CLAUDE.md not found at project root"

        content = claude_path.read_text(encoding='utf-8')
        assert "API_UNIFICATION_GUIDE" in content or "API Unification" in content, \
            "CLAUDE.md should reference the API Unification Guide"
