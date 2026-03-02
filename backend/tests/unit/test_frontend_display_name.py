"""
Frontend structure tests for F4-T1 and F4-T4: verify that index_v2.html
contains the required HTML elements and JS functions for display_name support.

F4-T1: Upload modal must have a "Nome do Documento" text input field
F4-T4: renderDocumentoItem() must use display_name instead of nome_arquivo

These are structural RED/GREEN tests. Runtime UI verification is done via
journey agent in Phase 5 (UX Validation).

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F4-T1, F4-T4)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import re
import pytest
from pathlib import Path


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def html_content():
    """Read the current index_v2.html content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


# ============================================================
# F4-T1: Upload modal "Nome do Documento" input
# ============================================================

class TestUploadModalDisplayNameInput:
    """
    F4-T1: The upload modal must contain a text input field for the
    document display name, labeled "Nome do Documento".
    """

    def test_upload_modal_has_display_name_input(self, html_content):
        """
        The upload modal must contain an input element with
        id="input-upload-display-name".
        """
        assert 'id="input-upload-display-name"' in html_content, (
            "Upload modal must contain <input id='input-upload-display-name'>. "
            "This field allows users to set a custom display name for the document."
        )

    def test_upload_modal_has_nome_do_documento_label(self, html_content):
        """
        The upload modal must have a label containing "Nome do Documento"
        to identify the display_name input field.
        """
        assert "Nome do Documento" in html_content, (
            "Upload modal must contain a label with text 'Nome do Documento'. "
            "This labels the display_name input field for the user."
        )

    def test_display_name_input_is_text_type(self, html_content):
        """
        The display_name input must be a text input (not hidden, not select).
        Users need to see and edit it.
        """
        # Find the input and verify it's type="text"
        pattern = r'<input[^>]*id="input-upload-display-name"[^>]*>'
        match = re.search(pattern, html_content)
        assert match, (
            "Could not find <input id='input-upload-display-name'> in HTML."
        )
        input_tag = match.group(0)
        assert 'type="text"' in input_tag, (
            f"Display name input must be type='text', got: {input_tag}"
        )


# ============================================================
# F4-T4: renderDocumentoItem() shows display_name
# ============================================================

class TestRenderDocumentoItemDisplayName:
    """
    F4-T4: renderDocumentoItem() must use display_name as the primary
    document name, falling back to nome_arquivo then id.
    """

    def test_render_function_uses_display_name(self, html_content):
        """
        renderDocumentoItem() must reference doc.display_name in its
        output template for the document name.
        """
        # Find the renderDocumentoItem function body
        func_start = html_content.find("function renderDocumentoItem(")
        assert func_start != -1, "renderDocumentoItem function not found"

        # Get the function body (until the next function or closing brace at same level)
        func_body = html_content[func_start:func_start + 2000]

        assert "doc.display_name" in func_body or "display_name" in func_body, (
            "renderDocumentoItem() must reference 'doc.display_name' to show "
            "the human-readable document name. Currently it only uses nome_arquivo."
        )

    def test_render_function_has_display_name_fallback(self, html_content):
        """
        The document name rendering must have a fallback chain:
        display_name → nome_arquivo → id
        """
        func_start = html_content.find("function renderDocumentoItem(")
        assert func_start != -1
        func_body = html_content[func_start:func_start + 2000]

        # The doc-name div should use display_name with fallback
        doc_name_pattern = r'doc\.display_name\s*\|\|\s*doc\.nome_arquivo\s*\|\|\s*doc\.id'
        assert re.search(doc_name_pattern, func_body), (
            "renderDocumentoItem() must use a fallback chain: "
            "doc.display_name || doc.nome_arquivo || doc.id "
            "for the document name display."
        )
