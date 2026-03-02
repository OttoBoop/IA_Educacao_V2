"""
Test H-T1: Fix visualizarDocumento() rendering

Tests:
- visualizarDocumento uses innerHTML (not only textContent) for markdown
- A markdown rendering function/library is called within the function
- XSS sanitization applied when using innerHTML
- JSON content still handled via textContent in <pre>

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_h_t1_document_viewer_fix.py -v
"""

from pathlib import Path
import re

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture
def viewer_func_body(html_content):
    """Extract the body of visualizarDocumento() function."""
    func_match = re.search(
        r'(?:async\s+)?function visualizarDocumento\(.*?\{(.*?)(?=\n\s{0,8}(?:async\s+)?function\s)',
        html_content,
        re.DOTALL
    )
    assert func_match, "visualizarDocumento() function must exist in HTML"
    return func_match.group(1)


# ============================================================
# TEST: MARKDOWN → innerHTML RENDERING
# ============================================================

class TestMarkdownRendering:
    """Markdown content is rendered via innerHTML, not textContent"""

    def test_uses_innerhtml_for_non_json_content(self, viewer_func_body):
        """Function must use innerHTML for rendering non-JSON content (markdown/text).
        The current bug: output.textContent = content for ALL content types."""
        assert "innerHTML" in viewer_func_body, (
            "visualizarDocumento() must use innerHTML for rendering markdown content. "
            "Currently uses only textContent which shows raw text."
        )

    def test_calls_markdown_renderer(self, viewer_func_body):
        """Function must call a markdown rendering function (marked, renderMarkdown, etc.)"""
        has_md_renderer = (
            "marked(" in viewer_func_body or
            "marked.parse(" in viewer_func_body or
            "renderMarkdown(" in viewer_func_body or
            "markdownToHtml(" in viewer_func_body or
            "showdown" in viewer_func_body.lower()
        )
        assert has_md_renderer, (
            "visualizarDocumento() must call a markdown rendering function "
            "(marked(), marked.parse(), renderMarkdown(), etc.) to convert markdown to HTML."
        )

    def test_marked_js_library_included(self, html_content):
        """marked.js CDN or local script must be loaded in the HTML"""
        has_marked = (
            "marked.min.js" in html_content or
            "marked@" in html_content or
            "cdn.jsdelivr.net/npm/marked" in html_content or
            "cdnjs.cloudflare.com/ajax/libs/marked" in html_content or
            # local definition of marked
            "function marked(" in html_content or
            "var marked" in html_content or
            "const marked" in html_content or
            "window.marked" in html_content
        )
        assert has_marked, (
            "marked.js library must be loaded (CDN or local) for markdown rendering. "
            "No marked.js reference found in HTML."
        )


# ============================================================
# TEST: XSS SANITIZATION
# ============================================================

class TestXssSanitization:
    """innerHTML usage must have XSS sanitization"""

    def test_sanitizes_before_innerhtml(self, viewer_func_body):
        """When setting innerHTML, content must be sanitized to prevent XSS"""
        # Only enforce if innerHTML is present (which it should be per test above)
        if "innerHTML" in viewer_func_body:
            has_sanitization = (
                "sanitize" in viewer_func_body.lower() or
                "DOMPurify" in viewer_func_body or
                "sanitizeHtml" in viewer_func_body or
                # Custom script stripping
                "replace(/<script" in viewer_func_body or
                "replace(/</script" in viewer_func_body or
                "<script" in viewer_func_body.lower() and "replace" in viewer_func_body
            )
            assert has_sanitization, (
                "innerHTML in visualizarDocumento() must have XSS sanitization "
                "(DOMPurify.sanitize(), sanitizeHtml(), or script tag stripping)."
            )


# ============================================================
# TEST: JSON STILL FORMATTED
# ============================================================

class TestJsonStillWorks:
    """JSON content continues to work with proper formatting"""

    def test_json_branch_uses_textcontent_or_pre(self, viewer_func_body):
        """JSON content path must use textContent (safe) not innerHTML"""
        # The function should distinguish between json and non-json
        has_json_branch = (
            "json" in viewer_func_body.lower() and
            "textContent" in viewer_func_body
        )
        assert has_json_branch, (
            "visualizarDocumento() must keep JSON rendering via textContent "
            "(safe, no innerHTML needed for formatted JSON)."
        )
