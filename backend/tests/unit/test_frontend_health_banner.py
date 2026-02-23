"""
Structural tests for the health warning banner in index_v2.html.

Verifies the frontend contains the required HTML, CSS, and JS for
the health banner feature. No browser needed — pure file content checks.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_frontend_health_banner.py -v
"""

from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


class TestHealthBannerHTML:
    """The banner HTML element must exist in index_v2.html."""

    def test_health_banner_element_exists(self, html_content):
        assert 'id="health-banner"' in html_content

    def test_health_banner_has_warning_text(self, html_content):
        assert "Sistema com problemas" in html_content


class TestHealthBannerCSS:
    """The banner CSS must be defined."""

    def test_health_banner_css_class(self, html_content):
        assert ".health-banner" in html_content

    def test_health_degraded_body_class(self, html_content):
        assert "health-degraded" in html_content


class TestHealthBannerJS:
    """The polling JS function must exist."""

    def test_check_health_function_exists(self, html_content):
        assert "function checkHealth" in html_content

    def test_polling_interval_set(self, html_content):
        # 300000ms = 5 minutes
        assert "300000" in html_content or "300_000" in html_content

    def test_health_check_called_on_load(self, html_content):
        assert "checkHealth()" in html_content
