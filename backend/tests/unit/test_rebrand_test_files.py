"""
Structural tests for NOVO CR branding in test files and journey agent templates.

F-T1: test_journey_diagnostics.py localStorage refs must use 'novocr-' prefix.
F-T2: test_pdf_report.py expected footer must say 'NOVO CR'.
F-T3: Journey agent templates (html_template, report_generator, llm_brain) must say 'NOVO CR'.
F-T4: Test file headers + conftest + fixtures/__init__ must say 'NOVO CR'.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_test_files.py -v
"""

from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent.parent
JOURNEY_DIAG = TESTS_DIR / "ui" / "test_journey_diagnostics.py"
PDF_REPORT = TESTS_DIR / "unit" / "test_pdf_report.py"
HTML_TEMPLATE = TESTS_DIR / "ui" / "investor_journey_agent" / "html_template.py"
REPORT_GEN = TESTS_DIR / "ui" / "investor_journey_agent" / "report_generator.py"
LLM_BRAIN = TESTS_DIR / "ui" / "investor_journey_agent" / "llm_brain.py"
CONFTEST = TESTS_DIR / "conftest.py"
FIXTURES_INIT = TESTS_DIR / "fixtures" / "__init__.py"

# Test files with "PROVA AI" in header docstrings (line 2)
HEADER_FILES = [
    TESTS_DIR / "unit" / "test_generator.py",
    TESTS_DIR / "unit" / "test_file_types.py",
    TESTS_DIR / "unit" / "test_model_manager.py",
    TESTS_DIR / "unit" / "test_api_keys.py",
    TESTS_DIR / "fixtures" / "test_document_generation.py",
    TESTS_DIR / "fixtures" / "document_factory.py",
    TESTS_DIR / "scenarios" / "test_downloads.py",
    TESTS_DIR / "models" / "test_models_stress.py",
    TESTS_DIR / "models" / "base_model_test.py",
]


def _read(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


# ── F-T1: test_journey_diagnostics.py localStorage refs ──────


class TestJourneyDiagnosticsLocalStorage:
    """F-T1: localStorage refs must use 'novocr-' prefix."""

    def test_uses_novocr_welcomed(self):
        """Should reference 'novocr-welcomed' key."""
        content = _read(JOURNEY_DIAG)
        assert "novocr-welcomed" in content

    def test_no_old_prova_ai_welcomed(self):
        """Must not reference old 'prova-ai-welcomed' key."""
        content = _read(JOURNEY_DIAG)
        assert "prova-ai-welcomed" not in content


# ── F-T2: test_pdf_report.py expected footer ─────────────────


class TestPDFReportFooter:
    """F-T2: PDF report footer expectation must say 'NOVO CR'."""

    def test_footer_says_novo_cr(self):
        """Expected footer should say 'NOVO CR'."""
        content = _read(PDF_REPORT)
        assert "NOVO CR" in content

    def test_footer_no_old_brand(self):
        """Expected footer must not say 'Prova AI'."""
        content = _read(PDF_REPORT)
        assert "Prova AI" not in content


# ── F-T3: Journey agent templates ────────────────────────────


class TestHTMLTemplateReferences:
    """F-T3: html_template.py must say 'NOVO CR'."""

    def test_page_title_novo_cr(self):
        """Page title should reference 'NOVO CR'."""
        content = _read(HTML_TEMPLATE)
        assert "NOVO CR</title>" in content

    def test_page_title_no_old(self):
        """Page title must not say 'Prova AI'."""
        content = _read(HTML_TEMPLATE)
        assert "Prova AI</title>" not in content

    def test_footer_novo_cr(self):
        """Footer should reference 'NOVO CR'."""
        content = _read(HTML_TEMPLATE)
        assert "NOVO CR</p>" in content

    def test_footer_no_old(self):
        """Footer must not say 'Prova AI'."""
        content = _read(HTML_TEMPLATE)
        # Check the footer div specifically
        assert "Prova AI</p>" not in content


class TestReportGeneratorReferences:
    """F-T3: report_generator.py must say 'NOVO CR'."""

    def test_markdown_footer_novo_cr(self):
        """Markdown footer should reference 'NOVO CR'."""
        content = _read(REPORT_GEN)
        assert "NOVO CR*" in content

    def test_markdown_footer_no_old(self):
        """Markdown footer must not say 'Prova AI'."""
        content = _read(REPORT_GEN)
        assert "Prova AI*" not in content


class TestLLMBrainReferences:
    """F-T3: llm_brain.py must say 'NOVO CR'."""

    def test_system_prompt_novo_cr(self):
        """System prompt should reference 'NOVO CR'."""
        content = _read(LLM_BRAIN)
        assert "NOVO CR application" in content

    def test_system_prompt_no_old(self):
        """System prompt must not say 'Prova AI application'."""
        content = _read(LLM_BRAIN)
        assert "Prova AI application" not in content


# ── F-T4: Test file headers + conftest + fixtures ────────────


class TestConftestHeader:
    """F-T4: conftest.py must say 'NOVO CR'."""

    def test_conftest_header_novo_cr(self):
        """conftest.py header should say 'NOVO CR'."""
        content = _read(CONFTEST)
        header = content.split('"""')[1]  # Get first docstring
        assert "NOVO CR" in header

    def test_conftest_header_no_old(self):
        """conftest.py header must not say 'Prova AI'."""
        content = _read(CONFTEST)
        header = content.split('"""')[1]
        assert "Prova AI" not in header


class TestFixturesInitHeader:
    """F-T4: fixtures/__init__.py must say 'NOVO CR'."""

    def test_fixtures_init_novo_cr(self):
        """fixtures/__init__.py header should say 'NOVO CR'."""
        content = _read(FIXTURES_INIT)
        header = content.split('"""')[1]
        assert "NOVO CR" in header

    def test_fixtures_init_no_old(self):
        """fixtures/__init__.py header must not say 'Prova AI'."""
        content = _read(FIXTURES_INIT)
        header = content.split('"""')[1]
        assert "Prova AI" not in header


class TestFileHeaderDocstrings:
    """F-T4: All test files with 'PROVA AI' headers must be updated."""

    @pytest.mark.parametrize("filepath", HEADER_FILES, ids=lambda p: p.name)
    def test_header_has_novo_cr(self, filepath):
        """Header docstring should say 'NOVO CR'."""
        content = _read(filepath)
        header = content.split('"""')[1]  # First docstring
        assert "NOVO CR" in header

    @pytest.mark.parametrize("filepath", HEADER_FILES, ids=lambda p: p.name)
    def test_header_no_old_prova_ai(self, filepath):
        """Header docstring must not say 'PROVA AI'."""
        content = _read(filepath)
        header = content.split('"""')[1]
        assert "PROVA AI" not in header
