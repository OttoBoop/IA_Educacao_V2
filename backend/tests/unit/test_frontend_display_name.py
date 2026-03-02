"""
Frontend structure tests for F4-T1, F4-T2, F4-T3, F4-T4: verify that
index_v2.html contains the required HTML elements and JS functions for
display_name support.

F4-T1: Upload modal must have a "Nome do Documento" text input field
F4-T2: Auto-suggest: on tipo/aluno change, call buildDisplayName() and populate field
F4-T3: uploadDocumento() must send display_name in FormData
F4-T4: renderDocumentoItem() must use display_name instead of nome_arquivo

These are structural RED/GREEN tests. Runtime UI verification is done via
journey agent in Phase 5 (UX Validation).

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F4-T1, F4-T2, F4-T3, F4-T4)
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
        func_body = html_content[func_start:func_start + 2500]

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
        func_body = html_content[func_start:func_start + 2500]

        # The doc-name div should use display_name with fallback
        doc_name_pattern = r'doc\.display_name\s*\|\|\s*doc\.nome_arquivo\s*\|\|\s*doc\.id'
        assert re.search(doc_name_pattern, func_body), (
            "renderDocumentoItem() must use a fallback chain: "
            "doc.display_name || doc.nome_arquivo || doc.id "
            "for the document name display."
        )


# ============================================================
# F4-T2: Auto-suggest wiring (tipo/aluno → buildDisplayName)
# ============================================================

class TestAutoSuggestDisplayName:
    """
    F4-T2: When the user changes tipo or aluno in the upload modal,
    the display_name input must auto-populate via buildDisplayName().
    """

    def test_tipo_change_triggers_display_name_update(self, html_content):
        """
        onUploadTipoChange() must call a function that updates the
        display name field using buildDisplayName().
        """
        func_start = html_content.find("function onUploadTipoChange(")
        assert func_start != -1, "onUploadTipoChange function not found"
        func_body = html_content[func_start:func_start + 1000]

        assert "updateUploadDisplayName" in func_body, (
            "onUploadTipoChange() must call updateUploadDisplayName() "
            "to auto-populate the display name field when tipo changes."
        )

    def test_aluno_change_triggers_display_name_update(self, html_content):
        """
        The aluno dropdown must trigger updateUploadDisplayName() when
        its selection changes. Either via onchange attribute referencing
        updateUploadDisplayName, or wired in carregarAlunosParaUpload().
        """
        # Option 1: onchange attribute on the select element
        has_onchange_attr = re.search(
            r'id="input-upload-aluno"[^>]*onchange="[^"]*updateUploadDisplayName',
            html_content
        )
        # Option 2: wired via JS in carregarAlunosParaUpload
        carregar_func_start = html_content.find("function carregarAlunosParaUpload(")
        carregar_body = ""
        if carregar_func_start != -1:
            carregar_body = html_content[carregar_func_start:carregar_func_start + 1000]
        has_wired_in_carregar = "updateUploadDisplayName" in carregar_body
        # Option 3: select.onchange = updateUploadDisplayName somewhere
        has_onchange_assign = re.search(
            r'input-upload-aluno[^;]*\.onchange\s*=\s*updateUploadDisplayName',
            html_content
        )

        assert has_onchange_attr or has_wired_in_carregar or has_onchange_assign, (
            "The aluno dropdown (input-upload-aluno) must call "
            "updateUploadDisplayName() when its selection changes. "
            "This can be via onchange attribute, .onchange assignment, or "
            "wired in carregarAlunosParaUpload()."
        )

    def test_update_function_calls_build_display_name(self, html_content):
        """
        There must be an updateUploadDisplayName() function that calls
        buildDisplayName() and sets the value on the display name input.
        """
        func_start = html_content.find("function updateUploadDisplayName(")
        assert func_start != -1, (
            "updateUploadDisplayName() function not found. "
            "This function must call buildDisplayName() with the current "
            "tipo, aluno name, materia name, and turma name, then set "
            "the result on input-upload-display-name."
        )
        func_body = html_content[func_start:func_start + 1500]

        assert "buildDisplayName" in func_body, (
            "updateUploadDisplayName() must call buildDisplayName() "
            "to generate the auto-suggested display name."
        )

    def test_update_function_sets_input_value(self, html_content):
        """
        updateUploadDisplayName() must set the value of
        input-upload-display-name with the generated name.
        """
        func_start = html_content.find("function updateUploadDisplayName(")
        assert func_start != -1, "updateUploadDisplayName() function not found"
        func_body = html_content[func_start:func_start + 1500]

        assert "input-upload-display-name" in func_body, (
            "updateUploadDisplayName() must reference 'input-upload-display-name' "
            "to set the auto-generated display name on the input field."
        )


# ============================================================
# F4-T3: uploadDocumento() sends display_name in FormData
# ============================================================

class TestUploadDocumentoSendsDisplayName:
    """
    F4-T3: uploadDocumento() must read the display_name input and
    send it as 'display_name' in the FormData to the server.
    """

    def test_upload_reads_display_name_input(self, html_content):
        """
        uploadDocumento() must read the value from
        input-upload-display-name.
        """
        func_start = html_content.find("async function uploadDocumento(")
        assert func_start != -1, "uploadDocumento function not found"
        func_body = html_content[func_start:func_start + 2000]

        assert "input-upload-display-name" in func_body, (
            "uploadDocumento() must read the display name from "
            "'input-upload-display-name' input field."
        )

    def test_upload_appends_display_name_to_formdata(self, html_content):
        """
        uploadDocumento() must append 'display_name' to the FormData
        object that gets sent to the server.
        """
        func_start = html_content.find("async function uploadDocumento(")
        assert func_start != -1, "uploadDocumento function not found"
        func_body = html_content[func_start:func_start + 2000]

        assert re.search(r"formData\.append\(\s*['\"]display_name['\"]", func_body), (
            "uploadDocumento() must call formData.append('display_name', ...) "
            "to send the display name to the server."
        )

    def test_upload_clears_display_name_after_success(self, html_content):
        """
        After successful upload, uploadDocumento() must clear the
        display_name input field (reset for next upload).
        """
        func_start = html_content.find("async function uploadDocumento(")
        assert func_start != -1, "uploadDocumento function not found"
        func_body = html_content[func_start:func_start + 2000]

        # Check that the display name input is cleared after upload
        # Look for setting value to '' or resetting the field
        has_clear = (
            "input-upload-display-name" in func_body
            and (
                re.search(r"input-upload-display-name.*value\s*=\s*['\"]", func_body)
                or re.search(r"getElementById.*input-upload-display-name.*value\s*=", func_body)
            )
        )
        assert has_clear, (
            "uploadDocumento() must clear the display_name input after "
            "successful upload so it's empty for the next upload."
        )
