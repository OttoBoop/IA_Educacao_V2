"""
Tests for display_name column in Supabase PostgreSQL schema.

F2-T3: The migrations/001_create_tables.sql must include display_name
       in the documentos CREATE TABLE and provide an ALTER TABLE migration
       for existing databases.
"""

import re
import pytest
from pathlib import Path


MIGRATION_PATH = Path(__file__).parent.parent.parent.parent / "backend" / "migrations" / "001_create_tables.sql"


@pytest.fixture
def migration_sql():
    """Load the PostgreSQL migration SQL."""
    assert MIGRATION_PATH.exists(), f"Migration file not found at {MIGRATION_PATH}"
    return MIGRATION_PATH.read_text(encoding="utf-8")


class TestDocumentosCreateTableHasDisplayName:
    """Verify the CREATE TABLE documentos includes display_name column."""

    def _extract_create_documentos(self, sql):
        """Extract the CREATE TABLE documentos(...) block."""
        pattern = r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+documentos\s*\(([\s\S]*?)\);'
        match = re.search(pattern, sql)
        return match.group(1) if match else None

    def test_display_name_column_in_create_table(self, migration_sql):
        """display_name column is present in CREATE TABLE documentos."""
        block = self._extract_create_documentos(migration_sql)
        assert block is not None, "CREATE TABLE documentos not found"
        assert "display_name" in block, \
            "display_name column missing from CREATE TABLE documentos"

    def test_display_name_is_text_type(self, migration_sql):
        """display_name column is TEXT type."""
        block = self._extract_create_documentos(migration_sql)
        assert block is not None, "CREATE TABLE documentos not found"
        # Match: display_name TEXT (possibly with DEFAULT)
        pattern = r'display_name\s+TEXT'
        assert re.search(pattern, block), \
            "display_name must be TEXT type"

    def test_display_name_has_default(self, migration_sql):
        """display_name column has a DEFAULT value."""
        block = self._extract_create_documentos(migration_sql)
        assert block is not None, "CREATE TABLE documentos not found"
        pattern = r"display_name\s+TEXT\s+DEFAULT\s+['\"]"
        assert re.search(pattern, block), \
            "display_name must have a DEFAULT '' value"

    def test_display_name_after_aluno_id(self, migration_sql):
        """display_name column appears after aluno_id (matches SQLite + model order)."""
        block = self._extract_create_documentos(migration_sql)
        assert block is not None, "CREATE TABLE documentos not found"
        aluno_pos = block.find("aluno_id")
        display_pos = block.find("display_name")
        nome_pos = block.find("nome_arquivo")
        assert aluno_pos < display_pos < nome_pos, \
            "display_name must be between aluno_id and nome_arquivo"


class TestAlterTableMigration:
    """Verify ALTER TABLE migration exists for adding display_name to existing DBs."""

    def test_alter_table_add_display_name(self, migration_sql):
        """An ALTER TABLE documentos ADD COLUMN display_name statement exists."""
        pattern = r'ALTER\s+TABLE\s+documentos\s+ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?display_name'
        assert re.search(pattern, migration_sql, re.IGNORECASE), \
            "ALTER TABLE documentos ADD COLUMN display_name not found in migration"

    def test_alter_table_uses_if_not_exists(self, migration_sql):
        """ALTER TABLE uses IF NOT EXISTS to be idempotent (safe to re-run)."""
        pattern = r'ALTER\s+TABLE\s+documentos\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS\s+display_name'
        assert re.search(pattern, migration_sql, re.IGNORECASE), \
            "ALTER TABLE should use IF NOT EXISTS for idempotent migration"
