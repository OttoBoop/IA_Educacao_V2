import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class _StoredDoc:
    def __init__(self, doc_id, extension, tool, status="concluido"):
        self.id = doc_id
        self.extensao = extension
        self.metadata = {"tool": tool}
        self.status = status


class _DummyStorage:
    def __init__(self, docs=None):
        self.docs = docs or {}
        self.saved_calls = []

    def get_documento(self, doc_id):
        return self.docs.get(doc_id)

    def salvar_documento(self, **kwargs):
        self.saved_calls.append(kwargs)
        doc_id = f"saved-{len(self.saved_calls)}"
        extension = ".json"
        self.docs[doc_id] = _StoredDoc(doc_id, extension, "create_document")
        return SimpleNamespace(
            id=doc_id,
            display_name=kwargs.get("display_name"),
            nome_arquivo=kwargs.get("display_name"),
        )


@pytest.mark.asyncio
async def test_pipeline_create_document_rejects_second_json_artifact(monkeypatch):
    from models import TipoDocumento
    from tool_handlers import handle_create_document
    from tools import ToolExecutionContext
    import storage as storage_module

    storage = _DummyStorage({
        "json-1": _StoredDoc("json-1", ".json", "create_document"),
    })
    monkeypatch.setattr(storage_module, "storage", storage)

    result = await handle_create_document(
        {
            "documents": [
                {
                    "filename": "desempenho_turma.json",
                    "content": {"resumo_evolucao": "ok"},
                }
            ]
        },
        ToolExecutionContext(
            atividade_id="ativ-1",
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TURMA,
            etapa="relatorio_desempenho_turma",
            created_document_ids=["json-1"],
        ),
    )

    assert result.is_error is True
    assert result.files_generated == []
    assert "already produced the required JSON" in result.content
    assert storage.saved_calls == []


@pytest.mark.asyncio
async def test_pipeline_create_document_rejects_multiple_jsons_in_one_call():
    from models import TipoDocumento
    from tool_handlers import handle_create_document
    from tools import ToolExecutionContext

    result = await handle_create_document(
        {
            "documents": [
                {"filename": "a.json", "content": {"ok": 1}},
                {"filename": "b.json", "content": {"ok": 2}},
            ]
        },
        ToolExecutionContext(
            atividade_id="ativ-1",
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TURMA,
            etapa="relatorio_desempenho_turma",
        ),
    )

    assert result.is_error is True
    assert result.files_generated == []
    assert "exactly one JSON artifact" in result.content


@pytest.mark.asyncio
async def test_pipeline_execute_python_rejects_second_pdf_artifact(monkeypatch):
    from models import TipoDocumento
    from tool_handlers import handle_execute_python_code
    from tools import ToolExecutionContext
    import code_executor as code_executor_module
    import storage as storage_module

    storage = _DummyStorage({
        "pdf-1": _StoredDoc("pdf-1", ".pdf", "execute_python_code"),
    })
    monkeypatch.setattr(storage_module, "storage", storage)

    generated_file = SimpleNamespace(
        filename="desempenho_turma.pdf",
        mime_type="application/pdf",
        size_bytes=12,
        content_base64=base64.b64encode(b"fake pdf").decode("utf-8"),
        to_dict=lambda: {"filename": "desempenho_turma.pdf"},
    )
    code_executor_module.code_executor.execute = AsyncMock(
        return_value=SimpleNamespace(
            is_success=True,
            files_generated=[generated_file],
            plots_generated=[],
            stdout="",
            execution_time_ms=10,
        )
    )

    result = await handle_execute_python_code(
        {"code": "print('pdf')"},
        ToolExecutionContext(
            atividade_id="ativ-1",
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TURMA,
            etapa="relatorio_desempenho_turma",
            created_document_ids=["pdf-1"],
        ),
    )

    assert result.is_error is True
    assert "already produced the required PDF" in result.content
    assert storage.saved_calls == []
