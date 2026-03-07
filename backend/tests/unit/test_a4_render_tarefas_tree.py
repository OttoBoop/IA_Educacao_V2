"""
Unit tests for A4: renderTarefasTree() 6-level hierarchy rewrite.

Tests verify the JavaScript function in index_v2.html groups tasks by
Materia > Turma > Atividade > Run N > Student > Stages and handles
desempenho nodes at the correct hierarchy level.

Uses source-inspection approach: reads the JS function text and asserts
it contains the required grouping logic. This is a snapshot/static test —
no browser execution required.

Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A4
Human Needed: Yes (visual deploy check after implementation)

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_a4_render_tarefas_tree.py -v
"""

import re
import pytest
from pathlib import Path

HTML_FILE = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


def get_render_tarefas_tree_source():
    """Extract the renderTarefasTree function body from index_v2.html."""
    html = HTML_FILE.read_text(encoding="utf-8")
    # Find the function start
    start = html.find("function renderTarefasTree(")
    assert start != -1, "renderTarefasTree not found in index_v2.html"
    # Grab a large enough window (up to 8000 chars covers the full function)
    return html[start:start + 8000]


class TestRenderTarefasTreeHierarchy:
    """A4: renderTarefasTree() must output 6-level hierarchy HTML.

    Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A4
    """

    def test_function_groups_by_materia_nome(self):
        """renderTarefasTree() must reference materia_nome for top-level grouping."""
        source = get_render_tarefas_tree_source()
        assert "materia_nome" in source, (
            "renderTarefasTree() must group tasks by materia_nome "
            "(Materia is the top level of the 6-level hierarchy)"
        )

    def test_function_groups_by_turma_nome(self):
        """renderTarefasTree() must reference turma_nome for second-level grouping."""
        source = get_render_tarefas_tree_source()
        assert "turma_nome" in source, (
            "renderTarefasTree() must group tasks by turma_nome "
            "(Turma is the second level of the 6-level hierarchy)"
        )

    def test_function_groups_by_atividade_nome(self):
        """renderTarefasTree() must reference atividade_nome for third-level grouping."""
        source = get_render_tarefas_tree_source()
        assert "atividade_nome" in source, (
            "renderTarefasTree() must group tasks by atividade_nome "
            "(Atividade is the third level of the 6-level hierarchy)"
        )

    def test_function_shows_run_counter(self):
        """renderTarefasTree() must emit 'Run N' labels for multiple pipeline runs."""
        source = get_render_tarefas_tree_source()
        assert "Run " in source, (
            "renderTarefasTree() must show 'Run N' counter for each pipeline "
            "run under the same atividade (4th level of hierarchy)"
        )

    def test_function_handles_desempenho_tasks(self):
        """renderTarefasTree() must handle pipeline_desempenho_* task types."""
        source = get_render_tarefas_tree_source()
        assert "pipeline_desempenho" in source or "desempenho" in source.lower(), (
            "renderTarefasTree() must have special handling for desempenho "
            "task types (embed at materia/turma/atividade level, not as a Run)"
        )

    def test_function_shows_unknown_placeholders(self):
        """Missing materia/turma names must show 'Unknown' placeholder text."""
        source = get_render_tarefas_tree_source()
        assert "Unknown" in source or "unknown" in source.lower() or "Desconhecida" in source, (
            "renderTarefasTree() must show a placeholder (Unknown/Desconhecida) "
            "when materia_nome or turma_nome is missing"
        )
