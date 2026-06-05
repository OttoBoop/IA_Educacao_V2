import os
import sys

from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def desempenho_aluno_turma_env(monkeypatch, temp_data_dir):
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from models import TipoDocumento
    from storage import StorageManager

    storage = StorageManager(base_path=str(temp_data_dir))
    materia = storage.criar_materia(nome="Calculo I")
    turma_2021 = storage.criar_turma(materia.id, "Turma 2021", ano_letivo=2021)
    turma_2022 = storage.criar_turma(materia.id, "Turma 2022", ano_letivo=2022)
    atividade_1 = storage.criar_atividade(turma_2021.id, "Prova 1")
    atividade_2 = storage.criar_atividade(turma_2021.id, "Prova 2")
    atividade_outra_turma = storage.criar_atividade(turma_2022.id, "Prova 1")

    aluno = storage.criar_aluno("Maria Silva", matricula="M001")
    outro_aluno = storage.criar_aluno("Outro Aluno", matricula="O001")
    aluno_sem_vinculo = storage.criar_aluno("Sem Vinculo", matricula="S001")

    storage.vincular_aluno_turma(aluno.id, turma_2021.id)
    storage.vincular_aluno_turma(aluno.id, turma_2022.id, observacoes="Repetente")
    storage.vincular_aluno_turma(outro_aluno.id, turma_2021.id)

    arquivo = temp_data_dir / "doc.pdf"
    arquivo.write_bytes(b"%PDF-1.4 desempenho aluno turma")

    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.PROVA_RESPONDIDA,
        atividade_1.id,
        aluno_id=aluno.id,
        display_name="Prova Maria 2021",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.CORRECAO,
        atividade_1.id,
        aluno_id=aluno.id,
        display_name="Correcao Maria 2021",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.RELATORIO_FINAL,
        atividade_1.id,
        aluno_id=aluno.id,
        display_name="Relatorio Maria 2021",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.CORRECAO,
        atividade_2.id,
        aluno_id=aluno.id,
        display_name="Correcao Maria Prova 2",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.RELATORIO_FINAL,
        atividade_1.id,
        aluno_id=outro_aluno.id,
        display_name="Relatorio Outro Aluno",
    )
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.RELATORIO_FINAL,
        atividade_outra_turma.id,
        aluno_id=aluno.id,
        display_name="Relatorio Maria 2022",
    )

    import main_v2
    import routes_extras
    import routes_prompts

    monkeypatch.setattr(main_v2, "storage", storage)
    monkeypatch.setattr(routes_extras, "storage", storage)
    monkeypatch.setattr(routes_prompts, "storage", storage)

    return {
        "client": TestClient(main_v2.app),
        "storage": storage,
        "aluno": aluno,
        "outro_aluno": outro_aluno,
        "aluno_sem_vinculo": aluno_sem_vinculo,
        "materia": materia,
        "turma_2021": turma_2021,
        "turma_2022": turma_2022,
        "atividade_1": atividade_1,
        "atividade_2": atividade_2,
        "atividade_outra_turma": atividade_outra_turma,
    }


def test_desempenho_aluno_turma_filtra_aluno_e_turma(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    response = env["client"].get(
        f"/api/desempenho/aluno/{env['aluno'].id}/turma/{env['turma_2021'].id}"
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["meta"]["scope"] == "aluno_turma"
    assert data["meta"]["aluno_id"] == env["aluno"].id
    assert data["meta"]["turma_id"] == env["turma_2021"].id
    assert data["meta"]["tipo_documento_futuro"] == "relatorio_desempenho_aluno_turma"
    assert data["turma"]["id"] == env["turma_2021"].id
    assert data["materia"]["id"] == env["materia"].id

    atividade_ids = {atividade["atividade_id"] for atividade in data["atividades"]}
    assert atividade_ids == {env["atividade_1"].id, env["atividade_2"].id}
    assert env["atividade_outra_turma"].id not in atividade_ids

    all_docs = [
        doc
        for atividade in data["atividades"]
        for doc in atividade["documentos_aluno"]
    ]
    assert {doc["aluno_id"] for doc in all_docs} == {env["aluno"].id}
    assert "Relatorio Outro Aluno" not in {doc["display_name"] for doc in all_docs}
    assert "Relatorio Maria 2022" not in {doc["display_name"] for doc in all_docs}


def test_desempenho_aluno_turma_base_minima(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    response = env["client"].get(
        f"/api/desempenho/aluno/{env['aluno'].id}/turma/{env['turma_2021'].id}"
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["base_minima"] == {
        "scope": "aluno_turma",
        "pode_gerar_relatorio": True,
        "faltando": [],
        "atividades_com_correcao": 2,
        "atividades_com_relatorio_final": 1,
        "total_atividades": 2,
        "total_documentos_aluno": 4,
    }

    atividades = {atividade["atividade_id"]: atividade for atividade in data["atividades"]}
    assert atividades[env["atividade_1"].id]["status_aluno"]["tem_relatorio_final"] is True
    assert atividades[env["atividade_2"].id]["status_aluno"]["tem_relatorio_final"] is False


def test_desempenho_aluno_turma_bloqueia_sem_relatorio_final(monkeypatch, temp_data_dir):
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from models import TipoDocumento
    from storage import StorageManager

    storage = StorageManager(base_path=str(temp_data_dir))
    materia = storage.criar_materia(nome="Fisica")
    turma = storage.criar_turma(materia.id, "Turma A")
    atividade = storage.criar_atividade(turma.id, "Prova 1")
    aluno = storage.criar_aluno("Aluno Sem Relatorio")
    storage.vincular_aluno_turma(aluno.id, turma.id)

    arquivo = temp_data_dir / "doc.pdf"
    arquivo.write_bytes(b"%PDF-1.4 sem relatorio")
    storage.salvar_documento(
        str(arquivo),
        TipoDocumento.CORRECAO,
        atividade.id,
        aluno_id=aluno.id,
        display_name="Correcao sem relatorio",
    )

    import main_v2
    import routes_extras
    import routes_prompts

    monkeypatch.setattr(main_v2, "storage", storage)
    monkeypatch.setattr(routes_extras, "storage", storage)
    monkeypatch.setattr(routes_prompts, "storage", storage)

    response = TestClient(main_v2.app).get(
        f"/api/desempenho/aluno/{aluno.id}/turma/{turma.id}"
    )

    assert response.status_code == 200, response.text
    assert response.json()["base_minima"]["pode_gerar_relatorio"] is False
    assert response.json()["base_minima"]["faltando"] == ["relatorio_final_do_aluno"]


def test_desempenho_aluno_turma_exige_vinculo(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    response = env["client"].get(
        f"/api/desempenho/aluno/{env['aluno_sem_vinculo'].id}/turma/{env['turma_2021'].id}"
    )

    assert response.status_code == 404


def test_pipeline_desempenho_aluno_turma_salva_documento(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    response = env["client"].post(
        "/api/executar/pipeline-desempenho-aluno-turma",
        data={
            "aluno_id": env["aluno"].id,
            "turma_id": env["turma_2021"].id,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "completed"
    assert data["atividades_usadas"] == 1
    assert data["metadata"]["scope"] == "aluno_turma"
    assert data["metadata"]["aluno_id"] == env["aluno"].id
    assert data["metadata"]["turma_id"] == env["turma_2021"].id
    assert data["metadata"]["materia_id"] == env["materia"].id
    assert data["metadata"]["atividade_ids"] == [env["atividade_1"].id]

    from models import TipoDocumento

    docs = env["storage"].listar_documentos(
        env["atividade_1"].id,
        aluno_id=env["aluno"].id,
        tipo=TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA,
    )
    assert len(docs) == 1
    assert docs[0].tipo == TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA
    assert docs[0].metadata["scope"] == "aluno_turma"


def test_pipeline_desempenho_aluno_turma_nao_duplica_sem_force(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    payload = {
        "aluno_id": env["aluno"].id,
        "turma_id": env["turma_2021"].id,
    }

    first = env["client"].post("/api/executar/pipeline-desempenho-aluno-turma", data=payload)
    second = env["client"].post("/api/executar/pipeline-desempenho-aluno-turma", data=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert second.json()["skipped"] is True

    from models import TipoDocumento

    docs = env["storage"].listar_documentos(
        env["atividade_1"].id,
        aluno_id=env["aluno"].id,
        tipo=TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA,
    )
    assert len(docs) == 1
