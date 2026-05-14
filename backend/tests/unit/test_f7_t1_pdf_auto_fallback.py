"""
F7-T1/P0: no PDF auto-fallback when LLM skips execute_python_code.

Bug: GPT-5 Nano (and potentially other models) call create_document (saving JSON)
but skip execute_python_code (no PDF generated). The professor gets a JSON report
but no downloadable PDF.

Expected P0 behavior now:
  - After executar_com_tools() processes all LLM tool calls, detect if
    create_document was called but execute_python_code was NOT called.
  - Retry explicitly on the same model.
  - If the model still fails to call execute_python_code, return sucesso=False.
  - Never auto-generate a fake PDF fallback.

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f7_t1_pdf_auto_fallback.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, ResultadoExecucao


# ============================================================
# HELPERS — same pattern as test_e_t1_tool_capability_gate.py
# ============================================================


def _make_mock_model(suporta_function_calling=True, tipo_value="openai"):
    """Build a minimal ModelConfig-like mock for a tool-capable model."""
    model = MagicMock()
    model.suporta_function_calling = suporta_function_calling
    model.tipo = MagicMock()
    model.tipo.value = tipo_value
    model.modelo = "gpt-5-nano"
    model.api_key_id = ""
    return model


def _make_chat_service_module(model, tool_calls_response):
    """Build a mock chat_service module.

    tool_calls_response: the dict returned by client.chat_with_tools()
    """
    mock_module = MagicMock()

    mock_manager = MagicMock()
    mock_manager.get = MagicMock(return_value=model)
    mock_manager.get_default = MagicMock(return_value=model)
    mock_module.model_manager = mock_manager

    mock_key_manager = MagicMock()
    api_key_config = MagicMock()
    api_key_config.api_key = "test-key"
    mock_key_manager.get = MagicMock(return_value=api_key_config)
    mock_key_manager.get_por_empresa = MagicMock(return_value=api_key_config)
    mock_module.api_key_manager = mock_key_manager

    from chat_service import ProviderType
    mock_module.ProviderType = ProviderType

    mock_client_instance = MagicMock()
    mock_client_instance.chat_with_tools = AsyncMock(return_value=tool_calls_response)
    mock_module.ChatClient = MagicMock(return_value=mock_client_instance)

    return mock_module


def _make_tools_module():
    """Build a minimal tools module mock."""
    mock_module = MagicMock()
    mock_module.ToolRegistry = MagicMock(return_value=MagicMock())
    mock_module.PIPELINE_TOOLS = []
    mock_module.CREATE_DOCUMENT = MagicMock()
    mock_module.EXECUTE_PYTHON_CODE = MagicMock()
    mock_module.ToolExecutionContext = MagicMock()
    return mock_module


def _make_tool_handlers_module():
    """Build a minimal tool_handlers module mock."""
    mock_module = MagicMock()
    mock_module.TOOL_HANDLERS = {}
    return mock_module


# ============================================================
# Shared response fixtures
# ============================================================

SAMPLE_REPORT_CONTENT = """\
# Relatório de Desempenho — Prova 1

## Análise do Aluno: Ana Silva

A aluna demonstrou bom domínio dos conceitos fundamentais de Cálculo Diferencial.

### Pontos Fortes
- Compreensão sólida de limites
- Boa aplicação da regra da cadeia

### Pontos a Melhorar
- Integração por partes precisa de mais prática
"""


def _response_with_create_document_only():
    """Simulate LLM calling create_document but NOT execute_python_code.

    This is the bug scenario: GPT-5 Nano produces JSON but no PDF.
    """
    return {
        "content": "",
        "tokens": 150,
        "modelo": "gpt-5-nano",
        "provider": "openai",
        "tool_calls": [
            {
                "name": "create_document",
                "input": {
                    "documents": [
                        {
                            "filename": "relatorio_desempenho_ana.json",
                            "content": SAMPLE_REPORT_CONTENT,
                            "type": "report",
                        }
                    ]
                },
                "result": {"files_generated": ["relatorio_desempenho_ana.json"]},
            }
        ],
    }


def _response_with_both_tools():
    """Simulate LLM calling BOTH create_document AND execute_python_code.

    This is the normal (correct) scenario — no fallback should trigger.
    """
    return {
        "content": "",
        "tokens": 250,
        "modelo": "gpt-5-nano",
        "provider": "openai",
        "tool_calls": [
            {
                "name": "create_document",
                "input": {
                    "documents": [
                        {
                            "filename": "relatorio_desempenho_ana.json",
                            "content": SAMPLE_REPORT_CONTENT,
                            "type": "report",
                        }
                    ]
                },
                "result": {"files_generated": ["relatorio_desempenho_ana.json"]},
            },
            {
                "name": "execute_python_code",
                "input": {"code": "# generate PDF..."},
                "result": {"files_generated": ["relatorio_desempenho_ana.pdf"]},
            },
        ],
    }


async def _call_executar_com_tools(tool_calls_response, tools_to_use=None):
    """Call executar_com_tools with mocked modules and return result."""
    model = _make_mock_model()
    chat_service_mock = _make_chat_service_module(model, tool_calls_response)
    tools_mock = _make_tools_module()
    tool_handlers_mock = _make_tool_handlers_module()

    with patch.dict(
        "sys.modules",
        {
            "chat_service": chat_service_mock,
            "tools": tools_mock,
            "tool_handlers": tool_handlers_mock,
        },
    ):
        executor = PipelineExecutor()
        result = await executor.executar_com_tools(
            mensagem="Gere o relatório de desempenho do aluno.",
            atividade_id="atividade_test_123",
            aluno_id="aluno_test_456",
            provider_id="gpt5nano001",
            tools_to_use=tools_to_use or ["create_document", "execute_python_code"],
        )

    return result


# ============================================================
# Test 1: missing execute_python_code fails high
# ============================================================


class TestPdfFallbackFlagSet:
    """F7-T1: When LLM calls create_document but NOT execute_python_code,
    the result must fail high instead of using a PDF fallback.
    """

    @pytest.mark.asyncio
    async def test_pdf_fallback_used_true_when_only_create_document(self):
        """JSON-only output must not be accepted as success."""
        response = _response_with_create_document_only()
        result = await _call_executar_com_tools(response)

        assert result.sucesso is False, (
            "executar_com_tools must fail high when the model does not generate the PDF"
        )
        assert hasattr(result, "pdf_fallback_used"), (
            "ResultadoExecucao must keep pdf_fallback_used for API compatibility."
        )
        assert result.pdf_fallback_used is False, (
            "PDF fallback is prohibited; the flag must stay False."
        )
        assert "PDF via execute_python_code" in (result.erro or "")


# ============================================================
# Test 2: pdf_fallback_used is False when BOTH tools are called
# ============================================================


class TestPdfFallbackNotTriggeredWhenBothTools:
    """F7-T1: When LLM calls BOTH create_document AND execute_python_code,
    pdf_fallback_used must be False (no fallback needed).
    """

    @pytest.mark.asyncio
    async def test_pdf_fallback_used_false_when_both_tools_called(self):
        """Normal case: LLM produced both JSON and PDF.
        Fallback should NOT trigger.

        Current: ResultadoExecucao has no pdf_fallback_used attribute at all.
        Expected: result.pdf_fallback_used == False
        """
        response = _response_with_both_tools()
        result = await _call_executar_com_tools(response)

        assert result.sucesso is True
        assert hasattr(result, "pdf_fallback_used"), (
            "F7-T1: ResultadoExecucao must have a pdf_fallback_used field."
        )
        assert result.pdf_fallback_used is False, (
            "F7-T1: pdf_fallback_used must be False when both create_document "
            "and execute_python_code were called by the LLM. No fallback needed."
        )


# ============================================================
# Test 3: no fallback alert is added; failure alert is explicit
# ============================================================


class TestPdfFallbackAlertAdded:
    """P0: missing PDF should produce a blocking warning, not pdf_fallback."""

    @pytest.mark.asyncio
    async def test_fallback_alert_in_alertas(self):
        """A JSON-only tool result must not emit pdf_fallback success alert."""
        response = _response_with_create_document_only()
        result = await _call_executar_com_tools(response)

        assert result.sucesso is False

        fallback_alerts = [
            a for a in result.alertas
            if a.get("tipo") == "pdf_fallback"
        ]
        assert fallback_alerts == [], (
            "No pdf_fallback alert should exist because fallback is prohibited."
        )
        assert any("fallback" in a.get("mensagem", "").lower() for a in result.alertas)


# ============================================================
# Test 4: to_dict() includes pdf_fallback_used
# ============================================================


class TestPdfFallbackInToDict:
    """F7-T1: The pdf_fallback_used flag remains serialized as False."""

    @pytest.mark.asyncio
    async def test_to_dict_includes_pdf_fallback_used(self):
        """to_dict() must include pdf_fallback_used=False on blocking failure."""
        response = _response_with_create_document_only()
        result = await _call_executar_com_tools(response)

        result_dict = result.to_dict()
        assert "pdf_fallback_used" in result_dict, (
            "F7-T1: to_dict() must include 'pdf_fallback_used' key so the "
            "frontend API response contains it for the loud notification. "
            f"\nActual keys: {list(result_dict.keys())}"
        )
        assert result_dict["pdf_fallback_used"] is False, (
            "PDF fallback is prohibited; serialized flag must remain False."
        )
