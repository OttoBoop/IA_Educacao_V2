"""
Tests for pipeline error framework (F2-T1, F3-T1, F4-T1, F3-T2, F5-T1, F5-T2).

F2-T1: Error constants, SeveridadeErro enum, criar_erro_pipeline() helper.
F3-T1: Missing document detection saves JSON with _erro_pipeline.
F4-T1: Missing questions detection saves JSON with _erro_pipeline.
F3-T2: Pipeline orchestration marks overall result as ERRO when stage fails.
F5-T1: API propagates _erro_pipeline in response JSON.
F5-T2: Visualizador includes erro_pipeline in VisaoAluno.
"""
import pytest
import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
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


# ============================================================
# F3-T2: Pipeline orchestration marks overall result as ERRO
# ============================================================

class TestF3T2_PipelineOrquestracao:
    """F3-T2: When pipeline stage fails, orchestration adds _pipeline_erro to results."""

    @pytest.fixture
    def executor_pipeline(self):
        """Create executor for pipeline orchestration testing."""
        from executor import PipelineExecutor
        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        return executor

    @pytest.mark.asyncio
    async def test_failed_stage_adds_pipeline_erro(self, executor_pipeline):
        """When a stage returns sucesso=False, results dict should have _pipeline_erro."""
        from executor import ResultadoExecucao, EtapaProcessamento
        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])

        async def mock_executar_etapa(etapa, ativ_id, aluno_id=None, **kwargs):
            return ResultadoExecucao(
                sucesso=False, etapa=etapa, erro="Doc faltante", retryable=False
            )

        executor.executar_etapa = mock_executar_etapa

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test", aluno_id="aluno_test"
        )

        assert "_pipeline_erro" in resultados, \
            "Failed pipeline should include _pipeline_erro in returned dict"

    @pytest.mark.asyncio
    async def test_pipeline_erro_has_stage_and_status(self, executor_pipeline):
        """_pipeline_erro should have etapa_falha and sucesso=False."""
        from executor import ResultadoExecucao, EtapaProcessamento
        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])

        async def mock_executar_etapa(etapa, ativ_id, aluno_id=None, **kwargs):
            return ResultadoExecucao(
                sucesso=False, etapa=etapa, erro="Fail", retryable=False
            )

        executor.executar_etapa = mock_executar_etapa

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test", aluno_id="aluno_test"
        )

        erro = resultados.get("_pipeline_erro")
        assert erro is not None, "_pipeline_erro should exist"
        assert "etapa_falha" in erro, "Should have etapa_falha field"
        assert erro.get("sucesso") is False, "sucesso should be False"


# ============================================================
# F5-T1: API propagates _erro_pipeline in response JSON
# ============================================================

class TestF5T1_APIPropagaErro:
    """F5-T1: API endpoint propagates _erro_pipeline when found in stored documents."""

    @pytest.mark.asyncio
    async def test_partial_result_with_erro_returns_status_erro(self):
        """When partial result has doc with _erro_pipeline, response has status=erro."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump({
                "_erro_pipeline": {
                    "tipo": "DOCUMENTO_FALTANTE",
                    "mensagem": "Docs faltando",
                    "severidade": "critico",
                    "etapa": "corrigir",
                    "timestamp": "2026-02-24T12:00:00"
                }
            }, f)
            temp_path = f.name

        try:
            mock_doc = MagicMock()
            mock_doc.tipo = MagicMock()
            mock_doc.tipo.value = "correcao"
            mock_doc.id = "doc_erro"
            mock_doc.extensao = ".json"
            mock_doc.aluno_id = "aluno_test"
            mock_doc.nome_arquivo = "correcao.json"

            mock_storage = MagicMock()
            mock_storage.listar_documentos = MagicMock(
                side_effect=lambda ativ_id, aluno_id=None: [mock_doc] if aluno_id else []
            )
            mock_storage.get_documento = MagicMock(return_value=mock_doc)
            mock_storage.resolver_caminho_documento = MagicMock(return_value=Path(temp_path))

            mock_visualizador = MagicMock()
            mock_visualizador.get_resultado_aluno = MagicMock(return_value=None)

            with patch("routes_resultados.visualizador", mock_visualizador), \
                 patch("routes_resultados.storage", mock_storage):
                from routes_resultados import get_resultado_aluno
                response = await get_resultado_aluno("ativ_test", "aluno_test")

            assert response.get("status") == "erro", \
                "Response should have status='erro' when doc has _erro_pipeline"
            assert "erro_pipeline" in response, \
                "Response should include erro_pipeline dict"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_partial_result_without_erro_no_status_erro(self):
        """Normal partial result should NOT have status=erro."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump({"nota": 8.5, "correcoes": []}, f)
            temp_path = f.name

        try:
            mock_doc = MagicMock()
            mock_doc.tipo = MagicMock()
            mock_doc.tipo.value = "correcao"
            mock_doc.id = "doc_ok"
            mock_doc.extensao = ".json"
            mock_doc.aluno_id = "aluno_test"
            mock_doc.nome_arquivo = "correcao.json"

            mock_storage = MagicMock()
            mock_storage.listar_documentos = MagicMock(
                side_effect=lambda ativ_id, aluno_id=None: [mock_doc] if aluno_id else []
            )
            mock_storage.get_documento = MagicMock(return_value=mock_doc)
            mock_storage.resolver_caminho_documento = MagicMock(return_value=Path(temp_path))

            mock_visualizador = MagicMock()
            mock_visualizador.get_resultado_aluno = MagicMock(return_value=None)

            with patch("routes_resultados.visualizador", mock_visualizador), \
                 patch("routes_resultados.storage", mock_storage):
                from routes_resultados import get_resultado_aluno
                response = await get_resultado_aluno("ativ_test", "aluno_test")

            assert response.get("status") != "erro", \
                "Normal partial result should NOT have status=erro"
        finally:
            os.unlink(temp_path)


# ============================================================
# F5-T2: Visualizador includes erro_pipeline in VisaoAluno
# ============================================================

class TestF5T2_VisualizadorPropagaErro:
    """F5-T2: Visualizador includes _erro_pipeline in VisaoAluno.to_dict()."""

    def test_correction_with_erro_pipeline_included_in_to_dict(self):
        """When correction JSON has _erro_pipeline, to_dict() should include erro_pipeline."""
        from visualizador import VisualizadorResultados
        from models import TipoDocumento

        vis = VisualizadorResultados()

        mock_atividade = MagicMock()
        mock_atividade.nome = "Prova 1"
        mock_atividade.nota_maxima = 10.0

        mock_aluno = MagicMock()
        mock_aluno.nome = "Joao"
        mock_aluno.id = "aluno_test"

        mock_correcao_doc = MagicMock()
        mock_correcao_doc.tipo = TipoDocumento.CORRECAO
        mock_correcao_doc.criado_em = None
        mock_correcao_doc.ia_provider = "test"

        vis.storage = MagicMock()
        vis.storage.get_atividade = MagicMock(return_value=mock_atividade)
        vis.storage.get_aluno = MagicMock(return_value=mock_aluno)
        vis.storage.listar_documentos = MagicMock(return_value=[mock_correcao_doc])

        erro_data = {
            "_erro_pipeline": {
                "tipo": "DOCUMENTO_FALTANTE",
                "mensagem": "Docs faltando",
                "severidade": "critico",
                "etapa": "corrigir",
                "timestamp": "2026-02-24T12:00:00"
            },
            "_documentos_faltantes": ["extracao_questoes.json"]
        }
        vis._ler_json = MagicMock(return_value=erro_data)

        resultado = vis.get_resultado_aluno("ativ_test", "aluno_test")

        assert resultado is not None, "Should return VisaoAluno even with error"
        resultado_dict = resultado.to_dict()
        assert "erro_pipeline" in resultado_dict, \
            "to_dict() should include erro_pipeline when correction has error"

    def test_normal_correction_no_erro_pipeline_in_to_dict(self):
        """Normal correction should NOT have erro_pipeline in to_dict()."""
        from visualizador import VisualizadorResultados
        from models import TipoDocumento

        vis = VisualizadorResultados()

        mock_atividade = MagicMock()
        mock_atividade.nome = "Prova 1"
        mock_atividade.nota_maxima = 10.0

        mock_aluno = MagicMock()
        mock_aluno.nome = "Maria"
        mock_aluno.id = "aluno_test"

        mock_correcao_doc = MagicMock()
        mock_correcao_doc.tipo = TipoDocumento.CORRECAO
        mock_correcao_doc.criado_em = None
        mock_correcao_doc.ia_provider = "test"

        vis.storage = MagicMock()
        vis.storage.get_atividade = MagicMock(return_value=mock_atividade)
        vis.storage.get_aluno = MagicMock(return_value=mock_aluno)
        vis.storage.listar_documentos = MagicMock(return_value=[mock_correcao_doc])

        vis._ler_json = MagicMock(return_value={"nota": 8.5, "feedback": "Bom"})

        resultado = vis.get_resultado_aluno("ativ_test", "aluno_test")

        assert resultado is not None
        resultado_dict = resultado.to_dict()
        assert "erro_pipeline" not in resultado_dict, \
            "Normal result should NOT have erro_pipeline"
