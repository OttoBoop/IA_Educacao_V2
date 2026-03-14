"""Tests for batched hot endpoint helpers in storage.py."""

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest


BACKEND_DIR = Path(__file__).parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("PROVA_AI_TESTING", "1")
os.environ.setdefault("PROVA_AI_DISABLE_LOCAL_LLM", "1")


def _make_storage(tmp_path: Path):
    with patch("storage.SUPABASE_DB_AVAILABLE", False):
        from storage import StorageManager

        return StorageManager(base_path=str(tmp_path))


def _insert_row(db_path: Path, query: str, params: tuple) -> None:
    conn = sqlite3.connect(str(db_path))
    conn.execute(query, params)
    conn.commit()
    conn.close()


def _insert_materia(db_path: Path, materia_id: str, nome: str) -> None:
    now = datetime.now().isoformat()
    _insert_row(
        db_path,
        """
        INSERT INTO materias (id, nome, descricao, nivel, criado_em, atualizado_em, metadata)
        VALUES (?, ?, NULL, 'outro', ?, ?, '{}')
        """,
        (materia_id, nome, now, now),
    )


def _insert_turma(db_path: Path, turma_id: str, materia_id: str, nome: str) -> None:
    now = datetime.now().isoformat()
    _insert_row(
        db_path,
        """
        INSERT INTO turmas (id, materia_id, nome, ano_letivo, periodo, descricao,
                            criado_em, atualizado_em, metadata)
        VALUES (?, ?, ?, 2026, NULL, NULL, ?, ?, '{}')
        """,
        (turma_id, materia_id, nome, now, now),
    )


def _insert_aluno(db_path: Path, aluno_id: str, nome: str) -> None:
    now = datetime.now().isoformat()
    _insert_row(
        db_path,
        """
        INSERT INTO alunos (id, nome, email, matricula, criado_em, atualizado_em, metadata)
        VALUES (?, ?, NULL, NULL, ?, ?, '{}')
        """,
        (aluno_id, nome, now, now),
    )


def _insert_vinculo(db_path: Path, vinculo_id: str, aluno_id: str, turma_id: str) -> None:
    now = datetime.now().isoformat()
    _insert_row(
        db_path,
        """
        INSERT INTO alunos_turmas (id, aluno_id, turma_id, ativo, data_entrada, observacoes)
        VALUES (?, ?, ?, 1, ?, NULL)
        """,
        (vinculo_id, aluno_id, turma_id, now),
    )


def _insert_atividade(db_path: Path, atividade_id: str, turma_id: str, nome: str) -> None:
    now = datetime.now().isoformat()
    _insert_row(
        db_path,
        """
        INSERT INTO atividades (
            id, turma_id, nome, tipo, data_aplicacao, data_entrega, peso, nota_maxima,
            descricao, criado_em, atualizado_em, metadata
        )
        VALUES (?, ?, ?, 'prova', NULL, NULL, 1.0, 10.0, NULL, ?, ?, '{}')
        """,
        (atividade_id, turma_id, nome, now, now),
    )


def _insert_documento(
    db_path: Path,
    documento_id: str,
    tipo: str,
    atividade_id: str,
    criado_em: str,
    aluno_id: str = None,
    nome_arquivo: str = None,
) -> None:
    _insert_row(
        db_path,
        """
        INSERT INTO documentos (
            id, tipo, atividade_id, aluno_id, display_name, nome_arquivo, caminho_arquivo,
            extensao, tamanho_bytes, status, criado_em, atualizado_em, criado_por, versao, metadata
        )
        VALUES (?, ?, ?, ?, '', ?, '', '.pdf', 100, 'concluido', ?, ?, 'teste', 1, '{}')
        """,
        (
            documento_id,
            tipo,
            atividade_id,
            aluno_id,
            nome_arquivo or f"{documento_id}.pdf",
            criado_em,
            criado_em,
        ),
    )


@pytest.fixture
def seeded_storage(tmp_path):
    storage = _make_storage(tmp_path)
    db_path = tmp_path / "database.db"

    _insert_materia(db_path, "mat-1", "Matematica")
    _insert_materia(db_path, "mat-2", "Matematica")

    _insert_turma(db_path, "turma-1", "mat-1", "9A")
    _insert_turma(db_path, "turma-2", "mat-2", "9B")

    _insert_aluno(db_path, "aluno-1", "Alice")
    _insert_aluno(db_path, "aluno-2", "Bob")
    _insert_aluno(db_path, "aluno-3", "Carol")

    _insert_vinculo(db_path, "v-1", "aluno-1", "turma-1")
    _insert_vinculo(db_path, "v-2", "aluno-2", "turma-1")
    _insert_vinculo(db_path, "v-3", "aluno-3", "turma-2")

    _insert_atividade(db_path, "ativ-1", "turma-1", "Prova 1")
    _insert_atividade(db_path, "ativ-2", "turma-2", "Prova 2")

    _insert_documento(db_path, "doc-base-1", "enunciado", "ativ-1", "2026-03-01T10:00:00")
    _insert_documento(db_path, "doc-base-2", "gabarito", "ativ-1", "2026-03-01T09:00:00")
    _insert_documento(
        db_path,
        "doc-aluno-1",
        "prova_respondida",
        "ativ-1",
        "2026-03-01T11:00:00",
        aluno_id="aluno-1",
    )
    _insert_documento(
        db_path,
        "doc-aluno-2",
        "prova_respondida",
        "ativ-1",
        "2026-03-01T12:00:00",
        aluno_id="aluno-2",
    )
    _insert_documento(db_path, "doc-base-3", "enunciado", "ativ-2", "2026-03-02T10:00:00")
    _insert_documento(
        db_path,
        "doc-aluno-3",
        "prova_respondida",
        "ativ-2",
        "2026-03-02T11:00:00",
        aluno_id="aluno-3",
    )

    return storage


def test_get_estatisticas_gerais_fast_aggregates_counts(seeded_storage):
    stats = seeded_storage.get_estatisticas_gerais_fast()

    assert stats == {
        "total_materias": 2,
        "total_turmas": 2,
        "total_alunos": 3,
        "total_atividades": 2,
        "total_documentos": 6,
        "alertas": {"atividades_sem_gabarito": 1},
    }


def test_get_arvore_navegacao_fast_merges_duplicate_materias(seeded_storage):
    arvore = seeded_storage.get_arvore_navegacao_fast()

    assert len(arvore["materias"]) == 1
    materia = arvore["materias"][0]
    assert materia["nome"] == "Matematica"
    assert len(materia["turmas"]) == 2

    turmas = {turma["id"]: turma for turma in materia["turmas"]}
    assert turmas["turma-1"]["total_alunos"] == 2
    assert turmas["turma-2"]["total_alunos"] == 1
    assert turmas["turma-1"]["atividades"][0]["total_documentos"] == 4
    assert turmas["turma-2"]["atividades"][0]["total_documentos"] == 2


def test_listar_documentos_com_contexto_fast_keeps_base_docs_for_selected_alunos(seeded_storage):
    documentos = seeded_storage.listar_documentos_com_contexto_fast(
        {"aluno_ids": ["aluno-1"]}
    )
    ids = [doc["id"] for doc in documentos]

    assert ids == ["doc-aluno-1", "doc-base-1", "doc-base-2", "doc-base-3"]
    assert all(doc["id"] != "doc-aluno-2" for doc in documentos)
    assert all(doc["id"] != "doc-aluno-3" for doc in documentos)
    assert next(doc for doc in documentos if doc["id"] == "doc-aluno-1")["aluno_nome"] == "Alice"


def test_listar_documentos_com_contexto_fast_applies_combined_filters(seeded_storage):
    documentos = seeded_storage.listar_documentos_com_contexto_fast(
        {"turma_ids": ["turma-1"], "tipos": ["prova_respondida"]}
    )

    assert [doc["id"] for doc in documentos] == ["doc-aluno-2", "doc-aluno-1"]
    assert {doc["turma_id"] for doc in documentos} == {"turma-1"}
    assert {doc["tipo"] for doc in documentos} == {"prova_respondida"}
