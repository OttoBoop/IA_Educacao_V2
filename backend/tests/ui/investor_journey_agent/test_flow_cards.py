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


class TestFlowCardOnclick:
    """F2-T1: Flow cards must have onclick handlers."""

    def test_pipeline_card_has_onclick(self, html):
        """Pipeline de Correção card must have an onclick attribute."""
        # Find the flow-card containing "Pipeline de Correção"
        # and verify it has onclick
        pipeline_idx = html.find("Pipeline de Correção")
        assert pipeline_idx != -1, "Pipeline de Correção text not found"
        # Look backwards for the opening div.flow-card tag
        card_start = html.rfind("<div", 0, pipeline_idx)
        card_tag = html[card_start:pipeline_idx]
        assert "onclick" in card_tag, (
            "Pipeline flow card is missing onclick handler"
        )

    def test_pipeline_card_calls_close_welcome(self, html):
        """Pipeline card onclick must call closeWelcome()."""
        pipeline_idx = html.find("Pipeline de Correção")
        card_start = html.rfind("<div", 0, pipeline_idx)
        card_tag = html[card_start:pipeline_idx]
        assert "closeWelcome()" in card_tag, (
            "Pipeline card onclick must call closeWelcome()"
        )

    def test_pipeline_card_calls_show_dashboard(self, html):
        """Pipeline card onclick must call showDashboard()."""
        pipeline_idx = html.find("Pipeline de Correção")
        card_start = html.rfind("<div", 0, pipeline_idx)
        card_tag = html[card_start:pipeline_idx]
        assert "showDashboard()" in card_tag, (
            "Pipeline card onclick must call showDashboard()"
        )

    def test_chat_card_has_onclick(self, html):
        """Chat com Documentos card must have an onclick attribute."""
        chat_idx = html.find("Chat com Documentos")
        assert chat_idx != -1, "Chat com Documentos text not found"
        card_start = html.rfind("<div", 0, chat_idx)
        card_tag = html[card_start:chat_idx]
        assert "onclick" in card_tag, (
            "Chat flow card is missing onclick handler"
        )

    def test_chat_card_calls_close_welcome(self, html):
        """Chat card onclick must call closeWelcome()."""
        chat_idx = html.find("Chat com Documentos")
        card_start = html.rfind("<div", 0, chat_idx)
        card_tag = html[card_start:chat_idx]
        assert "closeWelcome()" in card_tag, (
            "Chat card onclick must call closeWelcome()"
        )

    def test_chat_card_calls_show_chat(self, html):
        """Chat card onclick must call showChat()."""
        chat_idx = html.find("Chat com Documentos")
        card_start = html.rfind("<div", 0, chat_idx)
        card_tag = html[card_start:chat_idx]
        assert "showChat()" in card_tag, (
            "Chat card onclick must call showChat()"
        )
