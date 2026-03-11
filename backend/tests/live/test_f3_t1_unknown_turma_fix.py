"""
F3-T1 EXPANDED: Fix "Unknown turma" in sidebar tree for materia-level desempenho tasks.

Bug: renderTarefasTree() forces ALL tasks into a 3-level hierarchy
(Materia > Turma > Atividade). Materia-level desempenho tasks have
turma_nome=null, so they appear under "Unknown Turma > Unknown Atividade".

Expected: Materia-level desempenho tasks render directly under the materia
node as "Matemática-V > Desempenho da Matéria" (no turma intermediate).
Similarly, turma-level desempenho should render under materia>turma without
an atividade intermediate.

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f3_t1_unknown_turma_fix.py -v -m live
"""

import re
from pathlib import Path

import pytest

from .conftest import LIVE_URL

pytestmark = [pytest.mark.live]

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


# ============================================================
# Shared fixtures
# ============================================================

@pytest.fixture(scope="module")
def html_content():
    """Read the frontend HTML file once for all tests in this module."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def render_tarefas_tree_body(html_content):
    """Extract the renderTarefasTree function body."""
    match = re.search(
        r"function\s+renderTarefasTree\s*\([^)]*\)\s*\{",
        html_content,
    )
    assert match, "renderTarefasTree function not found in index_v2.html"
    # Function is ~120 lines, grab generous window
    return html_content[match.start():match.start() + 6000]


# ============================================================
# Test 1: Materia-level desempenho tasks must be separated
#          before the 3-level grouping
# ============================================================


class TestMateriaDesempenhoSeparated:
    """F3-T1: renderTarefasTree() must detect materia-level desempenho tasks
    and handle them separately from the normal 3-level hierarchy.

    Current state: ALL tasks are grouped into materia→turma→atividade,
    causing materia desempenho tasks to appear under "Unknown Turma".
    """

    def test_function_separates_materia_desempenho_tasks(self, render_tarefas_tree_body):
        """renderTarefasTree must filter or separate pipeline_desempenho_materia
        tasks from the normal grouping loop.

        Acceptable patterns:
          - Filter tasks by type before grouping (e.g., task.type !== 'pipeline_desempenho_materia')
          - Check task.type inside the grouping loop and skip turma/atividade levels
          - Render materia desempenho tasks in a separate section under the materia node

        The key requirement: tasks with type 'pipeline_desempenho_materia'
        must NOT be grouped under a turma node.
        """
        # Must have logic that references pipeline_desempenho_materia in the grouping context
        has_materia_desempenho_handling = bool(re.search(
            r"""(?:pipeline_desempenho_materia"""
            r"""|type.*===.*desempenho_materia"""
            r"""|desempenho_materia.*filter"""
            r"""|materiaDesempenho"""
            r"""|materia.*desempenho.*task)""",
            render_tarefas_tree_body,
            re.IGNORECASE,
        ))
        assert has_materia_desempenho_handling, (
            "F3-T1: renderTarefasTree() must handle 'pipeline_desempenho_materia' "
            "tasks separately from the normal 3-level hierarchy. "
            "\nCurrently: ALL tasks forced into Materia > Turma > Atividade grouping. "
            "\nResult: materia desempenho tasks appear under 'Unknown Turma'. "
            "\nExpected: detect task.type === 'pipeline_desempenho_materia' and render "
            "directly under the materia node."
        )


# ============================================================
# Test 2: Turma-level desempenho tasks must skip atividade level
# ============================================================


class TestTurmaDesempenhoSkipsAtividade:
    """F3-T1: renderTarefasTree() must detect turma-level desempenho tasks
    and NOT nest them under an atividade node.

    Current state: turma desempenho tasks with atividade_nome=null
    appear under the atividade_id or "Unknown Atividade".
    """

    def test_function_handles_turma_desempenho_tasks(self, render_tarefas_tree_body):
        """renderTarefasTree must handle pipeline_desempenho_turma tasks
        without forcing them into an atividade grouping.

        Acceptable patterns:
          - Filter out turma desempenho tasks before atividade grouping
          - Render turma desempenho under the turma node directly
          - Skip atividade level for desempenho_turma tasks

        The key requirement: tasks with type 'pipeline_desempenho_turma'
        must NOT show "Unknown Atividade".
        """
        has_turma_desempenho_handling = bool(re.search(
            r"""(?:pipeline_desempenho_turma"""
            r"""|type.*===.*desempenho_turma"""
            r"""|desempenho_turma.*filter"""
            r"""|turmaDesempenho"""
            r"""|turma.*desempenho.*task)""",
            render_tarefas_tree_body,
            re.IGNORECASE,
        ))
        assert has_turma_desempenho_handling, (
            "F3-T1: renderTarefasTree() must handle 'pipeline_desempenho_turma' "
            "tasks separately — they should not be nested under an atividade node. "
            "\nCurrently: turma desempenho tasks appear under 'Unknown Atividade'. "
            "\nExpected: detect task.type === 'pipeline_desempenho_turma' and render "
            "under the turma node, not an atividade."
        )


# ============================================================
# Test 3: "Unknown Turma" fallback must NOT apply to desempenho tasks
# ============================================================


class TestNoUnknownTurmaForDesempenho:
    """F3-T1: The 'Unknown Turma' fallback must not be applied to
    desempenho tasks that don't belong to a turma.

    Current state: line 7069 uses `task.turma_nome || 'Unknown Turma'`
    unconditionally for ALL tasks.
    """

    def test_unknown_turma_not_used_for_desempenho_materia(self, render_tarefas_tree_body):
        """The grouping code must NOT apply 'Unknown Turma' fallback to
        materia-level desempenho tasks.

        Acceptable patterns:
          - Filter materia desempenho tasks out BEFORE the materiaMap grouping loop
          - Guard the turma_nome fallback with a type check
          - Separate desempenho tasks by level BEFORE the for-loop

        The key requirement: a materia desempenho task must NEVER appear
        under a node labeled 'Unknown Turma'.
        """
        # The fix must happen BEFORE the materiaMap grouping, not after.
        # The existing `ativTasks.filter(t => t.type.startsWith('pipeline_desempenho'))`
        # at line ~7104 is AFTER grouping — it doesn't prevent "Unknown Turma".
        #
        # Look for a filter/separation that happens BEFORE the main grouping loop,
        # typically before `for (const task of taskList)` or before `materiaMap`.
        # This means the code must reference both 'desempenho_materia' (or similar)
        # AND a variable like 'taskList' or filter/separate logic.

        # Pattern: desempenho tasks separated into their own collection BEFORE grouping
        has_pre_grouping_separation = bool(re.search(
            r"""(?:taskList\.filter.*desempenho"""
            r"""|desempenho_materia.*=.*filter"""
            r"""|materiaDesempenhoTasks"""
            r"""|higherLevelDesempenho"""
            r"""|desempenhoByLevel)""",
            render_tarefas_tree_body,
            re.IGNORECASE,
        ))

        # Alternative: skip desempenho tasks inside the grouping loop
        has_continue_for_desempenho = bool(re.search(
            r"""(?:if\s*\(.*desempenho_materia.*\)\s*continue"""
            r"""|if\s*\(.*desempenho_turma.*\)\s*continue"""
            r"""|continue.*desempenho)""",
            render_tarefas_tree_body,
            re.IGNORECASE,
        ))

        assert has_pre_grouping_separation or has_continue_for_desempenho, (
            "F3-T1: 'Unknown Turma' must NOT appear for materia-level desempenho tasks. "
            "\nCurrently: `task.turma_nome || 'Unknown Turma'` applied to ALL tasks "
            "in the materiaMap grouping loop. "
            "\nExpected: materia/turma desempenho tasks filtered out BEFORE the loop "
            "or skipped with 'continue' inside it."
        )


# ============================================================
# Test 4: Materia desempenho rendered at correct tree level
# ============================================================


class TestMateriaDesempenhoRenderedAtMateriaLevel:
    """F3-T1: Materia-level desempenho tasks must be rendered as children
    of the materia node, at the same nesting level as turma groups.

    Expected tree:
      📚 Matemática-V
        📊 Desempenho da Matéria  ← directly under materia
        🏫 Alpha-V               ← turma groups at same level
        🏫 Beta-V
    """

    def test_materia_desempenho_rendered_after_materia_header(self, render_tarefas_tree_body):
        """The renderTarefasTree function must have a rendering path that
        places materia desempenho tasks directly after the materia header,
        before or alongside the turma loop.

        Acceptable patterns:
          - Separate loop/section for materia desempenho tasks within
            the materia iteration block
          - Insertion of desempenho HTML before `for (const [turmaNome, ...])`
          - A helper that renders high-level desempenho at the correct depth

        The key requirement: materia desempenho output is at the SAME
        tree depth as turma groups, not nested inside them.
        """
        # Look for materia desempenho rendering that's separate from turma loop
        has_materia_level_render = bool(re.search(
            r"""(?:materiaDesempenho.*forEach"""
            r"""|materiaDesempenho.*\.length"""
            r"""|tree-desempenho.*materia"""
            r"""|materia.*level.*desempenho"""
            r"""|desempenho_materia.*html)""",
            render_tarefas_tree_body,
            re.IGNORECASE,
        ))
        assert has_materia_level_render, (
            "F3-T1: renderTarefasTree() must render materia-level desempenho tasks "
            "directly under the materia node (at the same depth as turma groups). "
            "\nCurrently: materia desempenho tasks are buried under "
            "'Unknown Turma > Unknown Atividade'. "
            "\nExpected: a separate rendering path for materia desempenho within "
            "the materia iteration block."
        )


# ============================================================
# Test 5: Breadcrumb for materia desempenho has no turma
# ============================================================


class TestMateriaBreadcrumbNoTurma:
    """F3-T1: The breadcrumb API for materia type must NOT include
    a turma entry (materia desempenho has no turma).
    """

    def test_materia_breadcrumb_has_no_turma_entry(self):
        """GET /api/navegacao/breadcrumb/materia/{id} must return
        breadcrumb items without any 'turma' entry.

        Expected: [{"tipo": "materia", "nome": "Matemática-V"}]
        NOT: [{"tipo": "materia", ...}, {"tipo": "turma", ...}]
        """
        import requests
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/materia/0f615b57854235ec"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"Breadcrumb API returned {resp.status_code}: {resp.text[:300]}"
        )
        data = resp.json()
        crumbs = data.get("breadcrumb", [])
        tipos = [c.get("tipo") for c in crumbs]
        assert "turma" not in tipos, (
            f"F3-T1: Materia breadcrumb must NOT include a 'turma' entry. "
            f"Got tipos: {tipos}. Materia desempenho has no turma — it should "
            f"show 'Matemática-V > Desempenho da matéria' directly."
        )

    def test_materia_breadcrumb_contains_materia_name(self):
        """Breadcrumb for Matemática-V must contain the materia name."""
        import requests
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/materia/0f615b57854235ec"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200
        data = resp.json()
        crumbs = data.get("breadcrumb", [])
        names = [c.get("nome", "") for c in crumbs]
        has_materia_name = any("Matem" in n for n in names)
        assert has_materia_name, (
            f"F3-T1: Materia breadcrumb must contain the materia name "
            f"(e.g., 'Matemática-V'). Got names: {names}"
        )
