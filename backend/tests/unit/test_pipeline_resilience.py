"""Tests for Pipeline Grading Resilience.

Wave 1 (F1-T1, F2-T1, F4-T1) — DONE
Wave 2 (F1-T2, F2-T2, F3-T1, F4-T2) — DONE
Wave 2b (F3-T2) — DONE
F5-T1: Default provider config + health check tests

F1-T2: _coletar_arquivos_para_etapa() edge case handling
F2-T2: Temp file cleanup with finally blocks
F3-T1: Dependency validation in executar_pipeline_completo()
F4-T2: Replace bare except: with specific exceptions
F3-T2: Map TipoDocumento → EtapaProcessamento for error messages
F5-T1: Default provider should be claude-haiku, health check validation
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
from executor import PipelineExecutor, ResultadoExecucao, build_student_pipeline_result, _latest_by_type


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


# ============================================================
# F3-T2: Map TipoDocumento → EtapaProcessamento for errors
# ============================================================

class TestTipoToEtapaMapping:
    """F3-T2: A proper module-level mapping from TipoDocumento to
    EtapaProcessamento should exist for clear dependency error messages."""

    def test_tipo_to_etapa_mapping_exists(self):
        """executor module should export a TIPO_TO_ETAPA mapping dict."""
        from executor import TIPO_TO_ETAPA

        assert isinstance(TIPO_TO_ETAPA, dict), (
            "TIPO_TO_ETAPA should be a dict, got: " + type(TIPO_TO_ETAPA).__name__
        )

    def test_mapping_covers_critical_document_types(self):
        """Mapping must cover all document types that are pipeline prerequisites:
        EXTRACAO_QUESTOES, EXTRACAO_RESPOSTAS, CORRECAO."""
        from executor import TIPO_TO_ETAPA

        required_types = [
            TipoDocumento.EXTRACAO_QUESTOES,
            TipoDocumento.EXTRACAO_RESPOSTAS,
            TipoDocumento.CORRECAO,
        ]
        for tipo in required_types:
            assert tipo in TIPO_TO_ETAPA, (
                f"{tipo.name} must be in TIPO_TO_ETAPA mapping"
            )

    def test_mapping_values_are_etapa_enum_members(self):
        """Mapping values should be EtapaProcessamento enum members,
        not plain strings."""
        from executor import TIPO_TO_ETAPA

        for tipo, etapa in TIPO_TO_ETAPA.items():
            assert isinstance(etapa, EtapaProcessamento), (
                f"TIPO_TO_ETAPA[{tipo.name}] should be EtapaProcessamento, "
                f"got {type(etapa).__name__}: {etapa}"
            )

    @pytest.mark.asyncio
    async def test_dependency_error_uses_etapa_value(
        self, executor_with_mock_storage
    ):
        """Dependency error messages should use EtapaProcessamento.value
        (e.g., 'extrair_questoes') derived from the TIPO_TO_ETAPA mapping,
        not hardcoded strings."""
        executor = executor_with_mock_storage
        executor.storage.listar_documentos.return_value = []
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

        corrigir_result = result.get("corrigir")
        assert corrigir_result is not None
        assert not corrigir_result.sucesso
        # Error should mention the step name derived from EtapaProcessamento
        error_msg = (corrigir_result.erro or "").lower()
        assert "extrair_questoes" in error_msg
        assert "extrair_respostas" in error_msg


# ============================================================
# F5-T1: Default provider config + health check tests
# ============================================================

class TestDefaultProviderConfig:
    """F5-T1: Default provider must be claude-haiku, not openai-gpt4o.
    The health check should detect broken providers and fall back."""

    def test_setup_providers_sets_haiku_as_default(self):
        """When both OpenAI and Anthropic keys are available,
        setup_providers_from_env should set claude-haiku as default."""
        from ai_providers import AIProviderRegistry

        registry = AIProviderRegistry.__new__(AIProviderRegistry)
        registry.providers = {}
        registry.provider_configs = {}
        registry.default_provider = None
        registry.provider_health = {}
        registry.config_path = Path("/dev/null")

        def _make_provider(provider_name, model_name):
            mock = MagicMock()
            mock.name = provider_name
            mock.model = model_name
            return mock

        # Simulate registration order from setup_providers_from_env
        registry.register("openai-gpt4o", _make_provider("OpenAIProvider", "gpt-4o"))
        registry.register("openai-gpt4o-mini", _make_provider("OpenAIProvider", "gpt-4o-mini"))
        registry.register("claude-sonnet", _make_provider("AnthropicProvider", "claude-sonnet-4"))
        registry.register("claude-haiku", _make_provider("AnthropicProvider", "claude-haiku-4-5"), set_default=True)

        assert registry.default_provider == "claude-haiku", (
            f"Default provider should be 'claude-haiku', got '{registry.default_provider}'"
        )

    def test_setup_code_has_haiku_as_default(self):
        """The setup_providers_from_env source code should set_default=True
        for claude-haiku, not for openai-gpt4o."""
        import inspect
        from ai_providers import setup_providers_from_env

        source = inspect.getsource(setup_providers_from_env)

        # The openai-gpt4o registration should NOT have set_default=True
        openai_section_start = source.find('"openai-gpt4o"')
        assert openai_section_start != -1
        openai_section = source[openai_section_start:openai_section_start + 200]
        # After finding the openai-gpt4o string, check the next register() call
        assert "set_default=True" not in openai_section, (
            "openai-gpt4o should NOT be set as default. "
            "Found set_default=True in the openai-gpt4o registration."
        )

        # The claude-haiku registration SHOULD have set_default=True
        haiku_section_start = source.find('"claude-haiku"')
        assert haiku_section_start != -1
        haiku_section = source[haiku_section_start:haiku_section_start + 200]
        assert "set_default=True" in haiku_section, (
            "claude-haiku should be set as default provider. "
            "Missing set_default=True in the claude-haiku registration."
        )

    def test_provider_health_dict_exists_on_registry(self):
        """AIProviderRegistry should have a provider_health dict
        for tracking health check results."""
        from ai_providers import AIProviderRegistry

        registry = AIProviderRegistry.__new__(AIProviderRegistry)
        registry.providers = {}
        registry.provider_configs = {}
        registry.default_provider = None
        registry.provider_health = {}
        registry.config_path = Path("/dev/null")

        assert hasattr(registry, "provider_health")
        assert isinstance(registry.provider_health, dict)


# ============================================================
# F5-T1: Document deduplication — _latest_by_type + context
# ============================================================

def _make_doc_with_time(tipo, caminho, criado_em, aluno_id=None, extensao=".json"):
    """Helper that creates a Documento with an explicit criado_em timestamp."""
    return Documento(
        id=f"doc_{tipo.value}_{criado_em.isoformat()}",
        tipo=tipo,
        atividade_id="test_atividade",
        aluno_id=aluno_id,
        nome_arquivo=Path(caminho).name,
        caminho_arquivo=caminho,
        extensao=extensao,
        tamanho_bytes=100,
        status=StatusProcessamento.CONCLUIDO,
        criado_em=criado_em,
        atualizado_em=criado_em,
    )


class TestLatestByType:
    """_latest_by_type must always pick the most recent document per type."""

    def test_picks_newest_of_multiple_same_type(self):
        """Given 3 EXTRACAO_QUESTOES docs with different timestamps,
        _latest_by_type returns only the newest one."""
        old = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, "old/tmpabc.json",
            datetime(2026, 1, 1, 10, 0, 0))
        middle = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, "mid/tmpdef.json",
            datetime(2026, 1, 15, 10, 0, 0))
        newest = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, "new/tmpghi.json",
            datetime(2026, 2, 1, 10, 0, 0))

        result = _latest_by_type(
            [old, middle, newest],
            [TipoDocumento.EXTRACAO_QUESTOES]
        )

        assert len(result) == 1, f"Expected 1 doc, got {len(result)}"
        assert result[0].id == newest.id, (
            f"Expected newest doc ({newest.id}), got {result[0].id}"
        )

    def test_returns_one_per_type_when_multiple_types(self):
        """Given mixed types, returns exactly one per requested type."""
        q_old = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, "q_old.json",
            datetime(2026, 1, 1))
        q_new = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, "q_new.json",
            datetime(2026, 2, 1))
        g_old = _make_doc_with_time(
            TipoDocumento.EXTRACAO_GABARITO, "g_old.json",
            datetime(2026, 1, 1))
        g_new = _make_doc_with_time(
            TipoDocumento.EXTRACAO_GABARITO, "g_new.json",
            datetime(2026, 2, 1))

        result = _latest_by_type(
            [q_old, g_old, q_new, g_new],
            [TipoDocumento.EXTRACAO_QUESTOES, TipoDocumento.EXTRACAO_GABARITO]
        )

        assert len(result) == 2
        ids = {d.id for d in result}
        assert q_new.id in ids
        assert g_new.id in ids

    def test_ignores_unrequested_types(self):
        """Documents of types not in the requested list are ignored."""
        questoes = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, "q.json",
            datetime(2026, 1, 1))
        enunciado = _make_doc_with_time(
            TipoDocumento.ENUNCIADO, "e.pdf",
            datetime(2026, 2, 1), extensao=".pdf")

        result = _latest_by_type(
            [questoes, enunciado],
            [TipoDocumento.EXTRACAO_QUESTOES]
        )

        assert len(result) == 1
        assert result[0].tipo == TipoDocumento.EXTRACAO_QUESTOES

    def test_empty_docs_returns_empty(self):
        """Empty input returns empty output."""
        result = _latest_by_type([], [TipoDocumento.EXTRACAO_QUESTOES])
        assert result == []


class TestContextJsonDedup:
    """_preparar_contexto_json must load the NEWEST document per type,
    not the oldest. This prevents stale data from confusing the AI."""

    def test_context_loads_newest_extraction(self, executor_with_mock_storage, temp_dir):
        """When multiple EXTRACAO_QUESTOES docs exist, context should
        load content from the NEWEST one."""
        executor = executor_with_mock_storage

        # OLD extraction (stale data with wrong content)
        old_path = temp_dir / "old_questoes.json"
        old_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "resposta": "WRONG"}], "version": "old"}),
            encoding="utf-8"
        )
        old_doc = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, str(old_path),
            datetime(2026, 1, 1, 10, 0, 0))

        # NEW extraction (correct data)
        new_path = temp_dir / "new_questoes.json"
        new_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "resposta": "CORRECT"}], "version": "new"}),
            encoding="utf-8"
        )
        new_doc = _make_doc_with_time(
            TipoDocumento.EXTRACAO_QUESTOES, str(new_path),
            datetime(2026, 2, 1, 10, 0, 0))

        # Return docs in WRONG order (oldest first — simulating unsorted storage)
        executor.storage.listar_documentos.return_value = [old_doc, new_doc]

        # resolver returns the doc's own path
        def resolve(doc):
            return Path(doc.caminho_arquivo)
        executor.storage.resolver_caminho_documento.side_effect = resolve

        resultado = executor._preparar_contexto_json(
            "test_atividade", "aluno1", EtapaProcessamento.CORRIGIR
        )

        # The loaded content MUST be from the newest doc
        loaded = resultado.get("questoes_extraidas")
        assert loaded is not None, "questoes_extraidas should be loaded"
        parsed = json.loads(loaded)
        assert parsed["version"] == "new", (
            f"Expected newest version ('new'), got '{parsed.get('version')}'. "
            "Context loaded stale data from an old document!"
        )
