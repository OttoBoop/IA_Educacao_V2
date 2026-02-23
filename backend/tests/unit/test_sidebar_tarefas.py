"""
Unit tests for TAREFAS sidebar section in index_v2.html.

Tests verify:
- TAREFAS section exists in sidebar HTML below Matérias
- Section has correct structure (header, container, empty state)
- Uses existing CSS variable patterns

F2-T1 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_sidebar_tarefas.py -v
"""

import pytest
from pathlib import Path


@pytest.fixture
def html_content():
    """Read the index_v2.html file content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


class TestTarefasSidebarSection:
    """Tests for the TAREFAS section in the sidebar."""

    def test_tarefas_section_exists(self, html_content):
        """A TAREFAS section must exist in the sidebar."""
        assert 'id="tree-tarefas"' in html_content, (
            "Missing #tree-tarefas container in sidebar"
        )

    def test_tarefas_header_exists(self, html_content):
        """TAREFAS section must have a header with 'Tarefas' text."""
        # Look for the section header similar to Matérias
        assert "Tarefas</span>" in html_content or ">Tarefas<" in html_content, (
            "Missing 'Tarefas' header text in sidebar section"
        )

    def test_tarefas_section_after_materias(self, html_content):
        """TAREFAS section must appear AFTER the Matérias section in the HTML."""
        materias_pos = html_content.find('id="tree-materias"')
        tarefas_pos = html_content.find('id="tree-tarefas"')

        assert materias_pos > 0, "Matérias section not found"
        assert tarefas_pos > 0, "Tarefas section not found"
        assert tarefas_pos > materias_pos, (
            "TAREFAS section must appear after MATÉRIAS in sidebar"
        )

    def test_tarefas_empty_state(self, html_content):
        """TAREFAS section must show empty state when no tasks running, inside tree-tarefas."""
        tarefas_pos = html_content.find('id="tree-tarefas"')
        assert tarefas_pos > 0, "TAREFAS section not found"

        # The empty state must be near the tree-tarefas container, not in the old FAB
        section_around = html_content[tarefas_pos:tarefas_pos + 500]
        assert "Nenhuma tarefa" in section_around, (
            "Missing empty state text near #tree-tarefas container"
        )

    def test_tarefas_uses_tree_section_class(self, html_content):
        """TAREFAS section should use the same tree-section class as Matérias."""
        # Find the tarefas container and verify it's inside a tree-section
        tarefas_pos = html_content.find('id="tree-tarefas"')
        if tarefas_pos < 0:
            pytest.fail("TAREFAS section not found")

        # Look backwards from tarefas_pos for tree-section class
        section_before = html_content[max(0, tarefas_pos - 500):tarefas_pos]
        assert "tree-section" in section_before, (
            "TAREFAS container should be inside a tree-section div"
        )
