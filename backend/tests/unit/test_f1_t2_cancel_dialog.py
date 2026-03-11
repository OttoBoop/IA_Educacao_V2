"""
F1-T2 RED Phase — Cancel Confirmation Dialog + UI State Reset

Unit tests that verify index_v2.html has:
1. A confirmation dialog in cancelTask() ("Tem certeza?" / confirm())
2. Handling of data.status === 'cancelled' in _awaitDesempenhoCompletion()
3. Cleanup of _desempenhoGenerating state when a task is cancelled

All three tests MUST FAIL in the RED phase because:
- cancelTask() currently has NO confirmation dialog
- _awaitDesempenhoCompletion() does NOT handle 'cancelled' status
- The cancelled branch does not call _cleanupDesempenhoProgress (or delete _desempenhoGenerating)

Plan: docs/PLAN_Desempenho_UI_Pipeline_Bugs_R2.md — F1-T2

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f1_t2_cancel_dialog.py -v
"""

import re
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def html_content():
    """Read index_v2.html once for the entire module."""
    html_path = (
        Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    )
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def active_html(html_content):
    """HTML content with HTML comments stripped (only active code)."""
    return re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)


def _extract_function_body(source: str, func_name: str, max_chars: int = 2000) -> str:
    """
    Return up to max_chars characters starting from the function declaration.
    Raises pytest.fail if the function is not found.
    """
    pos = source.find(f"function {func_name}")
    if pos < 0:
        pytest.fail(f"Function '{func_name}' not found in index_v2.html")
    return source[pos : pos + max_chars]


# ---------------------------------------------------------------------------
# F1-T2-T1: cancelTask must ask for confirmation before cancelling
# ---------------------------------------------------------------------------

class TestCancelTaskHasConfirmation:
    """
    cancelTask() currently fires the cancel immediately with no user prompt.
    F1-T2 requires it to show a confirmation dialog ("Tem certeza?") first.

    Expected to FAIL (RED) until implementation adds confirm() or equivalent.
    """

    def test_cancel_task_has_confirmation(self, active_html):
        """
        cancelTask() must contain a confirmation prompt before executing the cancel.

        Accepted patterns (any one is sufficient):
        - confirm(          — native browser confirm()
        - "Tem certeza"     — Portuguese confirmation text anywhere in the function
        - showConfirmDialog — a custom dialog helper function call
        - .then(confirmed   — a promise-based custom dialog

        RED: fails because cancelTask() currently calls fetch() immediately
             without any guard, confirmation prompt, or dialog.
        GREEN: passes after F1-T2 implementation adds confirm() or custom dialog.
        """
        func_body = _extract_function_body(active_html, "cancelTask")

        has_confirmation = (
            "confirm(" in func_body
            or "Tem certeza" in func_body
            or "showConfirmDialog" in func_body
            or ".then(confirmed" in func_body
        )

        assert has_confirmation, (
            "cancelTask() must show a confirmation dialog before cancelling.\n"
            "Currently it calls fetch('/api/task-cancel/...') immediately — no user prompt.\n"
            "Fix: add `if (!confirm('Tem certeza que deseja cancelar?')) return;` before the fetch,\n"
            "or wire a custom modal dialog that resolves before proceeding.\n"
            f"\nFirst 600 chars of cancelTask():\n{func_body[:600]}"
        )


# ---------------------------------------------------------------------------
# F1-T2-T2: _awaitDesempenhoCompletion must handle 'cancelled' status
# ---------------------------------------------------------------------------

class TestAwaitCompletionHandlesCancelledStatus:
    """
    _awaitDesempenhoCompletion() currently handles 'completed' and 'failed'
    but silently ignores 'cancelled'. When the backend marks a task as
    'cancelled', the poll loop keeps running indefinitely and the UI stays stuck
    in "generating" state with no feedback to the professor.

    F1-T2 requires handling 'cancelled' to clean up progress state and show
    a "cancelado" toast.

    Expected to FAIL (RED) until F1-T2 implementation adds the cancelled branch.
    """

    def test_await_completion_handles_cancelled_status(self, active_html):
        """
        _awaitDesempenhoCompletion() must handle data.status === 'cancelled'.

        Accepted patterns (any one is sufficient):
        - === 'cancelled'   — strict equality check for the status string
        - == 'cancelled'    — loose equality check
        - case 'cancelled'  — switch/case pattern

        RED: fails because only 'completed' and 'failed' are handled.
             The comment on line 10153 even says: "// else 'running' — keep polling"
             which means 'cancelled' is silently treated as 'still running'.
        GREEN: passes after F1-T2 adds an `else if (data.status === 'cancelled')` branch.
        """
        func_body = _extract_function_body(active_html, "_awaitDesempenhoCompletion", max_chars=3000)

        has_cancelled_branch = (
            "'cancelled'" in func_body
            or '"cancelled"' in func_body
        )

        assert has_cancelled_branch, (
            "_awaitDesempenhoCompletion() must handle data.status === 'cancelled'.\n"
            "Currently it only handles 'completed' and 'failed'.\n"
            "When the backend cancels a task, the poll loop never terminates and\n"
            "the button stays stuck in 'gerando...' state.\n"
            "Fix: add an `else if (data.status === 'cancelled')` branch that calls\n"
            "_cleanupDesempenhoProgress() and shows a 'Cancelado' toast.\n"
            f"\nFirst 800 chars of _awaitDesempenhoCompletion():\n{func_body[:800]}"
        )


# ---------------------------------------------------------------------------
# F1-T2-T3: cancelled branch must clean up _desempenhoGenerating state
# ---------------------------------------------------------------------------

class TestCancelCleansDesempenhoGeneratingState:
    """
    After a cancel is confirmed and the backend reports 'cancelled', the
    _desempenhoGenerating entry for that level+entityId must be removed so the
    button is re-enabled. This requires either:
    - calling _cleanupDesempenhoProgress() from the cancelled branch, OR
    - directly deleting from _desempenhoGenerating in the cancelled branch.

    Expected to FAIL (RED) because the 'cancelled' branch doesn't exist yet,
    so neither cleanup path can be present there.
    """

    def test_cancel_cleans_desempenho_generating_state(self, active_html):
        """
        The 'cancelled' handling in _awaitDesempenhoCompletion() must remove the
        _desempenhoGenerating entry so the button is re-enabled after cancellation.

        Accepted patterns anywhere inside _awaitDesempenhoCompletion():
        - _cleanupDesempenhoProgress(  — calls the shared cleanup helper (preferred)
        - delete _desempenhoGenerating — directly removes the per-level key

        RED: fails because the cancelled branch does not exist yet, so neither
             cleanup call can be inside it.
        GREEN: passes after F1-T2 implementation adds cleanup in the cancelled branch.
        """
        func_body = _extract_function_body(active_html, "_awaitDesempenhoCompletion", max_chars=3000)

        # The 'cancelled' status must be handled
        has_cancelled_branch = (
            "'cancelled'" in func_body
            or '"cancelled"' in func_body
        )

        # AND the cancelled branch must trigger cleanup
        has_cleanup = (
            "_cleanupDesempenhoProgress(" in func_body
            or "delete _desempenhoGenerating" in func_body
        )

        # Both conditions must be true — cleanup inside the cancelled branch
        # We verify jointly: if there's no cancelled branch, there's no cleanup there
        assert has_cancelled_branch and has_cleanup, (
            "_awaitDesempenhoCompletion() must clean up _desempenhoGenerating when status is 'cancelled'.\n"
            "Without this, the button stays in 'gerando...' state forever after the user cancels.\n"
            "\nCurrent state:\n"
            f"  has 'cancelled' branch: {has_cancelled_branch}\n"
            f"  has cleanup call:       {has_cleanup}\n"
            "\nFix: In the cancelled branch, call _cleanupDesempenhoProgress(generateArea, level, entityId)\n"
            "or directly: delete _desempenhoGenerating[level + '-' + entityId]"
        )
