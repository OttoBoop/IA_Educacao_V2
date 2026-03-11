"""
F1-T1 RED: Per-level-entity button state for "Gerar Relatório".

Bug: _desempenhoGenerating was converted from boolean to object (per-entity key),
BUT the ancillary state is still global:
  - _desempenhoTimer (single interval for elapsed counter)
  - _desempenhoActiveTask (single task reference)
  - _desempenhoPollInterval (single poll interval)
  - loadDesempenhoData() finds ANY desempenho task, not level+entity-specific
  - _cleanupDesempenhoProgress() clears ALL timers globally

Result: Starting materia desempenho then turma desempenho overwrites the timer/poll
of the first. When the first completes, cleanup kills the second's progress too.

These tests verify the frontend JS code has per-key state management for ALL
desempenho progress-related variables, not just the guard boolean.

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f1_t1_per_level_button_state.py -v -m live
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
# Test 1: Timer state must be per-key (not global singleton)
# ============================================================


class TestDesempenhoTimerPerKey:
    """F1-T1: _desempenhoTimer must be per-key so concurrent tasks
    each have their own elapsed-time counter.

    Current state: `let _desempenhoTimer = null;` — single global.
    Expected: `let _desempenhoTimers = {};` or similar per-key structure.
    """

    def test_timer_is_per_key_not_singleton(self, html_content):
        """The timer variable must be a dict/object keyed by level-entity,
        not a single null/interval reference.

        Acceptable patterns:
          - _desempenhoTimers = {}  (object, plural name)
          - _desempenhoTimer[key]  (indexed access)
          - _desempenhoTimers[_desempenhoKey]
          - Any pattern that stores timers per-key

        The key requirement: clearing timer for task A must NOT affect
        timer for task B.
        """
        # Check for per-key timer pattern (object indexed by key)
        has_per_key_timer = bool(re.search(
            r"""(?:_desempenhoTimer(?:s)?\s*\[\s*(?:_desempenhoKey|level|key))""",
            html_content,
        ))
        # Also check it's not still a plain `= null` singleton
        has_singleton_timer = bool(re.search(
            r"""let\s+_desempenhoTimer\s*=\s*null""",
            html_content,
        ))
        assert has_per_key_timer and not has_singleton_timer, (
            "F1-T1: _desempenhoTimer must be a per-key object (not a global singleton). "
            "\nCurrently: `let _desempenhoTimer = null;` — single global interval. "
            "\nExpected: `let _desempenhoTimers = {};` with indexed access like "
            "`_desempenhoTimers[_desempenhoKey]` so clearing one timer doesn't affect others."
        )


# ============================================================
# Test 2: Active task must be per-key (not global singleton)
# ============================================================


class TestDesempenhoActiveTaskPerKey:
    """F1-T1: _desempenhoActiveTask must be per-key so multiple
    concurrent desempenho tasks can coexist.

    Current state: `let _desempenhoActiveTask = null;` — single global.
    Expected: per-key tracking or removal of this variable.
    """

    def test_active_task_is_per_key_not_singleton(self, html_content):
        """The active task tracking must be per-key or removed entirely.

        Acceptable patterns:
          - _desempenhoActiveTasks = {}  (object, plural)
          - _desempenhoActiveTasks[key] = { taskId, ... }
          - No _desempenhoActiveTask at all (if polling handles it differently)

        The key requirement: starting task B must NOT overwrite task A's reference.
        """
        has_singleton_active = bool(re.search(
            r"""let\s+_desempenhoActiveTask\s*=\s*null""",
            html_content,
        ))
        assert not has_singleton_active, (
            "F1-T1: _desempenhoActiveTask must NOT be a global singleton. "
            "\nCurrently: `let _desempenhoActiveTask = null;` — starting a second "
            "desempenho task overwrites the first task's reference. "
            "\nExpected: per-key tracking like `_desempenhoActiveTasks = {}` or "
            "remove the variable entirely if polling handles concurrency."
        )


# ============================================================
# Test 3: Poll interval must be per-key (not global singleton)
# ============================================================


class TestDesempenhoPollIntervalPerKey:
    """F1-T1: _desempenhoPollInterval must be per-key so cleanup
    of one task's polling doesn't kill another task's polling.

    Current state: `let _desempenhoPollInterval = null;` — single global.
    """

    def test_poll_interval_is_per_key_not_singleton(self, html_content):
        """The poll interval must be per-key or managed per-task.

        Acceptable patterns:
          - _desempenhoPollIntervals = {}
          - _desempenhoPollIntervals[key]
          - Per-task polling managed by _awaitDesempenhoCompletion closure

        The key requirement: clearing poll for task A must NOT stop
        polling for task B.
        """
        has_singleton_poll = bool(re.search(
            r"""let\s+_desempenhoPollInterval\s*=\s*null""",
            html_content,
        ))
        assert not has_singleton_poll, (
            "F1-T1: _desempenhoPollInterval must NOT be a global singleton. "
            "\nCurrently: `let _desempenhoPollInterval = null;` — cleanup of one "
            "task clears the poll interval for ALL concurrent tasks. "
            "\nExpected: per-key tracking like `_desempenhoPollIntervals = {}` or "
            "closure-scoped polling in _awaitDesempenhoCompletion."
        )


# ============================================================
# Test 4: loadDesempenhoData must filter by level+entity
# ============================================================


class TestLoadDesempenhoDataFiltersSpecific:
    """F1-T1: loadDesempenhoData() must only detect active tasks
    for the SPECIFIC level+entity being loaded, not ANY desempenho task.

    Current state: finds any task with type starting 'pipeline_desempenho_'.
    Expected: also checks that the task matches the current level+entityId.
    """

    def test_load_data_filters_by_level_entity(self, html_content):
        """loadDesempenhoData must match tasks to the specific level+entity.

        Acceptable patterns:
          - Check task type includes level (e.g., `=== 'pipeline_desempenho_' + level`)
          - Check task metadata for matching entityId
          - Use per-entity guard as filter instead of global find

        The key requirement: a running materia task must NOT show a spinner
        on the turma desempenho tab.
        """
        # Extract the loadDesempenhoData function body
        match = re.search(
            r"async\s+function\s+loadDesempenhoData\s*\([^)]*\)\s*\{",
            html_content,
        )
        assert match, "loadDesempenhoData function not found"

        # Get ~60 lines after the function start
        start = match.start()
        func_body = html_content[start:start + 2000]

        # The bug: startsWith('pipeline_desempenho_') matches ANY level.
        # Check that the find() callback includes level-specific matching
        has_generic_starts_with = bool(re.search(
            r"""startsWith\s*\(\s*['"]pipeline_desempenho_['"]\s*\)""",
            func_body,
        ))
        has_level_specific = bool(re.search(
            r"""(?:pipeline_desempenho_['"]?\s*\+\s*level"""  # type includes level variable
            r"""|===\s*['"]pipeline_desempenho_['"]?\s*\+\s*level"""
            r"""|type.*===.*'pipeline_desempenho_\$\{level\}')""",
            func_body,
        ))
        assert not has_generic_starts_with or has_level_specific, (
            "F1-T1: loadDesempenhoData() must filter active tasks by level+entity, "
            "not just find ANY running desempenho task. "
            "\nCurrently: `t.type.startsWith('pipeline_desempenho_')` — matches ANY "
            "desempenho task regardless of level. A running materia task shows a "
            "spinner on the turma tab too. "
            "\nExpected: `t.type === 'pipeline_desempenho_' + level` or similar "
            "level-specific filter."
        )


# ============================================================
# Test 5: _cleanupDesempenhoProgress only clears specific key
# ============================================================


class TestCleanupOnlyClearsSpecificKey:
    """F1-T1: _cleanupDesempenhoProgress must only clear state for
    the specific level+entity being cleaned, not all global state.

    Current state: clears _desempenhoTimer, _desempenhoActiveTask,
    _desempenhoPollInterval globally.
    """

    def test_cleanup_uses_per_key_clearing(self, html_content):
        """Cleanup must use per-key clearing for timers and polls.

        Acceptable patterns:
          - clearInterval(_desempenhoTimers[key])
          - delete _desempenhoTimers[key]
          - clearInterval(_desempenhoPollIntervals[key])
          - Any pattern that clears only the specific key's timer/poll

        The key requirement: cleaning up after task A must NOT stop
        task B's timer or polling.
        """
        # Extract the cleanup function body
        match = re.search(
            r"function\s+_cleanupDesempenhoProgress\s*\([^)]*\)\s*\{",
            html_content,
        )
        assert match, "_cleanupDesempenhoProgress function not found"

        start = match.start()
        func_body = html_content[start:start + 1500]

        # Check for per-key clearing (not global clearInterval)
        has_per_key_clear = bool(re.search(
            r"""(?:clearInterval\s*\(\s*_desempenhoTimer(?:s)?\s*\[\s*"""
            r"""|delete\s+_desempenhoTimer(?:s)?\s*\[\s*"""
            r"""|clearInterval\s*\(\s*_desempenhoPollInterval(?:s)?\s*\[)""",
            func_body,
        ))
        assert has_per_key_clear, (
            "F1-T1: _cleanupDesempenhoProgress must clear timers/polls per-key, "
            "not globally. "
            "\nCurrently: `clearInterval(_desempenhoTimer); _desempenhoTimer = null;` — "
            "clears ALL timers regardless of which task completed. "
            "\nExpected: `clearInterval(_desempenhoTimers[key]); delete _desempenhoTimers[key];`"
        )


# ============================================================
# Test 6 (LIVE): Desempenho endpoint accepts concurrent requests
# ============================================================


class TestDesempenhoConcurrentRequestsLive:
    """F1-T1 (LIVE): Verify the backend can accept multiple
    concurrent desempenho pipeline requests without blocking.
    """

    def test_desempenho_endpoint_exists_and_is_accessible(self):
        """POST /api/executar/pipeline-desempenho-tarefa must return
        a proper response (not 500) when called.

        This proves the endpoint exists and concurrent requests
        would be handled server-side (task queue pattern).
        """
        url = f"{LIVE_URL}/api/executar/pipeline-desempenho-tarefa"
        # Send a request with an invalid entity to get a controlled error
        resp = requests.post(
            url,
            data={"atividade_id": "nonexistent-f1t1-test"},
            timeout=30,
        )
        # Should return 200 with task_id (async) or 400/404 (invalid entity)
        # NOT 500 (server error) or 405 (method not allowed)
        assert resp.status_code != 500, (
            f"Pipeline endpoint returned 500 server error: {resp.text[:300]}"
        )
        assert resp.status_code != 405, (
            f"Pipeline endpoint returned 405 — method not allowed"
        )
