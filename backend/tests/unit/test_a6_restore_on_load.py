"""
Unit tests for A6: Restore-on-load — call GET /api/tasks on page load,
populate task panel with previously running tasks.

Tests verify that index_v2.html contains:
1. A restoreTasksFromBackend() function
2. That function fetches /api/tasks
3. That function calls startPolling for each running task
4. That function is called in DOMContentLoaded

Uses source-inspection approach: reads JS function text from index_v2.html.

Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A6
Human Needed: No (browser test is deferred to MC-1 visual check)
Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_a6_restore_on_load.py -v
"""

from pathlib import Path

HTML_FILE = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


def get_html():
    return HTML_FILE.read_text(encoding="utf-8")


class TestRestoreOnLoad:
    """A6: index_v2.html must have restore-on-load wiring for task panel."""

    def test_restore_function_exists(self):
        """restoreTasksFromBackend function must be defined in index_v2.html."""
        html = get_html()
        assert "restoreTasksFromBackend" in html, (
            "index_v2.html must define a restoreTasksFromBackend() function "
            "to reload previously running tasks after page reload"
        )

    def test_restore_function_fetches_api_tasks(self):
        """restoreTasksFromBackend must call /api/tasks endpoint."""
        html = get_html()
        # Find the function DEFINITION (not a call site) and check context
        start = html.find("function restoreTasksFromBackend")
        assert start != -1, "function restoreTasksFromBackend not found"
        context = html[start:start + 1000]
        assert "/api/tasks" in context, (
            "restoreTasksFromBackend() must fetch /api/tasks to get all running tasks"
        )

    def test_restore_function_starts_polling(self):
        """restoreTasksFromBackend must call startPolling for each running task."""
        html = get_html()
        start = html.find("function restoreTasksFromBackend")
        assert start != -1, "function restoreTasksFromBackend not found"
        context = html[start:start + 1500]
        assert "startPolling" in context, (
            "restoreTasksFromBackend() must call startPolling() for each running "
            "task so polling resumes after page reload"
        )

    def test_restore_called_on_domcontentloaded(self):
        """restoreTasksFromBackend must be called inside a DOMContentLoaded handler."""
        html = get_html()
        # Find DOMContentLoaded blocks and check if restoreTasksFromBackend appears in them
        search = html
        found_in_listener = False
        while True:
            dcl_pos = search.find("DOMContentLoaded")
            if dcl_pos == -1:
                break
            # Check the next 2000 chars for the call
            block = search[dcl_pos:dcl_pos + 2000]
            if "restoreTasksFromBackend" in block:
                found_in_listener = True
                break
            search = search[dcl_pos + 16:]
        assert found_in_listener, (
            "restoreTasksFromBackend() must be called inside a DOMContentLoaded "
            "listener so it runs automatically when the page loads"
        )
