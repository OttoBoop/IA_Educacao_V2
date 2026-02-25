"""
Tests for F8-T5: _salvar_resultado() must fail when narrative field is absent or empty.

Verifica que stages analíticos (CORRIGIR, ANALISAR_HABILIDADES, GERAR_RELATORIO)
falham com ValueError se o campo narrativo estiver ausente ou vazio em resposta_parsed.

O campo de cada stage:
- CORRIGIR            → narrativa_correcao
- ANALISAR_HABILIDADES → narrativa_habilidades
- GERAR_RELATORIO     → relatorio_narrativo

Stages de extração (EXTRAIR_QUESTOES, EXTRAIR_GABARITO, EXTRAIR_RESPOSTAS)
não têm campo narrativo obrigatório e NÃO devem ser afetados.

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Task: F8-T5
"""

import pytest
from unittest.mock import MagicMock


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def executor_com_mock_storage():
    """PipelineExecutor com storage mockado para testes de validação."""
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None
    return executor


# ============================================================
# F8-T5: Validação de narrativa vazia para stages analíticos
# ============================================================

class TestValidacaoNarrativaVazia:
    """
    F8-T5: _salvar_resultado() deve levantar ValueError se narrativa ausente ou vazia.

    Isso garante que o stage falha de forma explícita e observável em vez de
    silenciosamente omitir o documento narrativo quando o campo está ausente.
    """

    async def test_corrigir_falha_se_narrativa_correcao_ausente(
        self, executor_com_mock_storage
    ):
        """CORRIGIR deve falhar com ValueError se resposta_parsed não tem narrativa_correcao."""
        from prompts import EtapaProcessamento

        resposta_sem_narrativa = {
            "nota": 7.5,
            "questoes": [{"numero": 1, "nota": 2.5, "feedback": "Correto"}],
            # narrativa_correcao AUSENTE intencionalmente
        }

        with pytest.raises(ValueError, match="narrativa"):
            await executor_com_mock_storage._salvar_resultado(
                etapa=EtapaProcessamento.CORRIGIR,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
                resposta_raw='{"nota": 7.5}',
                resposta_parsed=resposta_sem_narrativa,
                provider="openai",
                modelo="gpt-4o",
                prompt_id="default_corrigir",
                tokens=1500,
                tempo_ms=3000.0,
                gerar_formatos_extras=False,
            )

    async def test_corrigir_falha_se_narrativa_correcao_string_vazia(
        self, executor_com_mock_storage
    ):
        """CORRIGIR deve falhar com ValueError se narrativa_correcao é string vazia."""
        from prompts import EtapaProcessamento

        resposta_narrativa_vazia = {
            "nota": 7.5,
            "narrativa_correcao": "",  # STRING VAZIA — não é um Markdown válido
        }

        with pytest.raises(ValueError, match="narrativa"):
            await executor_com_mock_storage._salvar_resultado(
                etapa=EtapaProcessamento.CORRIGIR,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
                resposta_raw='{"nota": 7.5}',
                resposta_parsed=resposta_narrativa_vazia,
                provider="openai",
                modelo="gpt-4o",
                prompt_id="default_corrigir",
                tokens=1500,
                tempo_ms=3000.0,
                gerar_formatos_extras=False,
            )

    async def test_analisar_habilidades_falha_se_narrativa_habilidades_ausente(
        self, executor_com_mock_storage
    ):
        """ANALISAR_HABILIDADES deve falhar se narrativa_habilidades está ausente."""
        from prompts import EtapaProcessamento

        resposta_sem_narrativa = {
            "habilidades_demonstradas": ["Interpretação de texto"],
            "habilidades_faltantes": ["Geometria"],
            # narrativa_habilidades AUSENTE
        }

        with pytest.raises(ValueError, match="narrativa"):
            await executor_com_mock_storage._salvar_resultado(
                etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
                resposta_raw='{}',
                resposta_parsed=resposta_sem_narrativa,
                provider="openai",
                modelo="gpt-4o",
                prompt_id="default_analisar_habilidades",
                tokens=1200,
                tempo_ms=2500.0,
                gerar_formatos_extras=False,
            )

    async def test_gerar_relatorio_falha_se_relatorio_narrativo_ausente(
        self, executor_com_mock_storage
    ):
        """GERAR_RELATORIO deve falhar se relatorio_narrativo está ausente."""
        from prompts import EtapaProcessamento

        resposta_sem_narrativa = {
            "nota_final": 7.5,
            "resumo": "Desempenho satisfatório.",
            "materia": "Matemática",
            # relatorio_narrativo AUSENTE
        }

        with pytest.raises(ValueError, match="narrativa"):
            await executor_com_mock_storage._salvar_resultado(
                etapa=EtapaProcessamento.GERAR_RELATORIO,
                atividade_id="ativ-001",
                aluno_id="aluno-001",
                resposta_raw='{"nota_final": 7.5}',
                resposta_parsed=resposta_sem_narrativa,
                provider="openai",
                modelo="gpt-4o",
                prompt_id="default_gerar_relatorio",
                tokens=2000,
                tempo_ms=4000.0,
                gerar_formatos_extras=False,
            )

    async def test_extrair_questoes_nao_afetado_por_validacao(
        self, executor_com_mock_storage
    ):
        """EXTRAIR_QUESTOES não tem campo narrativo obrigatório — não deve falhar."""
        from prompts import EtapaProcessamento

        resposta_extracao = {
            "questoes": [{"numero": 1, "enunciado": "Qual é a fórmula da água?"}],
            # Sem nenhum campo narrativo — correto para stages de extração
        }

        doc = MagicMock()
        doc.id = "doc-extracao-001"
        executor_com_mock_storage.storage.salvar_documento.return_value = doc

        # Não deve levantar ValueError
        result = await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{}',
            resposta_parsed=resposta_extracao,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_extrair_questoes",
            tokens=500,
            tempo_ms=1000.0,
            gerar_formatos_extras=False,
        )

        assert result is not None, (
            "EXTRAIR_QUESTOES deve retornar o documento_id normalmente. "
            "Stages de extração não têm campo narrativo e não devem ser afetados."
        )
