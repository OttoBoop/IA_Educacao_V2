"""
F2-T2 RED phase: Level-dependent hierarchy nesting in prefetchDesempenhoEtapasState().

Expected hierarchy:
  tarefa  → Aluno > Phases          (flat list, entityId = atividade_id)
  turma   → Atividade > Aluno > Phases  (atividade group headers)
  materia → Turma > Atividade > Aluno > Phases  (turma + atividade group headers)

Current state (what FAILS):
  - turma branch fetches only alunos, NOT atividades → no atividade grouping
  - no materia branch exists at all

These tests MUST FAIL until F2-T2 is implemented.

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f2_t2_hierarchy_nesting.py -v
"""

from pathlib import Path
import re

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"

# ── shared fixture ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def html_content():
    """Read the frontend HTML file once for all tests in this module."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def prefetch_body(html_content):
    """Extract the body of prefetchDesempenhoEtapasState(), up to the closing brace.

    Returns the slice starting at 'async function prefetchDesempenhoEtapasState(' and
    spanning approximately 3 000 chars — enough to cover all level branches without
    leaking into adjacent functions.
    """
    marker = "async function prefetchDesempenhoEtapasState("
    start = html_content.find(marker)
    assert start != -1, (
        "prefetchDesempenhoEtapasState() must be defined in index_v2.html. "
        "F2-T1 should have created it."
    )
    # 3 000 chars covers the full current implementation with room to spare
    return html_content[start : start + 3000]


# ── Test 1: turma branch fetches atividades ─────────────────────────────────


class TestTurmaBranchFetchesAtividades:
    """F2-T2: When level='turma', the function must fetch atividades for that turma
    so they can be used as group headers in the rendered tree.

    Current bug: the turma branch only fetches /alunos — no atividade grouping.
    """

    def test_prefetch_handles_turma_level_with_atividade_grouping(self, prefetch_body):
        """The turma branch must include an API call for /atividades?turma_id=.

        Expected pattern inside the `level === 'turma'` branch:
            api(`/atividades?turma_id=${entityId}`)
        or equivalent call that fetches atividades for the turma.
        """
        # Look for an atividades fetch inside the turma branch
        has_atividades_fetch = bool(re.search(
            r"""level\s*===\s*['"]turma['"][\s\S]{0,800}atividades\?turma_id""",
            prefetch_body,
            re.IGNORECASE,
        ))
        # Also accept a broader pattern: any atividades API call in the turma branch
        if not has_atividades_fetch:
            # Find the turma branch and check for /atividades within it
            turma_match = re.search(
                r"""level\s*===\s*['"]turma['"]""",
                prefetch_body,
            )
            if turma_match:
                # Slice from turma branch start (up to 600 chars covers the branch)
                turma_slice = prefetch_body[turma_match.start() : turma_match.start() + 600]
                has_atividades_fetch = "/atividades" in turma_slice

        assert has_atividades_fetch, (
            "prefetchDesempenhoEtapasState() turma branch must fetch atividades "
            "using an API call like api(`/atividades?turma_id=${entityId}`). "
            "\nCurrently the turma branch only fetches /alunos and sets docs=[], "
            "producing a flat aluno list instead of the required "
            "Atividade > Aluno > Phases grouping. "
            "\nF2-T2 must add atividade fetching in the turma branch."
        )


# ── Test 2: materia branch exists ───────────────────────────────────────────


class TestMateriaBranchExists:
    """F2-T2: prefetchDesempenhoEtapasState() must handle level='materia'.

    Current bug: there is NO materia branch — the function silently falls through
    to 'alunos.length === 0' with an empty list, showing 'Nenhum aluno encontrado'.
    """

    def test_prefetch_handles_materia_level(self, prefetch_body):
        """The function body must contain a branch for level === 'materia'.

        Expected: an `else if (level === 'materia')` (or `=== "materia"`) block
        that fetches turmas, then atividades per turma, then alunos + docs.
        """
        has_materia_branch = bool(re.search(
            r"""level\s*===\s*['"]materia['"]""",
            prefetch_body,
        ))
        assert has_materia_branch, (
            "prefetchDesempenhoEtapasState() has no branch for level === 'materia'. "
            "\nF2-T2 must add an `else if (level === 'materia')` branch that: "
            "\n  1. Fetches turmas for the materia: /turmas?materia_id=${entityId} "
            "\n  2. For each turma, fetches atividades: /atividades?turma_id=${t.id} "
            "\n  3. For each atividade, fetches alunos + docs "
            "\n  4. Renders: Turma group → Atividade group → Aluno > Phases "
            "\nCurrently the function silently falls through with alunos=[], "
            "causing 'Nenhum aluno encontrado' for all materia-level calls."
        )


# ── Test 3: turma renders atividade group headers ───────────────────────────


class TestTurmaRendersAtividadeGroupHeaders:
    """F2-T2: When rendering for turma level, the HTML output must include
    atividade names as section/group headers above the aluno rows.
    """

    def test_turma_renders_atividade_group_headers(self, html_content):
        """The rendering path for turma level must produce atividade group headers.

        Look for HTML template strings that produce group headers keyed on atividade
        data, within the body of prefetchDesempenhoEtapasState().

        Acceptable patterns (any of):
          - A div/section with class containing 'group' or 'header' that interpolates
            an atividade name variable (e.g., atividade.nome, atv.nome, a.nome)
          - innerHTML template containing 'atividade' as a grouping label
          - A helper function like renderAtividadeGroup() called from the turma branch

        The key requirement: atividade names must appear as structural group
        separators, NOT just incidentally within a flat aluno row.
        """
        # Locate the prefetch function
        func_start = html_content.find("async function prefetchDesempenhoEtapasState(")
        assert func_start != -1, "prefetchDesempenhoEtapasState must exist"
        func_body = html_content[func_start : func_start + 3000]

        # Must reference an atividade grouping in the rendering section
        has_atividade_group = bool(re.search(
            # Matches: .nome as a heading/header; or renderAtividadeGroup; or
            # a template literal with atividade.nome / atv.nome / atividade name
            r"""(?:renderAtividadeGroup|atividade[.\w]*nome|atv[.\w]*nome|atividadeNome"""
            r"""|<div[^>]*class=[^>]*group[^>]*>|<h[2-4][^>]*>)""",
            func_body,
            re.IGNORECASE,
        ))
        assert has_atividade_group, (
            "prefetchDesempenhoEtapasState() must render atividade group headers "
            "for the turma level. "
            "\nExpected: each atividade rendered as a group/section header "
            "(e.g., a div with a 'group' class, or an <h3> with the atividade name) "
            "above the list of alunos for that atividade. "
            "\nCurrently: the turma branch renders a flat aluno list with no grouping. "
            "\nF2-T2 must restructure the turma rendering: "
            "Atividade (group header) → Aluno row → Phase checkboxes."
        )


# ── Test 4: materia renders turma group headers ──────────────────────────────


class TestMateriaRendersTurmaGroupHeaders:
    """F2-T2: When rendering for materia level, the HTML output must include
    turma names as the outermost group headers (above atividade groups).
    """

    def test_materia_renders_turma_group_headers(self, html_content):
        """The rendering path for materia level must produce turma group headers.

        Acceptable patterns (any of):
          - A div/section that interpolates a turma name variable
            (e.g., turma.nome, t.nome, turmaName)
          - A helper function like renderTurmaGroup() called from the materia branch
          - Template literals containing 'turma' as a grouping label within the
            materia branch

        The key requirement: turma names must appear as the outermost structural
        group separators in the materia-level tree.
        """
        func_start = html_content.find("async function prefetchDesempenhoEtapasState(")
        assert func_start != -1, "prefetchDesempenhoEtapasState must exist"
        func_body = html_content[func_start : func_start + 3000]

        # First, there must be a materia branch at all
        has_materia_branch = bool(re.search(
            r"""level\s*===\s*['"]materia['"]""",
            func_body,
        ))
        assert has_materia_branch, (
            "No materia branch found — test_prefetch_handles_materia_level "
            "must pass first. Add the materia branch before testing its rendering."
        )

        # Within the materia branch, look for turma grouping in rendered output
        materia_match = re.search(r"""level\s*===\s*['"]materia['"]""", func_body)
        materia_slice = func_body[materia_match.start() : materia_match.start() + 1500]

        has_turma_group = bool(re.search(
            r"""(?:renderTurmaGroup|turma[.\w]*nome|t[.\w]*nome|turmaNome"""
            r"""|<div[^>]*class=[^>]*group[^>]*>|<h[1-3][^>]*>)""",
            materia_slice,
            re.IGNORECASE,
        ))
        assert has_turma_group, (
            "prefetchDesempenhoEtapasState() materia branch must render turma group "
            "headers as the outermost grouping. "
            "\nExpected: each turma rendered as a top-level group header "
            "(e.g., a div with a 'group' class or the turma name prominently displayed) "
            "wrapping the atividade groups below it. "
            "\nRequired structure: Turma group → Atividade group → Aluno row → Phase checkboxes. "
            "\nF2-T2 must build this nested rendering for the materia level."
        )
