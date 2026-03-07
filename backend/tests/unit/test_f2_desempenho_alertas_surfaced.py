"""
F2-T3: Tests that desempenho methods surface alertas from executar_com_tools().

The bug: executar_com_tools() generates alertas (dual-output warnings,
max_iterations warnings) but the desempenho methods don't include them
in their return dict. Callers can't see if PDF/JSON was incomplete.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f2_desempenho_alertas_surfaced.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, ResultadoExecucao, EtapaProcessamento


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def executor_com_mock():
    """PipelineExecutor with mocked storage and prompt_manager."""
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None
    return executor


def _mock_successful_resultado(alertas=None):
    """Build a ResultadoExecucao that simulates a successful tool execution."""
    return ResultadoExecucao(
        sucesso=True,
        etapa="tools",
        resposta_raw='{"alunos": [{"nome": "Ana"}]}',
        provider="openai",
        modelo="gpt-4o",
        tokens_entrada=500,
        tempo_ms=1200,
        alertas=alertas or [],
    )


# ============================================================
# F2-T3: Desempenho methods must surface alertas
# ============================================================

class TestDesempenhoAlertasSurfaced:
    """Desempenho methods must include alertas from executar_com_tools()
    in their return dict so callers can detect incomplete output."""

    @pytest.mark.asyncio
    async def test_tarefa_surfaces_alertas(self, executor_com_mock):
        """gerar_relatorio_desempenho_tarefa must include alertas in return dict."""
        from models import TipoDocumento

        alertas = [
            {"tipo": "aviso", "mensagem": "Saída parcial: PDF (execute_python_code) ausente após retry."},
            {"tipo": "info", "mensagem": "Documentos gerados: ['desempenho.json']"},
        ]
        mock_resultado = _mock_successful_resultado(alertas=alertas)

        # Setup: 2 students with RELATORIO_FINAL docs
        doc1 = MagicMock()
        doc1.tipo = TipoDocumento.RELATORIO_FINAL
        doc1.aluno_id = "aluno-001"
        doc2 = MagicMock()
        doc2.tipo = TipoDocumento.RELATORIO_FINAL
        doc2.aluno_id = "aluno-002"
        executor_com_mock.storage.listar_documentos.return_value = [doc1, doc2]
        # resolver_caminho_documento returns a fake path for open()
        executor_com_mock.storage.resolver_caminho_documento.return_value = "/fake/path.json"

        # Mock atividade/turma/materia lookups
        atividade = MagicMock()
        atividade.nome = "Prova 1"
        atividade.turma_id = "turma-001"
        executor_com_mock.storage.get_atividade.return_value = atividade
        turma = MagicMock()
        turma.nome = "Turma A"
        turma.materia_id = "mat-001"
        executor_com_mock.storage.get_turma.return_value = turma
        materia = MagicMock()
        materia.nome = "Matemática"
        materia.id = "mat-001"
        executor_com_mock.storage.get_materia.return_value = materia

        # Mock prompt
        prompt = MagicMock()
        prompt.id = "prompt-001"
        prompt.render.return_value = "Gere o relatório"
        prompt.render_sistema.return_value = "System prompt"
        executor_com_mock.prompt_manager.get_prompt_padrao.return_value = prompt

        # Mock _salvar_resultado
        executor_com_mock._salvar_resultado = AsyncMock()

        # Mock executar_com_tools to return our resultado with alertas
        executor_com_mock.executar_com_tools = AsyncMock(return_value=mock_resultado)

        # Mock file open for reading narrative files
        m_open = mock_open(read_data='{"resumo": "bom aluno"}')
        with patch("builtins.open", m_open):
            result = await executor_com_mock.gerar_relatorio_desempenho_tarefa(
                atividade_id="ativ-001",
            )

        assert "alertas" in result, (
            "gerar_relatorio_desempenho_tarefa must include 'alertas' in return dict. "
            f"Got keys: {list(result.keys())}"
        )
        assert len(result["alertas"]) == 2, (
            f"Expected 2 alertas, got {len(result['alertas'])}: {result['alertas']}"
        )
        assert any("parcial" in a.get("mensagem", "").lower() for a in result["alertas"]), (
            "Alertas must include the partial output warning"
        )
