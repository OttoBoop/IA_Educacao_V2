"""
F7-T1 RED: PDF auto-fallback when LLM skips execute_python_code.

Bug: GPT-5 Nano (and potentially other models) call create_document (saving JSON)
but skip execute_python_code (no PDF generated). The professor gets a JSON report
but no downloadable PDF.

Expected behavior after F7-T1:
  - After executar_com_tools() processes all LLM tool calls, detect if
    create_document was called but execute_python_code was NOT called.
  - Auto-generate PDF from the JSON content using document_generators.py functions.
  - Return pdf_fallback_used=True in the ResultadoExecucao so frontend can show
    a loud notification.

These tests MUST FAIL until F7-T1 is implemented.

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
# Test 1: pdf_fallback_used field exists and is True when
#          LLM only calls create_document (no execute_python_code)
# ============================================================


class TestPdfFallbackFlagSet:
    """F7-T1: When LLM calls create_document but NOT execute_python_code,
    the result must have pdf_fallback_used=True.

    Current state: ResultadoExecucao has no pdf_fallback_used field.
    The method returns without generating any PDF fallback.
    """

    @pytest.mark.asyncio
    async def test_pdf_fallback_used_true_when_only_create_document(self):
        """When LLM produces JSON only (create_document without
        execute_python_code), pdf_fallback_used must be True.

        Current: ResultadoExecucao has no pdf_fallback_used attribute.
        Expected: result.pdf_fallback_used == True
        """
        response = _response_with_create_document_only()
        result = await _call_executar_com_tools(response)

        assert result.sucesso is True, (
            "executar_com_tools should still succeed (fallback generates PDF)"
        )
        assert hasattr(result, "pdf_fallback_used"), (
            "F7-T1: ResultadoExecucao must have a pdf_fallback_used field. "
            "Currently missing — add pdf_fallback_used: bool = False to the dataclass."
        )
        assert result.pdf_fallback_used is True, (
            "F7-T1: pdf_fallback_used must be True when LLM called create_document "
            "but did NOT call execute_python_code. "
            "\nCurrently: no PDF fallback logic exists in executar_com_tools(). "
            "\nExpected: detect missing execute_python_code, auto-generate PDF from "
            "the create_document content, and set pdf_fallback_used=True."
        )


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
# Test 3: Fallback alert is added to alertas list
# ============================================================


class TestPdfFallbackAlertAdded:
    """F7-T1: When PDF fallback triggers, an alert must be added to
    the alertas list so the frontend can show a loud notification.
    """

    @pytest.mark.asyncio
    async def test_fallback_alert_in_alertas(self):
        """When PDF fallback triggers, alertas must contain an entry
        with tipo='pdf_fallback' and a descriptive message.

        Current: No such alert exists.
        Expected: alertas contains {'tipo': 'pdf_fallback', 'mensagem': '...'}.
        """
        response = _response_with_create_document_only()
        result = await _call_executar_com_tools(response)

        assert result.sucesso is True

        fallback_alerts = [
            a for a in result.alertas
            if a.get("tipo") == "pdf_fallback"
        ]
        assert len(fallback_alerts) >= 1, (
            "F7-T1: When PDF fallback triggers, alertas must contain at least "
            "one entry with tipo='pdf_fallback'. "
            "\nCurrently: no pdf_fallback alert exists in the alertas list. "
            f"\nActual alertas: {result.alertas}"
        )


# ============================================================
# Test 4: to_dict() includes pdf_fallback_used
# ============================================================


class TestPdfFallbackInToDict:
    """F7-T1: The pdf_fallback_used flag must be serialized in to_dict()
    so the frontend API response includes it.
    """

    @pytest.mark.asyncio
    async def test_to_dict_includes_pdf_fallback_used(self):
        """to_dict() must include pdf_fallback_used key.

        Current: to_dict() has no pdf_fallback_used key.
        Expected: result.to_dict()['pdf_fallback_used'] exists.
        """
        response = _response_with_create_document_only()
        result = await _call_executar_com_tools(response)

        result_dict = result.to_dict()
        assert "pdf_fallback_used" in result_dict, (
            "F7-T1: to_dict() must include 'pdf_fallback_used' key so the "
            "frontend API response contains it for the loud notification. "
            f"\nActual keys: {list(result_dict.keys())}"
        )
        assert result_dict["pdf_fallback_used"] is True, (
            "F7-T1: to_dict()['pdf_fallback_used'] must be True when "
            "the fallback was triggered."
        )
