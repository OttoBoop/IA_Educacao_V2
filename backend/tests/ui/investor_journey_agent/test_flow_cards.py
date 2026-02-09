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


# ============================================================
# F2-T2: Flow card mobile CSS affordance
# ============================================================


def _extract_css_block(html: str, selector: str) -> str:
    """Extract a CSS rule block for a given selector from inline <style> tags.

    Returns the full rule text including the selector and braces.
    Handles selectors that may appear multiple times; returns all matches concatenated.
    """
    import re

    results = []
    # Find all occurrences of the selector
    idx = 0
    while True:
        pos = html.find(selector, idx)
        if pos == -1:
            break
        # Find the opening brace
        brace_start = html.find("{", pos)
        if brace_start == -1:
            break
        # Find matching closing brace (handle nesting)
        depth = 0
        brace_end = brace_start
        for i in range(brace_start, len(html)):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    brace_end = i
                    break
        results.append(html[pos : brace_end + 1])
        idx = brace_end + 1
    return "\n".join(results)


class TestFlowCardMobileCSS:
    """F2-T2: Flow cards must have cursor: pointer and click affordance on mobile."""

    def test_flow_card_has_cursor_pointer(self, html):
        """Flow card base CSS must include cursor: pointer."""
        css = _extract_css_block(html, ".flow-card {")
        assert "cursor: pointer" in css or "cursor:pointer" in css, (
            "Flow card is missing cursor: pointer in base CSS"
        )

    def test_flow_card_active_state_exists(self, html):
        """.flow-card:active must be defined for mobile touch feedback."""
        assert ".flow-card:active" in html, (
            "Flow card is missing :active state for touch feedback"
        )

    def test_flow_card_active_has_visual_feedback(self, html):
        """.flow-card:active must have visual feedback (transform or opacity or background)."""
        css = _extract_css_block(html, ".flow-card:active")
        has_feedback = (
            "transform" in css
            or "opacity" in css
            or "background" in css
            or "scale" in css
        )
        assert has_feedback, (
            "Flow card :active state must have visual feedback "
            "(transform, opacity, background, or scale)"
        )
