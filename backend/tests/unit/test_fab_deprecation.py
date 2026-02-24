"""
Unit tests for FAB deprecation.

Tests verify:
- FAB button is no longer active in the rendered HTML
- FAB task panel is no longer active in the rendered HTML
- DEPRECATED markers are present in the source
- toggleTaskPanel function is deprecated

F6-T1 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_fab_deprecation.py -v
"""

import re
import pytest
from pathlib import Path


def _strip_html_comments(html):
    """Remove all HTML comments from content."""
    return re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)


@pytest.fixture
def html_content():
    """Read the index_v2.html file content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


@pytest.fixture
def active_html(html_content):
    """HTML content with comments stripped (only active code)."""
    return _strip_html_comments(html_content)


class TestFabHtmlDeprecated:
    """Tests that FAB HTML elements are no longer active."""

    def test_fab_button_not_active(self, active_html):
        """FAB button must not appear in active (uncommented) HTML."""
        assert 'id="task-fab"' not in active_html, (
            "FAB button (id='task-fab') is still active — should be commented out"
        )

    def test_fab_panel_not_active(self, active_html):
        """Task panel must not appear in active (uncommented) HTML."""
        assert 'id="task-panel"' not in active_html, (
            "Task panel (id='task-panel') is still active — should be commented out"
        )

    def test_fab_panel_body_not_active(self, active_html):
        """Task panel body must not appear in active HTML."""
        assert 'id="task-panel-body"' not in active_html, (
            "Task panel body (id='task-panel-body') is still active"
        )


class TestDeprecatedMarkers:
    """Tests that DEPRECATED markers are properly placed."""

    def test_deprecated_marker_exists(self, html_content):
        """At least one DEPRECATED marker must exist in the HTML source."""
        assert "DEPRECATED" in html_content, (
            "No DEPRECATED markers found — FAB code must be marked as deprecated"
        )

    def test_fab_code_preserved_in_comments(self, html_content):
        """Original FAB code must be preserved inside HTML comments."""
        # After deprecation, the FAB code should be inside <!-- DEPRECATED ... -->
        comments = re.findall(r'<!--.*?-->', html_content, flags=re.DOTALL)
        fab_in_comments = any("task-fab" in comment for comment in comments)
        assert fab_in_comments, (
            "FAB code must be preserved inside HTML comments (not deleted)"
        )

    def test_toggle_task_panel_not_active(self, active_html):
        """toggleTaskPanel function must not be active (should be commented out)."""
        assert "function toggleTaskPanel" not in active_html, (
            "toggleTaskPanel function is still active — should be deprecated"
        )
