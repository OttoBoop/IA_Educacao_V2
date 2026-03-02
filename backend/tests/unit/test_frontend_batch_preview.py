"""
Frontend structure tests for F5-T1 + F5-T2 + F5-T3: verify that index_v2.html
contains the required HTML elements and JS functions for the batch upload preview.

F5-T1: Batch upload modal must show a preview table after file selection,
       with columns for filename, matched student, and editable display_name.
F5-T2: JS: on file selection, generate preview rows with auto-names using
       buildDisplayName(). Each row has editable display_name input.
F5-T3: uploadProvasEmLote() must read the edited display_names from the
       preview table and send them as a JSON array in FormData.

These are structural RED/GREEN tests. Runtime UI verification is done via
journey agent in Phase 5 (UX Validation).

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F5-T1, F5-T2, F5-T3)
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
# F5-T1: Batch upload preview table HTML
# ============================================================

class TestBatchUploadPreviewTable:
    """
    F5-T1: The batch upload modal (modal-upload-provas) must contain
    a preview table where users see each file's matched student and
    auto-generated display_name before confirming the upload.
    """

    def test_batch_modal_has_preview_container(self, html_content):
        """
        The batch upload modal must contain a container element with
        id="batch-preview-container" to hold the preview table.
        """
        assert 'id="batch-preview-container"' in html_content, (
            "Batch upload modal must contain <div id='batch-preview-container'>. "
            "This container holds the file preview table that appears after "
            "file selection."
        )

    def test_preview_container_is_inside_batch_modal(self, html_content):
        """
        The batch-preview-container must be inside the modal-upload-provas
        modal, not somewhere else in the page.
        """
        modal_start = html_content.find('id="modal-upload-provas"')
        assert modal_start != -1, "modal-upload-provas not found"

        # Find the modal's closing </div> (approximate — look for next modal)
        modal_end = html_content.find('<!-- Modal:', modal_start + 1)
        if modal_end == -1:
            modal_end = modal_start + 5000  # fallback

        modal_body = html_content[modal_start:modal_end]
        assert 'id="batch-preview-container"' in modal_body, (
            "batch-preview-container must be INSIDE the modal-upload-provas modal, "
            "not elsewhere in the page."
        )

    def test_preview_table_has_header_row(self, html_content):
        """
        The preview table must have a header with columns for:
        Arquivo (filename), Aluno (matched student), Nome do Documento (display name).
        """
        # Find the batch preview container area
        container_start = html_content.find('id="batch-preview-container"')
        assert container_start != -1, "batch-preview-container not found"
        container_area = html_content[container_start:container_start + 2000]

        # The table header should contain column labels
        assert "Arquivo" in container_area or "arquivo" in container_area, (
            "Preview table must have a column header for 'Arquivo' (filename)."
        )

    def test_preview_table_has_display_name_column(self, html_content):
        """
        The preview table must have a 'Nome do Documento' column header
        so users know they can edit the auto-generated names.
        """
        container_start = html_content.find('id="batch-preview-container"')
        assert container_start != -1, "batch-preview-container not found"
        container_area = html_content[container_start:container_start + 2000]

        assert "Nome do Documento" in container_area, (
            "Preview table must have a 'Nome do Documento' column header "
            "for the editable display_name field per file."
        )


# ============================================================
# F5-T2: JS batch preview row generation
# ============================================================

class TestBatchPreviewRowGeneration:
    """
    F5-T2: On file selection in the batch upload modal, JS must populate
    the preview table with rows showing filename, matched student, and
    editable auto-generated display_name via buildDisplayName().
    """

    def test_batch_files_change_handler_exists(self, html_content):
        """
        There must be a JS function that handles file selection for batch
        preview. It should be wired to the input-upload-provas-files change
        event (either via addEventListener, onchange attribute, or .onchange).
        """
        # Option 1: addEventListener on the file input
        has_add_listener = re.search(
            r'input-upload-provas-files[^;]*\.addEventListener\s*\(\s*[\'"]change[\'"]',
            html_content
        )
        # Option 2: onchange attribute on input element
        has_onchange_attr = re.search(
            r'id="input-upload-provas-files"[^>]*onchange=',
            html_content
        )
        # Option 3: .onchange assignment in JS
        has_onchange_assign = re.search(
            r'input-upload-provas-files[^;]*\.onchange\s*=',
            html_content
        )

        assert has_add_listener or has_onchange_attr or has_onchange_assign, (
            "The batch file input (input-upload-provas-files) must have a change "
            "event handler wired. This triggers the preview table population. "
            "Wire via addEventListener('change', ...), onchange attribute, or "
            ".onchange assignment."
        )

    def test_batch_preview_function_exists(self, html_content):
        """
        There must be a function that populates the batch preview table.
        It should reference 'batch-preview-body' to insert rows.
        """
        # Look for a function that references batch-preview-body
        # Could be named populateBatchPreview, onBatchFilesChange, etc.
        has_func = re.search(
            r'function\s+\w*[Bb]atch\w*\s*\(',
            html_content
        )
        # Alternative: any function body that references batch-preview-body
        has_body_ref = 'batch-preview-body' in html_content and re.search(
            r'getElementById\s*\(\s*[\'"]batch-preview-body[\'"]',
            html_content
        )

        assert has_func or has_body_ref, (
            "There must be a JS function that populates the batch preview table. "
            "It should reference 'batch-preview-body' via getElementById to insert "
            "preview rows after file selection."
        )

    def test_batch_preview_calls_build_display_name(self, html_content):
        """
        The batch preview function must call buildDisplayName() to auto-generate
        display names for each file in the batch.
        """
        # Find all code that references both batch-preview and buildDisplayName
        # The function that populates the preview must call buildDisplayName
        batch_funcs = re.finditer(
            r'function\s+(\w*[Bb]atch\w*)\s*\([^)]*\)\s*\{',
            html_content
        )
        found_build_call = False
        for match in batch_funcs:
            func_start = match.start()
            func_body = html_content[func_start:func_start + 3000]
            if 'buildDisplayName' in func_body:
                found_build_call = True
                break

        assert found_build_call, (
            "The batch preview function must call buildDisplayName() to generate "
            "auto-suggested display names for each file. Each preview row needs "
            "a name like 'Prova Respondida - Maria Silva - Cálculo I - Turma A'."
        )

    def test_batch_preview_shows_container(self, html_content):
        """
        The batch preview function must make the preview container visible
        by setting display style via JS (not the static HTML attribute).
        """
        # Look for JS code that dynamically shows batch-preview-container
        # Must be getElementById(...).style.display = ... (JS), not HTML attribute
        has_display_set = re.search(
            r'getElementById\s*\(\s*[\'"]batch-preview-container[\'"]\s*\)'
            r'[^;]*\.style\.display\s*=',
            html_content
        )
        has_remove_hidden = re.search(
            r'getElementById\s*\(\s*[\'"]batch-preview-container[\'"]\s*\)'
            r'[^;]*\.classList\.remove\s*\([\'"]hidden',
            html_content
        )

        assert has_display_set or has_remove_hidden, (
            "The batch preview function must dynamically show 'batch-preview-container' "
            "via getElementById('batch-preview-container').style.display = 'block' "
            "or classList.remove('hidden') after populating preview rows."
        )

    def test_batch_preview_rows_have_editable_name_input(self, html_content):
        """
        Each preview row must contain an editable input for the display_name
        so users can customize names before upload.
        """
        # Find the batch preview function and check for input elements in rows
        batch_funcs = re.finditer(
            r'function\s+(\w*[Bb]atch\w*)\s*\([^)]*\)\s*\{',
            html_content
        )
        found_input = False
        for match in batch_funcs:
            func_start = match.start()
            func_body = html_content[func_start:func_start + 3000]
            # Look for <input in the row template with type="text" or class for editing
            if re.search(r'<input[^>]*type=[\'"]text[\'"]', func_body):
                found_input = True
                break
            if re.search(r'<input[^>]*class=[\'"][^"]*batch-name', func_body):
                found_input = True
                break

        assert found_input, (
            "Each batch preview row must contain an editable <input type='text'> "
            "for the display_name. Users must be able to customize the auto-generated "
            "name before confirming the upload."
        )


# ============================================================
# F5-T3: uploadProvasEmLote() sends per-file display_names
# ============================================================

class TestUploadProvasEmLoteSendsDisplayNames:
    """
    F5-T3: uploadProvasEmLote() must collect the edited display_names
    from the batch preview table's editable inputs and send them as
    a JSON-serialized array in the FormData to the backend.
    """

    def test_upload_reads_batch_name_inputs(self, html_content):
        """
        uploadProvasEmLote() must read the values from the batch preview
        table's editable name inputs (class='batch-name-input').
        """
        func_start = html_content.find("async function uploadProvasEmLote(")
        assert func_start != -1, "uploadProvasEmLote function not found"
        func_body = html_content[func_start:func_start + 3000]

        assert "batch-name-input" in func_body, (
            "uploadProvasEmLote() must reference 'batch-name-input' to read "
            "the edited display names from the preview table inputs."
        )

    def test_upload_sends_display_names_in_formdata(self, html_content):
        """
        uploadProvasEmLote() must append 'display_names' to the FormData
        sent to the backend.
        """
        func_start = html_content.find("async function uploadProvasEmLote(")
        assert func_start != -1, "uploadProvasEmLote function not found"
        func_body = html_content[func_start:func_start + 3000]

        assert re.search(
            r"formData\.append\(\s*['\"]display_names['\"]",
            func_body
        ), (
            "uploadProvasEmLote() must call formData.append('display_names', ...) "
            "to send the per-file display names to the backend."
        )

    def test_upload_serializes_display_names_as_json(self, html_content):
        """
        uploadProvasEmLote() must JSON.stringify the display_names array
        before appending to FormData (the backend expects a JSON string).
        """
        func_start = html_content.find("async function uploadProvasEmLote(")
        assert func_start != -1, "uploadProvasEmLote function not found"
        func_body = html_content[func_start:func_start + 3000]

        assert "JSON.stringify" in func_body, (
            "uploadProvasEmLote() must use JSON.stringify() to serialize the "
            "display_names array before appending to FormData. The backend "
            "expects a JSON string, not individual values."
        )

    def test_upload_clears_preview_after_success(self, html_content):
        """
        After successful batch upload, uploadProvasEmLote() must hide the
        preview container and clear the preview table body.
        """
        func_start = html_content.find("async function uploadProvasEmLote(")
        assert func_start != -1, "uploadProvasEmLote function not found"
        func_body = html_content[func_start:func_start + 3000]

        assert "batch-preview-container" in func_body, (
            "uploadProvasEmLote() must reference 'batch-preview-container' "
            "to hide the preview after successful upload."
        )
