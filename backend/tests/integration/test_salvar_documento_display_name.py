"""
Integration tests for display_name in salvar_documento().

F3-T1: salvar_documento() accepts display_name, auto-generates when missing,
       uses build_storage_filename() for disk filenames, persists to DB.
"""

import sqlite3
import re
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

from models import TipoDocumento


@patch("storage.SUPABASE_DB_AVAILABLE", False)
@patch("storage.SUPABASE_STORAGE_AVAILABLE", False)
class TestSalvarDocumentoDisplayName:
    """Tests for display_name parameter in salvar_documento()."""

    def _setup_storage(self, temp_data_dir):
        """Create a StorageManager with a pre-populated hierarchy.

        Creates: materia -> turma -> atividade, plus one aluno linked to turma.
        This is required because salvar_documento() validates atividade_id exists,
        and we need materia_nome/turma_nome/aluno_nome for auto-generation tests.
        """
        from storage import StorageManager
        sm = StorageManager(base_path=str(temp_data_dir))

        materia = sm.criar_materia(nome="Calcculo I")
        turma = sm.criar_turma(materia_id=materia.id, nome="Turma A")
        atividade = sm.criar_atividade(turma_id=turma.id, nome="Prova 1")
        aluno = sm.criar_aluno(nome="Maria Silva")
        sm.vincular_aluno_turma(aluno_id=aluno.id, turma_id=turma.id)

        return sm, materia, turma, atividade, aluno

    def _create_test_file(self, temp_data_dir, ext=".pdf"):
        """Create a minimal test file to use as arquivo_origem."""
        test_file = temp_data_dir / f"test_upload{ext}"
        test_file.write_text("test content", encoding="utf-8")
        return str(test_file)

    # ------------------------------------------------------------------
    # Test 1: salvar_documento() must accept the display_name keyword arg
    # ------------------------------------------------------------------

    def test_accepts_display_name_parameter(self, temp_data_dir):
        """Calling salvar_documento() with display_name='Custom Name' must not raise TypeError.

        Currently FAILS with TypeError because the parameter does not exist.
        """
        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir)

        # This call must succeed without raising TypeError.
        # It currently raises: TypeError: salvar_documento() got an unexpected keyword argument 'display_name'
        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id,
            display_name="Custom Name",
        )

        assert doc is not None

    # ------------------------------------------------------------------
    # Test 2: explicit display_name is stored on the returned Documento
    # ------------------------------------------------------------------

    def test_explicit_display_name_saved_on_documento(self, temp_data_dir):
        """The returned Documento must have display_name equal to the value passed in.

        Currently FAILS: display_name is never set so it stays as the default ''.
        """
        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir)

        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id,
            display_name="Custom Name",
        )

        assert doc.display_name == "Custom Name"

    # ------------------------------------------------------------------
    # Test 3: explicit display_name drives the on-disk filename
    # ------------------------------------------------------------------

    def test_explicit_display_name_used_in_filename(self, temp_data_dir):
        """When display_name is given, nome_arquivo must match build_storage_filename(display_name, ext).

        Currently FAILS: nome_arquivo uses the old '{tipo}_{timestamp}{ext}' pattern,
        not the build_storage_filename() pattern.
        """
        from storage import build_storage_filename

        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir, ext=".pdf")

        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id,
            display_name="Custom Name",
        )

        expected_filename = build_storage_filename("Custom Name", ".pdf")
        assert doc.nome_arquivo == expected_filename, (
            f"Expected filename based on build_storage_filename, "
            f"got '{doc.nome_arquivo}' instead of '{expected_filename}'"
        )

    # ------------------------------------------------------------------
    # Test 4: when display_name is omitted, one is auto-generated
    # ------------------------------------------------------------------

    def test_auto_generates_display_name_when_not_provided(self, temp_data_dir):
        """When display_name is NOT passed, salvar_documento() must auto-generate it.

        Currently FAILS: display_name stays '' (never populated).
        """
        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir)

        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id,
            # display_name intentionally omitted
        )

        # Must be non-empty after auto-generation
        assert doc.display_name != "", (
            "display_name should be auto-generated when not provided, but got ''"
        )

    # ------------------------------------------------------------------
    # Test 5: auto-generated name includes all relevant metadata pieces
    # ------------------------------------------------------------------

    def test_auto_generated_name_includes_metadata(self, temp_data_dir):
        """Auto-generated display_name must include tipo label, aluno name, materia name, turma name.

        Expected format: 'Prova Respondida - Maria Silva - Calcculo I - Turma A'
        Currently FAILS: display_name is '' so no parts are present.
        """
        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir)

        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id,
        )

        display = doc.display_name
        assert "Prova Respondida" in display, (
            f"Expected 'Prova Respondida' in display_name, got '{display}'"
        )
        assert "Maria Silva" in display, (
            f"Expected aluno name 'Maria Silva' in display_name, got '{display}'"
        )
        assert "Calcculo I" in display, (
            f"Expected materia name 'Calcculo I' in display_name, got '{display}'"
        )
        assert "Turma A" in display, (
            f"Expected turma name 'Turma A' in display_name, got '{display}'"
        )

    # ------------------------------------------------------------------
    # Test 6: display_name is persisted to the SQLite documentos table
    # ------------------------------------------------------------------

    def test_display_name_persisted_to_sqlite(self, temp_data_dir):
        """The display_name value must be stored in the SQLite documentos row.

        Currently FAILS: the INSERT in salvar_documento() does not include
        display_name in the column list or values tuple.
        """
        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir)

        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id,
            display_name="Stored In DB",
        )

        # Query SQLite directly to confirm the value made it into the DB
        db_path = Path(temp_data_dir) / "database.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT display_name FROM documentos WHERE id = ?", (doc.id,)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None, "Document row not found in SQLite"
        assert row["display_name"] == "Stored In DB", (
            f"Expected display_name='Stored In DB' in DB, got '{row['display_name']}'"
        )

    # ------------------------------------------------------------------
    # Test 7: base-doc type auto-generates without aluno in the name
    # ------------------------------------------------------------------

    def test_base_doc_auto_generates_without_aluno(self, temp_data_dir):
        """For base doc types (e.g. ENUNCIADO), auto-generated name must omit aluno.

        Expected format: 'Enunciado - Calcculo I - Turma A'  (no aluno part)
        Currently FAILS: display_name is '' (never generated).
        """
        sm, materia, turma, atividade, aluno = self._setup_storage(temp_data_dir)
        arquivo = self._create_test_file(temp_data_dir)

        doc = sm.salvar_documento(
            arquivo_origem=arquivo,
            tipo=TipoDocumento.ENUNCIADO,
            atividade_id=atividade.id,
            # aluno_id intentionally omitted — ENUNCIADO is a base doc
        )

        display = doc.display_name

        # Must be non-empty and contain tipo label
        assert "Enunciado" in display, (
            f"Expected 'Enunciado' in display_name, got '{display}'"
        )

        # Must NOT contain aluno name — base docs have no aluno
        assert "Maria Silva" not in display, (
            f"display_name for base doc must not contain aluno name, got '{display}'"
        )

        # Must contain materia and turma for context
        assert "Calcculo I" in display, (
            f"Expected materia name in display_name, got '{display}'"
        )
        assert "Turma A" in display, (
            f"Expected turma name in display_name, got '{display}'"
        )
