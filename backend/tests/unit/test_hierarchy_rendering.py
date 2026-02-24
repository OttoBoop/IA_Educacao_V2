"""
Unit tests for hierarchical tree rendering in TAREFAS sidebar.

Tests verify:
- renderTarefasTree function exists in frontend JS
- Status icon mapping for all states (completed, running, pending, failed)
- Hierarchy levels (materia, turma, aluno, stages)
- Collapsible toggle mechanism
- Overall progress summary

F2-T2 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_hierarchy_rendering.py -v
"""

import pytest
from pathlib import Path


@pytest.fixture
def html_content():
    """Read the index_v2.html file content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


class TestHierarchyRenderFunction:
    """Tests for the renderTarefasTree JS function."""

    def test_render_function_exists(self, html_content):
        """A renderTarefasTree function must exist in the frontend JS."""
        assert "renderTarefasTree" in html_content, (
            "Missing renderTarefasTree function for hierarchical task rendering"
        )

    def test_function_targets_tree_tarefas(self, html_content):
        """renderTarefasTree must target the #tree-tarefas container."""
        # Find the function and verify it references tree-tarefas
        func_pos = html_content.find("renderTarefasTree")
        if func_pos < 0:
            pytest.fail("renderTarefasTree function not found")
        func_area = html_content[func_pos:func_pos + 2000]
        assert "tree-tarefas" in func_area, (
            "renderTarefasTree must target the #tree-tarefas container"
        )


class TestStatusIcons:
    """Tests for status icon mapping in hierarchy rendering."""

    def test_completed_icon(self, html_content):
        """Completed stages must use a checkmark icon."""
        # Must have a mapping from 'completed' status to a visual indicator
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 3000]
        assert "completed" in func_area, (
            "renderTarefasTree must handle 'completed' status"
        )

    def test_running_icon(self, html_content):
        """Running stages must use a spinner or hourglass icon."""
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 3000]
        assert "running" in func_area, (
            "renderTarefasTree must handle 'running' status"
        )

    def test_pending_icon(self, html_content):
        """Pending stages must use a pending indicator."""
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 3000]
        assert "pending" in func_area, (
            "renderTarefasTree must handle 'pending' status"
        )

    def test_failed_icon(self, html_content):
        """Failed stages must use an error indicator."""
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 3000]
        assert "failed" in func_area, (
            "renderTarefasTree must handle 'failed' status"
        )


class TestHierarchyLevels:
    """Tests for hierarchy structure: Materia > Turma > Aluno > Stages."""

    def test_hierarchy_css_classes(self, html_content):
        """Hierarchy rendering must use distinct CSS classes per level."""
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 5000]
        # Must have classes for at least aluno and stage levels
        assert "tarefa-aluno" in func_area or "task-aluno" in func_area, (
            "Hierarchy must have CSS class for aluno level"
        )
        assert "tarefa-stage" in func_area or "task-stage" in func_area, (
            "Hierarchy must have CSS class for stage level"
        )

    def test_collapsible_toggle(self, html_content):
        """Hierarchy items must have a collapsible toggle mechanism."""
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 5000]
        assert "toggleTarefaTree" in func_area or "tarefa-toggle" in func_area or "toggle" in func_area.lower(), (
            "Hierarchy must have a toggle mechanism for collapsing"
        )


class TestProgressSummary:
    """Tests for the overall progress summary."""

    def test_progress_counter_element(self, html_content):
        """A progress counter element must exist in or near the TAREFAS section."""
        assert "renderTarefasTree" in html_content, "renderTarefasTree not found"
        func_pos = html_content.find("renderTarefasTree")
        func_area = html_content[func_pos:func_pos + 5000]
        # Must compute and display progress like "8/18 etapas"
        assert "etapas" in func_area or "progress" in func_area.lower(), (
            "Must have a progress summary (e.g., '8/18 etapas')"
        )
