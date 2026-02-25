"""
Integration tests for dual-file save behavior in PipelineExecutor (F8-T1/T2/T3).

Tests the WIRING between executor._salvar_resultado() and storage.salvar_documento():
- CORRIGIR stage saves 2 docs: CORRECAO (JSON) + CORRECAO_NARRATIVA (Markdown)
- ANALISAR_HABILIDADES saves 2 docs: ANALISE_HABILIDADES + ANALISE_HABILIDADES_NARRATIVA
- GERAR_RELATORIO saves 2 docs: RELATORIO_FINAL + RELATORIO_NARRATIVO

These are RED phase tests — _salvar_resultado() currently only saves 1 document.
The implementation (F8-T4) will extend it to extract and save the narrative field separately.

Related plan: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Tasks: F8-T1 (CORRIGIR), F8-T2 (ANALISAR_HABILIDADES), F8-T3 (GERAR_RELATORIO)
"""

import pytest
import json
from unittest.mock import MagicMock


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def mock_storage():
    """Mock storage that tracks salvar_documento calls."""
    mock = MagicMock()
    doc = MagicMock()
    doc.id = "doc-test-123"
    mock.salvar_documento.return_value = doc
    return mock


@pytest.fixture
def executor_com_mock_storage(mock_storage):
    """PipelineExecutor instance with storage replaced by mock.

    Uses __new__ to bypass __init__ (which reads global storage/providers),
    then injects the mock storage directly.
    """
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = mock_storage
    executor.prompt_manager = MagicMock()
    executor.preparador = None
    return executor


def _make_capture_salvar(saved_files):
    """Factory for a side_effect function that captures salvar_documento call arguments.

    Reads the temp file content before it can be deleted, supporting both
    JSON (for technical documents) and Markdown (for narrative documents).
    """
    def capture_salvar(arquivo_origem, tipo, **kwargs):
        with open(arquivo_origem, encoding="utf-8") as f:
            raw = f.read()
        try:
            content = json.loads(raw)
        except json.JSONDecodeError:
            content = raw  # Markdown file — store as plain string
        saved_files.append({"tipo": tipo, "content": content})
        doc = MagicMock()
        doc.id = f"doc-{tipo.value}"
        return doc
    return capture_salvar


# ============================================================
# F8-T1: CORRIGIR dual-file save
# ============================================================

class TestDualFileSaveCorrigir:
    """
    F8-T1: CORRIGIR stage must save 2 documents when narrativa_correcao is present.

    After F8-T4 implementation, _salvar_resultado() must:
    1. Extract narrativa_correcao from resposta_parsed
    2. Save JSON (without narrativa_correcao) as TipoDocumento.CORRECAO
    3. Save narrativa_correcao Markdown as TipoDocumento.CORRECAO_NARRATIVA
    """

    @pytest.fixture
    def resposta_corrigir_com_narrativa(self):
        """Parsed response from CORRIGIR stage with narrativa_correcao field."""
        return {
            "nota": 7.5,
            "questoes": [
                {
                    "numero": 1,
                    "nota": 2.5,
                    "feedback": "Correto",
                    "correcao_detalhada": "Solução correta e completa."
                }
            ],
            "narrativa_correcao": (
                "## Análise Pedagógica\n\n"
                "O aluno demonstrou compreensão parcial dos conceitos. "
                "Na questão 1, a resposta revela raciocínio lógico adequado, "
                "mas imprecisão no vocabulário técnico. Há potencial para "
                "desenvolvimento com prática direcionada."
            )
        }

    async def test_corrigir_chama_salvar_documento_duas_vezes(
        self, executor_com_mock_storage, mock_storage, resposta_corrigir_com_narrativa
    ):
        """_salvar_resultado() deve chamar storage.salvar_documento() 2x para CORRIGIR.

        Uma chamada para o JSON técnico (CORRECAO) e outra para o
        Markdown narrativo (CORRECAO_NARRATIVA).
        """
        from prompts import EtapaProcessamento

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"nota": 7.5}',
            resposta_parsed=resposta_corrigir_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_corrigir",
            tokens=1500,
            tempo_ms=3000.0,
            gerar_formatos_extras=False,
        )

        assert mock_storage.salvar_documento.call_count == 2, (
            f"Esperava 2 chamadas a salvar_documento (JSON técnico + Markdown narrativo), "
            f"mas houve {mock_storage.salvar_documento.call_count}. "
            "Implementar dual-file save em _salvar_resultado() (F8-T4)."
        )

    async def test_corrigir_salva_narrativa_como_correcao_narrativa(
        self, executor_com_mock_storage, mock_storage, resposta_corrigir_com_narrativa
    ):
        """Uma das chamadas a salvar_documento deve usar TipoDocumento.CORRECAO_NARRATIVA."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"nota": 7.5}',
            resposta_parsed=resposta_corrigir_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_corrigir",
            tokens=1500,
            tempo_ms=3000.0,
            gerar_formatos_extras=False,
        )

        tipos_usados = [
            call_args.kwargs.get("tipo") or call_args.args[1]
            for call_args in mock_storage.salvar_documento.call_args_list
        ]
        assert TipoDocumento.CORRECAO_NARRATIVA in tipos_usados, (
            f"TipoDocumento.CORRECAO_NARRATIVA não foi usado em nenhuma chamada. "
            f"Tipos usados: {tipos_usados}. "
            "O executor deve salvar o Markdown narrativo com CORRECAO_NARRATIVA."
        )

    async def test_corrigir_json_salvo_sem_campo_narrativa_correcao(
        self, executor_com_mock_storage, mock_storage, resposta_corrigir_com_narrativa
    ):
        """O JSON técnico (CORRECAO) não deve conter o campo narrativa_correcao."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        saved_files = []
        mock_storage.salvar_documento.side_effect = _make_capture_salvar(saved_files)

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"nota": 7.5}',
            resposta_parsed=resposta_corrigir_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_corrigir",
            tokens=1500,
            tempo_ms=3000.0,
            gerar_formatos_extras=False,
        )

        json_doc = next(
            (f for f in saved_files if f["tipo"] == TipoDocumento.CORRECAO), None
        )
        assert json_doc is not None, "Documento CORRECAO não foi salvo"
        assert "narrativa_correcao" not in json_doc["content"], (
            "O JSON técnico CORRECAO não deve conter narrativa_correcao. "
            "O campo narrativo deve ser extraído e salvo separadamente como Markdown."
        )


# ============================================================
# F8-T2: ANALISAR_HABILIDADES dual-file save
# ============================================================

class TestDualFileSaveAnalisarHabilidades:
    """
    F8-T2: ANALISAR_HABILIDADES stage must save 2 documents when narrativa_habilidades present.

    After F8-T4 implementation, _salvar_resultado() must:
    1. Extract narrativa_habilidades from resposta_parsed
    2. Save JSON (without narrativa_habilidades) as TipoDocumento.ANALISE_HABILIDADES
    3. Save narrativa_habilidades Markdown as TipoDocumento.ANALISE_HABILIDADES_NARRATIVA
    """

    @pytest.fixture
    def resposta_analisar_com_narrativa(self):
        """Parsed response from ANALISAR_HABILIDADES stage with narrativa_habilidades field."""
        return {
            "habilidades_demonstradas": ["Interpretação de texto", "Cálculo algébrico"],
            "habilidades_faltantes": ["Resolução de problemas geométricos"],
            "pontos_fortes": ["Boa base conceitual"],
            "areas_atencao": ["Geometria espacial"],
            "narrativa_habilidades": (
                "## Síntese de Padrões de Aprendizado\n\n"
                "O aluno apresenta consistência em habilidades analíticas, "
                "mas demonstra lacunas em raciocínio espacial. "
                "O esforço é evidente nas respostas dissertativas, "
                "sugerindo comprometimento com o aprendizado."
            )
        }

    async def test_analisar_habilidades_chama_salvar_documento_duas_vezes(
        self, executor_com_mock_storage, mock_storage, resposta_analisar_com_narrativa
    ):
        """_salvar_resultado() deve chamar storage.salvar_documento() 2x para ANALISAR_HABILIDADES."""
        from prompts import EtapaProcessamento

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"habilidades_demonstradas": []}',
            resposta_parsed=resposta_analisar_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_analisar_habilidades",
            tokens=1200,
            tempo_ms=2500.0,
            gerar_formatos_extras=False,
        )

        assert mock_storage.salvar_documento.call_count == 2, (
            f"Esperava 2 chamadas a salvar_documento, "
            f"houve {mock_storage.salvar_documento.call_count}. "
            "ANALISAR_HABILIDADES deve salvar JSON técnico + Markdown de síntese."
        )

    async def test_analisar_habilidades_usa_tipo_analise_narrativa(
        self, executor_com_mock_storage, mock_storage, resposta_analisar_com_narrativa
    ):
        """Uma das chamadas deve usar TipoDocumento.ANALISE_HABILIDADES_NARRATIVA."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"habilidades_demonstradas": []}',
            resposta_parsed=resposta_analisar_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_analisar_habilidades",
            tokens=1200,
            tempo_ms=2500.0,
            gerar_formatos_extras=False,
        )

        tipos_usados = [
            call_args.kwargs.get("tipo") or call_args.args[1]
            for call_args in mock_storage.salvar_documento.call_args_list
        ]
        assert TipoDocumento.ANALISE_HABILIDADES_NARRATIVA in tipos_usados, (
            f"ANALISE_HABILIDADES_NARRATIVA não usado. Tipos usados: {tipos_usados}"
        )

    async def test_analisar_habilidades_json_sem_narrativa_habilidades(
        self, executor_com_mock_storage, mock_storage, resposta_analisar_com_narrativa
    ):
        """O JSON técnico (ANALISE_HABILIDADES) não deve conter narrativa_habilidades."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        saved_files = []
        mock_storage.salvar_documento.side_effect = _make_capture_salvar(saved_files)

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{}',
            resposta_parsed=resposta_analisar_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_analisar_habilidades",
            tokens=1200,
            tempo_ms=2500.0,
            gerar_formatos_extras=False,
        )

        json_doc = next(
            (f for f in saved_files if f["tipo"] == TipoDocumento.ANALISE_HABILIDADES), None
        )
        assert json_doc is not None, "Documento ANALISE_HABILIDADES não foi salvo"
        assert "narrativa_habilidades" not in json_doc["content"], (
            "O JSON técnico não deve conter narrativa_habilidades. "
            "Deve ser extraído e salvo separadamente como Markdown."
        )


# ============================================================
# F8-T3: GERAR_RELATORIO dual-file save
# ============================================================

class TestDualFileSaveGerarRelatorio:
    """
    F8-T3: GERAR_RELATORIO stage must save 2 documents when relatorio_narrativo is present.

    After F8-T4 implementation, _salvar_resultado() must:
    1. Extract relatorio_narrativo from resposta_parsed
    2. Save JSON (without relatorio_narrativo) as TipoDocumento.RELATORIO_FINAL
    3. Save relatorio_narrativo Markdown as TipoDocumento.RELATORIO_NARRATIVO
    """

    @pytest.fixture
    def resposta_relatorio_com_narrativa(self):
        """Parsed response from GERAR_RELATORIO stage with relatorio_narrativo field."""
        return {
            "nota_final": 7.5,
            "resumo": "Desempenho satisfatório na avaliação bimestral.",
            "materia": "Matemática",
            "atividade": "Prova Bimestral 1",
            "relatorio_narrativo": (
                "## Relatório de Desempenho — João Silva\n\n"
                "João demonstrou sólida compreensão dos conceitos fundamentais. "
                "Com nota 7.5, o aluno atingiu os objetivos mínimos esperados, "
                "mas tem potencial para desenvolvimento em geometria espacial. "
                "Recomenda-se atividades complementares com foco em visualização 3D."
            )
        }

    async def test_gerar_relatorio_chama_salvar_documento_duas_vezes(
        self, executor_com_mock_storage, mock_storage, resposta_relatorio_com_narrativa
    ):
        """_salvar_resultado() deve chamar storage.salvar_documento() 2x para GERAR_RELATORIO."""
        from prompts import EtapaProcessamento

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.GERAR_RELATORIO,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"nota_final": 7.5}',
            resposta_parsed=resposta_relatorio_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_gerar_relatorio",
            tokens=2000,
            tempo_ms=4000.0,
            gerar_formatos_extras=False,
        )

        assert mock_storage.salvar_documento.call_count == 2, (
            f"Esperava 2 chamadas a salvar_documento, "
            f"houve {mock_storage.salvar_documento.call_count}. "
            "GERAR_RELATORIO deve salvar JSON técnico + Markdown do relatório holístico."
        )

    async def test_gerar_relatorio_usa_tipo_relatorio_narrativo(
        self, executor_com_mock_storage, mock_storage, resposta_relatorio_com_narrativa
    ):
        """Uma das chamadas deve usar TipoDocumento.RELATORIO_NARRATIVO."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.GERAR_RELATORIO,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{"nota_final": 7.5}',
            resposta_parsed=resposta_relatorio_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_gerar_relatorio",
            tokens=2000,
            tempo_ms=4000.0,
            gerar_formatos_extras=False,
        )

        tipos_usados = [
            call_args.kwargs.get("tipo") or call_args.args[1]
            for call_args in mock_storage.salvar_documento.call_args_list
        ]
        assert TipoDocumento.RELATORIO_NARRATIVO in tipos_usados, (
            f"RELATORIO_NARRATIVO não usado. Tipos usados: {tipos_usados}"
        )

    async def test_gerar_relatorio_json_sem_relatorio_narrativo(
        self, executor_com_mock_storage, mock_storage, resposta_relatorio_com_narrativa
    ):
        """O JSON técnico (RELATORIO_FINAL) não deve conter relatorio_narrativo."""
        from prompts import EtapaProcessamento
        from models import TipoDocumento

        saved_files = []
        mock_storage.salvar_documento.side_effect = _make_capture_salvar(saved_files)

        await executor_com_mock_storage._salvar_resultado(
            etapa=EtapaProcessamento.GERAR_RELATORIO,
            atividade_id="ativ-001",
            aluno_id="aluno-001",
            resposta_raw='{}',
            resposta_parsed=resposta_relatorio_com_narrativa,
            provider="openai",
            modelo="gpt-4o",
            prompt_id="default_gerar_relatorio",
            tokens=2000,
            tempo_ms=4000.0,
            gerar_formatos_extras=False,
        )

        json_doc = next(
            (f for f in saved_files if f["tipo"] == TipoDocumento.RELATORIO_FINAL), None
        )
        assert json_doc is not None, "Documento RELATORIO_FINAL não foi salvo"
        assert "relatorio_narrativo" not in json_doc["content"], (
            "O JSON técnico não deve conter relatorio_narrativo. "
            "Deve ser extraído e salvo separadamente como Markdown."
        )
