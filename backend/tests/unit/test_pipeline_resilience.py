"""Tests for Pipeline Grading Resilience (F1-T1, F2-T1, F4-T1).

RED phase: These tests describe the DESIRED behavior for Wave 1.
They should FAIL against the current code because the features
haven't been implemented yet.

F1-T1: _preparar_contexto_json() should use resolver_caminho_documento()
F2-T1: salvar_documento() should record Supabase upload status in metadata
F4-T1: Turma pipeline response should include etapa_falhou field
"""
import sys
import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models import TipoDocumento, Documento, StatusProcessamento
from prompts import EtapaProcessamento
from executor import PipelineExecutor, ResultadoExecucao, build_student_pipeline_result


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test data."""
    d = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mock_storage(temp_dir):
    """Create a mock StorageManager with essential methods."""
    storage = MagicMock()
    storage.base_path = temp_dir
    return storage


@pytest.fixture
def executor_with_mock_storage(mock_storage):
    """Create a PipelineExecutor with mocked storage."""
    with patch('executor.storage', mock_storage), \
         patch('executor.prompt_manager', MagicMock()):
        ex = PipelineExecutor()
        ex.storage = mock_storage
        return ex


def _make_document(tipo, caminho, aluno_id=None, extensao=".json"):
    """Helper to create a Documento object for testing."""
    return Documento(
        id=f"doc_{tipo.value}_{aluno_id or 'base'}",
        tipo=tipo,
        atividade_id="test_atividade",
        aluno_id=aluno_id,
        nome_arquivo=Path(caminho).name,
        caminho_arquivo=caminho,
        extensao=extensao,
        tamanho_bytes=100,
        status=StatusProcessamento.CONCLUIDO,
        criado_em=datetime.now(),
        atualizado_em=datetime.now(),
    )


# ============================================================
# F1-T1: _preparar_contexto_json() should use resolver_caminho_documento()
# ============================================================

class TestPreparContextoJsonUsesResolver:
    """F1-T1: When local file doesn't exist, resolver_caminho_documento()
    should be called to download from Supabase before reading."""

    def test_calls_resolver_when_local_file_missing(self, executor_with_mock_storage, temp_dir):
        """When the document's local path doesn't exist,
        _preparar_contexto_json should call resolver_caminho_documento
        to attempt Supabase download."""
        executor = executor_with_mock_storage

        # Create a JSON file that will be "resolved" by Supabase
        resolved_path = temp_dir / "resolved" / "questoes.json"
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "resposta": "x=5"}]}),
            encoding="utf-8"
        )

        # Create a document pointing to a NON-EXISTENT local path
        nonexistent_path = "nonexistent/tmpabc123.json"
        doc_questoes = _make_document(
            TipoDocumento.EXTRACAO_QUESTOES,
            nonexistent_path,
            extensao=".json"
        )

        # Mock listar_documentos to return our doc
        executor.storage.listar_documentos.return_value = [doc_questoes]

        # Mock resolver_caminho_documento to return the resolved path
        executor.storage.resolver_caminho_documento.return_value = resolved_path

        # Call _preparar_contexto_json for CORRIGIR step
        resultado = executor._preparar_contexto_json(
            "test_atividade", "aluno1", EtapaProcessamento.CORRIGIR
        )

        # ASSERT: resolver_caminho_documento MUST have been called
        executor.storage.resolver_caminho_documento.assert_called()
        # ASSERT: The JSON was loaded successfully (not in _documentos_faltantes)
        assert "questoes_extraidas" in resultado.get("_documentos_carregados", []), \
            f"Expected questoes_extraidas in loaded docs, got: {resultado}"

    def test_loads_json_from_resolved_supabase_path(self, executor_with_mock_storage, temp_dir):
        """Verify that the JSON content is actually loaded from the
        resolved path (not from the original nonexistent path)."""
        executor = executor_with_mock_storage

        # Create resolved JSON with specific content
        resolved_path = temp_dir / "from_supabase" / "questoes.json"
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        expected_content = {"questoes": [{"numero": 1, "resposta": "42"}], "total": 1}
        resolved_path.write_text(json.dumps(expected_content), encoding="utf-8")

        doc = _make_document(
            TipoDocumento.EXTRACAO_QUESTOES,
            "temp/nonexistent.json",
            extensao=".json"
        )

        executor.storage.listar_documentos.return_value = [doc]
        executor.storage.resolver_caminho_documento.return_value = resolved_path

        resultado = executor._preparar_contexto_json(
            "test_atividade", "aluno1", EtapaProcessamento.CORRIGIR
        )

        # The loaded JSON should match our expected content
        loaded = resultado.get("questoes_extraidas")
        assert loaded is not None, "questoes_extraidas should be loaded"
        parsed = json.loads(loaded)
        assert parsed["total"] == 1, f"Expected total=1, got: {parsed}"


# ============================================================
# F2-T1: salvar_documento() should record Supabase upload status
# ============================================================

class TestSalvarDocumentoSupabaseUpload:
    """F2-T1: After saving locally, salvar_documento() should attempt
    Supabase Storage upload and record the result in document metadata."""

    def test_upload_success_recorded_in_metadata(self, temp_dir):
        """When Supabase upload succeeds, documento.metadata should have
        supabase_uploaded=True."""
        from storage import StorageManager

        # Create a real StorageManager with temp dir
        sm = StorageManager.__new__(StorageManager)
        sm.base_path = temp_dir
        sm.use_postgresql = False
        sm.db_path = str(temp_dir / "test.db")

        # Create a source file
        source_file = temp_dir / "source.json"
        source_file.write_text('{"test": true}', encoding="utf-8")

        # Create a mock atividade
        sm.get_atividade = MagicMock(return_value=MagicMock(
            id="ativ1", materia_id="mat1"
        ))
        sm.get_aluno = MagicMock(return_value=MagicMock(id="aluno1"))
        sm._get_caminho_documento = MagicMock(
            return_value=temp_dir / "data" / "test_output.json"
        )
        (temp_dir / "data").mkdir(exist_ok=True)

        # Mock the database insert
        sm._get_connection = MagicMock()
        mock_conn = MagicMock()
        sm._get_connection.return_value = mock_conn

        # Mock Supabase storage upload
        mock_supabase = MagicMock()
        mock_supabase.upload.return_value = (True, "Upload OK")

        with patch('storage.SUPABASE_STORAGE_AVAILABLE', True), \
             patch('storage.supabase_storage', mock_supabase):
            doc = sm.salvar_documento(
                arquivo_origem=str(source_file),
                tipo=TipoDocumento.EXTRACAO_QUESTOES,
                atividade_id="ativ1",
            )

        # ASSERT: metadata should record upload status
        assert doc.metadata.get("supabase_uploaded") is True, \
            f"Expected supabase_uploaded=True in metadata, got: {doc.metadata}"

    def test_upload_failure_recorded_in_metadata(self, temp_dir):
        """When Supabase upload fails, documento.metadata should have
        supabase_uploaded=False with the error message."""
        from storage import StorageManager

        sm = StorageManager.__new__(StorageManager)
        sm.base_path = temp_dir
        sm.use_postgresql = False
        sm.db_path = str(temp_dir / "test.db")

        source_file = temp_dir / "source.json"
        source_file.write_text('{"test": true}', encoding="utf-8")

        sm.get_atividade = MagicMock(return_value=MagicMock(
            id="ativ1", materia_id="mat1"
        ))
        sm.get_aluno = MagicMock(return_value=MagicMock(id="aluno1"))
        sm._get_caminho_documento = MagicMock(
            return_value=temp_dir / "data" / "test_output.json"
        )
        (temp_dir / "data").mkdir(exist_ok=True)

        sm._get_connection = MagicMock()
        mock_conn = MagicMock()
        sm._get_connection.return_value = mock_conn

        mock_supabase = MagicMock()
        mock_supabase.upload.return_value = (False, "Network error")

        with patch('storage.SUPABASE_STORAGE_AVAILABLE', True), \
             patch('storage.supabase_storage', mock_supabase):
            doc = sm.salvar_documento(
                arquivo_origem=str(source_file),
                tipo=TipoDocumento.EXTRACAO_QUESTOES,
                atividade_id="ativ1",
            )

        # ASSERT: metadata should record upload failure
        assert doc.metadata.get("supabase_uploaded") is False, \
            f"Expected supabase_uploaded=False in metadata, got: {doc.metadata}"


# ============================================================
# F4-T1: Turma pipeline response should include etapa_falhou
# ============================================================

class TestTurmaResponseEtapaFalhou:
    """F4-T1: When a student's pipeline fails, the turma response should
    include 'etapa_falhou' (first failed stage) and distinguish failed
    stages from not-attempted stages."""

    def test_failed_student_has_etapa_falhou(self):
        """The per-student result should include 'etapa_falhou' with
        the name of the first stage that actually errored."""
        resultados = {
            EtapaProcessamento.EXTRAIR_QUESTOES: ResultadoExecucao(
                sucesso=True, etapa=EtapaProcessamento.EXTRAIR_QUESTOES
            ),
            EtapaProcessamento.CORRIGIR: ResultadoExecucao(
                sucesso=False, etapa=EtapaProcessamento.CORRIGIR,
                erro="arquivo de referência não encontrado"
            ),
        }

        result = build_student_pipeline_result("Test Student", resultados)

        assert "etapa_falhou" in result, \
            "Turma per-student result must include 'etapa_falhou' field"
        assert result["etapa_falhou"] == "corrigir", \
            f"Expected etapa_falhou='corrigir', got: {result.get('etapa_falhou')}"

    def test_successful_student_has_no_etapa_falhou(self):
        """When all stages succeed, etapa_falhou should be None."""
        resultados = {
            EtapaProcessamento.EXTRAIR_QUESTOES: ResultadoExecucao(
                sucesso=True, etapa=EtapaProcessamento.EXTRAIR_QUESTOES
            ),
            EtapaProcessamento.CORRIGIR: ResultadoExecucao(
                sucesso=True, etapa=EtapaProcessamento.CORRIGIR
            ),
        }

        result = build_student_pipeline_result("Good Student", resultados)

        assert "etapa_falhou" in result, \
            "Turma per-student result must include 'etapa_falhou' field even when successful"
        assert result["etapa_falhou"] is None

    def test_failed_student_has_etapas_nao_tentadas(self):
        """When a stage fails, subsequent stages should appear in
        'etapas_nao_tentadas', not in 'etapas_falharam'."""
        resultados = {
            EtapaProcessamento.EXTRAIR_QUESTOES: ResultadoExecucao(
                sucesso=True, etapa=EtapaProcessamento.EXTRAIR_QUESTOES
            ),
            EtapaProcessamento.CORRIGIR: ResultadoExecucao(
                sucesso=False, etapa=EtapaProcessamento.CORRIGIR,
                erro="arquivo não encontrado"
            ),
        }

        result = build_student_pipeline_result("Test Student", resultados)

        assert "etapas_nao_tentadas" in result, \
            "Turma per-student result must include 'etapas_nao_tentadas' field"
