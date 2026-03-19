"""Tests for optimized student detail, dashboard, and cache-first paths."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


BACKEND_DIR = Path(__file__).parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("PROVA_AI_TESTING", "1")
os.environ.setdefault("PROVA_AI_DISABLE_LOCAL_LLM", "1")

from models import Documento, TipoDocumento  # noqa: E402
from visualizador import VisualizadorResultados  # noqa: E402
from tests.unit.test_hot_endpoint_batch_helpers import seeded_storage  # noqa: E402,F401


def _make_storage(tmp_path: Path):
    with patch("storage.SUPABASE_DB_AVAILABLE", False):
        from storage import StorageManager

        return StorageManager(base_path=str(tmp_path))


def _doc_row(
    documento_id: str,
    atividade_id: str,
    aluno_id: str = None,
    *,
    tipo: str = "correcao",
    criado_em: str = "2026-03-14T12:00:00",
    caminho_arquivo: str = "arquivos/teste/correcao.json",
    extensao: str = ".json",
) -> dict:
    return {
        "id": documento_id,
        "tipo": tipo,
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "display_name": "",
        "nome_arquivo": f"{documento_id}{extensao}",
        "caminho_arquivo": caminho_arquivo,
        "extensao": extensao,
        "tamanho_bytes": 10,
        "ia_provider": None,
        "ia_modelo": None,
        "prompt_usado": None,
        "prompt_versao": None,
        "tokens_usados": 0,
        "tempo_processamento_ms": 0,
        "status": "concluido",
        "criado_em": criado_em,
        "atualizado_em": criado_em,
        "criado_por": "teste",
        "versao": 1,
        "documento_origem_id": None,
        "metadata": {},
    }


def test_get_aluno_detalhes_fast_preserves_contract_and_order(seeded_storage):
    data = seeded_storage.get_aluno_detalhes_fast("aluno-1")

    assert data["aluno"]["id"] == "aluno-1"
    assert data["total_turmas"] == 1
    assert len(data["turmas"]) == 1
    assert data["turmas"][0]["id"] == "turma-1"
    assert data["turmas"][0]["nome"] == "9A"
    assert data["turmas"][0]["materia_nome"] == "Matematica"
    assert data["turmas"][0]["data_entrada"]


def test_listar_documentos_postgresql_fetches_student_and_base_docs_only(seeded_storage, monkeypatch):
    seeded_storage.use_postgresql = True
    calls = []

    def fake_select_rows(table, filters=None, order_by=None, order_desc=False, limit=None, columns=None):
        calls.append((table, dict(filters or {})))
        if filters.get("aluno_id") == "aluno-1":
            return [
                _doc_row(
                    "doc-student",
                    "ativ-1",
                    "aluno-1",
                    tipo="prova_respondida",
                    criado_em="2026-03-14T12:30:00",
                    extensao=".pdf",
                    caminho_arquivo="arquivos/teste/prova.pdf",
                )
            ]
        if filters.get("aluno_id") is None:
            return [
                _doc_row(
                    "doc-base",
                    "ativ-1",
                    None,
                    tipo="gabarito",
                    criado_em="2026-03-14T12:00:00",
                    extensao=".pdf",
                    caminho_arquivo="arquivos/teste/gabarito.pdf",
                )
            ]
        return []

    monkeypatch.setattr(seeded_storage, "_select_rows", fake_select_rows)

    docs = seeded_storage.listar_documentos("ativ-1", aluno_id="aluno-1")

    assert [doc.id for doc in docs] == ["doc-student", "doc-base"]
    assert calls == [
        ("documentos", {"atividade_id": "ativ-1", "aluno_id": "aluno-1"}),
        ("documentos", {"atividade_id": "ativ-1", "aluno_id": None}),
    ]


def test_deletar_documentos_aluno_atividade_postgresql_uses_row_selection_and_delete(seeded_storage, monkeypatch):
    seeded_storage.use_postgresql = True
    select_calls = []
    deleted_ids = []

    def fake_select_rows(table, filters=None, order_by=None, order_desc=False, limit=None, columns=None):
        select_calls.append((table, dict(filters or {}), columns))
        assert table == "documentos"
        return [
            {"id": "doc-1"},
            {"id": "doc-2"},
        ]

    monkeypatch.setattr(seeded_storage, "_select_rows", fake_select_rows)
    monkeypatch.setattr(
        seeded_storage,
        "deletar_documento",
        lambda documento_id: deleted_ids.append(documento_id) or True,
    )

    deleted_count = seeded_storage.deletar_documentos_aluno_atividade("ativ-1", "aluno-1")

    assert deleted_count == 2
    assert deleted_ids == ["doc-1", "doc-2"]
    assert select_calls == [
        ("documentos", {"atividade_id": "ativ-1", "aluno_id": "aluno-1"}, ["id"])
    ]


def test_excluir_documentos_ai_aluno_atividade_postgresql_deletes_only_ai_docs(seeded_storage, monkeypatch):
    seeded_storage.use_postgresql = True
    deleted_ids = []

    monkeypatch.setattr(
        seeded_storage,
        "_select_rows",
        lambda *args, **kwargs: [
            {"id": "doc-ai-provider", "tipo": "correcao", "ia_provider": "openai"},
            {"id": "doc-ai-type", "tipo": "relatorio_final", "ia_provider": None},
            {"id": "doc-manual", "tipo": "prova_respondida", "ia_provider": None},
        ],
    )
    monkeypatch.setattr(
        seeded_storage,
        "deletar_documento",
        lambda documento_id: deleted_ids.append(documento_id) or True,
    )

    deleted_count = seeded_storage.excluir_documentos_ai_aluno_atividade("ativ-1", "aluno-1")

    assert deleted_count == 2
    assert deleted_ids == ["doc-ai-provider", "doc-ai-type"]


def test_resetar_extracoes_questoes_aluno_atividade_postgresql_deletes_only_question_extractions(seeded_storage, monkeypatch):
    seeded_storage.use_postgresql = True
    deleted_ids = []

    monkeypatch.setattr(
        seeded_storage,
        "_select_rows",
        lambda *args, **kwargs: [
            {"id": "doc-questoes", "tipo": "extracao_questoes"},
            {"id": "doc-outro", "tipo": "correcao"},
        ],
    )
    monkeypatch.setattr(
        seeded_storage,
        "deletar_documento",
        lambda documento_id: deleted_ids.append(documento_id) or True,
    )

    deleted_count = seeded_storage.resetar_extracoes_questoes_aluno_atividade("ativ-1", "aluno-1")

    assert deleted_count == 1
    assert deleted_ids == ["doc-questoes"]


def test_resolver_caminho_documento_prefers_local_cache(tmp_path, monkeypatch):
    storage = _make_storage(tmp_path)
    local_path = tmp_path / "arquivos" / "cache" / "correcao.json"
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text('{"nota": 9}', encoding="utf-8")

    document = Documento(
        id="doc-cache",
        tipo=TipoDocumento.CORRECAO,
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        nome_arquivo="correcao.json",
        caminho_arquivo="arquivos/cache/correcao.json",
        extensao=".json",
    )

    import storage as storage_module

    fake_remote = SimpleNamespace(enabled=True, download=MagicMock(side_effect=AssertionError("remote should not be used")))
    monkeypatch.setattr(storage_module, "SUPABASE_AVAILABLE", True)
    monkeypatch.setattr(storage_module, "supabase_storage", fake_remote)

    resolved = storage.resolver_caminho_documento(document)

    assert resolved == local_path
    fake_remote.download.assert_not_called()


def test_visualizador_historico_fast_uses_latest_correction_summary(monkeypatch):
    fake_storage = SimpleNamespace()
    fake_storage.get_turmas_do_aluno = lambda aluno_id: [
        {
            "id": "turma-1",
            "nome": "9A",
            "ano_letivo": 2026,
            "materia_nome": "Matematica",
        }
    ]
    fake_storage._log_hot_endpoint_profile = lambda *args, **kwargs: None

    atividades_rows = [
        {
            "id": "ativ-2",
            "turma_id": "turma-1",
            "nome": "Prova Final",
            "tipo": "prova",
            "data_aplicacao": "2026-03-11T09:00:00",
            "nota_maxima": 10.0,
        },
        {
            "id": "ativ-1",
            "turma_id": "turma-1",
            "nome": "Prova 1",
            "tipo": "prova",
            "data_aplicacao": "2026-03-10T09:00:00",
            "nota_maxima": 10.0,
        },
    ]
    correction_rows = [
        _doc_row("doc-new", "ativ-1", "aluno-1", criado_em="2026-03-12T11:00:00"),
        _doc_row("doc-old", "ativ-1", "aluno-1", criado_em="2026-03-11T10:00:00"),
    ]

    def fake_select_rows(table, filters=None, order_by=None, order_desc=False, limit=None, columns=None):
        if table == "atividades":
            return atividades_rows
        if table == "documentos":
            return correction_rows
        raise AssertionError(f"unexpected table lookup: {table}")

    fake_storage._select_rows = fake_select_rows

    visualizador = VisualizadorResultados()
    visualizador.storage = fake_storage

    correction_payloads = {
        "doc-new": {"nota": 8.5, "feedback": "ok"},
        "doc-old": {"nota": 2.0, "feedback": "old"},
    }
    monkeypatch.setattr(
        visualizador,
        "_ler_json",
        lambda documento: correction_payloads.get(documento.id, {}),
    )

    historico = visualizador.get_historico_aluno_fast("aluno-1")

    assert historico == [
        {
            "materia": "Matematica",
            "turma": "9A",
            "atividade_id": "ativ-2",
            "atividade": "Prova Final",
            "tipo": "prova",
            "data": "2026-03-11T09:00:00",
            "nota": None,
            "nota_maxima": 10.0,
            "percentual": None,
            "corrigido": False,
        },
        {
            "materia": "Matematica",
            "turma": "9A",
            "atividade_id": "ativ-1",
            "atividade": "Prova 1",
            "tipo": "prova",
            "data": "2026-03-10T09:00:00",
            "nota": 8.5,
            "nota_maxima": 10.0,
            "percentual": 85.0,
            "corrigido": True,
        },
    ]


def test_dashboard_aluno_fast_preserves_existing_shape(monkeypatch):
    visualizador = VisualizadorResultados()
    visualizador.storage = SimpleNamespace(
        get_aluno_detalhes_fast=lambda aluno_id: {
            "aluno": {"id": aluno_id, "nome": "Alice", "matricula": "2024001"},
            "turmas": [{"id": "turma-1"}],
            "total_turmas": 1,
        },
        _log_hot_endpoint_profile=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        visualizador,
        "get_historico_aluno_fast",
        lambda aluno_id, turmas_info=None: [
            {
                "materia": "Matematica",
                "turma": "9A",
                "atividade_id": "ativ-1",
                "atividade": "Prova 1",
                "tipo": "prova",
                "data": "2026-03-10T09:00:00",
                "nota": 8.0,
                "nota_maxima": 10.0,
                "percentual": 80.0,
                "corrigido": True,
            },
            {
                "materia": "Matematica",
                "turma": "9A",
                "atividade_id": "ativ-2",
                "atividade": "Prova 2",
                "tipo": "prova",
                "data": "2026-03-01T09:00:00",
                "nota": None,
                "nota_maxima": 10.0,
                "percentual": None,
                "corrigido": False,
            },
        ],
    )

    payload = visualizador.get_dashboard_aluno_fast("aluno-1")

    assert payload == {
        "aluno": {"id": "aluno-1", "nome": "Alice", "matricula": "2024001"},
        "resumo": {
            "total_turmas": 1,
            "total_atividades": 2,
            "atividades_corrigidas": 1,
            "media_geral": 8.0,
        },
        "por_materia": [
            {
                "materia": "Matematica",
                "total_atividades": 2,
                "corrigidas": 1,
                "media": 8.0,
            }
        ],
        "historico_recente": [
            {
                "materia": "Matematica",
                "turma": "9A",
                "atividade_id": "ativ-1",
                "atividade": "Prova 1",
                "tipo": "prova",
                "data": "2026-03-10T09:00:00",
                "nota": 8.0,
                "nota_maxima": 10.0,
                "percentual": 80.0,
                "corrigido": True,
            },
            {
                "materia": "Matematica",
                "turma": "9A",
                "atividade_id": "ativ-2",
                "atividade": "Prova 2",
                "tipo": "prova",
                "data": "2026-03-01T09:00:00",
                "nota": None,
                "nota_maxima": 10.0,
                "percentual": None,
                "corrigido": False,
            },
        ],
    }
