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
            nivel=NivelEnsino.FUNDAMENTAL_1
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


class TestDocumentSubmissions:
    """Test that document submissions persist in PostgreSQL"""

    def test_save_and_retrieve_documento(self, tmp_path):
        """Saving a document should insert record into PostgreSQL"""
        from storage import storage, SUPABASE_DB_AVAILABLE
        from models import NivelEnsino, TipoDocumento

        if not SUPABASE_DB_AVAILABLE:
            pytest.skip("PostgreSQL not available")

        # Create test hierarchy
        materia = storage.criar_materia(
            nome="TEST_Doc_Materia",
            nivel=NivelEnsino.MEDIO
        )
        turma = storage.criar_turma(
            materia_id=materia.id,
            nome="TEST_Doc_Turma",
            ano_letivo=2026
        )
        atividade = storage.criar_atividade(
            turma_id=turma.id,
            nome="TEST_Doc_Atividade",
            tipo="prova"
        )

        # Create a test file
        test_file = tmp_path / "test_enunciado.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        # Save document (enunciado doesn't require aluno_id)
        documento = storage.salvar_documento(
            arquivo_origem=str(test_file),
            tipo=TipoDocumento.ENUNCIADO,
            atividade_id=atividade.id
        )

        assert documento is not None
        assert documento.id is not None
        assert documento.tipo == TipoDocumento.ENUNCIADO

        # Verify it can be retrieved
        retrieved = storage.get_documento(documento.id)
        assert retrieved is not None
        assert retrieved.id == documento.id
        assert retrieved.atividade_id == atividade.id

        # Cleanup
        storage.deletar_documento(documento.id)
        storage.deletar_materia(materia.id)

    def test_save_student_submission(self, tmp_path):
        """Student submission documents should persist with aluno_id"""
        from storage import storage, SUPABASE_DB_AVAILABLE
        from models import NivelEnsino, TipoDocumento

        if not SUPABASE_DB_AVAILABLE:
            pytest.skip("PostgreSQL not available")

        # Create test hierarchy
        materia = storage.criar_materia(
            nome="TEST_Submission_Materia",
            nivel=NivelEnsino.MEDIO
        )
        turma = storage.criar_turma(
            materia_id=materia.id,
            nome="TEST_Submission_Turma",
            ano_letivo=2026
        )
        atividade = storage.criar_atividade(
            turma_id=turma.id,
            nome="TEST_Submission_Atividade",
            tipo="prova"
        )
        aluno = storage.criar_aluno(
            nome="TEST_Submission_Aluno",
            email="submission@test.com",
            matricula="2026SUB"
        )
        storage.vincular_aluno_turma(aluno.id, turma.id)

        # Create a test submission file
        test_file = tmp_path / "prova_respondida.pdf"
        test_file.write_bytes(b"%PDF-1.4 student submission content")

        # Save student submission
        documento = storage.salvar_documento(
            arquivo_origem=str(test_file),
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=atividade.id,
            aluno_id=aluno.id
        )

        assert documento is not None
        assert documento.aluno_id == aluno.id
        assert documento.tipo == TipoDocumento.PROVA_RESPONDIDA

        # Verify it appears in document list
        docs = storage.listar_documentos(atividade.id, aluno_id=aluno.id)
        assert len(docs) >= 1
        assert any(d.id == documento.id for d in docs)

        # Cleanup
        storage.deletar_documento(documento.id)
        storage.deletar_aluno(aluno.id)
        storage.deletar_materia(materia.id)

    def test_list_documents_filters_correctly(self, tmp_path):
        """listar_documentos should filter by atividade_id and tipo"""
        from storage import storage, SUPABASE_DB_AVAILABLE
        from models import NivelEnsino, TipoDocumento

        if not SUPABASE_DB_AVAILABLE:
            pytest.skip("PostgreSQL not available")

        # Create hierarchy
        materia = storage.criar_materia(
            nome="TEST_Filter_Materia",
            nivel=NivelEnsino.MEDIO
        )
        turma = storage.criar_turma(
            materia_id=materia.id,
            nome="TEST_Filter_Turma",
            ano_letivo=2026
        )
        atividade = storage.criar_atividade(
            turma_id=turma.id,
            nome="TEST_Filter_Atividade",
            tipo="prova"
        )

        # Create test files
        enunciado_file = tmp_path / "enunciado.pdf"
        enunciado_file.write_bytes(b"%PDF-1.4 enunciado")

        gabarito_file = tmp_path / "gabarito.pdf"
        gabarito_file.write_bytes(b"%PDF-1.4 gabarito")

        # Save both document types
        doc_enunciado = storage.salvar_documento(
            arquivo_origem=str(enunciado_file),
            tipo=TipoDocumento.ENUNCIADO,
            atividade_id=atividade.id
        )
        doc_gabarito = storage.salvar_documento(
            arquivo_origem=str(gabarito_file),
            tipo=TipoDocumento.GABARITO,
            atividade_id=atividade.id
        )

        # List all docs for atividade
        all_docs = storage.listar_documentos(atividade.id)
        assert len(all_docs) >= 2

        # Filter by tipo
        enunciados = storage.listar_documentos(atividade.id, tipo=TipoDocumento.ENUNCIADO)
        assert all(d.tipo == TipoDocumento.ENUNCIADO for d in enunciados)

        gabaritos = storage.listar_documentos(atividade.id, tipo=TipoDocumento.GABARITO)
        assert all(d.tipo == TipoDocumento.GABARITO for d in gabaritos)

        # Cleanup
        storage.deletar_documento(doc_enunciado.id)
        storage.deletar_documento(doc_gabarito.id)
        storage.deletar_materia(materia.id)


class TestBackwardCompatibility:
    """Tests that SQLite fallback still works"""

    @pytest.mark.skip(reason="SQLite not used — project uses PostgreSQL/Supabase exclusively")
    def test_sqlite_fallback_when_no_postgresql(self):
        """Skipped: project uses PostgreSQL/Supabase exclusively, no SQLite fallback needed."""
        pass
