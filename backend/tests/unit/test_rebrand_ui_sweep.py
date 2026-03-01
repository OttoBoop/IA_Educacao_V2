"""
Structural tests for NOVO CR UI text sweep (remaining Feature B tasks).

B-T3: Tutorial content text and help text must say "NOVO CR".
B-T4: localStorage keys must use "novocr-" prefix (not "prova-ai-").
B-T5: PDF export branding in index_v2.html and chat_system.js.
B-T6: diagram_pipeline.html title must say "NOVO CR".

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_ui_sweep.py -v
"""

from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
CHAT_SYSTEM_JS = Path(__file__).parent.parent.parent.parent / "frontend" / "chat_system.js"
DIAGRAM_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "diagram_pipeline.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture
def chat_js_content():
    """Read the chat_system.js file."""
    assert CHAT_SYSTEM_JS.exists(), f"File not found: {CHAT_SYSTEM_JS}"
    return CHAT_SYSTEM_JS.read_text(encoding="utf-8")


@pytest.fixture
def diagram_content():
    """Read the diagram_pipeline.html file."""
    assert DIAGRAM_HTML.exists(), f"File not found: {DIAGRAM_HTML}"
    return DIAGRAM_HTML.read_text(encoding="utf-8")


# ── B-T3: Tutorial Content + Help Text ─────────────────────────

class TestQuickTutorialContent:
    """B-T3: Quick tutorial title and body must say 'NOVO CR'."""

    def test_quick_tutorial_title_novo_cr(self, html_content):
        """Quick tutorial title should say 'O que é o NOVO CR?'."""
        assert "O que \u00e9 o NOVO CR?" in html_content

    def test_quick_tutorial_title_no_old(self, html_content):
        """Quick tutorial title must not say 'Prova AI'."""
        assert "O que \u00e9 o Prova AI?" not in html_content

    def test_quick_tutorial_body_novo_cr(self, html_content):
        """Quick tutorial body should reference 'NOVO CR'."""
        assert "O NOVO CR " in html_content

    def test_quick_tutorial_body_no_old(self, html_content):
        """Quick tutorial body must not say 'O Prova AI '."""
        assert "O Prova AI " not in html_content


class TestFullTutorialContent:
    """B-T3: Full tutorial title and body must say 'NOVO CR'."""

    def test_full_tutorial_title_novo_cr(self, html_content):
        """Full tutorial title should say 'A Filosofia do NOVO CR'."""
        assert "A Filosofia do NOVO CR" in html_content

    def test_full_tutorial_title_no_old(self, html_content):
        """Full tutorial title must not say 'Prova AI'."""
        assert "A Filosofia do Prova AI" not in html_content

    def test_full_tutorial_body_novo_cr(self, html_content):
        """Full tutorial body should reference 'NOVO CR'."""
        assert "O NOVO CR foi criado" in html_content

    def test_full_tutorial_body_no_old(self, html_content):
        """Full tutorial body must not say 'O Prova AI foi criado'."""
        assert "O Prova AI foi criado" not in html_content


class TestHelpText:
    """B-T3: Help text must say 'NOVO CR'."""

    def test_help_text_novo_cr(self, html_content):
        """Help section should reference 'NOVO CR'."""
        assert "O NOVO CR gera relat\u00f3rios" in html_content

    def test_help_text_no_old(self, html_content):
        """Help section must not say 'O Prova AI gera'."""
        assert "O Prova AI gera relat\u00f3rios" not in html_content


# ── B-T4: localStorage Key Rename ──────────────────────────────

class TestLocalStorageKeys:
    """B-T4: localStorage keys must use 'novocr-' prefix."""

    def test_view_mode_key_novo(self, html_content):
        """View mode key should be 'novocr-view-mode'."""
        assert "novocr-view-mode" in html_content

    def test_view_mode_key_no_old(self, html_content):
        """View mode key must not be 'prova-ai-view-mode'."""
        assert "prova-ai-view-mode" not in html_content

    def test_welcomed_key_novo(self, html_content):
        """Welcomed key should be 'novocr-welcomed'."""
        assert "novocr-welcomed" in html_content

    def test_welcomed_key_no_old(self, html_content):
        """Welcomed key must not be 'prova-ai-welcomed'."""
        assert "prova-ai-welcomed" not in html_content


# ── B-T5: PDF Export Branding ──────────────────────────────────

class TestPDFExportHTML:
    """B-T5: PDF export in index_v2.html must say 'NOVO CR'."""

    def test_pdf_title_novo_cr(self, html_content):
        """PDF template title should say 'NOVO CR'."""
        assert "- NOVO CR</title>" in html_content

    def test_pdf_title_no_old(self, html_content):
        """PDF template title must not say 'Prova AI'."""
        assert "- Prova AI</title>" not in html_content

    def test_pdf_footer_novo_cr(self, html_content):
        """PDF footer should say 'Documento gerado por NOVO CR'."""
        assert "Documento gerado por NOVO CR" in html_content

    def test_pdf_footer_no_old(self, html_content):
        """PDF footer must not say 'Prova AI'."""
        assert "Documento gerado por Prova AI" not in html_content


class TestPDFExportChatJS:
    """B-T5: PDF export in chat_system.js must say 'NOVO CR'."""

    def test_chat_header_novo_cr(self, chat_js_content):
        """Chat system header should say 'NOVO CR'."""
        assert "CHAT SYSTEM - NOVO CR" in chat_js_content

    def test_chat_header_no_old(self, chat_js_content):
        """Chat system header must not say 'Prova AI'."""
        assert "CHAT SYSTEM - Prova AI" not in chat_js_content

    def test_chat_pdf_title_novo_cr(self, chat_js_content):
        """Chat PDF title should say 'NOVO CR'."""
        assert "- NOVO CR</title>" in chat_js_content

    def test_chat_pdf_title_no_old(self, chat_js_content):
        """Chat PDF title must not say 'Prova AI'."""
        assert "- Prova AI</title>" not in chat_js_content

    def test_chat_pdf_footer_novo_cr(self, chat_js_content):
        """Chat PDF footer should say 'NOVO CR'."""
        assert "Documento gerado por NOVO CR" in chat_js_content

    def test_chat_pdf_footer_no_old(self, chat_js_content):
        """Chat PDF footer must not say 'Prova AI'."""
        assert "Documento gerado por Prova AI" not in chat_js_content


# ── B-T6: Diagram Pipeline Title ──────────────────────────────

class TestDiagramPipelineTitle:
    """B-T6: diagram_pipeline.html title must say 'NOVO CR'."""

    def test_diagram_title_novo_cr(self, diagram_content):
        """Diagram title should say 'Pipeline de Correção - NOVO CR'."""
        assert "Pipeline de Corre\u00e7\u00e3o - NOVO CR" in diagram_content

    def test_diagram_title_no_old(self, diagram_content):
        """Diagram title must not say 'Prova AI'."""
        assert "Pipeline de Corre\u00e7\u00e3o - Prova AI" not in diagram_content
