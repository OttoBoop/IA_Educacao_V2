"""
Unit tests for notification wiring into polling (F5-T2).

Tests verify that pollTaskProgress in index_v2.html:
- Calls showPipelineToast on completed status
- Calls showPipelineToast on failed status
- Uses 'success' type for completed pipelines
- Uses 'error' type for failed pipelines

F5-T2 from PLAN_Task_Panel_Sidebar_UI.md — RED PHASE

These tests SHOULD FAIL until F5-T2 is implemented.

Root cause they guard against:
  pollTaskProgress detects terminal status (completed/failed/cancelled)
  and stops polling — but never calls showPipelineToast() or
  playNotificationSound(). The professor finishes a 5-minute pipeline
  and gets no visual or audio feedback that it's done.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_notification_wiring.py -v
"""

import re
import pytest
from pathlib import Path


@pytest.fixture
def html_content():
    """Read the index_v2.html file content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


def _get_function_body(content, func_marker, window=3000):
    """Extract a slice of content starting at func_marker."""
    pos = content.find(func_marker)
    assert pos > 0, f"'{func_marker}' not found in index_v2.html"
    return content[pos : pos + window]


class TestNotificationWiring:
    """F5-T2: Verify pollTaskProgress calls showPipelineToast on terminal states."""

    def test_poll_calls_show_pipeline_toast(self, html_content):
        """pollTaskProgress must call showPipelineToast when task reaches terminal status.

        Without this call, the professor waits minutes for a pipeline to complete
        and gets zero feedback — no sound, no toast, nothing. They have to manually
        check the sidebar to notice completion.
        """
        func_body = _get_function_body(html_content, "async function pollTaskProgress")
        assert "showPipelineToast" in func_body, (
            "pollTaskProgress must call showPipelineToast() when the task "
            "reaches terminal status (completed/failed). Currently the function "
            "only stops polling but gives no user feedback."
        )

    def test_poll_notifies_on_completed(self, html_content):
        """pollTaskProgress must show a success notification when status is 'completed'.

        The professor needs positive confirmation that the pipeline finished
        successfully — a chime + green toast saying the pipeline is done.
        """
        func_body = _get_function_body(html_content, "async function pollTaskProgress")
        assert "'success'" in func_body or '"success"' in func_body, (
            "pollTaskProgress must use 'success' type when calling "
            "showPipelineToast for completed pipelines. "
            "Example: showPipelineToast('Pipeline concluído!', 'success')"
        )

    def test_poll_notifies_on_failed(self, html_content):
        """pollTaskProgress must show an error notification when status is 'failed'.

        The professor needs to know immediately when a pipeline fails —
        an alert sound + red toast with error context.
        """
        func_body = _get_function_body(html_content, "async function pollTaskProgress")
        assert "'error'" in func_body or '"error"' in func_body, (
            "pollTaskProgress must use 'error' type when calling "
            "showPipelineToast for failed pipelines. "
            "Example: showPipelineToast('Pipeline falhou.', 'error')"
        )

    def test_notification_distinguishes_completed_vs_failed(self, html_content):
        """The notification must differentiate between completed and failed states.

        A single generic toast is not enough — the professor needs to know
        whether the pipeline succeeded or failed without checking the sidebar.
        Both 'success' and 'error' must appear in the function body.
        """
        func_body = _get_function_body(html_content, "async function pollTaskProgress")
        has_success = "'success'" in func_body or '"success"' in func_body
        has_error = "'error'" in func_body or '"error"' in func_body
        assert has_success and has_error, (
            "pollTaskProgress must distinguish between completed (success) "
            "and failed (error) by calling showPipelineToast with different types. "
            "Currently neither type appears in the function body."
        )
