"""
Unit tests for F7-T1: backfill migration script that generates display_names
for all existing documents that have empty/missing display_names.

The script reads all documents from the database, resolves the metadata chain
(atividade → turma → matéria, aluno), and generates structured display_names
using build_display_name().

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F7-T1)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from models import TipoDocumento


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def backfill_env(monkeypatch, temp_data_dir):
    """Set up isolated SQLite-backed StorageManager with hierarchy and docs
    that have EMPTY display_names — simulating pre-migration state.
    """
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from storage import StorageManager
    sm = StorageManager(base_path=str(temp_data_dir))

    materia = sm.criar_materia(nome="Cálculo I")
    turma = sm.criar_turma(materia_id=materia.id, nome="Turma A")
    atividade = sm.criar_atividade(turma_id=turma.id, nome="Prova 1")
    aluno = sm.criar_aluno(nome="Maria Silva", matricula="2024001")
    sm.vincular_aluno_turma(aluno_id=aluno.id, turma_id=turma.id)

    # Create a document with a temp-style filename and EMPTY display_name
    source_file = temp_data_dir / "tmpdgvpjvxp.pdf"
    source_file.write_bytes(b"%PDF-1.4 test content")

    doc = sm.salvar_documento(
        arquivo_origem=str(source_file),
        tipo=TipoDocumento.PROVA_RESPONDIDA,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        criado_por="usuario",
    )

    # Force display_name to empty to simulate pre-migration state
    conn = sm._get_connection()
    conn.execute(
        "UPDATE documentos SET display_name = '' WHERE id = ?",
        (doc.id,)
    )
    conn.commit()
    conn.close()

    return {
        "storage": sm,
        "materia": materia,
        "turma": turma,
        "atividade": atividade,
        "aluno": aluno,
        "doc": doc,
        "temp_data_dir": temp_data_dir,
    }


@pytest.fixture
def orphan_env(monkeypatch, temp_data_dir):
    """Set up environment with a document whose aluno_id is None
    (e.g., a turma-level report) — simulates missing aluno metadata.
    """
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from storage import StorageManager
    sm = StorageManager(base_path=str(temp_data_dir))

    materia = sm.criar_materia(nome="Física")
    turma = sm.criar_turma(materia_id=materia.id, nome="Turma B")
    atividade = sm.criar_atividade(turma_id=turma.id, nome="Prova 2")

    # Document without aluno (turma-level report — in documentos_sem_aluno())
    source_file = temp_data_dir / "report.json"
    source_file.write_text('{"resumo": "ok"}', encoding="utf-8")

    doc = sm.salvar_documento(
        arquivo_origem=str(source_file),
        tipo=TipoDocumento.RELATORIO_DESEMPENHO_TURMA,
        atividade_id=atividade.id,
        aluno_id=None,
        criado_por="sistema",
    )

    # Force empty display_name
    conn = sm._get_connection()
    conn.execute(
        "UPDATE documentos SET display_name = '' WHERE id = ?",
        (doc.id,)
    )
    conn.commit()
    conn.close()

    return {
        "storage": sm,
        "materia": materia,
        "turma": turma,
        "atividade": atividade,
        "doc": doc,
    }


# ============================================================
# F7-T1 Tests: backfill_display_names script
# ============================================================

class TestBackfillDisplayNames:
    """
    The backfill script must:
    1. Find all docs with empty display_name
    2. Resolve metadata chain (atividade → turma → matéria, aluno)
    3. Generate display_name using build_display_name()
    4. Update DB records
    5. Report summary
    """

    def test_backfill_generates_display_name_complete_metadata(self, backfill_env):
        """
        A document with complete metadata (aluno + matéria + turma) must
        get a display_name like "Prova Respondida - Maria Silva - Cálculo I - Turma A".
        """
        from scripts.backfill_display_names import backfill_display_names

        result = backfill_display_names(backfill_env["storage"])

        # Verify the document was updated
        docs = backfill_env["storage"].listar_documentos(
            backfill_env["atividade"].id, backfill_env["aluno"].id
        )
        doc = next((d for d in docs if d.id == backfill_env["doc"].id), None)
        assert doc is not None

        assert doc.display_name, (
            f"display_name must not be empty after backfill, got '{doc.display_name}'"
        )
        assert "Prova Respondida" in doc.display_name, (
            f"display_name '{doc.display_name}' must contain 'Prova Respondida'"
        )
        assert "Maria Silva" in doc.display_name, (
            f"display_name '{doc.display_name}' must contain 'Maria Silva'"
        )

    def test_backfill_display_name_includes_materia_turma(self, backfill_env):
        """
        The generated display_name must include matéria and turma names.
        """
        from scripts.backfill_display_names import backfill_display_names

        backfill_display_names(backfill_env["storage"])

        docs = backfill_env["storage"].listar_documentos(
            backfill_env["atividade"].id, backfill_env["aluno"].id
        )
        doc = next((d for d in docs if d.id == backfill_env["doc"].id), None)
        assert doc is not None

        display = doc.display_name
        assert "Cálculo I" in display or "Calculo I" in display, (
            f"display_name '{display}' must contain matéria 'Cálculo I'"
        )
        assert "Turma A" in display, (
            f"display_name '{display}' must contain turma 'Turma A'"
        )

    def test_backfill_no_aluno_uses_no_placeholder(self, orphan_env):
        """
        A turma-level document (aluno_id=None) should get a display_name
        WITHOUT a student name — build_display_name() omits None parts.
        """
        from scripts.backfill_display_names import backfill_display_names

        backfill_display_names(orphan_env["storage"])

        docs = orphan_env["storage"].listar_documentos(
            orphan_env["atividade"].id, None
        )
        doc = next((d for d in docs if d.id == orphan_env["doc"].id), None)
        assert doc is not None

        assert doc.display_name, (
            "Turma-level doc must still get a non-empty display_name"
        )
        assert "Relatório de Desempenho (Turma)" in doc.display_name or "Relatorio de Desempenho" in doc.display_name, (
            f"display_name '{doc.display_name}' must contain the tipo label for RELATORIO_DESEMPENHO_TURMA"
        )

    def test_backfill_skips_docs_with_existing_display_name(self, backfill_env):
        """
        Documents that already have a display_name must NOT be overwritten.
        """
        from scripts.backfill_display_names import backfill_display_names

        # Set a custom display_name first
        conn = backfill_env["storage"]._get_connection()
        conn.execute(
            "UPDATE documentos SET display_name = ? WHERE id = ?",
            ("Custom Name", backfill_env["doc"].id)
        )
        conn.commit()
        conn.close()

        result = backfill_display_names(backfill_env["storage"])

        docs = backfill_env["storage"].listar_documentos(
            backfill_env["atividade"].id, backfill_env["aluno"].id
        )
        doc = next((d for d in docs if d.id == backfill_env["doc"].id), None)
        assert doc is not None

        assert doc.display_name == "Custom Name", (
            f"Expected 'Custom Name' (preserved), got '{doc.display_name}'. "
            "Backfill must not overwrite existing display_names."
        )

    def test_backfill_does_not_modify_physical_files(self, backfill_env):
        """
        The backfill must NOT rename or move physical files on disk.
        File paths (caminho_arquivo) must remain unchanged.
        """
        from scripts.backfill_display_names import backfill_display_names

        # Record file path before backfill
        docs_before = backfill_env["storage"].listar_documentos(
            backfill_env["atividade"].id, backfill_env["aluno"].id
        )
        doc_before = next(
            (d for d in docs_before if d.id == backfill_env["doc"].id), None
        )
        path_before = doc_before.caminho_arquivo

        backfill_display_names(backfill_env["storage"])

        # Verify file path unchanged
        docs_after = backfill_env["storage"].listar_documentos(
            backfill_env["atividade"].id, backfill_env["aluno"].id
        )
        doc_after = next(
            (d for d in docs_after if d.id == backfill_env["doc"].id), None
        )
        assert doc_after.caminho_arquivo == path_before, (
            f"File path must not change during backfill. "
            f"Before: '{path_before}', After: '{doc_after.caminho_arquivo}'"
        )

    def test_backfill_reports_summary(self, backfill_env):
        """
        The backfill function must return a summary dict with counts:
        - 'updated': number of docs that got new display_names
        - 'skipped': number of docs that already had display_names
        - 'total': total documents processed
        """
        from scripts.backfill_display_names import backfill_display_names

        result = backfill_display_names(backfill_env["storage"])

        assert isinstance(result, dict), (
            f"backfill_display_names must return a dict, got {type(result)}"
        )
        assert "updated" in result, "Result must include 'updated' count"
        assert "skipped" in result, "Result must include 'skipped' count"
        assert "total" in result, "Result must include 'total' count"

        assert result["updated"] >= 1, (
            f"Expected at least 1 updated doc, got {result['updated']}"
        )
        assert result["total"] >= 1, (
            f"Expected at least 1 total doc, got {result['total']}"
        )

    def test_backfill_placeholder_for_broken_atividade(self, monkeypatch, temp_data_dir):
        """
        If a document's atividade_id references a non-existent atividade,
        the backfill should use placeholders instead of crashing.
        """
        monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
        monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

        from storage import StorageManager
        sm = StorageManager(base_path=str(temp_data_dir))

        materia = sm.criar_materia(nome="Biologia")
        turma = sm.criar_turma(materia_id=materia.id, nome="Turma C")
        atividade = sm.criar_atividade(turma_id=turma.id, nome="Prova 3")

        source_file = temp_data_dir / "orphan.pdf"
        source_file.write_bytes(b"%PDF-1.4 orphan content")

        doc = sm.salvar_documento(
            arquivo_origem=str(source_file),
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=None,
            criado_por="usuario",
        )

        # Force empty display_name AND set atividade_id to a non-existent ID
        conn = sm._get_connection()
        conn.execute(
            "UPDATE documentos SET display_name = '', atividade_id = ? WHERE id = ?",
            ("nonexistent_atividade_id", doc.id)
        )
        conn.commit()
        conn.close()

        from scripts.backfill_display_names import backfill_display_names

        # Must not crash
        result = backfill_display_names(sm)

        assert result["total"] >= 1, "Must process at least the orphan document"
        # The doc should still get some display_name (with placeholders)
        conn = sm._get_connection()
        row = conn.execute(
            "SELECT display_name FROM documentos WHERE id = ?",
            (doc.id,)
        ).fetchone()
        conn.close()

        display = row["display_name"] if row else ""
        assert display, (
            "Even with broken metadata, backfill must generate a display_name "
            "using placeholder values rather than leaving it empty."
        )
