"""
F7-T2 RED: Frontend loud notification when pdf_fallback_used is true.

When the backend detects that the LLM called create_document but NOT
execute_python_code, it sets pdf_fallback_used=true and adds a
{tipo: 'pdf_fallback'} alert. The frontend must:

1. Detect pdf_fallback alerts in the task-progress polling response
2. Show a loud popup: "Relatório PDF gerado automaticamente — modelo não produziu PDF"
3. Log a console.warn()

These tests verify BOTH:
  - The frontend HTML contains the notification code (static analysis)
  - The backend API propagates the flag (live API check)

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f7_t2_pdf_fallback_notification.py -v -m live
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
# Test 1: Frontend JS checks for pdf_fallback in polling response
# ============================================================


class TestPdfFallbackDetectionInPolling:
    """F7-T2: The polling code must check for pdf_fallback alerts in the
    task-progress response and trigger a notification.

    Current state: pollTaskProgress() and _awaitDesempenhoCompletion()
    only check data.status === 'completed' and show a generic toast.
    No pdf_fallback check exists.
    """

    def test_polling_checks_pdf_fallback_alert(self, html_content):
        """The JS polling code must contain a check for pdf_fallback.

        Acceptable patterns (any of):
          - `pdf_fallback` string check in pollTaskProgress or
            _awaitDesempenhoCompletion functions
          - A check on `data.result?.alertas` for tipo === 'pdf_fallback'
          - A check on `data.pdf_fallback_used`
          - A dedicated function like `checkPdfFallback(data)` called
            from the polling code

        The key requirement: when a completed task has a pdf_fallback
        alert, the frontend must detect it during polling.
        """
        has_pdf_fallback_check = bool(re.search(
            r"""(?:pdf_fallback"""
            r"""|pdf.fallback"""
            r"""|pdfFallback)""",
            html_content,
            re.IGNORECASE,
        ))
        assert has_pdf_fallback_check, (
            "index_v2.html must contain JavaScript code that checks for "
            "'pdf_fallback' in the task-progress polling response. "
            "\nExpected: a check like `data.result?.alertas?.some(a => a.tipo === 'pdf_fallback')` "
            "or `data.pdf_fallback_used === true` in pollTaskProgress() or "
            "_awaitDesempenhoCompletion(). "
            "\nCurrently: NO pdf_fallback detection exists in the frontend. "
            "The polling code only checks data.status and shows a generic toast."
        )


# ============================================================
# Test 2: Frontend shows popup with correct message
# ============================================================


class TestPdfFallbackPopupMessage:
    """F7-T2: When pdf_fallback is detected, a loud popup must appear
    with the specific message about automatic PDF generation.

    Current state: No such popup exists.
    """

    def test_popup_contains_auto_pdf_message(self, html_content):
        """The frontend must show a popup with a message indicating
        the PDF was auto-generated because the model didn't produce one.

        Acceptable message patterns (any of):
          - "PDF gerado automaticamente"
          - "modelo não produziu PDF"
          - "Relatório PDF gerado automaticamente"
          - Any Portuguese message mentioning PDF + automático/fallback

        The key requirement: the user must see a LOUD notification
        (not just a subtle toast) about the auto-generated PDF.
        """
        has_fallback_message = bool(re.search(
            r"""(?:PDF\s+gerado\s+automaticamente"""
            r"""|modelo\s+n[aã]o\s+produziu\s+PDF"""
            r"""|Relat[oó]rio\s+PDF\s+gerado\s+automaticamente"""
            r"""|pdf.*fallback.*toast"""
            r"""|showPipelineToast.*pdf.*fallback)""",
            html_content,
            re.IGNORECASE,
        ))
        assert has_fallback_message, (
            "index_v2.html must contain a popup/toast message for the PDF "
            "auto-fallback notification. "
            "\nExpected: a string like 'Relatório PDF gerado automaticamente "
            "— modelo não produziu PDF' passed to showPipelineToast() or "
            "showToast() or alert(). "
            "\nCurrently: NO pdf_fallback notification message exists."
        )


# ============================================================
# Test 3: Frontend logs console.warn for pdf_fallback
# ============================================================


class TestPdfFallbackConsoleWarn:
    """F7-T2: When pdf_fallback triggers, the frontend must log a
    console.warn() for developer visibility.

    Current state: No console.warn related to pdf_fallback.
    """

    def test_console_warn_for_pdf_fallback(self, html_content):
        """The frontend must call console.warn() when pdf_fallback is detected.

        Acceptable patterns:
          - console.warn(...) with a message about pdf_fallback
          - console.warn('PDF fallback...')
          - console.warn('[PDF Fallback]...')

        The key requirement: browser dev tools must show a warning
        when the fallback triggered.
        """
        has_console_warn = bool(re.search(
            r"""console\.warn\s*\([^)]*(?:pdf.?fallback|PDF|fallback)""",
            html_content,
            re.IGNORECASE,
        ))
        assert has_console_warn, (
            "index_v2.html must call console.warn() when pdf_fallback is "
            "detected in the task result. "
            "\nExpected: `console.warn('[PDF Fallback]', ...)` or similar "
            "in the polling completion handler. "
            "\nCurrently: NO console.warn for pdf_fallback exists."
        )


# ============================================================
# Test 4 (LIVE): Backend task-progress API includes alertas
# ============================================================


class TestBackendPropagatesPdfFallbackFlag:
    """F7-T2 (LIVE): Verify the backend /api/task-progress response
    structure supports the pdf_fallback flag.

    This checks the data path: when a task completes, its result dict
    must include an 'alertas' key that the frontend can inspect.
    """

    def test_task_progress_api_is_accessible(self):
        """GET /api/task-progress/{unknown} must return 404 (not 500).

        This proves the endpoint exists and is correctly routed.
        """
        url = f"{LIVE_URL}/api/task-progress/nonexistent-task-f7t2"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 404, (
            f"Expected 404 from task-progress for unknown task, "
            f"got {resp.status_code}. Response: {resp.text[:300]}"
        )

    def test_completed_task_result_structure_includes_alertas(self):
        """A completed task's result dict must include 'alertas'.

        Query /api/tasks to find a completed task, then check its
        result dict includes alertas (the field that carries pdf_fallback).
        """
        url = f"{LIVE_URL}/api/tasks"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            pytest.skip("GET /api/tasks not available — cannot verify result structure")

        tasks = resp.json()
        if not isinstance(tasks, list):
            # May be a dict with a 'tasks' key
            tasks = tasks.get("tasks", [])

        completed_tasks = [
            t for t in tasks
            if isinstance(t, dict) and t.get("status") == "completed" and t.get("result")
        ]
        if not completed_tasks:
            pytest.skip("No completed tasks with result found — cannot verify alertas field")

        # Check at least one completed task has an 'alertas' field in its result
        task = completed_tasks[0]
        result = task["result"]
        assert "alertas" in result, (
            f"Completed task result must include 'alertas' key for the frontend "
            f"to detect pdf_fallback. Task {task.get('task_id')}: "
            f"result keys = {list(result.keys())}"
        )
