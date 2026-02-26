"""
Integration tests for polling loop wiring.

Tests verify that a startPolling() / pollTaskProgress() function exists,
calls /api/task-progress/{task_id}, and calls taskQueue.updateFromBackend()
with each response — not just that updateFromBackend() exists in taskQueue.

F2-T2 from PLAN_Task_Panel_Integration_Fix.md — RED PHASE

These tests SHOULD FAIL until F5-T1 is implemented.

Root cause they guard against:
  No polling function existed at all — the sidebar never updated after initial
  registration. Stages would stay ⬜⬜⬜ forever even as the pipeline ran.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_polling_integration.py -v
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


def _find_polling_function(html):
    """Return (pos, name) of the polling function, or (-1, None) if not found."""
    candidates = [
        "async function startPolling",
        "function startPolling",
        "async function pollTaskProgress",
        "function pollTaskProgress",
    ]
    for candidate in candidates:
        pos = html.find(candidate)
        if pos > 0:
            name = candidate.split("function ")[-1]
            return pos, name
    return -1, None


class TestPollingFunctionExists:
    """Verify the polling function is defined in the frontend code."""

    def test_start_polling_function_exists(self, active_html):
        """A startPolling or pollTaskProgress function must exist for polling pipeline tasks.

        Without this function, the sidebar never updates after the initial registration.
        Stages would stay ⬜⬜⬜ forever even as the pipeline runs on the backend.
        The polling function must call /api/task-progress/{task_id} every ~3 seconds.
        """
        pos, _ = _find_polling_function(active_html)
        assert pos > 0, (
            "A startPolling() or pollTaskProgress() function must be defined. "
            "This function uses setInterval to periodically call /api/task-progress/{task_id} "
            "and update the sidebar with real-time stage transitions ⬜→⏳→✅. "
            "Implement as part of F5-T1."
        )

    def test_polling_called_from_pipeline_trigger(self, active_html):
        """startPolling must be called from executarPipelineCompleto() after addBackendTask().

        The polling loop must start immediately when the pipeline is registered.
        Without this call, the polling function exists but never runs for new tasks.
        """
        func_body_start = active_html.find("async function executarPipelineCompleto")
        assert func_body_start > 0, "executarPipelineCompleto function not found"
        func_body = active_html[func_body_start : func_body_start + 15000]
        assert (
            "startPolling" in func_body
            or "pollTaskProgress" in func_body
        ), (
            "executarPipelineCompleto must call startPolling(task_id) after addBackendTask(). "
            "Without this call, polling never starts for the newly registered task. "
            "Implement in F5-T3 after startPolling() is defined in F5-T1."
        )


class TestPollingCallsBackend:
    """Verify the polling function calls the correct backend endpoint."""

    def test_polling_calls_task_progress_endpoint(self, active_html):
        """The polling function must fetch from /api/task-progress/{task_id}.

        This endpoint returns current stage statuses so the sidebar can
        show real-time transitions ⬜→⏳→✅ as each stage completes.
        """
        assert (
            "/api/task-progress/" in active_html
            or "task-progress" in active_html
        ), (
            "The polling function must call fetch('/api/task-progress/' + task_id). "
            "This endpoint returns { status, students: { aluno_id: { stages: {...} } } } "
            "for real-time sidebar updates. Implement as part of F5-T1."
        )

    def test_polling_calls_update_from_backend(self, active_html):
        """The polling function must call taskQueue.updateFromBackend() with each poll response.

        updateFromBackend() replaces pipelineTasks[task_id] with fresh data and
        calls updateUI() → sidebar rerenders with new stage statuses.
        Without this call, polling fetches data but the sidebar never reflects it.
        """
        poll_pos, poll_name = _find_polling_function(active_html)
        assert poll_pos > 0, (
            "startPolling or pollTaskProgress function not found — "
            "cannot verify it calls updateFromBackend. Implement F5-T1 first."
        )
        poll_body = active_html[poll_pos : poll_pos + 3000]
        assert (
            "updateFromBackend" in poll_body
            or "updateBackendTask" in poll_body
        ), (
            f"{poll_name} must call taskQueue.updateFromBackend(task_id, data) "
            "with each response from /api/task-progress/. "
            "Without this, polling fetches data but the sidebar never updates."
        )


class TestPollingMechanism:
    """Verify the polling uses setInterval for periodic execution."""

    def test_polling_uses_set_interval(self, active_html):
        """The polling mechanism must use setInterval for periodic execution.

        Polling must check the backend every ~3 seconds to track stage transitions
        ⬜→⏳→✅ in real-time as the pipeline runs. A one-shot fetch is not enough.
        """
        poll_pos, poll_name = _find_polling_function(active_html)
        assert poll_pos > 0, (
            "No polling function found — cannot verify setInterval usage. "
            "Implement startPolling() in F5-T1."
        )
        polling_area = active_html[poll_pos : poll_pos + 3000]
        assert (
            "setInterval" in polling_area
            or "setTimeout" in polling_area
        ), (
            f"{poll_name} must use setInterval (or recursive setTimeout) "
            "to periodically poll the backend every ~3 seconds. "
            "A single fetch call is not enough — the pipeline runs for minutes."
        )

    def test_polling_stops_on_terminal_status(self, active_html):
        """The polling loop must stop when task status is completed, failed, or cancelled.

        Without clearInterval, polling runs forever after the pipeline finishes —
        wasting server resources and potentially showing stale 'running' state.
        Stop conditions: status === 'completed' | 'failed' | 'cancelled'
        """
        poll_pos, poll_name = _find_polling_function(active_html)
        assert poll_pos > 0, (
            "No polling function found — cannot verify stop condition. "
            "Implement startPolling() in F5-T1."
        )
        polling_area = active_html[poll_pos : poll_pos + 5000]
        assert "clearInterval" in polling_area or (
            "completed" in polling_area
            and ("return" in polling_area or "clearInterval" in active_html)
        ), (
            f"{poll_name} must call clearInterval(intervalId) when status is "
            "'completed', 'failed', or 'cancelled'. "
            "Implement the stop condition in F5-T2."
        )

    def test_polling_handles_failure_count(self, active_html):
        """The polling function must track consecutive failures for 'Sem conexão' warning.

        After 3 consecutive poll failures (network error or 404), the sidebar must
        show a 'Sem conexão' warning on the task item. This requires a per-task
        failure counter that increments on error and resets on success.
        """
        poll_pos, poll_name = _find_polling_function(active_html)
        assert poll_pos > 0, (
            "No polling function found — cannot verify failure handling. "
            "Implement startPolling() in F5-T1."
        )
        polling_area = active_html[poll_pos : poll_pos + 5000]
        assert (
            "sem_conexao" in polling_area
            or "semConexao" in polling_area
            or "_pollFailures" in polling_area
            or "failCount" in polling_area
            or "failures" in polling_area
        ), (
            f"{poll_name} must track consecutive failures and set sem_conexao: true "
            "after 3 failures. This triggers the 'Sem conexão' warning in the sidebar. "
            "Implement the retry counter in F5-T2."
        )
