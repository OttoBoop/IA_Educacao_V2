"""
F2-T1/T2: Tests for desempenho resposta_raw population fix.

The bug: executar_com_tools() sets resposta_raw = resposta.get("content", ""),
but when the LLM calls tools (create_document), the actual content is in the
tool_calls inputs, not in the "content" field. This results in empty resposta_raw.

F2-T1: resposta_raw must contain create_document content (not empty string)
F2-T2: When max_iterations is hit, resposta_raw must still extract tool output

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f2_desempenho_resposta_raw.py -v
"""

import pytest
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def executor_com_mock():
    """PipelineExecutor with fully mocked storage — no database."""
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None
    return executor


def _make_tool_response(content="", tool_calls=None, error=None):
    """Build a mock chat_with_tools response dict."""
    resp = {
        "content": content,
        "tokens": 100,
        "modelo": "test-model",
        "provider": "openai",
        "tool_calls": tool_calls or [],
    }
    if error:
        resp["error"] = error
    return resp


# ============================================================
# F2-T1: resposta_raw must capture create_document content
# ============================================================

class TestRespostaRawFromToolCalls:
    """executar_com_tools() must populate resposta_raw from create_document
    tool call input when the API content field is empty."""

    @pytest.mark.asyncio
    async def test_resposta_raw_contains_create_document_content_when_api_content_empty(
        self, executor_com_mock
    ):
        """When the LLM calls create_document and content is empty,
        resposta_raw should contain the document content from create_document input."""
        from executor import ResultadoExecucao

        json_content = '{"alunos": [{"nome": "Ana", "nota": 8.5}], "resumo": "Turma vai bem"}'

        mock_response = _make_tool_response(
            content="",  # Empty — the bug
            tool_calls=[
                {
                    "id": "tc_001",
                    "name": "create_document",
                    "input": {
                        "filename": "desempenho_tarefa.json",
                        "content": json_content,
                    }
                },
                {
                    "id": "tc_002",
                    "name": "execute_python_code",
                    "input": {
                        "code": "# generate PDF",
                    }
                },
            ]
        )

        # Mock all dependencies
        mock_model = MagicMock()
        mock_model.tipo = MagicMock()
        mock_model.tipo.value = "openai"
        mock_model.modelo = "test-model"
        mock_model.api_key_id = None
        mock_model.suporta_function_calling = True

        mock_client = AsyncMock()
        mock_client.chat_with_tools = AsyncMock(return_value=mock_response)

        with patch("chat_service.model_manager") as mm, \
             patch("chat_service.api_key_manager") as akm, \
             patch("chat_service.ChatClient", return_value=mock_client), \
             patch("tools.ToolRegistry") as tr, \
             patch("tool_handlers.TOOL_HANDLERS", {}), \
             patch("tools.PIPELINE_TOOLS", []):
            mm.get.return_value = mock_model
            akm.get_por_empresa.return_value = MagicMock(api_key="test-key")

            result = await executor_com_mock.executar_com_tools(
                mensagem="Gere o relatório de desempenho",
                atividade_id="ativ-001",
                tools_to_use=["create_document", "execute_python_code"],
            )

        assert result.sucesso is True
        assert result.resposta_raw != "", (
            "resposta_raw must NOT be empty when create_document was called. "
            f"Got empty string. Tool calls had create_document with content."
        )
        assert "Ana" in result.resposta_raw, (
            "resposta_raw must contain the create_document content. "
            f"Expected 'Ana' in resposta_raw, got: {result.resposta_raw[:200]}"
        )

    @pytest.mark.asyncio
    async def test_resposta_raw_uses_api_content_when_no_create_document(
        self, executor_com_mock
    ):
        """When no create_document tool was called, resposta_raw should
        fall back to the API content field as before."""
        from executor import ResultadoExecucao

        api_content = "Relatório gerado com sucesso para todos os alunos."

        mock_response = _make_tool_response(
            content=api_content,
            tool_calls=[
                {
                    "id": "tc_001",
                    "name": "execute_python_code",
                    "input": {"code": "print('hello')"}
                }
            ]
        )

        mock_model = MagicMock()
        mock_model.tipo = MagicMock()
        mock_model.tipo.value = "openai"
        mock_model.modelo = "test-model"
        mock_model.api_key_id = None
        mock_model.suporta_function_calling = True

        mock_client = AsyncMock()
        mock_client.chat_with_tools = AsyncMock(return_value=mock_response)

        with patch("chat_service.model_manager") as mm, \
             patch("chat_service.api_key_manager") as akm, \
             patch("chat_service.ChatClient", return_value=mock_client), \
             patch("tools.ToolRegistry") as tr, \
             patch("tool_handlers.TOOL_HANDLERS", {}), \
             patch("tools.PIPELINE_TOOLS", []):
            mm.get.return_value = mock_model
            akm.get_por_empresa.return_value = MagicMock(api_key="test-key")

            result = await executor_com_mock.executar_com_tools(
                mensagem="Execute algo",
                atividade_id="ativ-002",
                tools_to_use=["execute_python_code"],
            )

        assert result.resposta_raw == api_content, (
            "When no create_document was called, resposta_raw should use API content. "
            f"Expected: {api_content!r}, Got: {result.resposta_raw!r}"
        )


# ============================================================
# F2-T2: Handle max_iterations sentinel gracefully
# ============================================================

class TestMaxIterationsSentinel:
    """When max_iterations is exceeded, resposta_raw must still capture
    tool output instead of the sentinel string."""

    @pytest.mark.asyncio
    async def test_resposta_raw_extracts_tool_content_on_max_iterations(
        self, executor_com_mock
    ):
        """When error=max_iterations_exceeded but create_document was called,
        resposta_raw should contain the document content, not the sentinel."""

        json_content = '{"turma": "Alpha", "media": 7.2}'

        mock_response = _make_tool_response(
            content="[Maximum tool iterations reached]",  # Sentinel
            tool_calls=[
                {
                    "id": "tc_001",
                    "name": "create_document",
                    "input": {
                        "filename": "desempenho_turma.json",
                        "content": json_content,
                    }
                },
            ],
            error="max_iterations_exceeded"
        )

        mock_model = MagicMock()
        mock_model.tipo = MagicMock()
        mock_model.tipo.value = "openai"
        mock_model.modelo = "test-model"
        mock_model.api_key_id = None
        mock_model.suporta_function_calling = True

        mock_client = AsyncMock()
        mock_client.chat_with_tools = AsyncMock(return_value=mock_response)

        with patch("chat_service.model_manager") as mm, \
             patch("chat_service.api_key_manager") as akm, \
             patch("chat_service.ChatClient", return_value=mock_client), \
             patch("tools.ToolRegistry") as tr, \
             patch("tool_handlers.TOOL_HANDLERS", {}), \
             patch("tools.PIPELINE_TOOLS", []):
            mm.get.return_value = mock_model
            akm.get_por_empresa.return_value = MagicMock(api_key="test-key")

            result = await executor_com_mock.executar_com_tools(
                mensagem="Gere desempenho turma",
                atividade_id="ativ-003",
                tools_to_use=["create_document"],
            )

        assert "[Maximum tool iterations reached]" not in result.resposta_raw, (
            "resposta_raw must NOT contain the sentinel string when tool output exists. "
            f"Got: {result.resposta_raw!r}"
        )
        assert "Alpha" in result.resposta_raw, (
            "resposta_raw must contain create_document content even on max_iterations. "
            f"Got: {result.resposta_raw!r}"
        )

    @pytest.mark.asyncio
    async def test_max_iterations_adds_alert(
        self, executor_com_mock
    ):
        """When max_iterations is exceeded, an alert must be added."""

        mock_response = _make_tool_response(
            content="[Maximum tool iterations reached]",
            tool_calls=[],
            error="max_iterations_exceeded"
        )

        mock_model = MagicMock()
        mock_model.tipo = MagicMock()
        mock_model.tipo.value = "openai"
        mock_model.modelo = "test-model"
        mock_model.api_key_id = None
        mock_model.suporta_function_calling = True

        mock_client = AsyncMock()
        mock_client.chat_with_tools = AsyncMock(return_value=mock_response)

        with patch("chat_service.model_manager") as mm, \
             patch("chat_service.api_key_manager") as akm, \
             patch("chat_service.ChatClient", return_value=mock_client), \
             patch("tools.ToolRegistry") as tr, \
             patch("tool_handlers.TOOL_HANDLERS", {}), \
             patch("tools.PIPELINE_TOOLS", []):
            mm.get.return_value = mock_model
            akm.get_por_empresa.return_value = MagicMock(api_key="test-key")

            result = await executor_com_mock.executar_com_tools(
                mensagem="Gere desempenho",
                atividade_id="ativ-004",
                tools_to_use=["create_document"],
            )

        alert_messages = [a.get("mensagem", "") for a in result.alertas]
        has_iteration_alert = any("iteraç" in m.lower() or "iteration" in m.lower() for m in alert_messages)
        assert has_iteration_alert, (
            "An alert about max iterations must be added when the limit is exceeded. "
            f"Got alerts: {result.alertas}"
        )
