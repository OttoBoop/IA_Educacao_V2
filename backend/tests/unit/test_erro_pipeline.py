"""
Tests for pipeline error framework (F2-T1, F3-T1, F4-T1).

F2-T1: Error constants, SeveridadeErro enum, criar_erro_pipeline() helper.
F3-T1: Missing document detection saves JSON with _erro_pipeline.
F4-T1: Missing questions detection saves JSON with _erro_pipeline.
"""
import pytest
import json
import tempfile
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, ANY


class TestF2T1_ErrorFramework:
    """F2-T1: Framework de erros estruturados."""

    def test_erro_documento_faltante_constant_exists(self):
        """ERRO_DOCUMENTO_FALTANTE constant exists and is correct string."""
        from models import ERRO_DOCUMENTO_FALTANTE
        assert ERRO_DOCUMENTO_FALTANTE == "DOCUMENTO_FALTANTE"

    def test_erro_questoes_faltantes_constant_exists(self):
        """ERRO_QUESTOES_FALTANTES constant exists and is correct string."""
        from models import ERRO_QUESTOES_FALTANTES
        assert ERRO_QUESTOES_FALTANTES == "QUESTOES_FALTANTES"

    def test_severidade_erro_enum_has_critico(self):
        """SeveridadeErro enum has CRITICO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "CRITICO")
        assert SeveridadeErro.CRITICO.value == "critico"

    def test_severidade_erro_enum_has_alto(self):
        """SeveridadeErro enum has ALTO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "ALTO")
        assert SeveridadeErro.ALTO.value == "alto"

    def test_severidade_erro_enum_has_medio(self):
        """SeveridadeErro enum has MEDIO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "MEDIO")
        assert SeveridadeErro.MEDIO.value == "medio"

    def test_criar_erro_pipeline_returns_dict_with_all_fields(self):
        """criar_erro_pipeline() returns dict with tipo, mensagem, severidade, etapa, timestamp."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="Arquivo não encontrado",
            severidade=SeveridadeErro.CRITICO,
            etapa="extrair_questoes"
        )
        assert isinstance(result, dict)
        assert result["tipo"] == "DOCUMENTO_FALTANTE"
        assert result["mensagem"] == "Arquivo não encontrado"
        assert result["severidade"] == "critico"
        assert result["etapa"] == "extrair_questoes"
        assert "timestamp" in result

    def test_criar_erro_pipeline_timestamp_is_iso_format(self):
        """Timestamp field is a valid ISO format string."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="test",
            severidade=SeveridadeErro.CRITICO,
            etapa="corrigir"
        )
        # Should not raise
        datetime.fromisoformat(result["timestamp"])

    def test_criar_erro_pipeline_severidade_accepts_string(self):
        """criar_erro_pipeline() works when severidade is passed as string too."""
        from models import criar_erro_pipeline
        result = criar_erro_pipeline(
            tipo="QUESTOES_FALTANTES",
            mensagem="Nenhuma questão extraída",
            severidade="alto",
            etapa="extrair_questoes"
        )
        assert result["severidade"] == "alto"

    def test_criar_erro_pipeline_no_extra_fields(self):
        """Result dict has exactly the expected fields."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="test",
            severidade=SeveridadeErro.CRITICO,
            etapa="test_etapa"
        )
        expected_keys = {"tipo", "mensagem", "severidade", "etapa", "timestamp"}
        assert set(result.keys()) == expected_keys


# ============================================================
# F3-T1: Missing document detection saves JSON with _erro_pipeline
# ============================================================

class TestF3T1_DocumentoFaltante:
    """F3-T1: When documents are missing, executor saves JSON with _erro_pipeline."""

    @pytest.fixture
    def executor_with_mocks(self):
        """Create a PipelineExecutor with mocked storage."""
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = None

        # Track what content gets saved via _salvar_resultado
        executor._saved_contents = []
        original_salvar = None

        return executor

    @pytest.mark.asyncio
    async def test_missing_doc_saves_json_with_erro_pipeline(self, executor_with_mocks):
        """When docs are missing, _executar_multimodal should save JSON with _erro_pipeline field."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        # Mock _preparar_contexto_json to return missing docs
        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["extracao_questoes.json"],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=[])

        # Mock _salvar_resultado to capture what gets saved
        saved_content = {}
        async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
            saved_content.update(resposta_parsed or {})
            return "mock_doc_id"

        executor._salvar_resultado = mock_salvar

        # Create mock prompt
        mock_prompt = MagicMock()
        mock_prompt.id = "test_prompt"

        # Call the method
        resultado = await executor._executar_multimodal(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            prompt=mock_prompt,
            materia=MagicMock(),
            atividade=MagicMock(),
            provider_id=None,
            variaveis_extra=None,
            salvar_resultado=True,
            inicio=time.time(),
        )

        # Verify: result is failure
        assert resultado.sucesso is False

        # Verify: JSON was saved with _erro_pipeline
        assert "_erro_pipeline" in saved_content, \
            "Missing doc should trigger saving JSON with _erro_pipeline field"

    @pytest.mark.asyncio
    async def test_missing_doc_erro_pipeline_has_correct_type(self, executor_with_mocks):
        """The _erro_pipeline saved should have tipo=DOCUMENTO_FALTANTE."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["extracao_gabarito.json"],
            "_documentos_carregados": ["extracao_questoes.json"]
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=[])

        saved_content = {}
        async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
            saved_content.update(resposta_parsed or {})
            return "mock_doc_id"

        executor._salvar_resultado = mock_salvar

        mock_prompt = MagicMock()
        mock_prompt.id = "test_prompt"

        await executor._executar_multimodal(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            prompt=mock_prompt,
            materia=MagicMock(),
            atividade=MagicMock(),
            provider_id=None,
            variaveis_extra=None,
            salvar_resultado=True,
            inicio=time.time(),
        )

        assert saved_content.get("_erro_pipeline", {}).get("tipo") == "DOCUMENTO_FALTANTE", \
            "_erro_pipeline.tipo should be DOCUMENTO_FALTANTE"

    @pytest.mark.asyncio
    async def test_missing_doc_erro_pipeline_has_all_fields(self, executor_with_mocks):
        """The _erro_pipeline should have tipo, mensagem, severidade, etapa, timestamp."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["extracao_questoes.json"],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=[])

        saved_content = {}
        async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
            saved_content.update(resposta_parsed or {})
            return "mock_doc_id"

        executor._salvar_resultado = mock_salvar

        mock_prompt = MagicMock()
        mock_prompt.id = "test_prompt"

        await executor._executar_multimodal(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            prompt=mock_prompt,
            materia=MagicMock(),
            atividade=MagicMock(),
            provider_id=None,
            variaveis_extra=None,
            salvar_resultado=True,
            inicio=time.time(),
        )

        erro = saved_content.get("_erro_pipeline", {})
        required_fields = {"tipo", "mensagem", "severidade", "etapa", "timestamp"}
        assert required_fields.issubset(set(erro.keys())), \
            f"_erro_pipeline missing fields: {required_fields - set(erro.keys())}"


# ============================================================
# F4-T1: Missing questions detection saves JSON with _erro_pipeline
# ============================================================

class TestF4T1_QuestoesFaltantes:
    """F4-T1: When question extraction returns 0 questions, save JSON with _erro_pipeline."""

    @pytest.fixture
    def executor_with_mocks(self):
        """Create a PipelineExecutor with mocked dependencies for post-extraction testing."""
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        return executor

    @pytest.mark.asyncio
    async def test_empty_questoes_saves_erro_pipeline(self, executor_with_mocks):
        """When EXTRAIR_QUESTOES returns empty questoes list, save JSON with _erro_pipeline."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        # Mock dependencies to get past the missing docs check
        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": [],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=["fake_file.pdf"])
        executor._get_provider_config = MagicMock(return_value={
            "tipo": "openai", "api_key": "fake", "modelo": "gpt-4"
        })

        # Mock the API client to return a response with empty questoes
        mock_response = MagicMock()
        mock_response.content = '{"questoes": []}'
        mock_response.input_tokens = 100
        mock_response.output_tokens = 50
        mock_response.tokens_used = 50
        mock_response.provider = "openai"
        mock_response.modelo = "gpt-4"
        mock_response.resposta = '{"questoes": []}'
        mock_response.anexos_enviados = []
        mock_response.anexos_confirmados = False
        mock_response.retryable = False
        mock_response.retry_after = None
        mock_response.tentativas = 1
        mock_response.sucesso = True

        # Mock ClienteAPIMultimodal
        with patch("executor.ClienteAPIMultimodal") as mock_client_class:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Mock _parsear_resposta to return parsed response with empty questoes
            executor._parsear_resposta = MagicMock(return_value={"questoes": []})

            # Track what gets saved
            saved_content = {}
            async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
                saved_content.update(resposta_parsed or {})
                return "mock_doc_id"

            executor._salvar_resultado = mock_salvar

            mock_prompt = MagicMock()
            mock_prompt.id = "test_prompt"
            mock_prompt.render = MagicMock(return_value="rendered prompt")
            mock_prompt.render_sistema = MagicMock(return_value=None)

            resultado = await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
                atividade_id="ativ_test",
                aluno_id=None,
                prompt=mock_prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        # Verify: result should indicate failure
        assert resultado.sucesso is False, \
            "Empty questoes should make the result fail"

        # Verify: JSON was saved with _erro_pipeline
        assert "_erro_pipeline" in saved_content, \
            "Empty questoes should trigger saving JSON with _erro_pipeline field"

    @pytest.mark.asyncio
    async def test_empty_questoes_erro_pipeline_type(self, executor_with_mocks):
        """The _erro_pipeline for empty questoes should have tipo=QUESTOES_FALTANTES."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": [],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=["fake.pdf"])
        executor._get_provider_config = MagicMock(return_value={
            "tipo": "openai", "api_key": "fake", "modelo": "gpt-4"
        })

        mock_response = MagicMock()
        mock_response.content = '{"questoes": []}'
        mock_response.input_tokens = 100
        mock_response.output_tokens = 50
        mock_response.tokens_used = 50
        mock_response.provider = "openai"
        mock_response.modelo = "gpt-4"
        mock_response.resposta = '{"questoes": []}'
        mock_response.anexos_enviados = []
        mock_response.anexos_confirmados = False
        mock_response.retryable = False
        mock_response.retry_after = None
        mock_response.tentativas = 1
        mock_response.sucesso = True

        with patch("executor.ClienteAPIMultimodal") as mock_client_class:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            executor._parsear_resposta = MagicMock(return_value={"questoes": []})

            saved_content = {}
            async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
                saved_content.update(resposta_parsed or {})
                return "mock_doc_id"

            executor._salvar_resultado = mock_salvar

            mock_prompt = MagicMock()
            mock_prompt.id = "test_prompt"
            mock_prompt.render = MagicMock(return_value="rendered prompt")
            mock_prompt.render_sistema = MagicMock(return_value=None)

            await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
                atividade_id="ativ_test",
                aluno_id=None,
                prompt=mock_prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        assert saved_content.get("_erro_pipeline", {}).get("tipo") == "QUESTOES_FALTANTES", \
            "_erro_pipeline.tipo should be QUESTOES_FALTANTES"
