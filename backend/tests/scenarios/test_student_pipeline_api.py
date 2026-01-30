"""
API-level tests for student pipeline routes using FastAPI TestClient.
"""

import importlib
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app_with_storage(monkeypatch, temp_data_dir: Path):
    import storage as storage_module
    from storage import StorageManager

    storage_instance = StorageManager(base_path=temp_data_dir)
    monkeypatch.setattr(storage_module, "storage", storage_instance)

    modules_to_reload = [
        "executor",
        "routes_prompts",
        "routes_pipeline",
        "routes_extras",
        "routes_resultados",
        "routes_chat",
        "main_v2",
    ]

    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)

    import main_v2

    return main_v2.app, storage_instance


@pytest.fixture
def seeded_context(app_with_storage, temp_data_dir: Path):
    app, storage_instance = app_with_storage
    from models import NivelEnsino, TipoDocumento
    from tests.fixtures.document_factory import DocumentFactory

    materia = storage_instance.criar_materia(
        "Matemática",
        "Matemática básica",
        NivelEnsino.FUNDAMENTAL_2,
    )
    turma = storage_instance.criar_turma(
        materia.id,
        "9º Ano A",
        ano_letivo=2024,
        periodo="Manhã",
    )
    atividade = storage_instance.criar_atividade(
        turma.id,
        "Prova 1 - Equações",
        tipo="prova",
        nota_maxima=10.0,
    )
    aluno = storage_instance.criar_aluno(
        "Ana Silva",
        "ana.silva@example.com",
        "2024001",
    )
    storage_instance.vincular_aluno_turma(aluno.id, turma.id)

    factory = DocumentFactory(temp_data_dir / "docs")
    enunciado = factory.criar_prova_teste("Matemática", num_questoes=3)
    gabarito = factory.criar_gabarito_teste("Matemática", num_questoes=3)
    prova_aluno = factory.criar_prova_aluno(aluno.nome, "Matemática", num_questoes=3)

    storage_instance.salvar_documento(
        str(enunciado.path),
        TipoDocumento.ENUNCIADO,
        atividade.id,
    )
    storage_instance.salvar_documento(
        str(gabarito.path),
        TipoDocumento.GABARITO,
        atividade.id,
    )
    storage_instance.salvar_documento(
        str(prova_aluno.path),
        TipoDocumento.PROVA_RESPONDIDA,
        atividade.id,
        aluno_id=aluno.id,
    )

    return {
        "app": app,
        "storage": storage_instance,
        "atividade": atividade,
        "aluno": aluno,
    }


def test_student_pipeline_api_flow(seeded_context, monkeypatch, temp_data_dir: Path):
    from executor import ResultadoExecucao, executor
    from models import TipoDocumento

    app = seeded_context["app"]
    storage_instance = seeded_context["storage"]
    atividade = seeded_context["atividade"]
    aluno = seeded_context["aluno"]

    async def fake_pipeline(
        atividade_id: str,
        aluno_id: str,
        **_kwargs,
    ):
        output_path = temp_data_dir / "extracao_respostas.json"
        output_path.write_text(json.dumps({"respostas": []}), encoding="utf-8")

        documento = storage_instance.salvar_documento(
            str(output_path),
            TipoDocumento.EXTRACAO_RESPOSTAS,
            atividade_id,
            aluno_id=aluno_id,
            ia_provider="test-provider",
            ia_modelo="test-model",
            criado_por="ai",
        )

        return {
            "extrair_respostas": ResultadoExecucao(
                sucesso=True,
                etapa="extrair_respostas",
                provider="test-provider",
                modelo="test-model",
                documento_id=documento.id,
            )
        }

    monkeypatch.setattr(executor, "executar_pipeline_completo", fake_pipeline)

    with TestClient(app) as client:
        response = client.post(
            "/api/executar/pipeline-completo",
            data={
                "atividade_id": atividade.id,
                "aluno_id": aluno.id,
                "selected_steps": json.dumps(["extrair_respostas"]),
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["sucesso"] is True
        assert "extrair_respostas" in payload["etapas_executadas"]

        documentos = storage_instance.listar_documentos(atividade.id, aluno.id)
        assert any(doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS for doc in documentos)

        status_response = client.get(
            f"/api/executar/status-etapas/{atividade.id}/{aluno.id}"
        )
        assert status_response.status_code == 200
        status_payload = status_response.json()
        status_doc = status_payload["etapas"]["extrair_respostas"]["documentos"][0]
        assert status_doc["provider"] == "test-provider"
        assert status_doc["modelo"] == "test-model"

        versions_response = client.get(
            f"/api/documentos/{atividade.id}/{aluno.id}/versoes"
        )
        assert versions_response.status_code == 200
        versions_payload = versions_response.json()
        extracao_docs = versions_payload["documentos_por_tipo"][
            TipoDocumento.EXTRACAO_RESPOSTAS.value
        ]
        assert extracao_docs[0]["provider"] == "test-provider"
        assert extracao_docs[0]["modelo"] == "test-model"

        documento_id = extracao_docs[0]["id"]
        download_response = client.get(f"/api/documentos/{documento_id}/download")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"].startswith("application/json")

        view_response = client.get(f"/api/documentos/{documento_id}/view")
        assert view_response.status_code == 200
        assert view_response.headers["content-type"].startswith("application/json")
