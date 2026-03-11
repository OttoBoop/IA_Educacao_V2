"""
F2-T3 RED phase: Lazy-loading for deeper hierarchy levels in the desempenho etapas modal.

Expected lazy-loading behavior (what MUST be implemented):
  turma  → Load only atividade names first; each atividade group collapsed by default;
            expanding a group triggers an API call to load its alunos + docs.
  materia → Load only turma names first; each turma group collapsed by default;
             expanding a turma triggers an API call to load its atividades (which are
             themselves lazy-loaded as above).

Current state (what FAILS):
  - turma branch uses Promise.all to load ALL alunos AND all docs for EVERY atividade
    upfront before rendering anything. No groups start collapsed. No onclick expand handler.
  - materia branch loads ALL turmas, then immediately loads atividades + alunos for EACH
    turma in a sequential for-loop before rendering. No groups start collapsed. No onclick.

These tests MUST FAIL until F2-T3 is implemented.

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f2_t3_lazy_loading.py -v
"""

from pathlib import Path
import re

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"

# ── shared fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def html_content():
    """Read the frontend HTML file once for all tests in this module."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def prefetch_body(html_content):
    """Extract the body of prefetchDesempenhoEtapasState().

    Returns a slice of ~4 000 chars starting from the function definition —
    enough to cover all level branches including lazy-loading additions.
    """
    marker = "async function prefetchDesempenhoEtapasState("
    start = html_content.find(marker)
    assert start != -1, (
        "prefetchDesempenhoEtapasState() must be defined in index_v2.html. "
        "F2-T1 should have created it."
    )
    return html_content[start : start + 4000]


# ── Test 1: turma branch renders groups collapsed by default ─────────────────


class TestTurmaBranchCollapsedByDefault:
    """F2-T3: The turma branch must render each atividade group collapsed.

    Expected: group children are hidden on initial render, e.g. via
    `display:none` or a CSS class like 'collapsed' on the child container.

    Current bug: the turma branch calls renderAtividadeGroups() which renders
    every aluno row immediately — no collapsed initial state exists.
    """

    def test_turma_branch_group_children_hidden_on_load(self, prefetch_body):
        """Atividade group children in the turma branch must start hidden.

        Acceptable patterns (any of):
          - CSS inline style `display:none` on the children container inside
            the turma rendering path
          - A CSS class name like 'collapsed', 'hidden', 'lazy-children' applied
            to the child wrapper element inside the turma branch template
          - A data attribute like `data-collapsed="true"` on child containers

        The key requirement: the initial HTML for each atividade group must NOT
        show all aluno rows rendered and visible at page load.
        """
        # Locate the turma branch
        turma_match = re.search(r"""level\s*===\s*['"]turma['"]""", prefetch_body)
        assert turma_match is not None, (
            "No turma branch found in prefetchDesempenhoEtapasState(). "
            "F2-T2 should have added it."
        )
        # Slice the turma branch — up to 1 500 chars covers the branch body
        turma_slice = prefetch_body[turma_match.start() : turma_match.start() + 1500]

        has_collapsed_state = bool(re.search(
            # Matches: display:none / display: none / class with collapsed|hidden|lazy
            # or data-collapsed attribute
            r"""(?:display\s*:\s*none"""
            r"""|class\s*=\s*['""][^'"]*(?:collapsed|hidden|lazy)[^'"]*['"]"""
            r"""|data-collapsed\s*=\s*['"]true['"])""",
            turma_slice,
            re.IGNORECASE,
        ))
        assert has_collapsed_state, (
            "prefetchDesempenhoEtapasState() turma branch must render atividade "
            "group children in a collapsed (hidden) state by default. "
            "\nExpected: child container uses `display:none`, a CSS class like "
            "'collapsed' or 'hidden', or a `data-collapsed='true'` attribute. "
            "\nCurrently: renderAtividadeGroups() renders ALL aluno rows immediately "
            "with no collapsed state — everything is visible on load. "
            "\nF2-T3 must restructure the turma rendering so each atividade group "
            "header is visible but its children are hidden until the user expands it."
        )


# ── Test 2: turma branch has expand onclick handler on group headers ──────────


class TestTurmaBranchHasExpandHandler:
    """F2-T3: The turma branch group headers must have an onclick expand handler.

    Expected: each atividade group header element has an onclick attribute (or
    addEventListener wiring) that triggers loading of aluno children on demand.

    Current bug: the turma branch renders group headers via renderAtividadeGroups()
    which produces static `<div class="desempenho-group-header">` elements with
    NO onclick handler — clicking them does nothing.
    """

    def test_turma_branch_group_header_has_onclick(self, prefetch_body):
        """Atividade group headers in the turma branch must have onclick expand behavior.

        Acceptable patterns (any of):
          - An `onclick` attribute on the group header element in the template string
          - A named expand function called from an onclick, e.g.
            `onclick="expandAtividadeGroup(this, ...)"` or
            `onclick="loadAtividadeChildren(this, ...)"` or similar
          - An `addEventListener('click', ...)` wired to the group header elements
            immediately after the HTML is set (within the turma branch)

        The key requirement: the group header must be clickable and trigger loading.
        """
        turma_match = re.search(r"""level\s*===\s*['"]turma['"]""", prefetch_body)
        assert turma_match is not None, (
            "No turma branch found — F2-T2 should have added it."
        )
        turma_slice = prefetch_body[turma_match.start() : turma_match.start() + 1500]

        has_onclick = bool(re.search(
            r"""(?:onclick\s*="""
            r"""|addEventListener\s*\(\s*['"]click['"]"""
            r"""|\.onclick\s*=)""",
            turma_slice,
            re.IGNORECASE,
        ))
        assert has_onclick, (
            "prefetchDesempenhoEtapasState() turma branch must wire an onclick handler "
            "to each atividade group header so users can expand groups on demand. "
            "\nExpected: template string includes `onclick=\"expandGroup(this, ...)\"` "
            "or similar, OR an addEventListener('click', ...) is attached to group "
            "header elements after the initial HTML is rendered. "
            "\nCurrently: the turma branch calls renderAtividadeGroups() which produces "
            "static headers with no interaction handler. Clicking a group header does "
            "nothing. "
            "\nF2-T3 must add onclick expand behavior to each atividade group header "
            "in the turma branch."
        )


# ── Test 3: turma branch defers aluno/doc loading until expand ───────────────


class TestTurmaBranchDefersChildLoading:
    """F2-T3: The turma branch must NOT load alunos or docs for all atividades upfront.

    Expected: the initial render only fetches atividade names. Aluno and doc data
    for each atividade is fetched only when the user expands that group.

    Current bug: the turma branch calls Promise.all([/atividades, /alunos]) and
    then renderAtividadeGroups() immediately loads /documentos for EVERY atividade
    before rendering. This defeats the purpose of lazy-loading.
    """

    def test_turma_branch_does_not_eagerly_load_all_alunos_upfront(self, prefetch_body):
        """The turma branch initial fetch must be atividade names only — not all alunos.

        The test checks that within the turma branch, the initial fetch is limited
        to atividades, and that the combined eager-load pattern of fetching BOTH
        atividades AND alunos in the same Promise.all is NOT present.

        Specifically: `Promise.all([...atividades..., ...alunos...])` within the
        turma branch's initial render block must be absent — alunos should only
        be fetched in a deferred expand handler (a separate function or callback).
        """
        turma_match = re.search(r"""level\s*===\s*['"]turma['"]""", prefetch_body)
        assert turma_match is not None, (
            "No turma branch found — F2-T2 should have added it."
        )
        # The turma branch body — up to the next `else if` or closing brace
        turma_slice = prefetch_body[turma_match.start() : turma_match.start() + 1200]

        # The current (wrong) pattern: Promise.all loading BOTH atividades AND alunos
        # together in the initial render block of the turma branch
        eager_load_pattern = bool(re.search(
            r"""Promise\.all\s*\(\s*\[[\s\S]{0,300}atividades[\s\S]{0,300}alunos[\s\S]{0,50}\]""",
            turma_slice,
        ))
        assert not eager_load_pattern, (
            "prefetchDesempenhoEtapasState() turma branch must NOT eagerly load both "
            "atividades AND alunos together in a single Promise.all upfront. "
            "\nCurrently: the turma branch calls "
            "`Promise.all([api('/atividades?turma_id=...'), api('/alunos?turma_id=...')])`"
            " which fetches all student data before any group is expanded. "
            "\nF2-T3 must change the turma branch to: "
            "\n  1. Fetch only atividade names initially "
            "\n  2. Render collapsed group headers "
            "\n  3. Load alunos + docs per-atividade only when a group is expanded. "
            "\nThe Promise.all([atividades, alunos]) eager pattern must be removed "
            "from the turma branch's top-level (non-deferred) code path."
        )


# ── Test 4: materia branch renders turma groups collapsed by default ──────────


class TestMateriaBranchCollapsedByDefault:
    """F2-T3: The materia branch must render each turma group collapsed.

    Expected: turma group children are hidden on initial render.

    Current bug: the materia branch loops through all turmas and immediately
    calls renderAtividadeGroups() for each — rendering all children upfront
    with no collapsed state.
    """

    def test_materia_branch_turma_groups_hidden_on_load(self, prefetch_body):
        """Turma group children in the materia branch must start hidden.

        Acceptable patterns (any of):
          - CSS inline style `display:none` on child containers inside the
            materia rendering path
          - A CSS class like 'collapsed', 'hidden', or 'lazy-children' on
            child wrapper elements inside the materia branch template
          - A `data-collapsed="true"` attribute on turma child containers

        The key requirement: the initial HTML for each turma group must NOT
        contain fully rendered atividade groups and aluno rows on load.
        """
        materia_match = re.search(r"""level\s*===\s*['"]materia['"]""", prefetch_body)
        assert materia_match is not None, (
            "No materia branch found in prefetchDesempenhoEtapasState(). "
            "F2-T2 should have added it."
        )
        materia_slice = prefetch_body[materia_match.start() : materia_match.start() + 1500]

        has_collapsed_state = bool(re.search(
            r"""(?:display\s*:\s*none"""
            r"""|class\s*=\s*['""][^'"]*(?:collapsed|hidden|lazy)[^'"]*['"]"""
            r"""|data-collapsed\s*=\s*['"]true['"])""",
            materia_slice,
            re.IGNORECASE,
        ))
        assert has_collapsed_state, (
            "prefetchDesempenhoEtapasState() materia branch must render turma groups "
            "in a collapsed (hidden) state by default. "
            "\nExpected: turma child container uses `display:none`, a CSS class like "
            "'collapsed' or 'hidden', or a `data-collapsed='true'` attribute. "
            "\nCurrently: the materia branch loops over turmas and for EACH calls "
            "renderAtividadeGroups() which renders all atividade and aluno rows "
            "immediately — no collapsed state exists. "
            "\nF2-T3 must restructure the materia rendering so each turma group "
            "header is visible but its children are hidden until the user expands it."
        )


# ── Test 5: materia branch has expand onclick handler on turma group headers ──


class TestMateriaBranchHasExpandHandler:
    """F2-T3: The materia branch turma group headers must have an onclick expand handler.

    Expected: each turma group header element has an onclick attribute or
    equivalent that triggers deferred loading of its atividade children.

    Current bug: the materia branch renders turma headers as plain
    `<div class="desempenho-turma-header">` elements with NO onclick —
    clicking them does nothing and all data is already loaded anyway.
    """

    def test_materia_branch_turma_header_has_onclick(self, prefetch_body):
        """Turma group headers in the materia branch must have onclick expand behavior.

        Acceptable patterns (any of):
          - An `onclick` attribute on the turma header element in the template string
          - A named expand function, e.g. `onclick="expandTurmaGroup(this, ...)"` or
            `onclick="loadTurmaChildren(this, ...)"` or similar
          - An `addEventListener('click', ...)` wired to turma header elements
            immediately after initial HTML is set (within the materia branch)
        """
        materia_match = re.search(r"""level\s*===\s*['"]materia['"]""", prefetch_body)
        assert materia_match is not None, (
            "No materia branch found — F2-T2 should have added it."
        )
        materia_slice = prefetch_body[materia_match.start() : materia_match.start() + 1500]

        has_onclick = bool(re.search(
            r"""(?:onclick\s*="""
            r"""|addEventListener\s*\(\s*['"]click['"]"""
            r"""|\.onclick\s*=)""",
            materia_slice,
            re.IGNORECASE,
        ))
        assert has_onclick, (
            "prefetchDesempenhoEtapasState() materia branch must wire an onclick handler "
            "to each turma group header so users can expand groups on demand. "
            "\nExpected: template string includes `onclick=\"expandTurmaGroup(this, ...)\"` "
            "or similar, OR an addEventListener('click', ...) is attached to turma "
            "header elements after the initial HTML is rendered. "
            "\nCurrently: the materia branch renders "
            "`<div class=\"desempenho-turma-header\">${turmaNome}</div>` with no "
            "interaction handler. "
            "\nF2-T3 must add onclick expand behavior to each turma group header "
            "in the materia branch."
        )


# ── Test 6: a lazy-load expand function exists in the HTML ───────────────────


class TestLazyLoadExpandFunctionExists:
    """F2-T3: A dedicated expand/lazy-load function must be defined in index_v2.html.

    Expected: a JavaScript function that is called when the user clicks a group
    header, fetches children from the API, and injects them into the DOM.

    Current state: no such function exists — all data is loaded eagerly in
    prefetchDesempenhoEtapasState() itself before any group is expanded.
    """

    def test_expand_or_lazy_load_function_is_defined(self, html_content):
        """A function for on-demand group expansion must be defined in the HTML.

        Acceptable function names (any of):
          - `expandAtividadeGroup`, `expandTurmaGroup`, `expandDesempenhoGroup`
          - `loadAtividadeChildren`, `loadTurmaChildren`, `loadGroupChildren`
          - `toggleDesempenhoGroup`, `toggleEtapasGroup`
          - Any `async function` whose name contains 'expand' or 'lazy' followed
            by 'group' or 'children' (case-insensitive)

        The function must:
          1. Accept a reference to the clicked element or group id
          2. Make an API call to fetch children (alunos, docs, or atividades)
          3. Inject the result into the DOM below the clicked header
        """
        has_expand_function = bool(re.search(
            r"""(?:function\s+(?:expand|load|toggle)(?:Atividade|Turma|Desempenho|Etapas)?"""
            r"""(?:Group|Children|Items)\s*\("""
            r"""|async\s+function\s+(?:expand|load|toggle)[\w]*(?:group|children|lazy)[\w]*\s*\()""",
            html_content,
            re.IGNORECASE,
        ))
        assert has_expand_function, (
            "index_v2.html must define a JavaScript function for on-demand group "
            "expansion in the desempenho etapas modal. "
            "\nExpected: a function like `expandAtividadeGroup(headerEl, atividadeId)` "
            "or `loadGroupChildren(groupId, level)` that fetches child data from the "
            "API and injects rendered rows into the DOM when a group header is clicked. "
            "\nCurrently: no such function exists. All data is loaded eagerly inside "
            "prefetchDesempenhoEtapasState() before any group is shown. "
            "\nF2-T3 must create this expand/lazy-load function as the backbone of "
            "the deferred loading mechanism."
        )
