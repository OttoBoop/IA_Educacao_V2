"""Desempenho de matéria must not fake cross-turma evidence."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def get_text(self):
        return self._text


class _FakePdf:
    def __init__(self, text: str):
        self._pages = [_FakePage(text)]

    def __iter__(self):
        return iter(self._pages)

    def close(self):
        pass


def _doc(aluno_id: str):
    from models import TipoDocumento

    doc = MagicMock()
    doc.tipo = TipoDocumento.RELATORIO_FINAL
    doc.aluno_id = aluno_id
    return doc


def _executor():
    from executor import PipelineExecutor

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.executar_com_tools = AsyncMock()
    return executor


@pytest.mark.asyncio
async def test_desempenho_materia_blocks_when_only_one_turma_has_results(monkeypatch):
    import executor as executor_module

    executor = _executor()
    turma_a = MagicMock(id="turma-a", nome="Turma A")
    turma_b = MagicMock(id="turma-b", nome="Turma B")
    executor.storage.listar_turmas.return_value = [turma_a, turma_b]
    executor.storage.listar_alunos.return_value = []

    atividades = {
        "turma-a": [MagicMock(id="atividade-a", nome="Prova A")],
        "turma-b": [MagicMock(id="atividade-b", nome="Prova B")],
    }
    documentos = {
        "atividade-a": [_doc("aluno-1"), _doc("aluno-2")],
        "atividade-b": [],
    }

    executor.storage.listar_atividades.side_effect = lambda turma_id: atividades[turma_id]
    executor.storage.listar_documentos.side_effect = (
        lambda atividade_id, tipo=None: documentos[atividade_id]
    )
    executor.storage.resolver_caminho_documento.return_value = Path("/fake/relatorio.pdf")
    monkeypatch.setattr(
        executor_module.fitz,
        "open",
        lambda path: _FakePdf("Relatorio final legivel."),
    )

    result = await executor.gerar_relatorio_desempenho_materia("materia-1")

    assert result["sucesso"] is False
    assert result["status"] == "BLOQUEADO_PREREQUISITO"
    assert "2 turmas distintas" in result["erro"]
    assert result["cobertura"]["turma-a"]["narrativas"] == 2
    assert result["cobertura"]["turma-b"]["narrativas"] == 0
    executor.executar_com_tools.assert_not_called()


@pytest.mark.asyncio
async def test_desempenho_materia_runs_when_two_distinct_turmas_have_results(monkeypatch):
    import executor as executor_module
    from executor import ResultadoExecucao

    executor = _executor()
    turma_a = MagicMock(id="turma-a", nome="9 Ano")
    turma_b = MagicMock(id="turma-b", nome="9 Ano")
    executor.storage.listar_turmas.return_value = [turma_a, turma_b]
    executor.storage.listar_alunos.return_value = []
    executor.storage.get_materia.return_value = MagicMock(id="materia-1", nome="Matematica")

    atividades = {
        "turma-a": [MagicMock(id="atividade-a", nome="Prova A")],
        "turma-b": [MagicMock(id="atividade-b", nome="Prova B")],
    }
    documentos = {
        "atividade-a": [_doc("aluno-1")],
        "atividade-b": [_doc("aluno-2")],
    }

    executor.storage.listar_atividades.side_effect = lambda turma_id: atividades[turma_id]
    executor.storage.listar_documentos.side_effect = (
        lambda atividade_id, tipo=None: documentos[atividade_id]
    )
    executor.storage.resolver_caminho_documento.return_value = Path("/fake/relatorio.pdf")
    monkeypatch.setattr(
        executor_module.fitz,
        "open",
        lambda path: _FakePdf("Relatorio final legivel."),
    )

    prompt = MagicMock(id="prompt-desempenho-materia")
    prompt.render.return_value = "prompt"
    prompt.render_sistema.return_value = "system"
    executor.prompt_manager.get_prompt_padrao.return_value = prompt
    executor.executar_com_tools.return_value = ResultadoExecucao(
        sucesso=True,
        etapa="relatorio_desempenho_materia",
        alertas=[],
    )

    result = await executor.gerar_relatorio_desempenho_materia("materia-1")

    assert result["sucesso"] is True
    assert result["status"] == "COMPLETO"
    assert result["cobertura"]["turma-a"]["narrativas"] == 1
    assert result["cobertura"]["turma-b"]["narrativas"] == 1
    executor.executar_com_tools.assert_awaited_once()
