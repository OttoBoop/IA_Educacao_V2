from types import SimpleNamespace
from unittest.mock import MagicMock
import json

import pytest

from cost_tracking import build_cost_summary
from model_catalog import model_catalog
from models import NivelEnsino, StatusProcessamento, TipoDocumento
from storage import StorageManager
from token_usage import TokenUsageRecord, TokenUsageStore


def _seed_storage(tmp_path):
    store = StorageManager(str(tmp_path))
    materia = store.criar_materia("Matematica", nivel=NivelEnsino.SUPERIOR)
    turma = store.criar_turma(materia.id, "T1")
    aluno = store.criar_aluno("Ada")
    atividade = store.criar_atividade(turma.id, "Prova 1")
    return store, atividade, aluno


def test_salvar_documento_persiste_tokens_tempo_e_metadata(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo = tmp_path / "correcao.json"
    arquivo.write_text('{"ok": true}', encoding="utf-8")

    doc = store.salvar_documento(
        arquivo_origem=str(arquivo),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        prompt_usado="prompt-correcao",
        tokens_usados=150,
        tempo_processamento_ms=1234.5,
        metadata={"tokens_entrada": 100, "tokens_saida": 50, "cost_run_id": "run-1"},
        criado_por="sistema",
    )

    saved = store.get_documento(doc.id)

    assert saved.ia_provider == "openai"
    assert saved.ia_modelo == "gpt-5-nano"
    assert saved.prompt_usado == "prompt-correcao"
    assert saved.tokens_usados == 150
    assert saved.tempo_processamento_ms == 1234.5
    assert saved.metadata["tokens_entrada"] == 100
    assert saved.metadata["tokens_saida"] == 50


def test_atualizar_documento_processamento_mescla_metadata_e_status(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo = tmp_path / "relatorio.json"
    arquivo.write_text("{}", encoding="utf-8")
    doc = store.salvar_documento(
        arquivo_origem=str(arquivo),
        tipo=TipoDocumento.RELATORIO_FINAL,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        metadata={"cost_run_id": "run-2"},
    )

    updated = store.atualizar_documento_processamento(
        doc.id,
        ia_provider="google",
        ia_modelo="gemini-3-flash-preview",
        tokens_usados=33,
        tempo_processamento_ms=99,
        status=StatusProcessamento.ERRO,
        metadata_patch={"tokens_entrada": 20, "tokens_saida": 13},
    )

    assert updated.status == StatusProcessamento.ERRO
    assert updated.ia_provider == "google"
    assert updated.ia_modelo == "gemini-3-flash-preview"
    assert updated.tokens_usados == 33
    assert updated.metadata["cost_run_id"] == "run-2"
    assert updated.metadata["tokens_entrada"] == 20
    assert updated.metadata["tokens_saida"] == 13


def test_cost_summary_precifica_apenas_split_real(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo_ok = tmp_path / "ok.json"
    arquivo_ok.write_text("{}", encoding="utf-8")
    arquivo_legacy = tmp_path / "legacy.json"
    arquivo_legacy.write_text("{}", encoding="utf-8")

    doc_ok = store.salvar_documento(
        arquivo_origem=str(arquivo_ok),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
        metadata={"tokens_entrada": 200, "tokens_saida": 100, "cost_run_id": "run-ok"},
    )
    doc_legacy = store.salvar_documento(
        arquivo_origem=str(arquivo_legacy),
        tipo=TipoDocumento.RELATORIO_FINAL,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
    )

    summary = build_cost_summary([doc_ok, doc_legacy])

    assert summary["runs_precificados"] == 1
    assert summary["runs_bloqueados"] == 1
    assert summary["bloqueios"]["token_split_missing"] == 1
    assert len(summary["amostras_bloqueadas"]) == 1
    assert summary["amostras_bloqueadas"][0]["documentos_ids"] == [doc_legacy.id]
    assert summary["amostras_bloqueadas"][0]["erro"] == "token_split_missing"
    assert summary["tokens_entrada"] == 200
    assert summary["tokens_saida"] == 100
    assert summary["custo_usd"] > 0


def test_catalogo_gemini_usa_precos_oficiais_standard():
    tokens_entrada = 74_257
    tokens_saida = 12_403

    flash = model_catalog.calculate_cost(
        "google/gemini-2.5-flash",
        input_tokens=tokens_entrada,
        output_tokens=tokens_saida,
    )
    flash_lite = model_catalog.calculate_cost(
        "google/gemini-2.5-flash-lite",
        input_tokens=tokens_entrada,
        output_tokens=tokens_saida,
    )
    flash_3 = model_catalog.calculate_cost(
        "google/gemini-3-flash-preview",
        input_tokens=tokens_entrada,
        output_tokens=tokens_saida,
    )

    assert flash["input_cost_used"] == 0.30
    assert flash["output_cost_used"] == 2.50
    assert flash["cost_per_request"] == 0.053285
    assert flash_lite["input_cost_used"] == 0.10
    assert flash_lite["output_cost_used"] == 0.40
    assert flash_lite["cost_per_request"] == 0.012387
    assert flash_3["input_cost_used"] == 0.50
    assert flash_3["output_cost_used"] == 3.00
    assert flash_3["cost_per_request"] == 0.074338


def test_catalogo_gemini_flash_lite_declara_tools():
    flash_lite = model_catalog.get_model_info("google", "gemini-2.5-flash-lite")

    assert flash_lite is not None
    assert flash_lite.supports_tools is True


def test_cost_summary_conta_um_run_com_json_e_pdf(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo_json = tmp_path / "correcao.json"
    arquivo_json.write_text('{"nota_final": 8}', encoding="utf-8")
    arquivo_pdf = tmp_path / "correcao.pdf"
    arquivo_pdf.write_bytes(b"%PDF-1.4\n")

    doc_json = store.salvar_documento(
        arquivo_origem=str(arquivo_json),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
        metadata={"tokens_entrada": 200, "tokens_saida": 100, "cost_run_id": "run-dual"},
    )
    doc_pdf = store.salvar_documento(
        arquivo_origem=str(arquivo_pdf),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
        metadata={"tokens_entrada": 200, "tokens_saida": 100, "cost_run_id": "run-dual"},
    )

    summary = build_cost_summary([doc_json, doc_pdf])

    assert summary["documentos_analisados"] == 2
    assert summary["runs_analisados"] == 1
    assert summary["runs_precificados"] == 1
    assert summary["tokens_entrada"] == 200
    assert summary["tokens_saida"] == 100
    assert len(summary["amostras"]) == 1
    assert summary["amostras"][0]["cost_run_id"] == "run-dual"
    assert summary["amostras"][0]["documentos_contagem"] == 2
    assert set(summary["amostras"][0]["documentos_ids"]) == {doc_json.id, doc_pdf.id}


def test_cost_summary_expoe_etapa_e_agregado_por_etapa(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo = tmp_path / "correcao.json"
    arquivo.write_text('{"nota_final": 8}', encoding="utf-8")

    doc = store.salvar_documento(
        arquivo_origem=str(arquivo),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
        metadata={
            "tokens_entrada": 200,
            "tokens_saida": 100,
            "cost_run_id": "run-stage",
            "etapa": "corrigir",
        },
    )

    summary = build_cost_summary([doc])

    sample = summary["amostras"][0]
    assert sample["etapa"] == "corrigir"
    assert sample["etapa_origem"] == "metadata"
    assert sample["documentos"][0]["etapa"] == "corrigir"
    assert summary["por_etapa"] == [
        {
            "etapa": "corrigir",
            "runs": 1,
            "tokens_entrada": 200,
            "tokens_saida": 100,
            "custo_usd": sample["custo_usd"],
        }
    ]


def test_cost_summary_expoe_erro_pipeline_em_documento_precificado(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo_pdf = tmp_path / "correcao.pdf"
    arquivo_pdf.write_bytes(b"%PDF-1.4\n")

    doc_pdf = store.salvar_documento(
        arquivo_origem=str(arquivo_pdf),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
        metadata={"tokens_entrada": 200, "tokens_saida": 100, "cost_run_id": "run-erro"},
    )
    updated = store.atualizar_documento_processamento(
        doc_pdf.id,
        status=StatusProcessamento.ERRO,
        metadata_patch={
            "erro_pipeline": "PDF divergiu do JSON",
            "erro_tipo": "pdf_json_consistency",
        },
    )

    summary = build_cost_summary([updated])

    assert summary["runs_precificados"] == 1
    documento = summary["amostras"][0]["documentos"][0]
    assert documento["status"] == "erro"
    assert documento["erro"] == "PDF divergiu do JSON"
    assert documento["erro_tipo"] == "pdf_json_consistency"


def test_cost_summary_expoe_resumo_estruturado_de_erro_provider(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo = tmp_path / "correcao.json"
    arquivo.write_text("{}", encoding="utf-8")
    erro_google = """
    Erro API Google: 429 - {
      "error": {
        "code": 429,
        "message": "You exceeded your current quota, please check your plan and billing details.",
        "status": "RESOURCE_EXHAUSTED"
      }
    }
    * Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests,
    limit: 20, model: gemini-2.5-flash-lite. Please retry later.
    """ + (" detalhe" * 120)

    doc = store.salvar_documento(
        arquivo_origem=str(arquivo),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="google",
        ia_modelo="gemini-2.5-flash-lite",
        tokens_usados=300,
        metadata={
            "tokens_entrada": 200,
            "tokens_saida": 100,
            "cost_run_id": "run-google-429",
            "erro_execucao": erro_google,
        },
    )
    updated = store.atualizar_documento_processamento(
        doc.id,
        status=StatusProcessamento.ERRO,
    )

    summary = build_cost_summary([updated])

    sample = summary["amostras"][0]
    documento = sample["documentos"][0]
    assert sample["erro_codigo"] == 429
    assert sample["erro_provider_status"] == "RESOURCE_EXHAUSTED"
    assert sample["erro_provider_modelo"] == "gemini-2.5-flash-lite"
    assert sample["erro_categoria"] == "quota_exhausted"
    assert len(sample["erro_resumo"]) <= 360
    assert sample["erro_resumo"].endswith("…")
    assert documento["erro_codigo"] == 429
    assert documento["erro_resumo"] == sample["erro_resumo"]


def test_cost_summary_bloqueia_run_com_metadata_conflitante(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo_json = tmp_path / "correcao.json"
    arquivo_json.write_text('{"nota_final": 8}', encoding="utf-8")
    arquivo_pdf = tmp_path / "correcao.pdf"
    arquivo_pdf.write_bytes(b"%PDF-1.4\n")

    doc_json = store.salvar_documento(
        arquivo_origem=str(arquivo_json),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=300,
        metadata={"tokens_entrada": 200, "tokens_saida": 100, "cost_run_id": "run-conflict"},
    )
    doc_pdf = store.salvar_documento(
        arquivo_origem=str(arquivo_pdf),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=310,
        metadata={"tokens_entrada": 210, "tokens_saida": 100, "cost_run_id": "run-conflict"},
    )

    summary = build_cost_summary([doc_json, doc_pdf])

    assert summary["runs_analisados"] == 1
    assert summary["runs_precificados"] == 0
    assert summary["runs_bloqueados"] == 1
    assert summary["bloqueios"]["run_metadata_conflict"] == 1
    assert summary["tokens_entrada"] == 0
    assert summary["tokens_saida"] == 0
    assert summary["amostras"][0]["erro"] == "run_metadata_conflict"
    assert summary["amostras_bloqueadas"][0]["erro"] == "run_metadata_conflict"
    assert set(summary["amostras"][0]["documentos_ids"]) == {doc_json.id, doc_pdf.id}
    assert summary["alertas"][0]["tipo"] == "run_metadata_conflict"


def test_cost_summary_inclui_token_usage_sem_documento():
    usage = TokenUsageRecord(
        id="usage-1",
        cost_run_id="run-no-doc",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        etapa="correcao",
        provider="openai",
        modelo="gpt-5-nano",
        tokens_entrada=300,
        tokens_saida=50,
        status="erro",
        erro="Saída obrigatória incompleta",
        source="test",
    )

    summary = build_cost_summary([], token_usage_records=[usage])

    assert summary["documentos_analisados"] == 0
    assert summary["token_usage_analisados"] == 1
    assert summary["runs_analisados"] == 1
    assert summary["runs_precificados"] == 1
    assert summary["tokens_entrada"] == 300
    assert summary["tokens_saida"] == 50
    assert summary["amostras"][0]["cost_run_id"] == "run-no-doc"
    assert summary["amostras"][0]["etapa"] == "correcao"
    assert summary["amostras"][0]["documentos_contagem"] == 0
    assert summary["amostras"][0]["token_usage_ids"] == ["usage-1"]
    assert summary["por_etapa"][0]["etapa"] == "correcao"


def test_cost_summary_alerta_quando_token_usage_nao_e_duravel(monkeypatch):
    import cost_tracking

    class FakeTokenUsageStore:
        def status(self):
            return {
                "local_path": "/tmp/token_usage",
                "local_record_count": 0,
                "local_error": None,
                "supabase": {
                    "enabled": True,
                    "table_available": False,
                    "record_count": None,
                    "error": "PGRST205",
                },
                "durable": False,
            }

        def list_records(self, limit=None):
            return []

    monkeypatch.setattr(cost_tracking, "token_usage_store", FakeTokenUsageStore())

    summary = cost_tracking.build_cost_summary([], token_usage_records=[])

    assert summary["custos_persistencia_status"] == "parcial_sem_token_usage_duravel"
    assert summary["token_usage_durable"] is False
    assert summary["token_usage_backend"]["durable"] is False
    assert any(
        alerta["tipo"] == "token_usage_not_durable"
        and alerta["severidade"] == "bloqueante"
        for alerta in summary["alertas"]
    )


def test_cost_summary_informa_quando_token_usage_duravel_esta_vazio(monkeypatch):
    import cost_tracking

    class FakeTokenUsageStore:
        def status(self):
            return {
                "local_path": "/tmp/token_usage",
                "local_record_count": 0,
                "local_error": None,
                "supabase": {
                    "enabled": True,
                    "table_available": True,
                    "record_count": 0,
                    "error": None,
                    "error_code": None,
                },
                "durable": True,
            }

        def list_records(self, limit=None):
            return []

    monkeypatch.setattr(cost_tracking, "token_usage_store", FakeTokenUsageStore())

    summary = cost_tracking.build_cost_summary([], token_usage_records=[])

    assert summary["custos_persistencia_status"] == "duravel"
    assert summary["token_usage_durable"] is True
    assert any(
        alerta["tipo"] == "token_usage_sem_registros"
        and alerta["severidade"] == "informativo"
        for alerta in summary["alertas"]
    )


@pytest.mark.asyncio
async def test_cost_status_nao_fica_ok_sem_token_usage_duravel(monkeypatch):
    import routes_costs

    monkeypatch.setattr(
        routes_costs,
        "build_cost_summary",
        lambda limit=500: {
            "catalog_loaded": True,
            "storage_backend": "postgresql",
            "persistent_storage": True,
            "custos_persistencia_status": "parcial_sem_token_usage_duravel",
            "token_usage_backend": {"durable": False},
            "token_usage_analisados": 0,
            "runs_analisados": 0,
            "runs_precificados": 0,
            "runs_bloqueados": 0,
            "bloqueios": {},
            "alertas": [{"tipo": "token_usage_not_durable"}],
        },
    )

    status = await routes_costs.get_cost_status()

    assert status["ok"] is False
    assert status["custos_persistencia_status"] == "parcial_sem_token_usage_duravel"
    assert status["alertas"][0]["tipo"] == "token_usage_not_durable"


def test_token_usage_store_persiste_json_mensal(tmp_path):
    store = TokenUsageStore(tmp_path, use_supabase=False)
    usage = TokenUsageRecord(
        id="usage-persist",
        cost_run_id="run-persist",
        atividade_id="ativ-1",
        aluno_id=None,
        etapa="tools",
        provider="openai",
        modelo="gpt-5-nano",
        tokens_entrada=11,
        tokens_saida=7,
        status="erro",
        criado_em="2026-05-15T12:00:00+00:00",
    )

    store.add(usage)

    saved_path = tmp_path / "token_usage" / "2026-05.json"
    assert saved_path.exists()
    loaded = store.list_records()
    assert len(loaded) == 1
    assert loaded[0].id == "usage-persist"
    assert loaded[0].tokens_total == 18


def test_token_usage_store_status_expoe_backend_local(tmp_path):
    store = TokenUsageStore(tmp_path, use_supabase=False)
    usage = TokenUsageRecord(
        id="usage-status",
        cost_run_id="run-status",
        atividade_id=None,
        aluno_id=None,
        etapa="tools",
        provider="openai",
        modelo="gpt-5-nano",
        tokens_entrada=1,
        tokens_saida=2,
        status="erro",
    )
    store.add(usage)

    status = store.status()

    assert status["local_record_count"] == 1
    assert status["supabase"]["enabled"] is False
    assert status["supabase"]["table_available"] is False
    assert status["durable"] is False


def test_token_usage_store_status_expoe_codigo_migration_supabase(tmp_path, monkeypatch):
    import token_usage

    class FakeQuery:
        def select(self, *args, **kwargs):
            return self

        def limit(self, *args, **kwargs):
            return self

        def execute(self):
            raise Exception(
                "{'message': \"Could not find the table 'public.token_usage' in the schema cache\", "
                "'code': 'PGRST205', 'hint': None, 'details': None}"
            )

    class FakeClient:
        def table(self, table_name):
            assert table_name == "token_usage"
            return FakeQuery()

    monkeypatch.setattr(token_usage, "supabase_db", SimpleNamespace(client=FakeClient()))
    store = TokenUsageStore(tmp_path, use_supabase=True)

    status = store.status()

    assert status["supabase"]["enabled"] is True
    assert status["supabase"]["table_available"] is False
    assert status["supabase"]["error_code"] == "PGRST205"
    assert status["supabase"]["missing_migration"] is True
    assert status["supabase"]["migration_path"] == "backend/migrations/002_create_token_usage.sql"
    assert status["durable"] is False


def test_cost_summary_deduplica_documento_e_token_usage_mesmo_run(tmp_path):
    store, atividade, aluno = _seed_storage(tmp_path)
    arquivo_json = tmp_path / "correcao.json"
    arquivo_json.write_text('{"nota_final": 8}', encoding="utf-8")
    doc = store.salvar_documento(
        arquivo_origem=str(arquivo_json),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="openai",
        ia_modelo="gpt-5-nano",
        tokens_usados=350,
        metadata={"tokens_entrada": 300, "tokens_saida": 50, "cost_run_id": "run-shared"},
    )
    usage = TokenUsageRecord(
        id="usage-shared",
        cost_run_id="run-shared",
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        etapa="correcao",
        provider="openai",
        modelo="gpt-5-nano",
        tokens_entrada=300,
        tokens_saida=50,
        status="erro",
        source="test",
    )

    summary = build_cost_summary([doc], token_usage_records=[usage])

    assert summary["runs_analisados"] == 1
    assert summary["runs_precificados"] == 1
    assert summary["tokens_entrada"] == 300
    assert summary["tokens_saida"] == 50
    assert summary["amostras"][0]["documentos_ids"] == [doc.id]
    assert summary["amostras"][0]["token_usage_ids"] == ["usage-shared"]


@pytest.mark.asyncio
async def test_executar_com_tools_falha_sem_pdf_obrigatorio(monkeypatch):
    import executor as executor_module
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="nano",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5-nano",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            return {
                "content": "",
                "tokens": 13,
                "input_tokens": 10,
                "output_tokens": 3,
                "tool_calls": [
                    {
                        "name": "create_document",
                        "input": {
                            "documents": [
                                {"filename": "correcao.json", "content": '{"nota_final": 7}'}
                            ]
                        },
                    }
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)
    record_usage = MagicMock()
    monkeypatch.setattr(executor_module, "record_token_usage", record_usage)

    executor = PipelineExecutor()
    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="nano",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert "Saída obrigatória incompleta" in resultado.erro
    assert "fallback automático" in resultado.erro
    record_usage.assert_called_once()
    assert record_usage.call_args.kwargs["status"] == "erro"
    assert record_usage.call_args.kwargs["tokens_entrada"] == 20
    assert record_usage.call_args.kwargs["tokens_saida"] == 6


@pytest.mark.asyncio
async def test_executar_com_tools_sucesso_registra_token_usage_mesmo_com_documentos(monkeypatch):
    import executor as executor_module
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gemini",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-2.5-flash",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.calls = 0

        async def chat_with_tools(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                kwargs["context"].created_document_ids.append("doc-json")
                return {
                    "content": "",
                    "tokens": 13,
                    "input_tokens": 10,
                    "output_tokens": 3,
                    "tool_calls": [{"name": "create_document", "is_error": False}],
                }
            kwargs["context"].created_document_ids.append("doc-pdf")
            return {
                "content": "",
                "tokens": 26,
                "input_tokens": 20,
                "output_tokens": 6,
                "tool_calls": [
                    {
                        "name": "execute_python_code",
                        "is_error": False,
                        "files_generated": ["relatorio.pdf"],
                    }
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)
    record_usage = MagicMock()
    monkeypatch.setattr(executor_module, "record_token_usage", record_usage)

    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            status=StatusProcessamento.CONCLUIDO,
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            status=StatusProcessamento.CONCLUIDO,
        ),
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gemini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TAREFA,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    record_usage.assert_called_once()
    kwargs = record_usage.call_args.kwargs
    assert kwargs["status"] == "concluido"
    assert kwargs["tokens_entrada"] == 30
    assert kwargs["tokens_saida"] == 9
    assert kwargs["metadata"]["documentos_ids"] == ["doc-json", "doc-pdf"]


@pytest.mark.asyncio
async def test_executar_com_tools_falha_quando_execute_code_nao_persiste_pdf(monkeypatch):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="nano",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5-nano",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        calls = 0

        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            DummyClient.calls += 1
            context = kwargs["context"]
            if "doc-json" not in context.created_document_ids:
                context.created_document_ids.append("doc-json")
            return {
                "content": "",
                "tokens": 13,
                "input_tokens": 10,
                "output_tokens": 3,
                "tool_calls": [
                    {
                        "id": f"json-{DummyClient.calls}",
                        "name": "create_document",
                        "input": {"content": '{"nota_final": 7}'},
                        "is_error": False,
                        "files_generated": [],
                    },
                    {
                        "id": f"pdf-{DummyClient.calls}",
                        "name": "execute_python_code",
                        "input": {"code": "print('sem pdf')"},
                        "is_error": False,
                        "files_generated": [],
                    },
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(
        return_value=SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        )
    )
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="nano",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert resultado.tentativas == 2
    assert "PDF persistido via execute_python_code" in resultado.erro
    assert "sem arquivo gerado" in resultado.erro
    update_kwargs = executor.storage.atualizar_documento_processamento.call_args.kwargs
    assert update_kwargs["status"] == StatusProcessamento.ERRO
    assert update_kwargs["ia_provider"] == "openai"
    assert update_kwargs["ia_modelo"] == "gpt-5-nano"
    assert update_kwargs["tokens_usados"] == 26
    assert update_kwargs["metadata_patch"]["tokens_entrada"] == 20
    assert update_kwargs["metadata_patch"]["tokens_saida"] == 6


@pytest.mark.asyncio
async def test_executar_com_tools_repara_pdf_nao_persistido_com_retry(monkeypatch, tmp_path):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="nano",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5-nano",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        calls = 0

        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            DummyClient.calls += 1
            context = kwargs["context"]
            if DummyClient.calls == 1:
                context.created_document_ids.append("doc-json")
                return {
                    "content": "",
                    "tokens": 13,
                    "input_tokens": 10,
                    "output_tokens": 3,
                    "tool_calls": [
                        {
                            "id": "json-1",
                            "name": "create_document",
                            "input": {"content": '{"nota_final": 7}'},
                            "is_error": False,
                            "files_generated": [],
                        },
                        {
                            "id": "pdf-1",
                            "name": "execute_python_code",
                            "input": {"code": "print('sem pdf')"},
                            "is_error": False,
                            "files_generated": [],
                        },
                    ],
                }

            context.created_document_ids.append("doc-pdf")
            return {
                "content": "",
                "tokens": 17,
                "input_tokens": 12,
                "output_tokens": 5,
                "tool_calls": [
                    {
                        "id": "pdf-2",
                        "name": "execute_python_code",
                        "input": {
                            "code": "from reportlab.pdfgen import canvas\ncanvas.Canvas('correcao.pdf').save()",
                            "output_files": ["correcao.pdf"],
                        },
                        "is_error": False,
                        "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                    }
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 3,
                "questoes": [{"numero": 1, "nota": 3, "acerto": True}],
                "total_acertos": 1,
                "total_erros": 0,
                "feedback_geral": "Bom desempenho geral.",
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text(
        (40, 80),
        "Nota final: 3.0 / 10.0\nQuestão 1 — Acerto | Nota: 3.0",
        fontsize=11,
    )
    pdf.save(str(pdf_path))
    pdf.close()

    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.resolver_caminho_documento = MagicMock(
        side_effect=lambda doc: {"doc-json": json_path, "doc-pdf": pdf_path}[doc.id]
    )
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="nano",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    assert resultado.tentativas == 2
    assert DummyClient.calls == 2
    assert executor.storage.atualizar_documento_processamento.call_count == 2


@pytest.mark.asyncio
async def test_executar_com_tools_repara_pdf_inconsistente_com_json(monkeypatch, tmp_path):
    import fitz
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="mini",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5.4-mini",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    def write_pdf(path, text):
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_textbox(fitz.Rect(40, 40, 560, 800), text, fontsize=11)
        pdf.save(str(path))
        pdf.close()

    json_path = tmp_path / "correcao.json"
    bad_pdf_path = tmp_path / "correcao_bad.pdf"
    good_pdf_path = tmp_path / "correcao_good.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3, "acerto": True},
                    {"numero": 2, "nota": 3, "acerto": True},
                    {"numero": 3, "nota": 0, "acerto": False},
                    {"numero": 4, "nota": 2, "acerto": True},
                ],
                "total_acertos": 3,
                "total_erros": 1,
                "feedback_geral": "Bom desempenho geral.",
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    write_pdf(
        bad_pdf_path,
        "Nota final: 8.0 / 10.0\nQuestão 3 — Erro | Nota: 3.0\n",
    )
    write_pdf(
        good_pdf_path,
        "Nota final: 8.0 / 10.0\nQuestão 3 — Erro | Nota: 0.0\n",
    )

    class DummyClient:
        calls = 0

        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            DummyClient.calls += 1
            context = kwargs["context"]
            if DummyClient.calls == 1:
                context.created_document_ids.append("doc-json")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "json-1",
                            "name": "create_document",
                            "input": {"content": json_path.read_text(encoding="utf-8")},
                            "is_error": False,
                            "files_generated": [],
                        }
                    ],
                }

            doc_id = "doc-pdf-bad" if DummyClient.calls == 2 else "doc-pdf-good"
            context.created_document_ids.append(doc_id)
            return {
                "content": "",
                "tokens": 20,
                "input_tokens": 15,
                "output_tokens": 5,
                "tool_calls": [
                    {
                        "id": f"pdf-{DummyClient.calls}",
                        "name": "execute_python_code",
                        "input": {
                            "code": "from reportlab.pdfgen import canvas\ncanvas.Canvas('correcao.pdf').save()",
                            "output_files": ["correcao.pdf"],
                        },
                        "is_error": False,
                        "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                    }
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-pdf-bad": SimpleNamespace(
            id="doc-pdf-bad",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
        "doc-pdf-good": SimpleNamespace(
            id="doc-pdf-good",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "doc-json": json_path,
        "doc-pdf-bad": bad_pdf_path,
        "doc-pdf-good": good_pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="mini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    assert resultado.tentativas == 3
    assert DummyClient.calls == 3
    assert any(
        call.args[0] == "doc-pdf-bad"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "pdf_json_consistency"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )


@pytest.mark.asyncio
async def test_executar_com_tools_repara_json_schema_invalido(monkeypatch, tmp_path):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gpt4o",
        tipo=ProviderType.OPENAI,
        modelo="gpt-4o",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    bad_json_path = tmp_path / "analise_bad.json"
    good_json_path = tmp_path / "analise_good.json"
    pdf_path = tmp_path / "analise.pdf"
    bad_json_path.write_text('[{"habilidades": [{"nome": "Porcentagem"}]}]', encoding="utf-8")
    good_json_path.write_text(
        json.dumps(
            {
                "habilidades": [
                    {
                        "nome": "Porcentagem",
                        "nivel": "em_desenvolvimento",
                        "evidencias": ["A questão de porcentagem concentrou o erro."],
                        "nota": 6.0,
                    }
                ],
                "indicadores": {
                    "proficiencia_geral": 60.0,
                    "areas_destaque": [],
                    "areas_atencao": ["Porcentagem"],
                },
                "recomendacoes": [
                    {
                        "tipo": "revisao",
                        "descricao": "Revisar conversão de porcentagens.",
                        "prioridade": "alta",
                    }
                ],
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    pdf_path.write_bytes(b"%PDF-1.4\n")

    class DummyClient:
        calls = 0

        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            DummyClient.calls += 1
            context = kwargs["context"]
            if DummyClient.calls == 1:
                context.created_document_ids.append("doc-json-bad")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "json-1",
                            "name": "create_document",
                            "input": {"content": bad_json_path.read_text(encoding="utf-8")},
                            "is_error": False,
                            "files_generated": [],
                        }
                    ],
                }
            if DummyClient.calls == 2:
                context.created_document_ids.append("doc-pdf")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "pdf-1",
                            "name": "execute_python_code",
                            "input": {"output_files": ["analise_habilidades.pdf"]},
                            "is_error": False,
                            "files_generated": [{"filename": "analise_habilidades.pdf", "size_bytes": 128}],
                        }
                    ],
                }

            context.created_document_ids.append("doc-json-good")
            return {
                "content": "",
                "tokens": 10,
                "input_tokens": 8,
                "output_tokens": 2,
                "tool_calls": [
                    {
                        "id": "json-2",
                        "name": "create_document",
                        "input": {"content": good_json_path.read_text(encoding="utf-8")},
                        "is_error": False,
                        "files_generated": [],
                    }
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs = {
        "doc-json-bad": SimpleNamespace(
            id="doc-json-bad",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-json-good": SimpleNamespace(
            id="doc-json-good",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "doc-json-bad": bad_json_path,
        "doc-json-good": good_json_path,
        "doc-pdf": pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="analise",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gpt4o",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.ANALISE_HABILIDADES,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    assert resultado.tentativas == 3
    assert DummyClient.calls == 3
    assert any(
        call.args[0] == "doc-json-bad"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "json_schema_validation"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )


@pytest.mark.asyncio
async def test_executar_com_tools_repara_correcao_json_array(monkeypatch, tmp_path):
    import fitz
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gpt4o",
        tipo=ProviderType.OPENAI,
        modelo="gpt-4o",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    bad_json_path = tmp_path / "correcao_bad.json"
    bad_json_path_2 = tmp_path / "correcao_bad_2.json"
    stale_json_path = tmp_path / "correcao_stale.json"
    good_json_path = tmp_path / "correcao_good.json"
    stale_pdf_path = tmp_path / "correcao_stale.pdf"
    good_pdf_path = tmp_path / "correcao_good.pdf"
    bad_json_path.write_text(
        '[{"nota_final": 8, "questoes": [{"numero": 3, "nota": 0}]}]',
        encoding="utf-8",
    )
    bad_json_path_2.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3, "acerto": True},
                    {"numero": 2, "nota": 3, "acerto": True},
                    {"numero": 3, "nota": 0, "acerto": False},
                    {"numero": 4, "nota": 2, "acerto": True},
                ],
                "total_acertos": 3,
                "total_erros": 1,
                "feedback_geral_texto": "Campo errado: precisa ser feedback_geral.",
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    stale_json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3, "acerto": True},
                    {"numero": 2, "nota": 3, "acerto": True},
                    {"numero": 3, "nota": 0, "acerto": False},
                    {"numero": 4, "nota": 2, "acerto": True},
                ],
                "total_acertos": 3,
                "total_erros": 1,
                "feedback_geral": "Bom desempenho geral.",
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    good_json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3, "acerto": True},
                    {"numero": 2, "nota": 3, "acerto": True},
                    {"numero": 3, "nota": 0, "acerto": False},
                    {"numero": 4, "nota": 2, "acerto": True},
                ],
                "total_acertos": 3,
                "total_erros": 1,
                "feedback_geral": "Bom desempenho geral.",
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    for pdf_path in (stale_pdf_path, good_pdf_path):
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_textbox(
            fitz.Rect(40, 40, 560, 800),
            "Nota final: 8.0 / 10.0\nQuestão 3 — Erro | Nota: 0.0\n",
            fontsize=11,
        )
        pdf.save(str(pdf_path))
        pdf.close()

    class DummyClient:
        calls = 0

        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            DummyClient.calls += 1
            context = kwargs["context"]
            if DummyClient.calls == 1:
                context.created_document_ids.extend(
                    ["doc-json-bad", "doc-json-stale", "doc-json-bad-2"]
                )
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "json-1",
                            "name": "create_document",
                            "input": {"content": bad_json_path.read_text(encoding="utf-8")},
                            "is_error": False,
                            "files_generated": [],
                        }
                    ],
                }
            if DummyClient.calls == 2:
                context.created_document_ids.append("doc-pdf-stale")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "pdf-1",
                            "name": "execute_python_code",
                            "input": {"output_files": ["correcao.pdf"]},
                            "is_error": False,
                            "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                        }
                    ],
                }

            context.created_document_ids.extend(["doc-json-good", "doc-pdf-good"])
            return {
                "content": "",
                "tokens": 10,
                "input_tokens": 8,
                "output_tokens": 2,
                "tool_calls": [
                    {
                        "id": "json-2",
                        "name": "create_document",
                        "input": {"content": good_json_path.read_text(encoding="utf-8")},
                        "is_error": False,
                        "files_generated": [],
                    },
                    {
                        "id": "pdf-2",
                        "name": "execute_python_code",
                        "input": {"output_files": ["correcao.pdf"]},
                        "is_error": False,
                        "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                    },
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs = {
        "doc-json-bad": SimpleNamespace(
            id="doc-json-bad",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-json-bad-2": SimpleNamespace(
            id="doc-json-bad-2",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-json-stale": SimpleNamespace(
            id="doc-json-stale",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-json-good": SimpleNamespace(
            id="doc-json-good",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-pdf-stale": SimpleNamespace(
            id="doc-pdf-stale",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
        "doc-pdf-good": SimpleNamespace(
            id="doc-pdf-good",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "doc-json-bad": bad_json_path,
        "doc-json-bad-2": bad_json_path_2,
        "doc-json-stale": stale_json_path,
        "doc-json-good": good_json_path,
        "doc-pdf-stale": stale_pdf_path,
        "doc-pdf-good": good_pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gpt4o",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    assert resultado.tentativas == 3
    assert any(
        call.args[0] == "doc-json-bad"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "json_schema_validation"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )
    assert any(
        call.args[0] == "doc-json-bad-2"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "json_schema_validation"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )
    assert any(
        call.args[0] == "doc-json-bad-2"
        and "feedback_geral" in call.kwargs["metadata_patch"].get("erro_pipeline", "")
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )
    assert any(
        call.args[0] == "doc-json-stale"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "stale_tool_artifact"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )
    assert any(
        call.args[0] == "doc-pdf-stale"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "stale_tool_artifact"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )


@pytest.mark.asyncio
async def test_executar_com_tools_rejeita_correcao_que_troca_resposta_do_aluno(
    monkeypatch,
    tmp_path,
):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gpt54mini",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5.4-mini",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    respostas_path = tmp_path / "respostas.json"
    gabarito_path = tmp_path / "gabarito.json"
    respostas_path.write_text(
        json.dumps({"respostas": [{"questao_numero": 3, "resposta_aluno": "25."}]}),
        encoding="utf-8",
    )
    gabarito_path.write_text(
        json.dumps({"respostas": [{"questao_numero": 3, "resposta_correta": "30"}]}),
        encoding="utf-8",
    )
    bad_correction_path = tmp_path / "correcao_bad.json"
    pdf_path = tmp_path / "correcao.pdf"

    bad_correction = {
        "nota_final": 10,
        "questoes": [
            {
                "numero": 3,
                "resposta_aluno": "30",
                "resposta_correta": "30",
                "nota": 2,
                "nota_maxima": 2,
                "acerto": True,
                "feedback": "Correto.",
            }
        ],
        "total_acertos": 1,
        "total_erros": 0,
        "feedback_geral": "Tudo certo.",
        "_avisos_documento": [],
        "_avisos_questao": [],
    }
    bad_correction_path.write_text(json.dumps(bad_correction), encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\n")

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            context = kwargs["context"]
            context.created_document_ids.extend(["doc-json", "doc-pdf"])
            return {
                "content": "",
                "tokens": 10,
                "input_tokens": 8,
                "output_tokens": 2,
                "tool_calls": [
                    {
                        "id": "json-bad",
                        "name": "create_document",
                        "input": {
                            "documents": [
                                {
                                    "filename": "correcao.json",
                                    "content": bad_correction_path.read_text(encoding="utf-8"),
                                }
                            ]
                        },
                        "is_error": False,
                        "files_generated": [],
                    },
                    {
                        "id": "pdf-ok",
                        "name": "execute_python_code",
                        "input": {"output_files": ["correcao.pdf"]},
                        "is_error": False,
                        "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                    },
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs_base = [
        SimpleNamespace(
            id="gabarito-json",
            tipo=TipoDocumento.EXTRACAO_GABARITO,
            extensao=".json",
            criado_em="2026-05-17T10:00:00",
            metadata={},
        )
    ]
    docs_aluno = [
        SimpleNamespace(
            id="respostas-json",
            tipo=TipoDocumento.EXTRACAO_RESPOSTAS,
            extensao=".json",
            criado_em="2026-05-17T10:01:00",
            metadata={},
        )
    ]
    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            nome_arquivo="correcao.json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="pipeline_tool",
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            nome_arquivo="correcao.pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "gabarito-json": gabarito_path,
        "respostas-json": respostas_path,
        "doc-json": bad_correction_path,
        "doc-pdf": pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.listar_documentos = MagicMock(
        side_effect=lambda _atividade_id, aluno_id=None: docs_aluno if aluno_id else docs_base
    )
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gpt54mini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert "resposta_aluno divergente da EXTRAIR_RESPOSTAS" in (resultado.erro or "")
    assert "nota_final 10 mas a soma de questoes[].nota e 2" in (resultado.erro or "")


@pytest.mark.asyncio
async def test_executar_com_tools_aceita_correcao_de_resposta_em_branco_rastreavel(
    monkeypatch,
    tmp_path,
):
    import fitz
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gpt54mini",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5.4-mini",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    respostas_path = tmp_path / "respostas.json"
    gabarito_path = tmp_path / "gabarito.json"
    correcao_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    respostas_path.write_text(
        json.dumps(
            {
                "respostas": [
                    {
                        "questao_numero": 2,
                        "resposta_aluno": "",
                        "em_branco": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    gabarito_path.write_text(
        json.dumps({"respostas": [{"questao_numero": 2, "resposta_correta": "Área = 20 cm²"}]}),
        encoding="utf-8",
    )
    correcao = {
        "nota_final": 0,
        "questoes": [
            {
                "numero": 2,
                "resposta_aluno": "",
                "resposta_correta": "Área = 20 cm²",
                "nota": 0,
                "nota_maxima": 2,
                "acerto": False,
                "feedback": "Resposta em branco registrada corretamente.",
            }
        ],
        "total_acertos": 0,
        "total_erros": 1,
        "feedback_geral": "Questão em branco identificada e corrigida sem inventar resposta.",
        "_avisos_documento": [],
        "_avisos_questao": [],
    }
    correcao_path.write_text(json.dumps(correcao), encoding="utf-8")

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(
        fitz.Rect(40, 40, 560, 800),
        "Correção\nNota final: 0.0 / 10.0\nQuestão 2 — Erro | Nota: 0.0\nFeedback Geral\n"
        "Questão em branco identificada e corrigida sem inventar resposta.",
        fontsize=11,
    )
    pdf.save(str(pdf_path))
    pdf.close()

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            context = kwargs["context"]
            context.created_document_ids.extend(["doc-json", "doc-pdf"])
            return {
                "content": "",
                "tokens": 10,
                "input_tokens": 8,
                "output_tokens": 2,
                "tool_calls": [
                    {
                        "id": "json-ok",
                        "name": "create_document",
                        "input": {
                            "documents": [
                                {
                                    "filename": "correcao.json",
                                    "content": correcao_path.read_text(encoding="utf-8"),
                                }
                            ]
                        },
                        "is_error": False,
                        "files_generated": [],
                    },
                    {
                        "id": "pdf-ok",
                        "name": "execute_python_code",
                        "input": {"output_files": ["correcao.pdf"]},
                        "is_error": False,
                        "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                    },
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs_base = [
        SimpleNamespace(
            id="gabarito-json",
            tipo=TipoDocumento.EXTRACAO_GABARITO,
            extensao=".json",
            criado_em="2026-05-17T10:00:00",
            metadata={},
        )
    ]
    docs_aluno = [
        SimpleNamespace(
            id="respostas-json",
            tipo=TipoDocumento.EXTRACAO_RESPOSTAS,
            extensao=".json",
            criado_em="2026-05-17T10:01:00",
            metadata={},
        )
    ]
    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            nome_arquivo="correcao.json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="pipeline_tool",
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            nome_arquivo="correcao.pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "gabarito-json": gabarito_path,
        "respostas-json": respostas_path,
        "doc-json": correcao_path,
        "doc-pdf": pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.listar_documentos = MagicMock(
        side_effect=lambda _atividade_id, aluno_id=None: docs_aluno if aluno_id else docs_base
    )
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gpt54mini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    assert resultado.resposta_parsed["questoes"][0]["resposta_aluno"] == ""
    assert "sem resposta_aluno rastreável" not in (resultado.erro or "")


@pytest.mark.asyncio
async def test_executar_com_tools_rejeita_acerto_literal_divergente_do_gabarito(
    monkeypatch,
    tmp_path,
):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gpt54mini",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5.4-mini",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    respostas_path = tmp_path / "respostas.json"
    gabarito_path = tmp_path / "gabarito.json"
    respostas_path.write_text(
        json.dumps({"respostas": [{"questao_numero": 1, "resposta_aluno": "B"}]}),
        encoding="utf-8",
    )
    gabarito_path.write_text(
        json.dumps({"respostas": [{"questao_numero": 1, "resposta_correta": "C"}]}),
        encoding="utf-8",
    )
    bad_correction_path = tmp_path / "correcao_literal_bad.json"
    pdf_path = tmp_path / "correcao.pdf"

    bad_correction = {
        "nota_final": 1,
        "questoes": [
            {
                "numero": 1,
                "resposta_aluno": "B",
                "resposta_correta": "C",
                "nota": 1,
                "nota_maxima": 1,
                "acerto": True,
                "feedback": "Correto.",
            }
        ],
        "total_acertos": 1,
        "total_erros": 0,
        "feedback_geral": "Tudo certo.",
        "_avisos_documento": [],
        "_avisos_questao": [],
    }
    bad_correction_path.write_text(json.dumps(bad_correction), encoding="utf-8")
    pdf_path.write_bytes(b"%PDF-1.4\n")

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            context = kwargs["context"]
            context.created_document_ids.extend(["doc-json", "doc-pdf"])
            return {
                "content": "",
                "tokens": 10,
                "input_tokens": 8,
                "output_tokens": 2,
                "tool_calls": [
                    {
                        "id": "json-bad",
                        "name": "create_document",
                        "input": {
                            "documents": [
                                {
                                    "filename": "correcao.json",
                                    "content": bad_correction_path.read_text(encoding="utf-8"),
                                }
                            ]
                        },
                        "is_error": False,
                        "files_generated": [],
                    },
                    {
                        "id": "pdf-ok",
                        "name": "execute_python_code",
                        "input": {"output_files": ["correcao.pdf"]},
                        "is_error": False,
                        "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
                    },
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs_base = [
        SimpleNamespace(
            id="gabarito-json",
            tipo=TipoDocumento.EXTRACAO_GABARITO,
            extensao=".json",
            criado_em="2026-05-17T10:00:00",
            metadata={},
        )
    ]
    docs_aluno = [
        SimpleNamespace(
            id="respostas-json",
            tipo=TipoDocumento.EXTRACAO_RESPOSTAS,
            extensao=".json",
            criado_em="2026-05-17T10:01:00",
            metadata={},
        )
    ]
    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            nome_arquivo="correcao.json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="pipeline_tool",
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            nome_arquivo="correcao.pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "gabarito-json": gabarito_path,
        "respostas-json": respostas_path,
        "doc-json": bad_correction_path,
        "doc-pdf": pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.listar_documentos = MagicMock(
        side_effect=lambda _atividade_id, aluno_id=None: docs_aluno if aluno_id else docs_base
    )
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gpt54mini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert "resposta_aluno literal divergir do gabarito" in (resultado.erro or "")


@pytest.mark.asyncio
async def test_executar_com_tools_falha_json_placeholder_analisar(monkeypatch, tmp_path):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="nano",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5-nano",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            context = kwargs["context"]
            context.created_document_ids.extend(["doc-json", "doc-pdf"])
            return {
                "content": "",
                "tokens": 20,
                "input_tokens": 15,
                "output_tokens": 5,
                "tool_calls": [
                    {
                        "id": "json-1",
                        "name": "create_document",
                        "input": {
                            "documents": [
                                {
                                    "filename": "analise_habilidades_student123.json",
                                    "content": '{"habilidades": [{"nome": "student123"}]}',
                                }
                            ]
                        },
                        "is_error": False,
                        "files_generated": [{"filename": "analise_habilidades_student123.json"}],
                    },
                    {
                        "id": "pdf-1",
                        "name": "execute_python_code",
                        "input": {"code": "gera pdf"},
                        "is_error": False,
                        "files_generated": [{"filename": "analise.pdf", "size_bytes": 128}],
                    },
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    json_path = tmp_path / "analise_habilidades_student123.json"
    json_path.write_text(
        '{"habilidades": [{"nome": "student123", "nivel": "placeholder"}]}',
        encoding="utf-8",
    )

    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            nome_arquivo="analise_habilidades_student123.json",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="pipeline_tool",
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            nome_arquivo="analise.pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.resolver_caminho_documento = MagicMock(return_value=json_path)
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="analise habilidades de Eric",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="nano",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.ANALISE_HABILIDADES,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert "placeholder proibido" in resultado.erro
    assert "student123" in resultado.erro
    assert any(
        call_args.kwargs["status"] == StatusProcessamento.ERRO
        and call_args.kwargs["metadata_patch"].get("erro_tipo") == "json_schema_validation"
        for call_args in executor.storage.atualizar_documento_processamento.call_args_list
    )
    final_error_calls = [
        call_args
        for call_args in executor.storage.atualizar_documento_processamento.call_args_list
        if call_args.kwargs["metadata_patch"].get("custo_origem") == "tool_use_error"
    ]
    assert len(final_error_calls) >= 2
    for call_args in final_error_calls:
        assert call_args.kwargs["status"] == StatusProcessamento.ERRO


@pytest.mark.asyncio
async def test_executar_com_tools_repara_relatorio_nota_final_divergente(
    monkeypatch,
    tmp_path,
):
    import fitz
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderType

    model = SimpleNamespace(
        id="gpt5nano",
        tipo=ProviderType.OPENAI,
        modelo="gpt-5-nano",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=2048,
        temperature=0,
        suporta_temperature=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    correction_path = tmp_path / "correcao.json"
    bad_json_path = tmp_path / "relatorio_bad.json"
    good_json_path = tmp_path / "relatorio_good.json"
    bad_pdf_path = tmp_path / "relatorio_bad.pdf"
    good_pdf_path = tmp_path / "relatorio_good.pdf"

    correction_path.write_text(
        json.dumps({"nota_final": 8.0, "questoes": [{"numero": 3, "nota": 0.0}]}),
        encoding="utf-8",
    )
    bad_json_path.write_text(
        json.dumps({"nota_final": 0.0, "resumo_geral": "Resumo errado."}),
        encoding="utf-8",
    )
    good_json_path.write_text(
        json.dumps(
            {
                "nota_final": 8.0,
                "resumo_geral": "Resumo corrigido.",
                "pontos_fortes": ["Resolveu três questões corretamente."],
                "areas_melhoria": ["Porcentagens"],
                "recomendacoes": [
                    {
                        "tipo": "revisao",
                        "descricao": "Praticar conversão entre porcentagem e fração.",
                        "prioridade": "alta",
                    }
                ],
                "detalhamento": "A nota final segue a correção oficial.",
                "_avisos_documento": [],
                "_avisos_questao": [],
                "_fontes_utilizadas": ["CORRIGIR", "ANALISAR_HABILIDADES"],
            }
        ),
        encoding="utf-8",
    )

    def _write_pdf(path, text):
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_textbox(fitz.Rect(40, 40, 560, 800), text, fontsize=11)
        pdf.save(str(path))
        pdf.close()

    _write_pdf(bad_pdf_path, "Relatório Final\nNota final: 0.0\n")
    _write_pdf(good_pdf_path, "Relatório Final\nNota final: 8.0\nProficiência geral: 72%\n")

    class DummyClient:
        calls = 0

        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            DummyClient.calls += 1
            context = kwargs["context"]
            if DummyClient.calls == 1:
                context.created_document_ids.append("doc-json-bad")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "json-bad",
                            "name": "create_document",
                            "input": {"content": bad_json_path.read_text(encoding="utf-8")},
                            "is_error": False,
                            "files_generated": [],
                        }
                    ],
                }
            if DummyClient.calls == 2:
                context.created_document_ids.append("doc-pdf-bad")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "pdf-bad",
                            "name": "execute_python_code",
                            "input": {"output_files": ["relatorio.pdf"]},
                            "is_error": False,
                            "files_generated": [{"filename": "relatorio.pdf", "size_bytes": 128}],
                        }
                    ],
                }
            if DummyClient.calls == 3:
                context.created_document_ids.append("doc-json-good")
                return {
                    "content": "",
                    "tokens": 10,
                    "input_tokens": 8,
                    "output_tokens": 2,
                    "tool_calls": [
                        {
                            "id": "json-good",
                            "name": "create_document",
                            "input": {"content": good_json_path.read_text(encoding="utf-8")},
                            "is_error": False,
                            "files_generated": [],
                        }
                    ],
                }

            context.created_document_ids.append("doc-pdf-good")
            return {
                "content": "",
                "tokens": 10,
                "input_tokens": 8,
                "output_tokens": 2,
                "tool_calls": [
                    {
                        "id": "pdf-good",
                        "name": "execute_python_code",
                        "input": {"output_files": ["relatorio.pdf"]},
                        "is_error": False,
                        "files_generated": [{"filename": "relatorio.pdf", "size_bytes": 128}],
                    }
                ],
            }

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    docs = {
        "doc-correcao": SimpleNamespace(
            id="doc-correcao",
            tipo=TipoDocumento.CORRECAO,
            extensao=".json",
            status=StatusProcessamento.CONCLUIDO,
            criado_em="2026-05-16T20:00:00",
            metadata={"cost_run_id": "correcao-run"},
        ),
        "doc-json-bad": SimpleNamespace(
            id="doc-json-bad",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-json-good": SimpleNamespace(
            id="doc-json-good",
            extensao=".json",
            metadata={"tool": "create_document"},
            criado_por="ia_create_document",
        ),
        "doc-pdf-bad": SimpleNamespace(
            id="doc-pdf-bad",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
        "doc-pdf-good": SimpleNamespace(
            id="doc-pdf-good",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            criado_por="ia_execute_python_code",
        ),
    }
    paths = {
        "doc-correcao": correction_path,
        "doc-json-bad": bad_json_path,
        "doc-json-good": good_json_path,
        "doc-pdf-bad": bad_pdf_path,
        "doc-pdf-good": good_pdf_path,
    }

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(side_effect=lambda doc_id: docs[doc_id])
    executor.storage.listar_documentos = MagicMock(return_value=[docs["doc-correcao"]])
    executor.storage.resolver_caminho_documento = MagicMock(side_effect=lambda doc: paths[doc.id])
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="gere relatório",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gpt5nano",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.RELATORIO_FINAL,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is True
    assert resultado.tentativas == 4
    assert DummyClient.calls == 4
    assert any(
        call.args[0] == "doc-json-bad"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "json_schema_validation"
        and "CORRECAO oficial" in call.kwargs["metadata_patch"]["erro_pipeline"]
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )
    assert any(
        call.args[0] == "doc-pdf-bad"
        and call.kwargs.get("status") == StatusProcessamento.ERRO
        and call.kwargs["metadata_patch"]["erro_tipo"] == "pdf_json_consistency"
        for call in executor.storage.atualizar_documento_processamento.call_args_list
    )


@pytest.mark.asyncio
async def test_executar_com_tools_preserva_503_retryable(monkeypatch):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderAPIError, ProviderType

    model = SimpleNamespace(
        id="gemini",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-3-flash-preview",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat_with_tools(self, **kwargs):
            kwargs["context"].created_document_ids.extend(["doc-json", "doc-pdf"])
            raise ProviderAPIError(
                "Google",
                503,
                '{"error":{"status":"UNAVAILABLE","message":"high demand"}}',
            )

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    executor = PipelineExecutor()
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gemini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert resultado.retryable is True
    assert resultado.erro_codigo == 503
    assert "UNAVAILABLE" in resultado.erro
    assert executor.storage.atualizar_documento_processamento.call_count == 2
    for call in executor.storage.atualizar_documento_processamento.call_args_list:
        assert call.kwargs["status"] == StatusProcessamento.ERRO
        assert "UNAVAILABLE" in call.kwargs["metadata_patch"]["erro_pipeline"]


@pytest.mark.asyncio
async def test_executar_com_tools_provider_error_preserva_tokens_de_documento_parcial(monkeypatch):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderAPIError, ProviderType

    model = SimpleNamespace(
        id="gemini",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-2.5-flash",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        def __init__(self, model_config, api_key):
            self.calls = 0

        async def chat_with_tools(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                kwargs["context"].created_document_ids.append("doc-json")
                return {
                    "content": "",
                    "tokens": 26,
                    "input_tokens": 20,
                    "output_tokens": 6,
                    "modelo": "gemini-2.5-flash",
                    "provider": "google",
                    "tool_calls": [{"name": "create_document", "is_error": False}],
                }
            raise ProviderAPIError(
                "Google",
                429,
                '{"error":{"status":"RESOURCE_EXHAUSTED","message":"quota. Please retry in 8.610734207s."}}',
            )

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    executor = PipelineExecutor()
    executor.storage.get_documento = MagicMock(
        return_value=SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            status=StatusProcessamento.CONCLUIDO,
        )
    )
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gemini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert resultado.erro_codigo == 429
    assert resultado.retry_after == 9
    assert resultado.tokens_entrada == 20
    assert resultado.tokens_saida == 6

    executor.storage.atualizar_documento_processamento.assert_called_once()
    call = executor.storage.atualizar_documento_processamento.call_args
    assert call.args[0] == "doc-json"
    assert call.kwargs["tokens_usados"] == 26
    assert call.kwargs["metadata_patch"]["tokens_entrada"] == 20
    assert call.kwargs["metadata_patch"]["tokens_saida"] == 6
    assert call.kwargs["metadata_patch"]["tokens_total"] == 26
    assert call.kwargs["metadata_patch"]["custo_origem"] == "provider_error_after_partial_tool_use"


@pytest.mark.asyncio
async def test_executar_com_tools_provider_error_usa_usage_do_erro_sem_resposta_final(monkeypatch):
    import chat_service
    from executor import PipelineExecutor
    from chat_service import ProviderAPIError, ProviderType

    model = SimpleNamespace(
        id="gemini",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-2.5-flash",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda provider: SimpleNamespace(api_key="test-key"),
    )

    class DummyClient:
        def __init__(self, model_config, api_key):
            pass

        async def chat_with_tools(self, **kwargs):
            kwargs["context"].created_document_ids.append("doc-json")
            raise ProviderAPIError(
                "Google",
                429,
                '{"error":{"status":"RESOURCE_EXHAUSTED","message":"quota. Please retry in 8.610734207s."}}',
                input_tokens=20,
                output_tokens=6,
                total_tokens=26,
            )

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    executor = PipelineExecutor()
    executor.storage.atualizar_documento_processamento = MagicMock()

    resultado = await executor.executar_com_tools(
        mensagem="corrija",
        atividade_id="ativ-1",
        aluno_id="aluno-1",
        provider_id="gemini",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
        prompt_id="prompt-1",
    )

    assert resultado.sucesso is False
    assert resultado.erro_codigo == 429
    assert resultado.retry_after == 9
    assert resultado.tokens_entrada == 20
    assert resultado.tokens_saida == 6

    executor.storage.atualizar_documento_processamento.assert_called_once()
    call = executor.storage.atualizar_documento_processamento.call_args
    assert call.args[0] == "doc-json"
    assert call.kwargs["tokens_usados"] == 26
    assert call.kwargs["metadata_patch"]["tokens_entrada"] == 20
    assert call.kwargs["metadata_patch"]["tokens_saida"] == 6
    assert call.kwargs["metadata_patch"]["tokens_total"] == 26
    assert call.kwargs["metadata_patch"]["custo_origem"] == "provider_error_after_partial_tool_use"
