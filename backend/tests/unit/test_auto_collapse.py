"""
Unit tests for auto-collapse logic in renderTarefasTree.

Tests verify:
- renderTarefasTree applies auto-collapse when 3+ alunos
- renderTarefasTree auto-expands when ≤2 alunos
- Collapse logic uses student count comparison

F2-T3 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_auto_collapse.py -v
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


def _get_render_function(active_html):
    """Extract the renderTarefasTree function body."""
    pos = active_html.find("function renderTarefasTree")
    if pos < 0:
        pytest.fail("renderTarefasTree function not found")
    return active_html[pos:pos + 8000]


class TestAutoCollapseLogic:
    """Tests for auto-collapse behavior based on student count."""

    def test_auto_collapse_counts_students(self, active_html):
        """renderTarefasTree must count students and compare against a threshold."""
        func = _get_render_function(active_html)
        # Must have a variable or expression that counts students/alunos
        # and compares against a numeric threshold for auto-collapse.
        # Look for patterns like: alunoCount, studentCount, numAlunos, etc.
        assert (
            "alunoCount" in func
            or "studentCount" in func
            or "numAlunos" in func
            or "aluno_count" in func
            or "autoCollapse" in func
        ), (
            "renderTarefasTree must count students for auto-collapse "
            "(e.g., alunoCount, studentCount, numAlunos)"
        )

    def test_collapse_threshold_is_three(self, active_html):
        """Auto-collapse threshold must be 3 (collapse when 3+ students)."""
        func = _get_render_function(active_html)
        # Must reference the number 3 as a threshold for collapsing
        # Could be: > 2, >= 3, <= 2 (for expand), < 3 (for expand)
        assert (
            "> 2" in func or ">= 3" in func
            or "< 3" in func or "<= 2" in func
        ), "Auto-collapse threshold must reference 3 (collapse at 3+ students)"

    def test_conditional_expanded_class(self, active_html):
        """The 'expanded' class must be added conditionally based on student count."""
        func = _get_render_function(active_html)
        # The expanded class must appear in a CONDITIONAL context, not just
        # in the toggle mechanism. Look for ternary or if/else that sets expanded.
        # Pattern: something like (count <= 2 ? 'expanded' : '') or
        # if (count <= 2) { ... expanded ... }
        has_conditional_expand = bool(re.search(
            r'(alunoCount|studentCount|numAlunos|aluno_count|autoCollapse)'
            r'.*expanded',
            func, re.DOTALL
        ))
        assert has_conditional_expand, (
            "'expanded' class must be set conditionally based on student count "
            "(not just in the toggle mechanism)"
        )

    def test_tree_children_expanded_inline(self, active_html):
        """tree-children elements must get 'expanded' class inline during rendering."""
        func = _get_render_function(active_html)
        # The rendered HTML must conditionally include 'expanded' in the
        # tree-children class attribute, e.g.: class="tree-children expanded"
        # or class="tree-children ' + expandClass + '"
        has_inline_expand = bool(re.search(
            r'tree-children.*expanded|tree-children.*expand',
            func
        ))
        assert has_inline_expand, (
            "tree-children elements must get 'expanded' class inline during rendering "
            "(e.g., class='tree-children expanded')"
        )
