"""
Tests for flow card interactivity in the welcome modal.

F2-T1: Flow cards must have onclick handlers that close the welcome modal
and navigate to the corresponding section.
F2-T2: Flow cards must have cursor: pointer and click affordance on mobile.
"""

from pathlib import Path

import pytest

# Path to the frontend HTML file
INDEX_PATH = Path(__file__).parents[4] / "frontend" / "index_v2.html"


@pytest.fixture
def html():
    return INDEX_PATH.read_text(encoding="utf-8")


# ============================================================
# F2-T1: Flow card onclick handlers
# ============================================================


def _find_flow_card_tag(html: str, title: str) -> str:
    """Find the opening <div class="flow-card" ...> tag for a flow card by title.

    Searches backwards from the title text for 'class="flow-card"' to find
    the parent card div, skipping inner elements like flow-card-icon.
    """
    title_idx = html.find(title)
    assert title_idx != -1, f"'{title}' text not found in HTML"
    # Search backwards for the flow-card class (not flow-card-icon)
    search_area = html[:title_idx]
    card_class_idx = search_area.rfind('class="flow-card"')
    assert card_class_idx != -1, f"flow-card class not found before '{title}'"
    # Find the opening < of that div
    tag_start = search_area.rfind("<", 0, card_class_idx)
    # Get everything from <div to the title text
    return html[tag_start:title_idx]


class TestFlowCardOnclick:
    """F2-T1: Flow cards must have onclick handlers."""

    def test_pipeline_card_has_onclick(self, html):
        """Pipeline de Correção card must have an onclick attribute."""
        card_tag = _find_flow_card_tag(html, "Pipeline de Correção")
        assert "onclick" in card_tag, (
            "Pipeline flow card is missing onclick handler"
        )

    def test_pipeline_card_calls_close_welcome(self, html):
        """Pipeline card onclick must call closeWelcome()."""
        card_tag = _find_flow_card_tag(html, "Pipeline de Correção")
        assert "closeWelcome()" in card_tag, (
            "Pipeline card onclick must call closeWelcome()"
        )

    def test_pipeline_card_calls_show_dashboard(self, html):
        """Pipeline card onclick must call showDashboard()."""
        card_tag = _find_flow_card_tag(html, "Pipeline de Correção")
        assert "showDashboard()" in card_tag, (
            "Pipeline card onclick must call showDashboard()"
        )

    def test_chat_card_has_onclick(self, html):
        """Chat com Documentos card must have an onclick attribute."""
        card_tag = _find_flow_card_tag(html, "Chat com Documentos")
        assert "onclick" in card_tag, (
            "Chat flow card is missing onclick handler"
        )

    def test_chat_card_calls_close_welcome(self, html):
        """Chat card onclick must call closeWelcome()."""
        card_tag = _find_flow_card_tag(html, "Chat com Documentos")
        assert "closeWelcome()" in card_tag, (
            "Chat card onclick must call closeWelcome()"
        )

    def test_chat_card_calls_show_chat(self, html):
        """Chat card onclick must call showChat()."""
        card_tag = _find_flow_card_tag(html, "Chat com Documentos")
        assert "showChat()" in card_tag, (
            "Chat card onclick must call showChat()"
        )
