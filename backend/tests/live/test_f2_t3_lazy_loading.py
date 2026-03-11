"""
F2-T3: Lazy-loading for deeper hierarchy levels.

When opening the desempenho settings modal at turma or materia level,
the hierarchy tree must NOT load all data upfront. Instead:
  - Turma level: renders atividade group headers with collapsed children
  - Materia level: renders turma group headers with collapsed children
  - expandDesempenhoGroup() lazy-loads children on demand (API call on click)
  - Children containers have data-loaded="false" until expanded

These tests verify the frontend HTML contains the lazy-loading implementation
and the backend APIs support the required endpoints.

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f2_t3_lazy_loading.py -v -m live
"""

import re
from pathlib import Path

import pytest
import requests

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


# ============================================================
# Test 1: expandDesempenhoGroup function exists and handles
#          both 'atividade' and 'turma' group types
# ============================================================


class TestExpandDesempenhoGroupExists:
    """F2-T3: The expandDesempenhoGroup function must exist and handle
    lazy-loading for both atividade and turma group types.
    """

    def test_expand_function_exists(self, html_content):
        """expandDesempenhoGroup must be a declared function that accepts
        groupType and groupId parameters.
        """
        has_function = bool(re.search(
            r"""function\s+expandDesempenhoGroup\s*\(""",
            html_content,
        ))
        assert has_function, (
            "F2-T3: expandDesempenhoGroup function must exist in index_v2.html. "
            "This function lazy-loads children when a hierarchy group is expanded."
        )

    def test_expand_handles_atividade_type(self, html_content):
        """expandDesempenhoGroup must handle groupType === 'atividade'
        by loading alunos + docs for that atividade.
        """
        # Extract the function body
        match = re.search(
            r"function\s+expandDesempenhoGroup\s*\([^)]*\)\s*\{",
            html_content,
        )
        assert match, "expandDesempenhoGroup function not found"
        func_body = html_content[match.start():match.start() + 3000]

        has_atividade_branch = bool(re.search(
            r"""groupType\s*===?\s*['"]atividade['"]""",
            func_body,
        ))
        assert has_atividade_branch, (
            "F2-T3: expandDesempenhoGroup must handle groupType 'atividade' "
            "to lazy-load alunos and documents for an atividade."
        )

    def test_expand_handles_turma_type(self, html_content):
        """expandDesempenhoGroup must handle groupType === 'turma'
        by loading atividades for that turma.
        """
        match = re.search(
            r"function\s+expandDesempenhoGroup\s*\([^)]*\)\s*\{",
            html_content,
        )
        assert match, "expandDesempenhoGroup function not found"
        func_body = html_content[match.start():match.start() + 3000]

        has_turma_branch = bool(re.search(
            r"""groupType\s*===?\s*['"]turma['"]""",
            func_body,
        ))
        assert has_turma_branch, (
            "F2-T3: expandDesempenhoGroup must handle groupType 'turma' "
            "to lazy-load atividades for a turma."
        )


# ============================================================
# Test 2: Lazy-loading containers use data-loaded="false"
# ============================================================


class TestLazyLoadingContainersRendered:
    """F2-T3: The turma and materia branches of prefetchDesempenhoEtapasState
    must render lazy-loading containers with data-loaded='false'.
    """

    def test_lazy_children_containers_rendered(self, html_content):
        """The hierarchy rendering must include elements with class
        'desempenho-lazy-children' and data-loaded='false'.
        """
        has_lazy_container = bool(re.search(
            r"""desempenho-lazy-children.*data-loaded\s*=\s*["']false["']""",
            html_content,
        ))
        assert has_lazy_container, (
            "F2-T3: prefetchDesempenhoEtapasState must render containers with "
            "class='desempenho-lazy-children' and data-loaded='false' for "
            "turma/materia hierarchy groups. This enables lazy-loading on expand."
        )

    def test_expand_sets_loaded_true(self, html_content):
        """After loading children, expandDesempenhoGroup must set
        data-loaded='true' to prevent redundant API calls.
        """
        match = re.search(
            r"function\s+expandDesempenhoGroup\s*\([^)]*\)\s*\{",
            html_content,
        )
        assert match, "expandDesempenhoGroup function not found"
        # Use a larger window — the function is ~50 lines
        func_body = html_content[match.start():match.start() + 5000]

        sets_loaded_true = bool(re.search(
            r"""\.dataset\.loaded\s*=\s*['"]true['"]""",
            func_body,
        ))
        assert sets_loaded_true, (
            "F2-T3: expandDesempenhoGroup must set dataset.loaded = 'true' "
            "after loading children to prevent redundant API calls."
        )


# ============================================================
# Test 3: Turma-level prefetch renders lazy groups, not direct rows
# ============================================================


class TestTurmaLevelUsesLazyGroups:
    """F2-T3: When level === 'turma', prefetchDesempenhoEtapasState
    must render atividade group headers (not direct student rows).
    """

    def test_turma_branch_renders_atividade_groups(self, html_content):
        """The turma branch must render atividade groups with
        expandDesempenhoGroup onclick handlers.
        """
        # Find prefetchDesempenhoEtapasState function
        match = re.search(
            r"async\s+function\s+prefetchDesempenhoEtapasState\s*\(",
            html_content,
        )
        assert match, "prefetchDesempenhoEtapasState function not found"
        func_body = html_content[match.start():match.start() + 3000]

        # Check turma branch renders atividade groups with lazy-loading
        has_turma_lazy = bool(re.search(
            r"""level\s*===?\s*['"]turma['"]""",
            func_body,
        ))
        has_atividade_group = bool(re.search(
            r"""desempenho-atividade-group""",
            func_body,
        ))
        assert has_turma_lazy and has_atividade_group, (
            "F2-T3: prefetchDesempenhoEtapasState turma branch must render "
            "atividade group elements (not direct student rows) for lazy-loading."
        )


# ============================================================
# Test 4: Materia-level prefetch renders lazy turma groups
# ============================================================


class TestMateriaLevelUsesLazyGroups:
    """F2-T3: When level === 'materia', prefetchDesempenhoEtapasState
    must render turma group headers (not direct content).
    """

    def test_materia_branch_renders_turma_groups(self, html_content):
        """The materia branch must render turma groups with
        expandDesempenhoGroup onclick handlers.
        """
        match = re.search(
            r"async\s+function\s+prefetchDesempenhoEtapasState\s*\(",
            html_content,
        )
        assert match, "prefetchDesempenhoEtapasState function not found"
        func_body = html_content[match.start():match.start() + 3000]

        has_materia_lazy = bool(re.search(
            r"""level\s*===?\s*['"]materia['"]""",
            func_body,
        ))
        has_turma_group = bool(re.search(
            r"""desempenho-turma-group""",
            func_body,
        ))
        assert has_materia_lazy and has_turma_group, (
            "F2-T3: prefetchDesempenhoEtapasState materia branch must render "
            "turma group elements for lazy-loading."
        )


# ============================================================
# Test 5: expandDesempenhoGroup skips refetch when already loaded
# ============================================================


class TestExpandSkipsRefetch:
    """F2-T3: When a group is already loaded (data-loaded='true'),
    expanding it again must NOT re-fetch data.
    """

    def test_expand_checks_loaded_before_fetch(self, html_content):
        """expandDesempenhoGroup must check data-loaded before making
        API calls to prevent redundant network requests.
        """
        match = re.search(
            r"function\s+expandDesempenhoGroup\s*\([^)]*\)\s*\{",
            html_content,
        )
        assert match, "expandDesempenhoGroup function not found"
        func_body = html_content[match.start():match.start() + 3000]

        # Must check dataset.loaded === 'true' and return early
        checks_loaded = bool(re.search(
            r"""(?:dataset\.loaded\s*===?\s*['"]true['"]|data-loaded)""",
            func_body,
        ))
        assert checks_loaded, (
            "F2-T3: expandDesempenhoGroup must check if children are already "
            "loaded (dataset.loaded === 'true') to skip redundant API calls."
        )


# ============================================================
# Test 6 (LIVE): Backend APIs support lazy-loading endpoints
# ============================================================


class TestLazyLoadingApisAccessible:
    """F2-T3 (LIVE): Verify the backend APIs used by lazy-loading
    are accessible and return proper responses.
    """

    def test_turmas_api_by_materia(self):
        """GET /api/turmas?materia_id={id} must return a list of turmas.
        Used by materia-level lazy-loading.
        """
        # Use Matemática-V materia ID from seed data
        url = f"{LIVE_URL}/api/turmas?materia_id=0f615b57854235ec"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"GET /api/turmas?materia_id=... returned {resp.status_code}: {resp.text[:300]}"
        )
        data = resp.json()
        turmas = data.get("turmas", [])
        assert len(turmas) >= 1, (
            "F2-T3: /api/turmas must return at least 1 turma for Matemática-V. "
            f"Got: {data}"
        )

    def test_atividades_api_by_turma(self):
        """GET /api/atividades?turma_id={id} must return a list of atividades.
        Used by turma-level lazy-loading.
        """
        # Use Alpha-V turma ID from seed data
        url = f"{LIVE_URL}/api/atividades?turma_id=cc739cc55191d056"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"GET /api/atividades?turma_id=... returned {resp.status_code}: {resp.text[:300]}"
        )
        data = resp.json()
        atividades = data.get("atividades", [])
        assert len(atividades) >= 1, (
            "F2-T3: /api/atividades must return at least 1 atividade for Alpha-V. "
            f"Got: {data}"
        )
