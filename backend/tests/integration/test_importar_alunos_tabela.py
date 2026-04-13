import io
import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@pytest.fixture
def client_env(monkeypatch, temp_data_dir):
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from storage import StorageManager

    storage = StorageManager(base_path=str(temp_data_dir))
    materia = storage.criar_materia(nome="Matematica")
    turma = storage.criar_turma(materia_id=materia.id, nome="9A")

    monkeypatch.setattr("main_v2.storage", storage)
    monkeypatch.setattr("routes_extras.storage", storage)

    from main_v2 import app

    return {
        "client": TestClient(app),
        "storage": storage,
        "turma": turma,
    }


def _post_table(client, endpoint, filename, content, data=None, content_type="text/csv"):
    return client.post(
        endpoint,
        data=data or {},
        files={"file": (filename, content, content_type)},
    )


def test_preview_csv_semicolon_suggests_flexible_headers(client_env):
    client = client_env["client"]
    csv_bytes = "nome do aluno;matrícula;e-mail\nAna Lima;A001;ana@example.com\n".encode("utf-8")

    response = _post_table(
        client,
        "/api/alunos/importar-tabela/preview",
        "alunos.csv",
        csv_bytes,
        data={"turma_id": client_env["turma"].id},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["formato"] == "csv"
    assert data["sugestoes"]["nome"] == 0
    assert data["sugestoes"]["matricula"] == 1
    assert data["sugestoes"]["email"] == 2
    assert data["analise"]["novos"] == 1


def test_import_is_idempotent_and_links_existing_students(client_env):
    client = client_env["client"]
    turma_id = client_env["turma"].id
    csv_bytes = (
        "nome do aluno;matrícula;e-mail\n"
        "Ana Lima;A001;ana@example.com\n"
        "Bruno Reis;B002;bruno@example.com\n"
    ).encode("utf-8")
    mapping = json.dumps({"nome": 0, "matricula": 1, "email": 2})

    first = _post_table(
        client,
        "/api/alunos/importar-tabela",
        "alunos.csv",
        csv_bytes,
        data={"turma_id": turma_id, "mapping": mapping},
    )
    assert first.status_code == 200, first.text
    first_data = first.json()
    assert first_data["criados"] == 2
    assert first_data["vinculados"] == 2

    second = _post_table(
        client,
        "/api/alunos/importar-tabela",
        "alunos.csv",
        csv_bytes,
        data={"turma_id": turma_id, "mapping": mapping},
    )
    assert second.status_code == 200, second.text
    second_data = second.json()
    assert second_data["criados"] == 0
    assert second_data["reaproveitados"] == 2
    assert second_data["ja_vinculados"] == 2
    assert len(client_env["storage"].listar_alunos()) == 2


def test_import_requires_nome_mapping(client_env):
    response = _post_table(
        client_env["client"],
        "/api/alunos/importar-tabela",
        "alunos.csv",
        b"email\nana@example.com\n",
        data={"turma_id": client_env["turma"].id, "mapping": json.dumps({"email": 0})},
    )

    assert response.status_code == 400
    assert "nome" in response.text.lower()


def test_import_allows_fixing_missing_name_from_preview(client_env):
    csv_bytes = (
        "nome do aluno;matrícula;e-mail\n"
        "Ana Lima;A001;ana@example.com\n"
        ";B002;bruno@example.com\n"
    ).encode("utf-8")
    mapping = json.dumps({"nome": 0, "matricula": 1, "email": 2})
    row_overrides = json.dumps({"3": {"nome": "Bruno Reis"}})

    response = _post_table(
        client_env["client"],
        "/api/alunos/importar-tabela",
        "alunos.csv",
        csv_bytes,
        data={
            "turma_id": client_env["turma"].id,
            "mapping": mapping,
            "row_overrides": row_overrides,
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["criados"] == 2
    assert data["ignorados"] == 0
    assert data["erros"] == 0
    assert {aluno.nome for aluno in client_env["storage"].listar_alunos(client_env["turma"].id)} == {
        "Ana Lima",
        "Bruno Reis",
    }


def test_import_accepts_name_only_mapping(client_env):
    response = _post_table(
        client_env["client"],
        "/api/alunos/importar-tabela",
        "nomes.csv",
        "Nome completo\nAluno Sem Extras\n".encode("utf-8"),
        data={
            "turma_id": client_env["turma"].id,
            "mapping": json.dumps({"nome": 0}),
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["criados"] == 1
    assert data["ignorados"] == 0
    aluno = client_env["storage"].listar_alunos(client_env["turma"].id)[0]
    assert aluno.nome == "Aluno Sem Extras"
    assert aluno.email is None
    assert aluno.matricula is None


def test_preview_xlsx_and_ods(client_env):
    pytest.importorskip("pandas")
    pytest.importorskip("openpyxl")
    pytest.importorskip("odf")
    import pandas as pd

    client = client_env["client"]
    df = pd.DataFrame({
        "Nome do aluno": ["Carla Dias"],
        "RA": ["C003"],
        "Email": ["carla@example.com"],
    })

    xlsx = io.BytesIO()
    df.to_excel(xlsx, index=False, engine="openpyxl")
    xlsx_response = _post_table(
        client,
        "/api/alunos/importar-tabela/preview",
        "alunos.xlsx",
        xlsx.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    assert xlsx_response.status_code == 200, xlsx_response.text
    assert xlsx_response.json()["sugestoes"]["nome"] == 0

    ods = io.BytesIO()
    df.to_excel(ods, index=False, engine="odf")
    ods_response = _post_table(
        client,
        "/api/alunos/importar-tabela/preview",
        "alunos.ods",
        ods.getvalue(),
        content_type="application/vnd.oasis.opendocument.spreadsheet",
    )
    assert ods_response.status_code == 200, ods_response.text
    assert ods_response.json()["sugestoes"]["matricula"] == 1
