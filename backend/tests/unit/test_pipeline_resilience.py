"""Tests for Pipeline Grading Resilience.

Wave 1 (F1-T1, F2-T1, F4-T1) — DONE
Wave 2 (F1-T2, F2-T2, F3-T1, F4-T2) — RED phase

F1-T2: _coletar_arquivos_para_etapa() edge case handling
F2-T2: Temp file cleanup with finally blocks
F3-T1: Dependency validation in executar_pipeline_completo()
F4-T2: Replace bare except: with specific exceptions
"""
import sys
import os
import json
import re
import tempfile
import shutil
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
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


# ============================================================
# WAVE 2 TESTS: F1-T2, F2-T2, F3-T1, F4-T2
# ============================================================

# ============================================================
# F1-T2: _coletar_arquivos_para_etapa() edge case handling
# ============================================================

class TestColetarArquivosEdgeCases:
    """F1-T2: _coletar_arquivos_para_etapa() should handle edge cases
    where resolver_caminho_documento() returns non-existent path,
    None, or raises an exception."""

    def test_handles_nonexistent_resolved_path(self, executor_with_mock_storage):
        """When resolver returns a Path that doesn't exist on disk,
        function should return empty list without crashing."""
        executor = executor_with_mock_storage
        doc = _make_document(
            TipoDocumento.ENUNCIADO, "fake/path.pdf", extensao=".pdf"
        )
        executor.storage.listar_documentos.return_value = [doc]
        executor.storage.resolver_caminho_documento.return_value = Path(
            "/nonexistent/path.pdf"
        )

        result = executor._coletar_arquivos_para_etapa(
            EtapaProcessamento.EXTRAIR_QUESTOES, "ativ1", None
        )

        assert isinstance(result, list)
        assert len(result) == 0

    def test_handles_resolver_returning_none(self, executor_with_mock_storage):
        """When resolver returns None, function should return empty list."""
        executor = executor_with_mock_storage
        doc = _make_document(
            TipoDocumento.ENUNCIADO, "fake/path.pdf", extensao=".pdf"
        )
        executor.storage.listar_documentos.return_value = [doc]
        executor.storage.resolver_caminho_documento.return_value = None

        result = executor._coletar_arquivos_para_etapa(
            EtapaProcessamento.EXTRAIR_QUESTOES, "ativ1", None
        )

        assert isinstance(result, list)
        assert len(result) == 0

    def test_handles_resolver_exception(self, executor_with_mock_storage):
        """When resolver raises an exception, function should catch it
        and return empty list without crashing."""
        executor = executor_with_mock_storage
        doc = _make_document(
            TipoDocumento.ENUNCIADO, "fake/path.pdf", extensao=".pdf"
        )
        executor.storage.listar_documentos.return_value = [doc]
        executor.storage.resolver_caminho_documento.side_effect = Exception(
            "Supabase connection error"
        )

        result = executor._coletar_arquivos_para_etapa(
            EtapaProcessamento.EXTRAIR_QUESTOES, "ativ1", None
        )

        assert isinstance(result, list)
        assert len(result) == 0


# ============================================================
# F2-T2: Temp file cleanup with finally blocks
# ============================================================

class TestTempFileCleanupFinally:
    """F2-T2: Temp files must be cleaned up even when save operations fail.
    regenerar_formato endpoint should use finally blocks."""

    def test_regenerar_formato_has_finally_cleanup(self):
        """regenerar_formato endpoint should use 'finally' block for
        temp file cleanup so files aren't leaked on save failure."""
        routes_path = (
            Path(__file__).parent.parent.parent / "routes_pipeline.py"
        )
        source = routes_path.read_text(encoding="utf-8")

        # Extract regenerar_documento function source
        start_marker = "async def regenerar_documento"
        start = source.find(start_marker)
        assert start != -1, "regenerar_documento not found in routes_pipeline.py"

        # Find the next function definition to delimit the function body
        next_func = source.find("\nasync def ", start + len(start_marker))
        if next_func == -1:
            next_func = source.find("\ndef ", start + len(start_marker))
        if next_func == -1:
            next_func = len(source)

        func_source = source[start:next_func]

        assert "finally:" in func_source, (
            "regenerar_documento should use 'finally' for temp file cleanup. "
            "Current code has os.unlink in the success path only — "
            "temp files leak when salvar_documento() raises."
        )


# ============================================================
# F3-T1: Dependency validation in executar_pipeline_completo
# ============================================================

class TestDependencyValidation:
    """F3-T1: executar_pipeline_completo() should validate that required
    prerequisite documents exist before running a step.
    Only critical dependencies are checked — some documents are optional."""

    @pytest.mark.asyncio
    async def test_corrigir_without_questoes_returns_dependency_error(
        self, executor_with_mock_storage
    ):
        """Running CORRIGIR step without prior EXTRACAO_QUESTOES should
        return a clear error mentioning 'extrair_questoes'."""
        executor = executor_with_mock_storage

        # No documents exist for this activity
        executor.storage.listar_documentos.return_value = []

        # Mock executar_etapa — should NOT be called if deps are checked
        executor.executar_etapa = AsyncMock(
            return_value=ResultadoExecucao(
                sucesso=True, etapa=EtapaProcessamento.CORRIGIR
            )
        )

        result = await executor.executar_pipeline_completo(
            atividade_id="ativ1",
            aluno_id="aluno1",
            selected_steps=["corrigir"],
            provider_name="test-provider",
        )

        # executar_etapa should NOT have been called — deps missing
        if executor.executar_etapa.called:
            pytest.fail(
                "executar_etapa was called for CORRIGIR without checking "
                "dependencies. Should validate that EXTRACAO_QUESTOES "
                "exists first."
            )

        corrigir_result = result.get("corrigir")
        assert corrigir_result is not None, (
            f"Expected 'corrigir' in results, got keys: {list(result.keys())}"
        )
        assert not corrigir_result.sucesso
        assert "extrair_questoes" in (corrigir_result.erro or "").lower(), (
            f"Error should mention 'extrair_questoes' dependency, "
            f"got: {corrigir_result.erro}"
        )

    @pytest.mark.asyncio
    async def test_gerar_relatorio_without_correcao_returns_dependency_error(
        self, executor_with_mock_storage
    ):
        """Running GERAR_RELATORIO without prior CORRECAO should
        return a clear error mentioning 'corrigir'."""
        executor = executor_with_mock_storage

        # No documents exist
        executor.storage.listar_documentos.return_value = []
        executor.executar_etapa = AsyncMock(
            return_value=ResultadoExecucao(
                sucesso=True, etapa=EtapaProcessamento.GERAR_RELATORIO
            )
        )

        result = await executor.executar_pipeline_completo(
            atividade_id="ativ1",
            aluno_id="aluno1",
            selected_steps=["gerar_relatorio"],
            provider_name="test-provider",
        )

        if executor.executar_etapa.called:
            pytest.fail(
                "executar_etapa was called for GERAR_RELATORIO without "
                "checking dependencies. Should validate that CORRECAO "
                "exists first."
            )

        relatorio_result = result.get("gerar_relatorio")
        assert relatorio_result is not None, (
            f"Expected 'gerar_relatorio' in results, "
            f"got keys: {list(result.keys())}"
        )
        assert not relatorio_result.sucesso
        assert "corrigir" in (relatorio_result.erro or "").lower(), (
            f"Error should mention 'corrigir' dependency, "
            f"got: {relatorio_result.erro}"
        )


# ============================================================
# F4-T2: Replace bare except with specific exceptions
# ============================================================

class TestSpecificExceptions:
    """F4-T2: Replace bare except: with specific exception types.
    Bare except catches everything (including SystemExit, KeyboardInterrupt)
    and masks real errors."""

    def test_no_bare_except_in_gerar_relatorios_turma(self):
        """gerar_relatorios_turma should not use bare 'except:' patterns.
        Must use specific exception types like FileNotFoundError."""
        import inspect

        source = inspect.getsource(PipelineExecutor.gerar_relatorios_turma)

        # Find bare 'except:' (with optional whitespace before colon)
        bare_excepts = re.findall(r"^\s*except\s*:", source, re.MULTILINE)

        assert len(bare_excepts) == 0, (
            f"Found {len(bare_excepts)} bare 'except:' pattern(s) in "
            "gerar_relatorios_turma. Use specific exception types "
            "(FileNotFoundError, json.JSONDecodeError, etc.)."
        )

    def test_ler_conteudo_documento_propagates_unexpected_errors(
        self, temp_dir
    ):
        """_ler_conteudo_documento should catch only expected exceptions
        (FileNotFoundError, JSONDecodeError), not all Exception subclasses.
        Unexpected errors like PermissionError should propagate."""
        from routes_prompts import _ler_conteudo_documento

        # Create a real file so .exists() returns True
        test_file = temp_dir / "test_perm.json"
        test_file.write_text('{"test": true}', encoding="utf-8")

        doc = MagicMock()
        doc.caminho_arquivo = str(test_file)
        doc.extensao = ".json"
        doc.nome_arquivo = "test_perm.json"

        # PermissionError is unexpected — should propagate, not be caught
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                _ler_conteudo_documento(doc)
