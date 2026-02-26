"""
Integration tests for pipeline registration wiring.

Tests verify that executarPipelineCompleto() calls taskQueue.addBackendTask()
after receiving task_id from backend — not just that the method exists in taskQueue.

F2-T1 from PLAN_Task_Panel_Integration_Fix.md — RED PHASE

These tests SHOULD FAIL until F3-T1 + F4-T1 are implemented.

Root cause they guard against:
  executarPipelineCompleto() was calling taskQueue.addTask() → populates tasks[]
  but taskQueue.updateUI() renders only pipelineTasks{} (always empty).
  These are disconnected collections — tasks were invisible in the sidebar.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_pipeline_integration.py -v
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


def _strip_html_comments(html):
    """Remove all HTML comments from content."""
    return re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)


@pytest.fixture
def active_html(html_content):
    """HTML content with comments stripped (only active code)."""
    return _strip_html_comments(html_content)


def _get_function_body(html, func_marker, window=15000):
    """Extract a slice of HTML starting at func_marker."""
    pos = html.find(func_marker)
    assert pos > 0, f"'{func_marker}' not found in HTML"
    return html[pos : pos + window]


class TestPipelineRegistrationWiring:
    """
    Verify executarPipelineCompleto() registers tasks via addBackendTask().

    The root bug: executarPipelineCompleto was calling taskQueue.addTask() which
    populates tasks[], but taskQueue.updateUI() renders pipelineTasks{} only.
    These two collections are disconnected — tasks were invisible in the sidebar.
    """

    def test_executar_pipeline_completo_calls_add_backend_task(self, active_html):
        """executarPipelineCompleto must call taskQueue.addBackendTask() with task_id from backend.

        After F3-T1 converts the backend endpoint to async BackgroundTask, it returns
        { task_id, status: 'started' } immediately. The frontend must call
        taskQueue.addBackendTask(task_id, initialPendingState) so pipelineTasks{}
        is populated and updateUI() can render the sidebar.
        """
        func_body = _get_function_body(
            active_html, "async function executarPipelineCompleto"
        )
        assert "addBackendTask" in func_body, (
            "executarPipelineCompleto must call taskQueue.addBackendTask(task_id, initialState). "
            "This populates pipelineTasks{} so updateUI() renders the TAREFAS sidebar. "
            "Currently calls addTask() → tasks[] which updateUI() ignores — root cause of invisible tasks."
        )

    def test_executar_pipeline_completo_does_not_use_legacy_add_task(self, active_html):
        """executarPipelineCompleto must NOT call legacy taskQueue.addTask().

        taskQueue.addTask() populates tasks[] which taskQueue.updateUI() does NOT render.
        The new flow: backend returns task_id → addBackendTask(task_id) → pipelineTasks{}
        → _sidebarRender → TAREFAS sidebar shows task with stages.
        """
        func_body = _get_function_body(
            active_html, "async function executarPipelineCompleto"
        )
        assert "taskQueue.addTask(" not in func_body, (
            "executarPipelineCompleto must not call legacy taskQueue.addTask(). "
            "Remove the addTask() call and replace with addBackendTask(task_id, initialPendingState). "
            "The legacy addTask() was the root cause of the invisible-tasks bug."
        )

    def test_executar_pipeline_completo_does_not_call_complete_task(self, active_html):
        """executarPipelineCompleto must not call taskQueue.completeTask().

        In the new async flow, the backend response only returns task_id immediately
        (pipeline runs as a BackgroundTask). The frontend no longer waits for the full result.
        Completion is detected by polling /api/task-progress — not by awaiting the response.
        """
        func_body = _get_function_body(
            active_html, "async function executarPipelineCompleto"
        )
        assert "taskQueue.completeTask(" not in func_body, (
            "executarPipelineCompleto must not call taskQueue.completeTask(). "
            "After F3-T1 converts to BackgroundTask, the API returns task_id instantly. "
            "Completion is detected via polling /api/task-progress — not awaited in the call."
        )

    def test_executar_pipeline_completo_does_not_reference_deprecated_task_panel(self, active_html):
        """executarPipelineCompleto must NOT reference getElementById('task-panel').

        Regression guard for the MC-1 null reference crash:
        - #task-panel is inside an HTML comment (deprecated since F6-T1)
        - getElementById('task-panel') returns null at runtime
        - Calling .classList.add('show') on null crashes the function BEFORE the API call
        - Result: pipeline never triggers, addBackendTask never runs, TAREFAS stays empty

        Fix: open the sidebar with toggleMobileSidebar() instead.
        """
        func_body = _get_function_body(
            active_html, "async function executarPipelineCompleto"
        )
        assert "getElementById('task-panel')" not in func_body, (
            "executarPipelineCompleto must NOT call getElementById('task-panel'). "
            "#task-panel is deprecated and commented out — this causes a null reference crash "
            "that silently kills the function before the API call. "
            "Use toggleMobileSidebar() to open the sidebar instead."
        )

    def test_executar_pipeline_completo_opens_sidebar_with_toggle(self, active_html):
        """executarPipelineCompleto must call toggleMobileSidebar() to open the task sidebar.

        On mobile: toggleMobileSidebar() adds .mobile-open to the sidebar, making it visible.
        On desktop: sidebar is always visible, the guard prevents a double-toggle.
        This replaces the broken getElementById('task-panel').classList.add('show') pattern.
        """
        func_body = _get_function_body(
            active_html, "async function executarPipelineCompleto"
        )
        assert "toggleMobileSidebar" in func_body, (
            "executarPipelineCompleto must call toggleMobileSidebar() to open the TAREFAS sidebar. "
            "This is the correct replacement for the deprecated task-panel FAB approach."
        )

    def test_backend_response_provides_task_id(self, active_html):
        """executarPipelineCompleto must extract task_id from the backend API response.

        After F3-T1, the endpoint returns { task_id, status: 'started' } immediately.
        The frontend must read data.task_id (or equivalent) to call addBackendTask()
        and to start the polling loop for this specific task.
        """
        func_body = _get_function_body(
            active_html, "async function executarPipelineCompleto"
        )
        assert (
            "data.task_id" in func_body
            or "result.task_id" in func_body
            or "response.task_id" in func_body
            or "taskId" in func_body
            or ".task_id" in func_body
        ), (
            "executarPipelineCompleto must extract task_id from the backend API response. "
            "After F3-T1, the endpoint returns { task_id, status: 'started' } immediately. "
            "Frontend must read data.task_id to call addBackendTask(task_id, pendingState)."
        )
