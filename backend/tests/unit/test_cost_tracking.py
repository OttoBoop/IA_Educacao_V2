from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from cost_tracking import build_cost_summary
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
    assert summary["tokens_entrada"] == 200
    assert summary["tokens_saida"] == 100
    assert summary["custo_usd"] > 0


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
    assert summary["amostras"][0]["documentos_contagem"] == 0
    assert summary["amostras"][0]["token_usage_ids"] == ["usage-1"]


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
        '{"nota_final": 7, "questoes": [{"numero": 1, "nota": 3}]}',
        encoding="utf-8",
    )
    import fitz

    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_text(
        (40, 80),
        "Nota final: 7.0 / 10.0\nQuestão 1 — Acerto | Nota: 3.0",
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
        '{"nota_final": 8, "questoes": [{"numero": 3, "nota": 0}]}',
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
    good_json_path.write_text('{"habilidades": [{"nome": "Porcentagem"}]}', encoding="utf-8")
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
    good_json_path = tmp_path / "correcao_good.json"
    pdf_path = tmp_path / "correcao.pdf"
    bad_json_path.write_text(
        '[{"nota_final": 8, "questoes": [{"numero": 3, "nota": 0}]}]',
        encoding="utf-8",
    )
    good_json_path.write_text(
        '{"nota_final": 8, "questoes": [{"numero": 3, "nota": 0}]}',
        encoding="utf-8",
    )
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
                            "input": {"output_files": ["correcao.pdf"]},
                            "is_error": False,
                            "files_generated": [{"filename": "correcao.pdf", "size_bytes": 128}],
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
