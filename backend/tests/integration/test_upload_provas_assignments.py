import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def upload_env(monkeypatch, temp_data_dir):
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from models import TipoDocumento
    from storage import StorageManager

    storage = StorageManager(base_path=str(temp_data_dir))
    materia = storage.criar_materia(nome="Fisica")
    turma = storage.criar_turma(materia_id=materia.id, nome="Turma D")
    atividade = storage.criar_atividade(turma_id=turma.id, nome="Prova 1")
    aluno1 = storage.criar_aluno(nome="Ana Lima", matricula="A001")
    aluno2 = storage.criar_aluno(nome="Bruno Reis", matricula="B002")
    storage.vincular_aluno_turma(aluno1.id, turma.id)
    storage.vincular_aluno_turma(aluno2.id, turma.id)

    existing_path = temp_data_dir / "existing.pdf"
    existing_path.write_bytes(b"%PDF-1.4 existing")
    storage.salvar_documento(
        arquivo_origem=str(existing_path),
        tipo=TipoDocumento.PROVA_RESPONDIDA,
        atividade_id=atividade.id,
        aluno_id=aluno1.id,
        display_name="Prova antiga Ana",
    )

    monkeypatch.setattr("main_v2.storage", storage)
    monkeypatch.setattr("routes_extras.storage", storage)

    from main_v2 import app

    return {
        "client": TestClient(app),
        "storage": storage,
        "atividade": atividade,
        "aluno1": aluno1,
        "aluno2": aluno2,
        "TipoDocumento": TipoDocumento,
    }


def test_assignment_upload_replaces_existing_student_exam(upload_env):
    assignments = [{
        "aluno_id": upload_env["aluno1"].id,
        "action": "substituir",
        "display_name": "Prova nova Ana",
    }]

    response = upload_env["client"].post(
        "/api/documentos/upload-provas-alunos",
        data={
            "atividade_id": upload_env["atividade"].id,
            "assignments": json.dumps(assignments),
        },
        files=[("files", ("ana_nova.pdf", b"%PDF-1.4 new", "application/pdf"))],
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["salvos"] == 1
    assert data["substituidos"] == 1

    docs = upload_env["storage"].listar_documentos(
        upload_env["atividade"].id,
        aluno_id=upload_env["aluno1"].id,
        tipo=upload_env["TipoDocumento"].PROVA_RESPONDIDA,
    )
    assert len(docs) == 1
    assert docs[0].display_name == "Prova nova Ana"


def test_assignment_upload_rejects_file_without_student(upload_env):
    assignments = [{
        "aluno_id": "",
        "action": "enviar",
        "display_name": "Sem aluno",
    }]

    response = upload_env["client"].post(
        "/api/documentos/upload-provas-alunos",
        data={
            "atividade_id": upload_env["atividade"].id,
            "assignments": json.dumps(assignments),
        },
        files=[("files", ("sem_aluno.pdf", b"%PDF-1.4", "application/pdf"))],
    )

    assert response.status_code == 400
    detail = response.json()["error"]["message"]
    assert "Selecione um aluno" in detail["erros"][0]["erro"]


def test_assignment_upload_blocks_two_files_for_same_student(upload_env):
    assignments = [
        {"aluno_id": upload_env["aluno2"].id, "action": "enviar", "display_name": "Bruno A"},
        {"aluno_id": upload_env["aluno2"].id, "action": "enviar", "display_name": "Bruno B"},
    ]

    response = upload_env["client"].post(
        "/api/documentos/upload-provas-alunos",
        data={
            "atividade_id": upload_env["atividade"].id,
            "assignments": json.dumps(assignments),
        },
        files=[
            ("files", ("bruno_a.pdf", b"%PDF-1.4 a", "application/pdf")),
            ("files", ("bruno_b.pdf", b"%PDF-1.4 b", "application/pdf")),
        ],
    )

    assert response.status_code == 400
    detail = response.json()["error"]["message"]
    assert "mesmo aluno" in detail["erros"][0]["erro"]

    docs = upload_env["storage"].listar_documentos(
        upload_env["atividade"].id,
        aluno_id=upload_env["aluno2"].id,
        tipo=upload_env["TipoDocumento"].PROVA_RESPONDIDA,
    )
    assert docs == []
