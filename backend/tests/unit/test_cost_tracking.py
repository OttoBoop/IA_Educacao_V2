from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from cost_tracking import build_cost_summary
from models import NivelEnsino, StatusProcessamento, TipoDocumento
from storage import StorageManager


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


@pytest.mark.asyncio
async def test_executar_com_tools_falha_sem_pdf_obrigatorio(monkeypatch):
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
    assert executor.storage.atualizar_documento_processamento.call_args.kwargs["status"] == StatusProcessamento.ERRO


@pytest.mark.asyncio
async def test_executar_com_tools_repara_pdf_nao_persistido_com_retry(monkeypatch):
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
