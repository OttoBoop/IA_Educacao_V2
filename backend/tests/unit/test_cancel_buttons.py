"""
Unit tests for cancel buttons in TAREFAS sidebar section.

Tests verify:
- "Cancelar Tudo" button exists in TAREFAS section header
- Individual cancel (X) button per task in rendered output
- cancelAllTasks JS function exists
- Per-task cancel function exists

F4-T1 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_cancel_buttons.py -v
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
    return re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)


@pytest.fixture
def active_html(html_content):
    """HTML content with comments stripped (only active code)."""
    return _strip_html_comments(html_content)


class TestCancelarTudoButton:
    """Tests for the 'Cancelar Tudo' button in TAREFAS header."""

    def test_cancelar_tudo_in_header(self, active_html):
        """A 'Cancelar Tudo' button must exist in the TAREFAS section header."""
        # Find the TAREFAS tree-section-header
        tarefas_pos = active_html.find('id="tree-tarefas"')
        assert tarefas_pos > 0, "TAREFAS section not found"
        # Look backwards for the header (it's just before tree-tarefas)
        header_area = active_html[max(0, tarefas_pos - 500):tarefas_pos]
        assert "Cancelar Tudo" in header_area or "cancelar-tudo" in header_area, (
            "'Cancelar Tudo' button must exist in TAREFAS section header"
        )

    def test_cancelar_tudo_calls_function(self, active_html):
        """'Cancelar Tudo' button must call a cancel-all function on click."""
        tarefas_pos = active_html.find('id="tree-tarefas"')
        assert tarefas_pos > 0, "TAREFAS section not found"
        header_area = active_html[max(0, tarefas_pos - 500):tarefas_pos]
        assert (
            "cancelAllTasks" in header_area
            or "cancelarTudo" in header_area
            or "cancelAllPipelines" in header_area
        ), "'Cancelar Tudo' button must have an onclick calling a cancel-all function"


class TestCancelAllFunction:
    """Tests for the cancelAllTasks JS function."""

    def test_cancel_all_function_exists(self, active_html):
        """A cancelAllTasks (or equivalent) function must exist."""
        assert (
            "function cancelAllTasks" in active_html
            or "cancelAllTasks" in active_html
            or "function cancelarTudo" in active_html
        ), "cancelAllTasks function must exist in active JS"

    def test_cancel_all_iterates_tasks(self, active_html):
        """cancelAllTasks must iterate over running tasks to cancel each."""
        # Find the cancel-all function
        for fname in ["cancelAllTasks", "cancelarTudo", "cancelAllPipelines"]:
            pos = active_html.find(f"function {fname}")
            if pos >= 0:
                func_area = active_html[pos:pos + 1500]
                # Must iterate or loop over tasks
                assert (
                    "forEach" in func_area
                    or "for" in func_area
                    or "map" in func_area
                ), f"{fname} must iterate over tasks to cancel each one"
                return
        pytest.fail("No cancel-all function found to test iteration")


class TestPerTaskCancelButton:
    """Tests for individual cancel X button per task."""

    def test_cancel_button_in_render(self, active_html):
        """renderTarefasTree must include a cancel/X button per task item."""
        func_pos = active_html.find("function renderTarefasTree")
        if func_pos < 0:
            pytest.fail("renderTarefasTree not found")
        func_area = active_html[func_pos:func_pos + 8000]
        # Must have cancel button or X button in rendered task HTML
        assert (
            "cancel" in func_area.lower()
            or "cancelTask" in func_area
            or "cancelarTarefa" in func_area
            or "\u2716" in func_area  # ✖ symbol
            or "\u00D7" in func_area  # × symbol
        ), "renderTarefasTree must include a cancel button per task"

    def test_cancel_task_function_exists(self, active_html):
        """A function to cancel individual tasks must exist."""
        assert (
            "function cancelTask" in active_html
            or "function cancelarTarefa" in active_html
            or "function cancelPipelineTask" in active_html
        ), "Individual task cancel function must exist"


class TestCancelBackendWiring:
    """
    Tests that cancelTask() calls the backend /api/task-cancel/ endpoint.

    F2-T3 from PLAN_Task_Panel_Integration_Fix.md — RED PHASE
    These tests SHOULD FAIL until F6-T1 is implemented.

    Root cause they guard against:
      cancelTask() was only setting task.cancel_requested = true locally (frontend only).
      The backend never received the cancel signal, so pipelines continued running even
      after the user clicked cancel. The backend cancel flag was never set.
    """

    def test_cancel_task_calls_backend_api(self, active_html):
        """cancelTask(backendTaskId) must call POST /api/task-cancel/{task_id}.

        Setting task.cancel_requested = true locally is NOT enough — the backend
        runs in a separate process with its own task_registry. The cancel signal
        must be sent via HTTP so the backend sets cancel_requested = True in
        task_registry and stops the pipeline after the current stage.
        """
        func_pos = active_html.find("function cancelTask")
        assert func_pos > 0, "cancelTask function not found"
        func_body = active_html[func_pos : func_pos + 1500]
        assert (
            "task-cancel" in func_body
            or "/api/task-cancel" in func_body
        ), (
            "cancelTask must call POST /api/task-cancel/{task_id} to signal the backend. "
            "Currently only sets task.cancel_requested = true locally — backend ignores this. "
            "Implement: fetch('/api/task-cancel/' + backendTaskId, { method: 'POST' })"
        )

    def test_cancel_task_uses_fetch(self, active_html):
        """cancelTask must use fetch() to make the HTTP cancel request to the backend.

        A local flag (task.cancel_requested = true) does NOT reach the backend server.
        The cancel request must be sent via HTTP using fetch() so the backend's
        cancel_requested flag is set in task_registry and the pipeline stops.
        """
        func_pos = active_html.find("function cancelTask")
        assert func_pos > 0, "cancelTask function not found"
        func_body = active_html[func_pos : func_pos + 1500]
        assert "fetch" in func_body, (
            "cancelTask must use fetch() to call POST /api/task-cancel/{task_id}. "
            "The current implementation only mutates frontend state. "
            "Backend cancellation requires an HTTP call to routes_tasks.py."
        )
