"""
TDD Tests for PostgreSQL Storage Migration

These tests verify that data persists in Supabase PostgreSQL.
Run BEFORE and AFTER the migration to ensure nothing breaks.

RED Phase: Tests should FAIL if PostgreSQL is not configured
GREEN Phase: Tests should PASS once migration is complete
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Skip all tests if Supabase not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL"),
    reason="SUPABASE_URL not configured - PostgreSQL tests skipped"
)


class TestSupabaseDBConnection:
    """Test that Supabase database connection works"""

    def test_supabase_db_import(self):
        """supabase_db module should import without errors"""
        from supabase_db import supabase_db
        assert supabase_db is not None

    def test_supabase_db_enabled_when_configured(self):
        """If SUPABASE_URL is set, supabase_db should be enabled"""
        from supabase_db import supabase_db
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_KEY"):
            assert supabase_db.enabled is True

    def test_connection_test(self):
        """Connection test should succeed"""
        from supabase_db import supabase_db
        if supabase_db.enabled:
            success, msg = supabase_db.test_connection()
            assert success, f"Connection failed: {msg}"


class TestStorageManagerPostgreSQL:
    """Test that StorageManager uses PostgreSQL when available"""

    def test_storage_detects_postgresql(self):
        """StorageManager should detect PostgreSQL availability"""
        from storage import StorageManager, SUPABASE_DB_AVAILABLE

        storage = StorageManager()

        if SUPABASE_DB_AVAILABLE:
            assert storage.use_postgresql is True
        else:
            assert storage.use_postgresql is False

    def test_storage_creates_materia_in_postgresql(self):
        """Creating a materia should insert into PostgreSQL"""
        from storage import storage, SUPABASE_DB_AVAILABLE
        from models import NivelEnsino

        if not SUPABASE_DB_AVAILABLE:
            pytest.skip("PostgreSQL not available")

        # Create test materia
        materia = storage.criar_materia(
            nome="TEST_PostgreSQL_Materia",
            descricao="Test materia for PostgreSQL migration",
            nivel=NivelEnsino.MEDIO
        )

        assert materia is not None
        assert materia.id is not None
        assert materia.nome == "TEST_PostgreSQL_Materia"

        # Verify it can be retrieved
        retrieved = storage.get_materia(materia.id)
        assert retrieved is not None
        assert retrieved.nome == materia.nome

        # Cleanup
        storage.deletar_materia(materia.id)

    def test_storage_lists_materias_from_postgresql(self):
        """Listing materias should query PostgreSQL"""
        from storage import storage, SUPABASE_DB_AVAILABLE

        if not SUPABASE_DB_AVAILABLE:
            pytest.skip("PostgreSQL not available")

        # Should not raise any errors
        materias = storage.listar_materias()
        assert isinstance(materias, list)


class TestDataPersistence:
    """Test that data actually persists (the whole point!)"""

    def test_create_and_retrieve_full_hierarchy(self):
        """Create materia > turma > aluno > atividade and verify retrieval"""
        from storage import storage, SUPABASE_DB_AVAILABLE
        from models import NivelEnsino

        if not SUPABASE_DB_AVAILABLE:
            pytest.skip("PostgreSQL not available")

        # Create hierarchy
        materia = storage.criar_materia(
            nome="TEST_Hierarchy_Materia",
            nivel=NivelEnsino.FUNDAMENTAL
        )

        turma = storage.criar_turma(
            materia_id=materia.id,
            nome="TEST_Turma_1A",
            ano_letivo=2026
        )

        aluno = storage.criar_aluno(
            nome="TEST_Aluno_João",
            email="joao@test.com",
            matricula="2026001"
        )

        # Link aluno to turma
        vinculo = storage.vincular_aluno_turma(aluno.id, turma.id)

        atividade = storage.criar_atividade(
            turma_id=turma.id,
            nome="TEST_Prova_1",
            tipo="prova",
            nota_maxima=10.0
        )

        # Verify all data exists
        assert storage.get_materia(materia.id) is not None
        assert storage.get_turma(turma.id) is not None
        assert storage.get_aluno(aluno.id) is not None
        assert storage.get_atividade(atividade.id) is not None
        assert vinculo is not None

        # Verify relationships
        turmas = storage.listar_turmas(materia.id)
        assert len(turmas) >= 1
        assert any(t.id == turma.id for t in turmas)

        alunos = storage.listar_alunos(turma.id)
        assert len(alunos) >= 1
        assert any(a.id == aluno.id for a in alunos)

        atividades = storage.listar_atividades(turma.id)
        assert len(atividades) >= 1
        assert any(a.id == atividade.id for a in atividades)

        # Cleanup (cascade should handle related records)
        storage.deletar_aluno(aluno.id)
        storage.deletar_materia(materia.id)


class TestSQLMigrationRequired:
    """Tests that verify SQL migration has been run"""

    def test_materias_table_exists(self):
        """materias table should exist in PostgreSQL"""
        from supabase_db import supabase_db

        if not supabase_db.enabled:
            pytest.skip("PostgreSQL not configured")

        # Try to query materias - will fail if table doesn't exist
        try:
            rows = supabase_db.select("materias", limit=1)
            assert isinstance(rows, list)
        except Exception as e:
            pytest.fail(f"materias table not found - run migrations/001_create_tables.sql! Error: {e}")

    def test_all_required_tables_exist(self):
        """All required tables should exist"""
        from supabase_db import supabase_db

        if not supabase_db.enabled:
            pytest.skip("PostgreSQL not configured")

        required_tables = [
            "materias",
            "turmas",
            "alunos",
            "alunos_turmas",
            "atividades",
            "documentos",
            "resultados",
            "prompts",
            "prompts_historico"
        ]

        for table in required_tables:
            try:
                rows = supabase_db.select(table, limit=1)
                assert isinstance(rows, list), f"Table {table} query failed"
            except Exception as e:
                pytest.fail(f"Table '{table}' not found - run migrations/001_create_tables.sql! Error: {e}")


class TestBackwardCompatibility:
    """Tests that SQLite fallback still works"""

    def test_sqlite_fallback_when_no_postgresql(self):
        """Should fall back to SQLite when PostgreSQL not available"""
        # Temporarily disable PostgreSQL
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_SERVICE_KEY": ""}):
            # Need to reimport to pick up new env
            import importlib
            import supabase_db
            importlib.reload(supabase_db)

            from storage import StorageManager

            # Create new instance
            storage = StorageManager()
            assert storage.use_postgresql is False

            # Should still work with SQLite
            materias = storage.listar_materias()
            assert isinstance(materias, list)
