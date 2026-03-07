"""
Unit tests for A5: CSS for new 6-level hierarchy node levels.

Tests verify that index_v2.html contains CSS rules for the classes
produced by renderTarefasTree(): tree-materia, tree-turma, tree-atividade,
tree-run, tree-desempenho, tree-group-header, tree-group-label.

Uses source-inspection approach: reads the HTML/CSS text and asserts
required selectors are present in the <style> block.

Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A5
Human Needed: No
Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_a5_tree_hierarchy_css.py -v
"""

import pytest
from pathlib import Path

HTML_FILE = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


def get_css_section():
    """Extract content from the <style> blocks in index_v2.html."""
    html = HTML_FILE.read_text(encoding="utf-8")
    # Collect all text between <style> and </style> tags
    css_parts = []
    search = html
    while True:
        start = search.find("<style")
        if start == -1:
            break
        end = search.find("</style>", start)
        if end == -1:
            break
        css_parts.append(search[start:end])
        search = search[end + 8:]
    return "\n".join(css_parts)


class TestTreeHierarchyCss:
    """A5: index_v2.html must contain CSS rules for all 6-level hierarchy node classes.

    Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A5
    """

    def test_css_has_tree_group_header_rule(self):
        """CSS must contain a rule for .tree-group-header (base header class)."""
        css = get_css_section()
        assert ".tree-group-header" in css, (
            "Missing CSS rule for .tree-group-header — the clickable header "
            "element shared by all 6-level hierarchy nodes"
        )

    def test_css_has_tree_materia_rule(self):
        """CSS must contain a rule for .tree-materia (top-level grouping container)."""
        css = get_css_section()
        assert ".tree-materia" in css, (
            "Missing CSS rule for .tree-materia — the top-level (Materia) "
            "container in the 6-level hierarchy"
        )

    def test_css_has_tree_turma_rule(self):
        """CSS must contain a rule for .tree-turma (second-level grouping container)."""
        css = get_css_section()
        assert ".tree-turma" in css, (
            "Missing CSS rule for .tree-turma — the second-level (Turma) "
            "container in the 6-level hierarchy"
        )

    def test_css_has_tree_atividade_rule(self):
        """CSS must contain a rule for .tree-atividade (third-level grouping container)."""
        css = get_css_section()
        assert ".tree-atividade" in css, (
            "Missing CSS rule for .tree-atividade — the third-level (Atividade) "
            "container in the 6-level hierarchy"
        )

    def test_css_has_tree_run_rule(self):
        """CSS must contain a rule for .tree-run (Run N container at 4th level)."""
        css = get_css_section()
        assert ".tree-run" in css, (
            "Missing CSS rule for .tree-run — the fourth-level (Run N) "
            "container in the 6-level hierarchy"
        )

    def test_css_has_tree_desempenho_rule(self):
        """CSS must contain a rule for .tree-desempenho (desempenho status node)."""
        css = get_css_section()
        assert ".tree-desempenho" in css, (
            "Missing CSS rule for .tree-desempenho — the status-only node "
            "for desempenho tasks at atividade level"
        )

    def test_css_has_tree_group_label_rule(self):
        """CSS must contain a rule for .tree-group-label (label text inside headers)."""
        css = get_css_section()
        assert ".tree-group-label" in css, (
            "Missing CSS rule for .tree-group-label — the text label element "
            "inside all tree-group-header nodes"
        )
