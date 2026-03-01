"""
Structural tests for NOVO CR UI text sweep in index_v2.html.

B-T1: Title tag and file header must say "NOVO CR".
B-T2: Welcome modal and tutorial modal titles must say "NOVO CR".

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_ui_text.py -v
"""

from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


class TestHTMLTitle:
    """B-T1: The <title> tag must say 'NOVO CR'."""

    def test_title_tag_contains_novo_cr(self, html_content):
        """Title tag should say NOVO CR."""
        assert "<title>NOVO CR</title>" in html_content

    def test_title_tag_no_old_brand(self, html_content):
        """Title tag must not contain 'Prova AI'."""
        assert "<title>Prova AI" not in html_content

    def test_file_header_contains_novo_cr(self, html_content):
        """File header comment should reference NOVO CR."""
        assert "NOVO CR" in html_content.split("-->")[0]

    def test_file_header_no_old_brand(self, html_content):
        """File header comment must not reference 'PROVA AI'."""
        header = html_content.split("-->")[0]
        assert "PROVA AI" not in header


class TestWelcomeModal:
    """B-T2: Welcome modal title must say 'NOVO CR'."""

    def test_welcome_title_contains_novo_cr(self, html_content):
        """Welcome modal title should say 'Bem-vindo ao NOVO CR'."""
        assert "Bem-vindo ao NOVO CR" in html_content

    def test_welcome_title_no_old_brand(self, html_content):
        """Welcome modal title must not say 'Prova AI'."""
        assert "Bem-vindo ao Prova AI" not in html_content


class TestTutorialModalTitle:
    """B-T2: Tutorial modal title must say 'NOVO CR'."""

    def test_tutorial_title_contains_novo_cr(self, html_content):
        """Tutorial modal title should say 'Tutorial - NOVO CR'."""
        assert "Tutorial - NOVO CR" in html_content

    def test_tutorial_title_no_old_brand(self, html_content):
        """Tutorial modal title must not say 'Prova AI'."""
        assert "Tutorial - Prova AI" not in html_content
