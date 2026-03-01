"""
Structural tests for NOVO CR branding in documentation files.

E-T1: README.md title + CLAUDE.md (4 refs) must say 'NOVO CR'.
E-T2: STYLE_GUIDE.md (2), TESTING_GUIDE.md (2), MODELS_REFERENCE.md (1), tests/README.md (1).

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_docs.py -v
"""

from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent.parent
PROJECT_DIR = BACKEND_DIR.parent  # IA_Educacao_V2/
WORKSPACE_DIR = PROJECT_DIR.parent  # prova-ai/ (workspace root)

# E-T1 files
README = PROJECT_DIR / "README.md"
CLAUDE_MD = PROJECT_DIR / "CLAUDE.md"

# E-T2 files
STYLE_GUIDE = WORKSPACE_DIR / ".claude" / "design" / "STYLE_GUIDE.md"
TESTING_GUIDE = BACKEND_DIR / "docs" / "TESTING_GUIDE.md"
MODELS_REF = BACKEND_DIR / "docs" / "MODELS_REFERENCE.md"
TESTS_README = BACKEND_DIR / "tests" / "README.md"


def _read(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


# ── E-T1: README.md ──────────────────────────────────────


class TestReadmeBranding:
    """E-T1: README.md title must say 'NOVO CR'."""

    def test_readme_title_novo_cr(self):
        """README title should say 'NOVO CR'."""
        content = _read(README)
        first_line = content.split("\n")[0]
        assert "NOVO CR" in first_line

    def test_readme_title_no_old(self):
        """README title must not say 'Prova AI'."""
        content = _read(README)
        first_line = content.split("\n")[0]
        assert "Prova AI" not in first_line


# ── E-T1: CLAUDE.md ──────────────────────────────────────


class TestClaudeMdBranding:
    """E-T1: CLAUDE.md must say 'NOVO CR' (4 refs)."""

    def test_title_novo_cr(self):
        """CLAUDE.md title line should say 'NOVO CR'."""
        content = _read(CLAUDE_MD)
        first_line = content.split("\n")[0]
        assert "NOVO CR" in first_line

    def test_title_no_old(self):
        """CLAUDE.md title must not say 'Prova AI'."""
        content = _read(CLAUDE_MD)
        first_line = content.split("\n")[0]
        assert "Prova AI" not in first_line

    def test_subtitle_novo_cr(self):
        """CLAUDE.md subtitle should reference 'NOVO CR-specific'."""
        content = _read(CLAUDE_MD)
        assert "NOVO CR-specific" in content

    def test_subtitle_no_old(self):
        """CLAUDE.md subtitle must not say 'Prova AI-specific'."""
        content = _read(CLAUDE_MD)
        assert "Prova AI-specific" not in content

    def test_overview_novo_cr(self):
        """Project overview should say '**NOVO CR**'."""
        content = _read(CLAUDE_MD)
        assert "**NOVO CR**" in content

    def test_overview_no_old(self):
        """Project overview must not say '**Prova AI**'."""
        content = _read(CLAUDE_MD)
        assert "**Prova AI**" not in content

    def test_project_structure_novo_cr(self):
        """Project structure comment should say 'NOVO CR-specific config'."""
        content = _read(CLAUDE_MD)
        assert "NOVO CR-specific config" in content

    def test_project_structure_no_old(self):
        """Project structure comment must not say 'Prova AI-specific config'."""
        content = _read(CLAUDE_MD)
        assert "Prova AI-specific config" not in content


# ── E-T2: STYLE_GUIDE.md ─────────────────────────────────


class TestStyleGuideBranding:
    """E-T2: STYLE_GUIDE.md must say 'NOVO CR' (2 refs)."""

    def test_title_novo_cr(self):
        """Style guide title should say 'NOVO CR'."""
        content = _read(STYLE_GUIDE)
        first_line = content.split("\n")[0]
        assert "NOVO CR" in first_line

    def test_title_no_old(self):
        """Style guide title must not say 'Prova AI'."""
        content = _read(STYLE_GUIDE)
        first_line = content.split("\n")[0]
        assert "Prova AI" not in first_line

    def test_mission_novo_cr(self):
        """Core mission should say 'NOVO CR enhances'."""
        content = _read(STYLE_GUIDE)
        assert "NOVO CR enhances" in content

    def test_mission_no_old(self):
        """Core mission must not say 'Prova AI enhances'."""
        content = _read(STYLE_GUIDE)
        assert "Prova AI enhances" not in content


# ── E-T2: TESTING_GUIDE.md ───────────────────────────────


class TestTestingGuideBranding:
    """E-T2: TESTING_GUIDE.md must say 'NOVO CR'."""

    def test_title_novo_cr(self):
        """Testing guide title should say 'NOVO CR'."""
        content = _read(TESTING_GUIDE)
        first_line = content.split("\n")[0]
        assert "NOVO CR" in first_line

    def test_title_no_old(self):
        """Testing guide title must not say 'Prova AI'."""
        content = _read(TESTING_GUIDE)
        first_line = content.split("\n")[0]
        assert "Prova AI" not in first_line

    def test_overview_novo_cr(self):
        """Overview section should reference 'NOVO CR'."""
        content = _read(TESTING_GUIDE)
        assert "NOVO CR" in content.split("## Vis")[1].split("##")[0]

    def test_overview_no_old(self):
        """Overview must not reference 'Prova AI'."""
        content = _read(TESTING_GUIDE)
        overview = content.split("## Vis")[1].split("##")[0]
        assert "Prova AI" not in overview


# ── E-T2: MODELS_REFERENCE.md ────────────────────────────


class TestModelsReferenceBranding:
    """E-T2: MODELS_REFERENCE.md title must say 'NOVO CR'."""

    def test_title_novo_cr(self):
        """Models reference title should say 'NOVO CR'."""
        content = _read(MODELS_REF)
        first_line = content.split("\n")[0]
        assert "NOVO CR" in first_line

    def test_title_no_old(self):
        """Models reference title must not say 'Prova AI'."""
        content = _read(MODELS_REF)
        first_line = content.split("\n")[0]
        assert "Prova AI" not in first_line


# ── E-T2: tests/README.md ────────────────────────────────


class TestTestsReadmeBranding:
    """E-T2: tests/README.md title must say 'NOVO CR'."""

    def test_title_novo_cr(self):
        """Tests README title should say 'NOVO CR'."""
        content = _read(TESTS_README)
        first_line = content.split("\n")[0]
        assert "NOVO CR" in first_line

    def test_title_no_old(self):
        """Tests README title must not say 'Prova AI'."""
        content = _read(TESTS_README)
        first_line = content.split("\n")[0]
        assert "Prova AI" not in first_line
