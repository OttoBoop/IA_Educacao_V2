import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def visao_aluno_env(monkeypatch, temp_data_dir):
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from models import TipoDocumento
    from storage import StorageManager

    storage = StorageManager(base_path=str(temp_data_dir))
    materia = storage.criar_materia(nome="Calculo I")
    turma_2021 = storage.criar_turma(materia.id, "Turma 2021", ano_letivo=2021)
    turma_2022 = storage.criar_turma(materia.id, "Turma 2022", ano_letivo=2022)
    atividade_2021 = storage.criar_atividade(turma_2021.id, "Prova 1")
    atividade_2022 = storage.criar_atividade(turma_2022.id, "Prova 1")

    aluno = storage.criar_aluno("Maria Silva", matricula="M001")
    aluno_sem_docs = storage.criar_aluno("Joao Sem Docs", matricula="J001")
    outro_aluno = storage.criar_aluno("Outro Aluno", matricula="O001")

    storage.vincular_aluno_turma(aluno.id, turma_2021.id)
    storage.vincular_aluno_turma(aluno.id, turma_2022.id, observacoes="Repetente")
    storage.vincular_aluno_turma(aluno_sem_docs.id, turma_2021.id)
    storage.vincular_aluno_turma(outro_aluno.id, turma_2021.id)

    arquivo = temp_data_dir / "doc.pdf"
    arquivo.write_bytes(b"%PDF-1.4 visao aluno test")

    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.ENUNCIADO,
        atividade_2021.id,
        display_name="Enunciado Prova 1",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.PROVA_RESPONDIDA,
        atividade_2021.id,
        aluno_id=aluno.id,
        display_name="Prova Maria",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.CORRECAO,
        atividade_2021.id,
        aluno_id=aluno.id,
        display_name="Correcao Maria",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.RELATORIO_FINAL,
        atividade_2021.id,
        aluno_id=aluno.id,
        display_name="Relatorio Maria",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.ANALISE_HABILIDADES,
        atividade_2021.id,
        aluno_id=outro_aluno.id,
        display_name="Analise Outro Aluno",
    )

    import main_v2

    monkeypatch.setattr(main_v2, "storage", storage)

    return {
        "client": TestClient(main_v2.app),
        "storage": storage,
        "aluno": aluno,
        "aluno_sem_docs": aluno_sem_docs,
        "outro_aluno": outro_aluno,
        "materia": materia,
        "turma_2021": turma_2021,
        "turma_2022": turma_2022,
        "atividade_2021": atividade_2021,
        "atividade_2022": atividade_2022,
    }


def _flatten_atividades(payload):
    atividades = {}
    for materia in payload["materias"]:
        for turma in materia["turmas"]:
            for atividade in turma["atividades"]:
                atividades[atividade["atividade_id"]] = atividade
    return atividades


def test_visao_aluno_preserva_duas_turmas_da_mesma_materia(visao_aluno_env):
    env = visao_aluno_env
    response = env["client"].get(f"/api/alunos/{env['aluno'].id}/visao")

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["total_materias"] == 1
    assert data["materias"][0]["materia_id"] == env["materia"].id
    turmas = data["materias"][0]["turmas"]
    assert {t["turma_id"] for t in turmas} == {
        env["turma_2021"].id,
        env["turma_2022"].id,
    }


def test_visao_aluno_inclui_turma_historica_inativa(visao_aluno_env):
    env = visao_aluno_env
    env["storage"].desvincular_aluno_turma(env["aluno"].id, env["turma_2021"].id)

    response = env["client"].get(f"/api/alunos/{env['aluno'].id}/visao")

    assert response.status_code == 200, response.text
    data = response.json()
    turmas = data["materias"][0]["turmas"]
    assert {t["turma_id"] for t in turmas} == {
        env["turma_2021"].id,
        env["turma_2022"].id,
    }


def test_visao_aluno_status_usa_apenas_documentos_do_aluno(visao_aluno_env):
    env = visao_aluno_env
    response = env["client"].get(f"/api/alunos/{env['aluno'].id}/visao")

    assert response.status_code == 200, response.text
    atividade = _flatten_atividades(response.json())[env["atividade_2021"].id]
    status = atividade["status_aluno"]

    assert status["tem_prova_respondida"] is True
    assert status["tem_correcao"] is True
    assert status["tem_relatorio_final"] is True
    assert status["tem_analise_habilidades"] is False

    tipos = {doc["tipo"] for doc in atividade["documentos_aluno"]}
    assert tipos == {"prova_respondida", "correcao", "relatorio_final"}
    assert atividade["total_documentos_aluno"] == 3


def test_visao_aluno_sem_documentos_mostra_atividade_pendente(visao_aluno_env):
    env = visao_aluno_env
    response = env["client"].get(f"/api/alunos/{env['aluno_sem_docs'].id}/visao")

    assert response.status_code == 200, response.text
    atividade = _flatten_atividades(response.json())[env["atividade_2021"].id]

    assert atividade["total_documentos_aluno"] == 0
    assert atividade["status_aluno"] == {
        "tem_prova_respondida": False,
        "tem_correcao": False,
        "tem_analise_habilidades": False,
        "tem_relatorio_final": False,
    }


def test_visao_aluno_inexistente_retorna_404(visao_aluno_env):
    response = visao_aluno_env["client"].get("/api/alunos/aluno-inexistente/visao")

    assert response.status_code == 404
