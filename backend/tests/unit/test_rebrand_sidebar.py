"""
Structural tests for NOVO CR sidebar branding in index_v2.html.

Verifies the sidebar logo uses a CSS "CR" monogram (not emoji),
and the brand name reads "NOVO CR".

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_sidebar.py -v
"""

from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


class TestSidebarLogo:
    """The sidebar logo must be a CSS 'CR' monogram, not the old emoji."""

    def test_logo_icon_contains_cr_text(self, html_content):
        """Logo icon div should contain 'CR' text instead of emoji."""
        assert '<div class="logo-icon">CR</div>' in html_content

    def test_logo_icon_no_emoji(self, html_content):
        """Logo icon must not contain the old pencil emoji."""
        # Find the logo-icon div and verify no emoji
        assert '<div class="logo-icon">\U0001f4dd</div>' not in html_content

    def test_logo_icon_has_text_styling(self, html_content):
        """Logo icon CSS must have font-weight for the CR monogram."""
        assert "font-weight: 800" in html_content or "font-weight:800" in html_content


class TestSidebarBrandName:
    """The sidebar brand name must read 'NOVO CR'."""

    def test_sidebar_brand_text(self, html_content):
        """Sidebar span should say 'NOVO CR'."""
        assert "<span>NOVO CR</span>" in html_content

    def test_no_old_brand_in_sidebar(self, html_content):
        """Sidebar must not contain 'Prova AI' brand text."""
        assert "<span>Prova AI</span>" not in html_content
