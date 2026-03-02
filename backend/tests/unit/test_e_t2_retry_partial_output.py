"""
Test E-T2: Retry logic for partial dual-output in executar_com_tools()

Tests:
1. test_both_outputs_produced_no_retry
   When tool_calls contains both create_document AND execute_python_code, no retry
   happens — chat_with_tools is called exactly once.

2. test_only_json_triggers_retry
   Only create_document in tool_calls → retry triggered. A second call to
   chat_with_tools must happen and the follow-up message must mention PDF/código.

3. test_only_pdf_triggers_retry
   Only execute_python_code in tool_calls → retry triggered. A second call to
   chat_with_tools must happen and the follow-up message must mention JSON/documento.

4. test_retry_succeeds_both_outputs_produced
   First call: only create_document. Retry call: both create_document AND
   execute_python_code → sucesso=True, tentativas=2.

5. test_retry_fails_partial_saved_with_warning
   Both calls produce only create_document → result is still sucesso=True (partial
   is saved) but alertas contains a warning entry.

6. test_single_tool_in_tools_to_use_no_dual_check
   When tools_to_use=["create_document"] only (no execute_python_code), the
   dual-output check must NOT apply — no retry even if execute_python_code is absent.

Root cause these tests guard against:
  executor.py lines ~1839-1869 call chat_with_tools exactly once and return
  immediately. There is no check for whether both create_document AND
  execute_python_code appear in tool_calls. Tests 2/3/4/5 will fail because
  the second call never happens, and test 4 will fail because tentativas==1.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_e_t2_retry_partial_output.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, ResultadoExecucao


# ============================================================
# RESPONSE FACTORIES
# ============================================================

def _tool_response(tool_names: list[str]) -> dict:
    """Build a chat_with_tools response dict containing the specified tool names."""
    tool_calls = []
    for name in tool_names:
        if name == "create_document":
            tool_calls.append({
                "name": "create_document",
                "input": {
                    "documents": [
                        {"filename": "relatorio_aluno.json", "content": "{}"}
                    ]
                },
            })
        elif name == "execute_python_code":
            tool_calls.append({
                "name": "execute_python_code",
                "input": {"code": "# generate PDF\nprint('done')"},
            })

    return {
        "content": "Relatório gerado com sucesso.",
        "tokens": 150,
        "modelo": "test-model",
        "provider": "anthropic",
        "tool_calls": tool_calls,
    }


def _make_mock_model(suporta_function_calling: bool = True, tipo_value: str = "anthropic"):
    """Build a minimal ModelConfig-like mock."""
    model = MagicMock()
    model.suporta_function_calling = suporta_function_calling
    model.tipo = MagicMock()
    model.tipo.value = tipo_value
    model.modelo = "claude-haiku-test"
    model.api_key_id = ""
    return model


def _make_chat_service_module(model, chat_with_tools_side_effect):
    """
    Build a mock chat_service module.

    chat_with_tools_side_effect must be a list of return values (one per call)
    or a single return value.  We use AsyncMock with side_effect so we can
    track multiple sequential calls (first call / retry call).
    """
    mock_module = MagicMock()

    mock_manager = MagicMock()
    mock_manager.get = MagicMock(return_value=model)
    mock_manager.get_default = MagicMock(return_value=model)
    mock_module.model_manager = mock_manager

    mock_key_manager = MagicMock()
    api_key_config = MagicMock()
    api_key_config.api_key = "test-api-key-abc"
    mock_key_manager.get = MagicMock(return_value=None)
    mock_key_manager.get_por_empresa = MagicMock(return_value=api_key_config)
    mock_module.api_key_manager = mock_key_manager

    from chat_service import ProviderType
    mock_module.ProviderType = ProviderType

    mock_client_instance = MagicMock()

    # Build the side_effect list for AsyncMock
    if isinstance(chat_with_tools_side_effect, list):
        mock_client_instance.chat_with_tools = AsyncMock(
            side_effect=chat_with_tools_side_effect
        )
    else:
        # Single return value — only one call expected
        mock_client_instance.chat_with_tools = AsyncMock(
            return_value=chat_with_tools_side_effect
        )

    mock_client_instance.chat = AsyncMock(return_value={
        "content": "Fallback text",
        "tokens": 10,
        "modelo": "test-model",
        "provider": "anthropic",
    })

    mock_chat_client_cls = MagicMock(return_value=mock_client_instance)
    mock_module.ChatClient = mock_chat_client_cls

    return mock_module, mock_client_instance


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


async def _call_executar_com_tools(
    chat_side_effect,
    tools_to_use=None,
    provider_id=None,
):
    """
    Patch lazy-imported modules and call executar_com_tools.

    chat_side_effect: list of dicts (one per chat_with_tools call) OR a single dict.
    Returns: (ResultadoExecucao, mock_client_instance)
    """
    model = _make_mock_model(suporta_function_calling=True)
    chat_service_mock, mock_client = _make_chat_service_module(model, chat_side_effect)
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
            mensagem="Gere o relatório completo do aluno.",
            atividade_id="atividade_test_et2",
            aluno_id="aluno_test_et2",
            provider_id=provider_id,
            tools_to_use=tools_to_use,
        )

    return result, mock_client


# ============================================================
# TEST 1: Both outputs produced → no retry
# ============================================================

class TestBothOutputsNoRetry:
    """When tool_calls contains both create_document and execute_python_code,
    no retry should happen — chat_with_tools must be called exactly once."""

    async def test_both_outputs_produced_no_retry(self):
        """Both create_document AND execute_python_code present → single call, no retry.

        This test should PASS immediately (no retry needed when both outputs exist).
        It is the baseline / control case.
        """
        both_response = _tool_response(["create_document", "execute_python_code"])
        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert isinstance(result, ResultadoExecucao)
        assert result.sucesso is True, (
            f"Both outputs present → expected sucesso=True, got sucesso={result.sucesso}"
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 1, (
            f"Both outputs present → chat_with_tools should be called exactly ONCE "
            f"(no retry needed). Got call_count={call_count}."
        )


# ============================================================
# TEST 2: Only JSON → retry with PDF mention
# ============================================================

class TestOnlyJsonTriggersRetry:
    """When only create_document appears in tool_calls (no execute_python_code),
    a second call to chat_with_tools must happen and the follow-up message
    must mention PDF or código."""

    async def test_only_json_triggers_retry(self):
        """Only create_document called → retry triggered.

        Currently FAILS: chat_with_tools is called once and returns immediately.
        After E-T2 the executor must detect missing execute_python_code and retry.
        """
        only_json_response = _tool_response(["create_document"])
        # Provide two responses: first call (only JSON), second call (retry — irrelevant content)
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Only create_document in first response → retry expected. "
            f"chat_with_tools should be called TWICE (original + retry). "
            f"Got call_count={call_count}. "
            "Current code calls once and returns — this is the bug E-T2 must fix."
        )

    async def test_only_json_retry_message_mentions_pdf(self):
        """The retry follow-up message must reference PDF or código so the model
        knows what to generate on the second attempt.

        Currently FAILS: no second call exists, so no follow-up message is sent.
        """
        only_json_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Retry call expected but got call_count={call_count}."
        )

        # Inspect the second call's mensagem argument
        second_call_kwargs = mock_client.chat_with_tools.call_args_list[1]
        # Accept both positional and keyword forms
        mensagem_retry = (
            second_call_kwargs.kwargs.get("mensagem")
            or (second_call_kwargs.args[0] if second_call_kwargs.args else None)
        )

        assert mensagem_retry is not None, (
            "Second (retry) call to chat_with_tools must receive a mensagem argument."
        )

        mensagem_lower = mensagem_retry.lower()
        has_pdf_ref = any(
            keyword in mensagem_lower
            for keyword in ["pdf", "código", "codigo", "execute_python_code", "python"]
        )
        assert has_pdf_ref, (
            f"Retry message must mention PDF/código so the model knows what to create. "
            f"Got mensagem_retry={mensagem_retry!r}"
        )


# ============================================================
# TEST 3: Only PDF → retry with JSON mention
# ============================================================

class TestOnlyPdfTriggersRetry:
    """When only execute_python_code appears in tool_calls (no create_document),
    a second call to chat_with_tools must happen and the follow-up message
    must mention JSON or documento."""

    async def test_only_pdf_triggers_retry(self):
        """Only execute_python_code called → retry triggered.

        Currently FAILS: chat_with_tools is called once and returns immediately.
        """
        only_pdf_response = _tool_response(["execute_python_code"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_pdf_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Only execute_python_code in first response → retry expected. "
            f"chat_with_tools should be called TWICE. Got call_count={call_count}."
        )

    async def test_only_pdf_retry_message_mentions_document(self):
        """The retry follow-up message must reference JSON/documento.

        Currently FAILS: no second call exists.
        """
        only_pdf_response = _tool_response(["execute_python_code"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_pdf_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Retry call expected but got call_count={call_count}."
        )

        second_call_kwargs = mock_client.chat_with_tools.call_args_list[1]
        mensagem_retry = (
            second_call_kwargs.kwargs.get("mensagem")
            or (second_call_kwargs.args[0] if second_call_kwargs.args else None)
        )

        assert mensagem_retry is not None, (
            "Second (retry) call must receive a mensagem argument."
        )

        mensagem_lower = mensagem_retry.lower()
        has_doc_ref = any(
            keyword in mensagem_lower
            for keyword in ["json", "documento", "document", "create_document"]
        )
        assert has_doc_ref, (
            f"Retry message must mention JSON/documento so the model knows what to create. "
            f"Got mensagem_retry={mensagem_retry!r}"
        )


# ============================================================
# TEST 4: Retry succeeds — both outputs on second call
# ============================================================

class TestRetrySucceedsBothOutputs:
    """First call: only create_document. Retry: both outputs produced.
    Result must be sucesso=True and tentativas=2."""

    async def test_retry_succeeds_both_outputs_produced(self):
        """First call → only JSON. Retry → both JSON + PDF. sucesso=True, tentativas=2.

        Currently FAILS on both:
        - call_count will be 1 (no retry logic exists yet)
        - tentativas will be 1 (retry never happened)
        """
        first_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[first_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert isinstance(result, ResultadoExecucao)
        assert result.sucesso is True, (
            f"Retry succeeded (both outputs on second call) → sucesso must be True. "
            f"Got sucesso={result.sucesso}."
        )

        assert result.tentativas == 2, (
            f"First call + one retry = 2 attempts total. "
            f"Got tentativas={result.tentativas}. "
            "Current code always returns tentativas=1 because retry logic is missing."
        )

    async def test_retry_succeeds_call_count_is_two(self):
        """Confirm exactly two calls: original + one retry (not three)."""
        first_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[first_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Expected exactly 2 calls (original + one retry). Got call_count={call_count}."
        )


# ============================================================
# TEST 5: Both retries fail partial → saved with warning
# ============================================================

class TestRetryFailsPartialSavedWithWarning:
    """Both calls produce only create_document (no execute_python_code).
    Result: sucesso=True (partial is still saved) but alertas contains a warning."""

    async def test_retry_fails_partial_saved_with_warning(self):
        """Both calls: only create_document. sucesso=True but a warning alert is added.

        Currently FAILS on:
        - call_count will be 1 (no second call exists)
        - alertas will not contain a warning (just an info entry)
        """
        only_json_first = _tool_response(["create_document"])
        only_json_retry = _tool_response(["create_document"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_first, only_json_retry],
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert isinstance(result, ResultadoExecucao)

        # Partial output is still saved (sucesso=True)
        assert result.sucesso is True, (
            f"Partial output should still be saved (sucesso=True) even after retry fails. "
            f"Got sucesso={result.sucesso}."
        )

        # A warning alert must be added
        warning_alerts = [
            a for a in result.alertas
            if a.get("tipo") == "aviso" or a.get("tipo") == "warning"
        ]
        assert len(warning_alerts) >= 1, (
            f"After two failed dual-output attempts, a warning alert must be added to alertas. "
            f"Got alertas={result.alertas}. "
            "Current code adds only an 'info' alert (no warning) and never retries."
        )

    async def test_retry_fails_partial_call_count_is_two(self):
        """Even when retry fails, exactly two calls should have been made."""
        only_json_first = _tool_response(["create_document"])
        only_json_retry = _tool_response(["create_document"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_first, only_json_retry],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Retry was attempted (even though it failed) → call_count must be 2. "
            f"Got call_count={call_count}."
        )

    async def test_retry_fails_warning_message_mentions_partial(self):
        """Warning alert message must communicate that output is incomplete/partial."""
        only_json_first = _tool_response(["create_document"])
        only_json_retry = _tool_response(["create_document"])

        result, _mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_first, only_json_retry],
            tools_to_use=["create_document", "execute_python_code"],
        )

        warning_alerts = [
            a for a in result.alertas
            if a.get("tipo") in ("aviso", "warning")
        ]
        assert len(warning_alerts) >= 1, (
            f"No warning alert found. Got alertas={result.alertas}"
        )

        warning_mensagem = warning_alerts[0].get("mensagem", "")
        mensagem_lower = warning_mensagem.lower()
        has_partial_ref = any(
            keyword in mensagem_lower
            for keyword in [
                "parcial", "partial", "incompleto", "incompleta",
                "pdf", "execute_python_code", "faltando", "ausente",
            ]
        )
        assert has_partial_ref, (
            f"Warning message should communicate that output is partial/incomplete. "
            f"Got warning mensagem={warning_mensagem!r}"
        )


# ============================================================
# TEST 6: Single tool in tools_to_use → no dual-output check
# ============================================================

class TestSingleToolNoDualCheck:
    """When tools_to_use contains only one tool (e.g., ["create_document"]),
    the dual-output check must NOT apply — no retry even if execute_python_code
    is absent from tool_calls."""

    async def test_single_tool_in_tools_to_use_no_dual_check(self):
        """tools_to_use=["create_document"] only → dual check does NOT apply.

        Only one type of output is expected, so producing only create_document
        is a complete (not partial) result. No retry should happen.

        This test verifies that the dual-output guard is gated on whether BOTH
        tool types are in tools_to_use — not just on what the model returns.
        """
        only_json_response = _tool_response(["create_document"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=only_json_response,
            tools_to_use=["create_document"],  # Only one tool — no dual check
        )

        assert isinstance(result, ResultadoExecucao)
        assert result.sucesso is True, (
            f"Single tool in tools_to_use → no dual-output check → sucesso=True. "
            f"Got sucesso={result.sucesso}."
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 1, (
            f"tools_to_use=['create_document'] only → no retry should happen. "
            f"chat_with_tools must be called exactly once. Got call_count={call_count}."
        )

    async def test_single_tool_execute_python_only_no_dual_check(self):
        """tools_to_use=["execute_python_code"] only → dual check does NOT apply.

        Producing only execute_python_code is a complete result for this call.
        """
        only_pdf_response = _tool_response(["execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=only_pdf_response,
            tools_to_use=["execute_python_code"],
        )

        assert result.sucesso is True, (
            f"Single tool (execute_python_code only) → sucesso=True. "
            f"Got sucesso={result.sucesso}."
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 1, (
            f"tools_to_use=['execute_python_code'] only → no retry. "
            f"Got call_count={call_count}."
        )

    async def test_empty_tools_to_use_no_dual_check(self):
        """tools_to_use=None (default) with only one output type.

        When tools_to_use is None, the function expands to the default list which
        includes both tools → dual-output check DOES apply. This is the opposite
        of the single-tool case. We confirm that with default tools, partial output
        triggers a retry (call_count > 1).

        Currently FAILS: no retry exists, so call_count will be 1.
        """
        only_json_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=None,  # Expands to default: both tools → dual check applies
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"tools_to_use=None expands to both tools → dual-output check applies → "
            f"retry expected on partial output. Got call_count={call_count}. "
            "Current code never retries — this is the bug E-T2 must fix."
        )
