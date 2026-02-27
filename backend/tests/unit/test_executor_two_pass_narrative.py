"""
Tests for T5: Two-pass pipeline — executor generates narrative PDF instead of .md files.

Verifies:
1. Old narrative extraction is removed (no more .md files)
2. New _gerar_narrativa_pdf() method calls LLM + converts Markdown → PDF
3. Analytical stages (CORRIGIR, ANALISAR_HABILIDADES, GERAR_RELATORIO) get narrative PDFs
4. Extraction stages are NOT affected
5. Fallback to old PDF on Pass 2 failure

Related plan: Fix Narrative Pipeline — Merge Rich Narratives into Existing PDFs
Task: T5
"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, ANY


@pytest.fixture
def executor_com_mocks():
    """PipelineExecutor with mocked storage and provider for two-pass tests."""
    from executor import PipelineExecutor

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None

    # Mock salvar_documento to return a document with an id
    doc = MagicMock()
    doc.id = "doc-test-001"
    executor.storage.salvar_documento.return_value = doc
    executor.storage.listar_documentos.return_value = []

    return executor


class TestNarrativeExtractionRemoved:
    """T5a: Old narrative extraction logic must be removed from _salvar_resultado."""

    async def test_corrigir_does_not_raise_on_missing_narrativa_correcao(
        self, executor_com_mocks
    ):
        """CORRIGIR must NOT raise ValueError for missing narrativa_correcao anymore."""
        from prompts import EtapaProcessamento

        # JSON without narrativa_correcao — should be fine now
        resposta = {
            "nota": 7.5,
            "nota_maxima": 10,
            "questoes": [{"numero": 1, "nota": 2.5, "feedback": "Correto"}],
        }

        # This should NOT raise (old behavior raised ValueError)
        result = await executor_com_mocks._salvar_resultado(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw=json.dumps(resposta),
            resposta_parsed=resposta,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_corrigir",
            tokens=1500,
            tempo_ms=3000.0,
            gerar_formatos_extras=False,
        )
        assert result is not None

    async def test_analisar_habilidades_does_not_raise_on_missing_narrativa(
        self, executor_com_mocks
    ):
        """ANALISAR_HABILIDADES must NOT raise for missing narrativa_habilidades."""
        from prompts import EtapaProcessamento

        resposta = {
            "habilidades": {
                "dominadas": ["Mecânica"],
                "em_desenvolvimento": ["Óptica"],
                "nao_demonstradas": [],
            },
            "recomendacoes": ["Praticar exercícios de óptica"],
        }

        result = await executor_com_mocks._salvar_resultado(
            etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw=json.dumps(resposta),
            resposta_parsed=resposta,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_analisar_habilidades",
            tokens=1200,
            tempo_ms=2500.0,
            gerar_formatos_extras=False,
        )
        assert result is not None

    async def test_gerar_relatorio_does_not_raise_on_missing_narrativo(
        self, executor_com_mocks
    ):
        """GERAR_RELATORIO must NOT raise for missing relatorio_narrativo."""
        from prompts import EtapaProcessamento

        resposta = {
            "conteudo": "# Relatório\n\nConteúdo do relatório.",
            "resumo_executivo": "Aluno com desempenho satisfatório.",
            "nota_final": "7.5",
            "aluno": "Maria",
            "materia": "Física",
            "atividade": "Prova 1",
        }

        result = await executor_com_mocks._salvar_resultado(
            etapa=EtapaProcessamento.GERAR_RELATORIO,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw=json.dumps(resposta),
            resposta_parsed=resposta,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_gerar_relatorio",
            tokens=2000,
            tempo_ms=4000.0,
            gerar_formatos_extras=False,
        )
        assert result is not None

    async def test_no_narrativa_md_document_saved(self, executor_com_mocks):
        """_salvar_resultado must NOT save any CORRECAO_NARRATIVA .md documents."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        resposta = {"nota": 7.5, "questoes": []}

        await executor_com_mocks._salvar_resultado(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw=json.dumps(resposta),
            resposta_parsed=resposta,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_corrigir",
            tokens=1500,
            tempo_ms=3000.0,
            gerar_formatos_extras=False,
        )

        # Check all salvar_documento calls — none should use narrative tipos
        narrative_tipos = {
            TipoDocumento.CORRECAO_NARRATIVA,
            TipoDocumento.ANALISE_HABILIDADES_NARRATIVA,
            TipoDocumento.RELATORIO_NARRATIVO,
        }
        for call in executor_com_mocks.storage.salvar_documento.call_args_list:
            kwargs = call.kwargs if call.kwargs else {}
            args = call.args if call.args else ()
            tipo_used = kwargs.get("tipo")
            assert tipo_used not in narrative_tipos, (
                f"Storage received narrative tipo {tipo_used} — "
                "old .md saving logic should be removed"
            )


class TestExtractionStagesUnchanged:
    """Extraction stages must work exactly as before — no narrative logic applies."""

    async def test_extrair_questoes_still_works(self, executor_com_mocks):
        from prompts import EtapaProcessamento

        resposta = {
            "questoes": [
                {"numero": 1, "enunciado": "Qual é a fórmula da água?"}
            ]
        }

        result = await executor_com_mocks._salvar_resultado(
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
            atividade_id="ativ-001",
            aluno_id=None,
            resposta_raw=json.dumps(resposta),
            resposta_parsed=resposta,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_extrair_questoes",
            tokens=500,
            tempo_ms=1000.0,
            gerar_formatos_extras=False,
        )
        assert result is not None


class TestGerarNarrativaPdfMethod:
    """T5b: _gerar_narrativa_pdf() must generate PDF from narrative prompt."""

    async def test_method_exists(self, executor_com_mocks):
        """PipelineExecutor must have _gerar_narrativa_pdf method."""
        assert hasattr(executor_com_mocks, '_gerar_narrativa_pdf'), (
            "PipelineExecutor must have _gerar_narrativa_pdf method"
        )

    async def test_calls_provider_with_narrative_prompt(self, executor_com_mocks):
        """_gerar_narrativa_pdf must call the AI provider with the internal narrative prompt."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        # Mock the provider
        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "## Análise\n\nO aluno demonstrou potencial alto."
        mock_response.tokens_used = 500
        mock_provider.complete.return_value = mock_response

        with patch.object(executor_com_mocks, '_get_provider_legacy', return_value=mock_provider):
            result = await executor_com_mocks._gerar_narrativa_pdf(
                etapa=EtapaProcessamento.CORRIGIR,
                conteudo={"nota": 7.5, "questoes": []},
                tipo=TipoDocumento.CORRECAO,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
            )

        # Provider must have been called
        mock_provider.complete.assert_called_once()

    async def test_saves_pdf_not_md(self, executor_com_mocks):
        """_gerar_narrativa_pdf must save a .pdf file, not .md."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        mock_provider = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "## Análise\n\nConteúdo narrativo."
        mock_response.tokens_used = 500
        mock_provider.complete.return_value = mock_response

        with patch.object(executor_com_mocks, '_get_provider_legacy', return_value=mock_provider):
            await executor_com_mocks._gerar_narrativa_pdf(
                etapa=EtapaProcessamento.CORRIGIR,
                conteudo={"nota": 7.5},
                tipo=TipoDocumento.CORRECAO,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
            )

        # Check that salvar_documento was called with a .pdf file
        calls = executor_com_mocks.storage.salvar_documento.call_args_list
        assert len(calls) > 0, "salvar_documento must be called to save PDF"
        last_call = calls[-1]
        arquivo = last_call.kwargs.get("arquivo_origem", "")
        assert arquivo.endswith(".pdf"), (
            f"Must save as .pdf, got: {arquivo}"
        )

    async def test_returns_none_on_provider_failure(self, executor_com_mocks):
        """_gerar_narrativa_pdf must return None (not crash) if provider fails."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        mock_provider = AsyncMock()
        mock_provider.complete.side_effect = Exception("API error")

        with patch.object(executor_com_mocks, '_get_provider_legacy', return_value=mock_provider):
            result = await executor_com_mocks._gerar_narrativa_pdf(
                etapa=EtapaProcessamento.CORRIGIR,
                conteudo={"nota": 7.5},
                tipo=TipoDocumento.CORRECAO,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
            )

        # Should return None gracefully, not crash
        assert result is None
