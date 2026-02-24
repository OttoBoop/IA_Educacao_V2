"""
Unit tests for taskQueue refactor — hierarchical sub-tasks + polling support.

Tests verify:
- taskQueue has a method to register backend pipeline tasks
- taskQueue stores backend task_ids for polling
- taskQueue.updateUI() renders to sidebar (tree-tarefas), not FAB
- taskQueue supports hierarchical task data (backend format)

F3-T1 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_taskqueue_refactor.py -v
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


class TestBackendTaskRegistration:
    """Tests for backend task registration in taskQueue."""

    def test_add_backend_task_method(self, active_html):
        """taskQueue must have a method to register backend pipeline tasks."""
        # Must have a method like addBackendTask or registerBackendTask
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        assert (
            "addBackendTask" in taskqueue_area
            or "registerBackendTask" in taskqueue_area
            or "addPipelineTask" in taskqueue_area
        ), "taskQueue must have a method to register backend pipeline tasks (addBackendTask, registerBackendTask, or addPipelineTask)"

    def test_stores_backend_task_id(self, active_html):
        """Backend tasks must store the backend-generated task_id for polling."""
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        # Must store backend task_id (not the frontend-generated 'task_' + Date.now())
        assert "backendTaskId" in taskqueue_area or "task_id" in taskqueue_area, (
            "taskQueue must store the backend-generated task_id for polling"
        )

    def test_backend_tasks_collection(self, active_html):
        """taskQueue must have a collection for backend tasks (separate from frontend tasks)."""
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        assert (
            "backendTasks" in taskqueue_area
            or "pipelineTasks" in taskqueue_area
        ), "taskQueue must have a backendTasks or pipelineTasks collection"


class TestSidebarRendering:
    """Tests that taskQueue renders to sidebar instead of FAB."""

    def test_update_ui_targets_sidebar(self, active_html):
        """taskQueue.updateUI() must call renderTarefasTree for sidebar rendering."""
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        assert "renderTarefasTree" in taskqueue_area, (
            "taskQueue must call renderTarefasTree() to render tasks in sidebar"
        )

    def test_update_ui_passes_task_data(self, active_html):
        """updateUI must pass task data to renderTarefasTree."""
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        # Must pass backendTasks or pipelineTasks to renderTarefasTree
        assert (
            "renderTarefasTree(this.backendTasks" in taskqueue_area
            or "renderTarefasTree(this.pipelineTasks" in taskqueue_area
            or "renderTarefasTree(backendTasks" in taskqueue_area
        ), "updateUI must pass backend task data to renderTarefasTree()"


class TestPollingSupport:
    """Tests for polling infrastructure in taskQueue."""

    def test_get_polling_ids_method(self, active_html):
        """taskQueue must have a method to get task_ids that need polling."""
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        assert (
            "getPollingIds" in taskqueue_area
            or "getRunningBackendIds" in taskqueue_area
            or "getActivePipelineIds" in taskqueue_area
        ), "taskQueue must have a method to get backend task_ids for polling"

    def test_update_from_backend_method(self, active_html):
        """taskQueue must have a method to update task state from backend response."""
        taskqueue_pos = active_html.find("const taskQueue")
        assert taskqueue_pos > 0, "taskQueue object not found"
        taskqueue_area = active_html[taskqueue_pos:taskqueue_pos + 8000]
        assert (
            "updateFromBackend" in taskqueue_area
            or "updateBackendTask" in taskqueue_area
            or "updatePipelineProgress" in taskqueue_area
        ), "taskQueue must have a method to update state from backend polling response"
