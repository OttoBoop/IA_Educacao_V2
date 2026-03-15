"""
Warning Badge UI Tests — F5-T1 (orange badge + inline dropdown)

Tests that index_v2.html contains the JS/HTML code to render warning
badges on pipeline stage cards and the expandable dropdown.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_warning_badge_ui.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Path to the frontend HTML file
INDEX_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the full index_v2.html content."""
    assert INDEX_HTML.exists(), f"index_v2.html not found at {INDEX_HTML}"
    return INDEX_HTML.read_text(encoding="utf-8")


class TestWarningBadgeRendering:
    """F5-T1: Orange badge appears on pipeline stage cards when warnings exist."""

    def test_html_reads_avisos_documento(self, html_content):
        """Frontend JS must read avisos_documento from the API response."""
        assert "avisos_documento" in html_content, (
            "index_v2.html must reference 'avisos_documento' from API response"
        )

    def test_html_reads_avisos_questao(self, html_content):
        """Frontend JS must read avisos_questao from the API response."""
        assert "avisos_questao" in html_content, (
            "index_v2.html must reference 'avisos_questao' from API response"
        )

    def test_orange_badge_css_exists(self, html_content):
        """An orange/warning badge CSS class for avisos must exist."""
        # Either a dedicated .badge-aviso or reuse of .badge-warning with orange color
        has_aviso_badge = "badge-aviso" in html_content or "aviso-badge" in html_content
        has_warning_orange = "badge-warning" in html_content and "avisos" in html_content
        assert has_aviso_badge or has_warning_orange, (
            "index_v2.html must have a badge class for avisos (orange)"
        )

    def test_dropdown_toggle_exists(self, html_content):
        """A click handler to expand/collapse the warning dropdown must exist."""
        # Look for toggle function or onclick handler related to avisos
        has_toggle = (
            "toggleAvisos" in html_content
            or "aviso-dropdown" in html_content
            or "avisos-expand" in html_content
            or "warning-dropdown" in html_content
        )
        assert has_toggle, (
            "index_v2.html must have a toggle mechanism for the warning dropdown"
        )

    def test_warning_codes_displayed(self, html_content):
        """The dropdown must display warning codes and explanations."""
        # The JS must iterate over warnings and show codigo + explicacao
        assert "codigo" in html_content and "explicacao" in html_content, (
            "index_v2.html must render warning 'codigo' and 'explicacao' fields"
        )

    def test_severidade_color_applied(self, html_content):
        """Badge color must vary based on aviso severidade (orange vs yellow)."""
        # Must reference severidade specifically in the context of avisos/warnings
        has_aviso_severidade = (
            "aviso.severidade" in html_content
            or "w.severidade" in html_content
            or "warning.severidade" in html_content
        )
        assert has_aviso_severidade, (
            "index_v2.html must use aviso 'severidade' field to determine badge color"
        )


class TestYellowBadgeUnaffected:
    """F5-T1: Yellow dados_incompletos badge still works after warning badge addition."""

    def test_dados_incompletos_badge_still_present(self, html_content):
        """The yellow 'Dados incompletos' badge must still be rendered."""
        assert "dados_incompletos" in html_content, (
            "dados_incompletos badge rendering must not be removed"
        )
        assert "Dados incompletos" in html_content, (
            "The 'Dados incompletos' label text must still exist"
        )
