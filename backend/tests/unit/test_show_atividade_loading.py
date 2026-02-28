"""
Tests for showAtividade() loading state in index_v2.html.

F1-T2: Verify that showAtividade() adds .card-loading class + disables
pointerEvents before the API call, and cleans up in the catch block.

RED phase — these tests MUST FAIL before implementation.
"""
import re
from pathlib import Path

import pytest

# Resolve the HTML file relative to this test file.
FRONTEND_DIR = Path(__file__).parent.parent.parent.parent / "frontend"
HTML_FILE = FRONTEND_DIR / "index_v2.html"


def _read_html() -> str:
    """Read index_v2.html and return its full contents."""
    assert HTML_FILE.exists(), f"index_v2.html not found at {HTML_FILE}"
    return HTML_FILE.read_text(encoding="utf-8")


def _extract_show_atividade_body(html: str) -> str:
    """
    Extract the body of the showAtividade() function.

    Uses brace-counting to find the matching closing brace for
    'async function showAtividade(...)'.
    """
    marker = "async function showAtividade("
    idx = html.find(marker)
    if idx == -1:
        return ""

    # Find opening brace
    brace_start = html.find("{", idx)
    if brace_start == -1:
        return ""

    # Count braces to find matching close
    depth = 0
    for i in range(brace_start, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                return html[brace_start + 1 : i]
    return ""


def _extract_catch_block(func_body: str) -> str:
    """
    Extract the catch block contents from a function body.

    Finds 'catch' followed by a brace-delimited block.
    """
    match = re.search(r"catch\s*\([^)]*\)\s*\{", func_body)
    if not match:
        return ""

    brace_start = func_body.find("{", match.start())
    depth = 0
    for i in range(brace_start, len(func_body)):
        if func_body[i] == "{":
            depth += 1
        elif func_body[i] == "}":
            depth -= 1
            if depth == 0:
                return func_body[brace_start + 1 : i]
    return ""


class TestShowAtividadeLoadingStateAdded:
    """showAtividade() must add .card-loading class and disable pointerEvents."""

    def test_show_atividade_function_exists_in_html(self):
        """Gate test: showAtividade function must exist in the HTML."""
        html = _read_html()
        assert "function showAtividade(" in html, (
            "showAtividade() function not found in index_v2.html"
        )

    def test_show_atividade_adds_card_loading_class(self):
        """
        showAtividade() must add the 'card-loading' CSS class to the
        clicked card before making the API call.
        """
        html = _read_html()
        body = _extract_show_atividade_body(html)
        assert body, "Could not extract showAtividade() function body"

        assert "card-loading" in body, (
            "showAtividade() must add the 'card-loading' CSS class to provide "
            "visual loading feedback. No 'card-loading' reference found in "
            "the function body."
        )

    def test_show_atividade_disables_pointer_events(self):
        """
        showAtividade() must set pointerEvents to prevent double-clicks
        during loading.
        """
        html = _read_html()
        body = _extract_show_atividade_body(html)
        assert body, "Could not extract showAtividade() function body"

        assert "pointerEvents" in body, (
            "showAtividade() must disable pointerEvents on the card to prevent "
            "double-click during loading."
        )


class TestShowAtividadeCatchBlockCleanup:
    """showAtividade() catch block must clean up loading state on error."""

    def test_catch_block_removes_card_loading_class(self):
        """
        The catch block in showAtividade() must remove the 'card-loading'
        CSS class on error so the card returns to its normal state.
        """
        html = _read_html()
        body = _extract_show_atividade_body(html)
        catch_body = _extract_catch_block(body)
        assert catch_body, "Could not extract catch block from showAtividade()"

        assert "card-loading" in catch_body, (
            "The catch block in showAtividade() must remove the 'card-loading' "
            "CSS class on error. No 'card-loading' reference found in the catch block."
        )

    def test_catch_block_re_enables_pointer_events(self):
        """
        The catch block must re-enable pointerEvents so the user can
        click the card again after an error.
        """
        html = _read_html()
        body = _extract_show_atividade_body(html)
        catch_body = _extract_catch_block(body)
        assert catch_body, "Could not extract catch block from showAtividade()"

        assert "pointerEvents" in catch_body, (
            "The catch block in showAtividade() must re-enable pointerEvents "
            "on error. No 'pointerEvents' reference found in the catch block."
        )
