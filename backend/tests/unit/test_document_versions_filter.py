import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import routes_prompts
from models import TipoDocumento


def _doc(doc_id, tipo, aluno_id=None, nome=None):
    return SimpleNamespace(
        id=doc_id,
        tipo=tipo,
        aluno_id=aluno_id,
        versao=1,
        ia_modelo=None,
        ia_provider=None,
        nome_arquivo=nome or f"{doc_id}.json",
        criado_em=None,
        documento_origem_id=None,
    )


@pytest.mark.asyncio
async def test_listar_versoes_documentos_filters_other_students(monkeypatch):
    base_doc = _doc("base-enunciado", TipoDocumento.ENUNCIADO)
    diana_report = _doc(
        "diana-report",
        TipoDocumento.RELATORIO_FINAL,
        aluno_id="diana",
        nome="relatorio-diana.pdf",
    )
    erik_report = _doc(
        "erik-report",
        TipoDocumento.RELATORIO_FINAL,
        aluno_id="erik",
        nome="relatorio-erik.pdf",
    )

    storage = MagicMock()
    storage.listar_documentos.side_effect = lambda atividade_id, aluno_id=None: (
        [base_doc, diana_report, erik_report]
        if aluno_id is None
        else [erik_report]
    )
    monkeypatch.setattr(routes_prompts, "storage", storage)

    result = await routes_prompts.listar_versoes_documentos("atividade", "erik")

    por_tipo = result["documentos_por_tipo"]
    assert [doc["id"] for doc in por_tipo["enunciado"]] == ["base-enunciado"]
    assert [doc["id"] for doc in por_tipo["relatorio_final"]] == ["erik-report"]


@pytest.mark.asyncio
async def test_listar_versoes_documentos_type_filter_keeps_student_scope(monkeypatch):
    base_doc = _doc("base-enunciado", TipoDocumento.ENUNCIADO)
    diana_report = _doc("diana-report", TipoDocumento.RELATORIO_FINAL, aluno_id="diana")
    erik_report = _doc("erik-report", TipoDocumento.RELATORIO_FINAL, aluno_id="erik")

    storage = MagicMock()
    storage.listar_documentos.side_effect = lambda atividade_id, aluno_id=None: (
        [base_doc, diana_report, erik_report]
        if aluno_id is None
        else [erik_report]
    )
    monkeypatch.setattr(routes_prompts, "storage", storage)

    result = await routes_prompts.listar_versoes_documentos(
        "atividade",
        "erik",
        tipo="relatorio_final",
    )

    assert list(result["documentos_por_tipo"]) == ["relatorio_final"]
    assert [doc["id"] for doc in result["documentos_por_tipo"]["relatorio_final"]] == [
        "erik-report"
    ]
