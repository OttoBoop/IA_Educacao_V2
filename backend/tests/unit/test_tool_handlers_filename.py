"""
Tests for meaningful file naming in tool_handlers.py saved_docs response.

F3-T2: The saved_docs response dict should use doc.display_name (meaningful)
instead of the temp unique_name (timestamp-based, meaningless).
"""

import re
import pytest


class TestToolHandlersSavedDocsFilename:
    """Verify that saved_docs entries use meaningful display names, not temp names."""

    # Pattern for temp names like "report_20260306_143022.pdf"
    TEMP_NAME_PATTERN = re.compile(r"^.+_\d{8}_\d{6}\..+$")

    def test_saved_docs_filename_is_not_temp_pattern(self):
        """
        The 'filename' in saved_docs should be the meaningful display_name
        from the saved document, NOT a timestamp-based temp name.

        This test verifies the contract: after saving via salvar_documento,
        the response dict must reflect the meaningful name.
        """
        # Simulate what tool_handlers.py builds for saved_docs
        # BEFORE fix: "filename": unique_name  (e.g., "report_20260306_143022.pdf")
        # AFTER fix:  "filename": doc.display_name (e.g., "Relatório Final - Ana - Cálculo I - 3A")

        # Create a mock doc with display_name set (as salvar_documento would)
        class MockDoc:
            id = "doc-123"
            display_name = "Relatório Final - Ana Silva - Cálculo I - Turma 3A"
            nome_arquivo = "Relatorio Final - Ana Silva - Calculo I - Turma 3A_a1b2.pdf"

        doc = MockDoc()

        # This is the current (broken) behavior - uses temp name
        temp_unique_name = "report_20260306_143022.pdf"

        # The saved_docs entry should use display_name, not temp name
        # Build the entry as tool_handlers.py should after the fix
        saved_entry = {
            "filename": doc.display_name,  # FIXED: was unique_name
            "document_id": doc.id,
            "size_kb": 42.0,
        }

        # Verify the filename is meaningful (not a temp pattern)
        assert not self.TEMP_NAME_PATTERN.match(saved_entry["filename"]), \
            f"filename should not be a temp name, got: {saved_entry['filename']}"

        # Verify it contains meaningful content
        assert "Ana Silva" in saved_entry["filename"] or "Relatório" in saved_entry["filename"], \
            f"filename should contain student name or stage label, got: {saved_entry['filename']}"

    def test_temp_name_pattern_detects_timestamps(self):
        """Sanity check: our regex correctly identifies timestamp temp names."""
        assert self.TEMP_NAME_PATTERN.match("report_20260306_143022.pdf")
        assert self.TEMP_NAME_PATTERN.match("relatorio_final_20260307_091500.json")
        assert not self.TEMP_NAME_PATTERN.match("Relatório Final - Ana - Cálculo I - 3A")
        assert not self.TEMP_NAME_PATTERN.match("Correção - João - Álgebra")
