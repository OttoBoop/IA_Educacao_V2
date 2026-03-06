"""
D-T1: Structural tests for the Desempenho Silent Failure Fix — polling integration.

Verifies that executarDesempenho() polls /task-progress/ for completion instead of
showing an instant success toast. These are pure file-content checks (no browser).

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_desempenho_polling.py -v
"""

import re
from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture
def executar_desempenho_body(html_content):
    """Extract the body of executarDesempenho() for targeted assertions."""
    # Find the function start and extract until the next top-level function
    match = re.search(
        r'(async\s+)?function\s+executarDesempenho\s*\([^)]*\)\s*\{',
        html_content,
    )
    assert match, "executarDesempenho function not found in index_v2.html"
    start = match.start()

    # Simple brace-counting to find function end
    depth = 0
    func_start = html_content.index('{', start)
    for i in range(func_start, len(html_content)):
        if html_content[i] == '{':
            depth += 1
        elif html_content[i] == '}':
            depth -= 1
            if depth == 0:
                return html_content[func_start:i + 1]

    pytest.fail("Could not extract executarDesempenho function body")


# ============================================================
# D-T1-1: executarDesempenho must poll /task-progress/
# ============================================================

class TestDT1PollingIntegration:
    """D-T1: executarDesempenho() must use polling instead of instant success."""

    def test_dt1_references_task_progress_endpoint(self, executar_desempenho_body):
        """executarDesempenho must reference /task-progress/ for polling completion."""
        assert "task-progress" in executar_desempenho_body, (
            "executarDesempenho() must poll /api/task-progress/{taskId} to check "
            "background task completion. Currently shows instant success toast."
        )

    def test_dt1_uses_add_backend_task_or_start_polling(self, executar_desempenho_body):
        """executarDesempenho must register task in sidebar via addBackendTask or startPolling."""
        has_add_backend = "addBackendTask" in executar_desempenho_body
        has_start_polling = "startPolling" in executar_desempenho_body
        assert has_add_backend or has_start_polling, (
            "executarDesempenho() must call taskQueue.addBackendTask() or startPolling() "
            "to register the background task in the sidebar and start polling."
        )

    def test_dt1_no_immediate_success_toast_in_try_block(self, executar_desempenho_body):
        """executarDesempenho must NOT show success toast in the same try block as apiForm.

        The old code calls showToast('sucesso') right after apiForm returns the task_id,
        within the same try block. The fix should only show success after polling
        confirms status='completed' — which happens in a separate callback/handler.
        """
        # Find the try block containing apiForm
        api_form_pos = executar_desempenho_body.find("apiForm(")
        assert api_form_pos != -1, "apiForm call not found in executarDesempenho"

        # Extract from apiForm to the catch block (the synchronous try body)
        catch_pos = executar_desempenho_body.find("} catch", api_form_pos)
        if catch_pos == -1:
            catch_pos = len(executar_desempenho_body)
        try_after_api = executar_desempenho_body[api_form_pos:catch_pos]

        # Should NOT have a success toast in this synchronous block
        has_immediate_success = bool(
            re.search(r"showToast\([^)]*sucesso[^)]*\)", try_after_api)
        )
        assert not has_immediate_success, (
            "executarDesempenho() shows a success toast in the same try block as apiForm(). "
            "Success should only appear after polling confirms status='completed'."
        )

    def test_dt1_extracts_task_id_from_api_response(self, executar_desempenho_body):
        """executarDesempenho must extract task_id from the apiForm response."""
        assert "task_id" in executar_desempenho_body, (
            "executarDesempenho() must extract task_id from the apiForm response "
            "to use for polling. The backend returns {task_id, status: 'started'}."
        )
