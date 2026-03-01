"""
Tests for display_name field in Documento dataclass and SQLite schema.

F2-T1: Documento dataclass has display_name field with default ""
F2-T2: SQLite schema includes display_name column + ALTER TABLE migration
"""

import sqlite3
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
from models import TipoDocumento, StatusProcessamento, Documento


# ============================================================
# F2-T1: Documento.display_name field tests
# ============================================================

class TestDocumentoDisplayNameField:
    """Tests for the display_name field on the Documento dataclass."""

    def test_display_name_default_empty_string(self):
        """New Documento without display_name has empty string default."""
        doc = Documento(
            id="test-1",
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id="ativ-1",
        )
        assert doc.display_name == ""

    def test_display_name_set_on_creation(self):
        """Documento created with display_name stores it correctly."""
        doc = Documento(
            id="test-2",
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id="ativ-1",
            display_name="Prova Respondida - Maria Silva - Cálculo I",
        )
        assert doc.display_name == "Prova Respondida - Maria Silva - Cálculo I"

    def test_display_name_mutable(self):
        """display_name can be reassigned after creation."""
        doc = Documento(
            id="test-3",
            tipo=TipoDocumento.ENUNCIADO,
            atividade_id="ativ-1",
        )
        doc.display_name = "Enunciado - Cálculo I - Turma A"
        assert doc.display_name == "Enunciado - Cálculo I - Turma A"

    def test_display_name_preserves_accents(self):
        """Portuguese accents are preserved in display_name."""
        doc = Documento(
            id="test-4",
            tipo=TipoDocumento.CORRECAO,
            atividade_id="ativ-1",
            display_name="Correção - João Santos - Álgebra",
        )
        assert "ç" in doc.display_name
        assert "ã" in doc.display_name
        assert "á" in doc.display_name


class TestDocumentoToDict:
    """Tests for display_name in Documento.to_dict()."""

    def test_to_dict_includes_display_name(self):
        """to_dict() output includes the display_name key."""
        doc = Documento(
            id="test-5",
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id="ativ-1",
            display_name="Test Display Name",
        )
        d = doc.to_dict()
        assert "display_name" in d
        assert d["display_name"] == "Test Display Name"

    def test_to_dict_display_name_empty_default(self):
        """to_dict() includes display_name even when it's the default empty string."""
        doc = Documento(
            id="test-6",
            tipo=TipoDocumento.ENUNCIADO,
            atividade_id="ativ-1",
        )
        d = doc.to_dict()
        assert "display_name" in d
        assert d["display_name"] == ""


class TestDocumentoFromDict:
    """Tests for display_name in Documento.from_dict()."""

    def _base_dict(self, **overrides):
        """Helper to create a valid Documento dict."""
        data = {
            "id": "test-fd-1",
            "tipo": "prova_respondida",
            "atividade_id": "ativ-1",
            "nome_arquivo": "test.pdf",
            "caminho_arquivo": "/tmp/test.pdf",
            "extensao": ".pdf",
            "tamanho_bytes": 1024,
            "status": "concluido",
            "criado_em": datetime.now().isoformat(),
            "atualizado_em": datetime.now().isoformat(),
            "versao": 1,
        }
        data.update(overrides)
        return data

    def test_from_dict_with_display_name(self):
        """from_dict() correctly restores display_name."""
        data = self._base_dict(display_name="Prova Respondida - Maria")
        doc = Documento.from_dict(data)
        assert doc.display_name == "Prova Respondida - Maria"

    def test_from_dict_without_display_name_defaults_empty(self):
        """from_dict() handles missing display_name (backward compat)."""
        data = self._base_dict()
        # Ensure display_name is NOT in the dict (simulates old data)
        data.pop("display_name", None)
        doc = Documento.from_dict(data)
        assert doc.display_name == ""

    def test_roundtrip_to_dict_from_dict(self):
        """Roundtrip: to_dict → from_dict preserves display_name."""
        original = Documento(
            id="test-rt-1",
            tipo=TipoDocumento.CORRECAO,
            atividade_id="ativ-1",
            display_name="Correção - João - Cálculo I",
        )
        data = original.to_dict()
        restored = Documento.from_dict(data)
        assert restored.display_name == original.display_name


# ============================================================
# F2-T2: SQLite schema tests
# ============================================================

@patch("storage.SUPABASE_DB_AVAILABLE", False)
@patch("storage.SUPABASE_STORAGE_AVAILABLE", False)
class TestSQLiteDisplayNameColumn:
    """Tests for display_name column in SQLite documentos table."""

    def test_new_db_has_display_name_column(self, temp_data_dir):
        """A fresh StorageManager DB has display_name in documentos table."""
        from storage import StorageManager

        sm = StorageManager(base_path=str(temp_data_dir))
        conn = sqlite3.connect(sm.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("PRAGMA table_info(documentos)")
        columns = {row["name"] for row in c.fetchall()}
        conn.close()

        assert "display_name" in columns

    def test_insert_with_display_name(self, temp_data_dir):
        """INSERT into documentos with display_name succeeds and is retrievable."""
        from storage import StorageManager

        sm = StorageManager(base_path=str(temp_data_dir))
        conn = sqlite3.connect(sm.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            INSERT INTO documentos (id, tipo, atividade_id, display_name)
            VALUES (?, ?, ?, ?)
        ''', ("doc-1", "prova_respondida", "ativ-1", "Prova Respondida - Maria"))
        conn.commit()

        c.execute("SELECT display_name FROM documentos WHERE id = ?", ("doc-1",))
        row = c.fetchone()
        conn.close()

        assert row is not None
        assert row["display_name"] == "Prova Respondida - Maria"

    def test_display_name_defaults_to_empty(self, temp_data_dir):
        """INSERT without display_name defaults to empty string."""
        from storage import StorageManager

        sm = StorageManager(base_path=str(temp_data_dir))
        conn = sqlite3.connect(sm.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('''
            INSERT INTO documentos (id, tipo, atividade_id)
            VALUES (?, ?, ?)
        ''', ("doc-2", "enunciado", "ativ-1"))
        conn.commit()

        c.execute("SELECT display_name FROM documentos WHERE id = ?", ("doc-2",))
        row = c.fetchone()
        conn.close()

        assert row is not None
        assert row["display_name"] == "" or row["display_name"] is None  # DEFAULT '' or NULL

    def test_alter_table_migration_adds_column(self, temp_data_dir):
        """Existing DB without display_name gets it via ALTER TABLE migration."""
        db_path = temp_data_dir / "database.db"

        # Create a DB with the OLD schema (no display_name column)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS documentos (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL,
                atividade_id TEXT NOT NULL,
                aluno_id TEXT,
                nome_arquivo TEXT,
                caminho_arquivo TEXT,
                extensao TEXT,
                tamanho_bytes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'concluido',
                criado_em TEXT,
                atualizado_em TEXT,
                criado_por TEXT,
                versao INTEGER DEFAULT 1,
                documento_origem_id TEXT,
                metadata TEXT
            )
        ''')
        # Insert a row WITHOUT display_name
        c.execute('''
            INSERT INTO documentos (id, tipo, atividade_id, nome_arquivo)
            VALUES (?, ?, ?, ?)
        ''', ("old-doc-1", "prova_respondida", "ativ-1", "tmpdgvpjvxp.pdf"))
        conn.commit()
        conn.close()

        # Now create StorageManager pointing at this existing DB
        # It should run migration that ADDs display_name column
        from storage import StorageManager
        sm = StorageManager(base_path=str(temp_data_dir))

        # Verify column was added
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("PRAGMA table_info(documentos)")
        columns = {row["name"] for row in c.fetchall()}
        assert "display_name" in columns

        # Verify existing row still accessible and display_name is null/empty
        c.execute("SELECT display_name FROM documentos WHERE id = ?", ("old-doc-1",))
        row = c.fetchone()
        conn.close()

        assert row is not None
        # After ALTER TABLE ADD COLUMN, existing rows have NULL for the new column
        assert row["display_name"] is None or row["display_name"] == ""
