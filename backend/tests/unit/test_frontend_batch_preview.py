"""
Frontend structure tests for F5-T1: verify that index_v2.html contains
the required HTML elements for the batch upload preview table.

F5-T1: Batch upload modal must show a preview table after file selection,
       with columns for filename, matched student, and editable display_name.

These are structural RED/GREEN tests. Runtime UI verification is done via
journey agent in Phase 5 (UX Validation).

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F5-T1)
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
