import os
import sys
from types import SimpleNamespace

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

    class FakeResolution:
        def __init__(self, model_id=None, provider_id=None):
            self.requested_model_id = model_id
            self.legacy_provider_id = provider_id
            self.resolved_model_id = model_id or provider_id or "fake-default-model"
            self.provider_type = "fake-modern-api"
            self.model_name = model_id or provider_id or "fake-doc-reader"

        def metadata(self):
            return {
                "requested_model_id": self.requested_model_id,
                "legacy_provider_id": self.legacy_provider_id,
                "resolved_model_id": self.resolved_model_id,
                "resolved_provider": self.provider_type,
                "resolved_model": self.model_name,
                "provider_resolution_source": "test",
            }

    class FakeAlunoTurmaProvider:
        def __init__(self, model_id=None):
            self.model_id = model_id or "fake-doc-reader"

        async def analyze_document(self, file_path, instruction):
            assert file_path.endswith(".pdf")
            if "aluno-turma" in instruction:
                assert "Relatorio Maria 2021" not in instruction
                assert "Maria Silva" in instruction
                assert "Turma 2021" in instruction
                assert "Prova 1" in instruction
            return SimpleNamespace(
                content=(
                    "## Sintese pedagogica\n"
                    "Maria demonstra dominio consistente de funcoes e precisa "
                    "revisar justificativas formais.\n\n"
                    "## Recomendacoes\n"
                    "- Resolver dois exercicios de verificacao por semana."
                ),
                provider="fake-modern-api",
                model=self.model_id,
                tokens_used=123,
                input_tokens=80,
                output_tokens=43,
                latency_ms=456.0,
            )

    monkeypatch.setattr(main_v2, "storage", storage)
    monkeypatch.setattr(routes_extras, "storage", storage)
    monkeypatch.setattr(routes_prompts, "storage", storage)
    provider_calls = []

    def fake_resolve_document_read_provider(model_id=None, provider_id=None):
        provider_calls.append({"model_id": model_id, "provider_id": provider_id})
        resolution = FakeResolution(model_id=model_id, provider_id=provider_id)
        return resolution, FakeAlunoTurmaProvider(resolution.model_name)

    monkeypatch.setattr(routes_prompts, "_resolve_document_read_provider", fake_resolve_document_read_provider)

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
        "provider_calls": provider_calls,
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
    assert data["metadata"]["geracao"] == "provider_document_read_v1"
    assert data["metadata"]["leituras"][0]["provider"] == "fake-modern-api"

    from models import TipoDocumento

    docs = env["storage"].listar_documentos(
        env["atividade_1"].id,
        aluno_id=env["aluno"].id,
        tipo=TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA,
    )
    assert len(docs) == 1
    assert docs[0].tipo == TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA
    assert docs[0].metadata["scope"] == "aluno_turma"
    assert docs[0].metadata["geracao"] == "provider_document_read_v1"
    assert docs[0].metadata["selection_mode"] == "latest_valid"
    assert docs[0].metadata["requested_model_id"] is None
    assert docs[0].metadata["resolved_model_id"] == "fake-default-model"
    assert docs[0].ia_provider == "fake-modern-api"
    assert docs[0].ia_modelo == "fake-doc-reader"
    assert docs[0].tokens_usados == 123

    conteudo = env["storage"].resolver_caminho_documento(docs[0]).read_text(encoding="utf-8")
    assert "Maria demonstra dominio consistente" in conteudo
    assert "conteudo nao extraido automaticamente" not in conteudo
    assert "Documento disponivel" not in conteudo


def test_pipeline_desempenho_aluno_turma_aceita_model_id(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    response = env["client"].post(
        "/api/executar/pipeline-desempenho-aluno-turma",
        data={
            "aluno_id": env["aluno"].id,
            "turma_id": env["turma_2021"].id,
            "model_id": "modelo-novo-cadastrado",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert env["provider_calls"][0] == {
        "model_id": "modelo-novo-cadastrado",
        "provider_id": None,
    }
    assert data["metadata"]["model_id"] == "modelo-novo-cadastrado"
    assert data["metadata"]["provider_id"] is None
    assert data["metadata"]["provider_ref"] == "modelo-novo-cadastrado"
    assert data["metadata"]["requested_model_id"] == "modelo-novo-cadastrado"
    assert data["metadata"]["resolved_model_id"] == "modelo-novo-cadastrado"


def test_pipeline_desempenho_aluno_turma_aceita_multiplos_model_ids(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    response = env["client"].post(
        "/api/executar/pipeline-desempenho-aluno-turma",
        data={
            "aluno_id": env["aluno"].id,
            "turma_id": env["turma_2021"].id,
            "model_ids": '["modelo-a", "modelo-b"]',
            "force_reexec": "true",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "completed"
    assert [call["model_id"] for call in env["provider_calls"]] == ["modelo-a", "modelo-b"]
    assert len(data["resultados"]) == 2
    assert {item["metadata"]["requested_model_id"] for item in data["resultados"]} == {
        "modelo-a",
        "modelo-b",
    }


def test_pipeline_desempenho_aluno_turma_usa_source_document_explicitamente(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    from models import TipoDocumento

    docs = env["storage"].listar_documentos(
        env["atividade_1"].id,
        aluno_id=env["aluno"].id,
        tipo=TipoDocumento.RELATORIO_FINAL,
    )
    relatorio_id = docs[0].id

    response = env["client"].post(
        "/api/executar/pipeline-desempenho-aluno-turma",
        data={
            "aluno_id": env["aluno"].id,
            "turma_id": env["turma_2021"].id,
            "model_id": "modelo-source",
            "source_document_ids": f'{{"relatorio_final": "{relatorio_id}"}}',
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["metadata"]["selection_mode"] == "explicit"
    assert data["metadata"]["source_document_ids"] == [relatorio_id]


def test_documento_multi_ia_salva_um_documento_por_modelo(desempenho_aluno_turma_env):
    env = desempenho_aluno_turma_env
    from models import TipoDocumento

    origem = env["storage"].listar_documentos(
        env["atividade_1"].id,
        aluno_id=env["aluno"].id,
        tipo=TipoDocumento.RELATORIO_FINAL,
    )[0]

    response = env["client"].post(
        "/api/executar/documento-multi-ia",
        data={
            "documento_id": origem.id,
            "model_ids": '["modelo-a", "modelo-b"]',
            "instruction": "Analise este relatorio.",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "completed"
    assert len(data["resultados"]) == 2
    assert {item["metadata"]["requested_model_id"] for item in data["resultados"]} == {
        "modelo-a",
        "modelo-b",
    }

    docs = env["storage"].listar_documentos(
        env["atividade_1"].id,
        tipo=TipoDocumento.ANALISE_DOCUMENTO_IA,
    )
    assert len(docs) == 2
    assert {doc.metadata["documento_origem_id"] for doc in docs} == {origem.id}
    assert {doc.metadata["selection_mode"] for doc in docs} == {"explicit"}


def test_documento_multi_ia_falha_de_um_modelo_nao_apaga_sucesso(
    desempenho_aluno_turma_env,
    monkeypatch,
):
    env = desempenho_aluno_turma_env
    from models import TipoDocumento
    import routes_prompts

    origem = env["storage"].listar_documentos(
        env["atividade_1"].id,
        aluno_id=env["aluno"].id,
        tipo=TipoDocumento.RELATORIO_FINAL,
    )[0]

    class FakeResolution:
        def __init__(self, model_id):
            self.requested_model_id = model_id
            self.legacy_provider_id = None
            self.resolved_model_id = model_id
            self.provider_type = "fake-modern-api"
            self.model_name = model_id

        def metadata(self):
            return {
                "requested_model_id": self.requested_model_id,
                "legacy_provider_id": None,
                "resolved_model_id": self.resolved_model_id,
                "resolved_provider": self.provider_type,
                "resolved_model": self.model_name,
                "provider_resolution_source": "test",
            }

    class PartiallyFailingProvider:
        def __init__(self, model_id):
            self.model_id = model_id

        async def analyze_document(self, file_path, instruction):
            if self.model_id == "modelo-b":
                raise RuntimeError("falha simulada")
            return SimpleNamespace(
                content="Analise objetiva do documento.",
                provider="fake-modern-api",
                model=self.model_id,
                tokens_used=11,
                input_tokens=7,
                output_tokens=4,
                latency_ms=12.0,
            )

    def resolver(model_id=None, provider_id=None):
        resolution = FakeResolution(model_id)
        return resolution, PartiallyFailingProvider(model_id)

    monkeypatch.setattr(routes_prompts, "_resolve_document_read_provider", resolver)

    response = env["client"].post(
        "/api/executar/documento-multi-ia",
        data={
            "documento_id": origem.id,
            "model_ids": '["modelo-a", "modelo-b"]',
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["status"] == "completed"
    assert [item["status"] for item in data["resultados"]] == ["completed", "failed"]
    assert data["resultados"][1]["model_id"] == "modelo-b"
    assert "falha simulada" in data["resultados"][1]["erro"]["erro"]

    docs = env["storage"].listar_documentos(
        env["atividade_1"].id,
        tipo=TipoDocumento.ANALISE_DOCUMENTO_IA,
    )
    assert len(docs) == 2
    by_model = {doc.metadata["requested_model_id"]: doc for doc in docs}
    assert by_model["modelo-a"].status.value == "concluido"
    assert by_model["modelo-b"].status.value == "erro"
    assert by_model["modelo-b"].metadata["erro"]["erro"] == "falha simulada"


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
