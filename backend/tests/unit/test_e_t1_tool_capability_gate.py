"""
Test E-T1: Tool capability gate in executar_com_tools()

Tests:
- Non-tool model + tools_to_use non-empty → sucesso=False with exact Portuguese error message
- Tool-capable model with tools_to_use non-empty → gate passes (does NOT return early error)
- Exact error message string is preserved
- Default tools_to_use (None → resolves to ["create_document", "execute_python_code"]) +
  non-tool model → still blocked (non-empty after default expansion)
- tools_to_use=[] explicitly empty + non-tool model → NOT blocked (no tools requested)

Root cause this test guards against:
  executor.py lines 1829-1843 currently return sucesso=True when the model does not
  support function calling, silently running the prompt without any tools and returning
  a fake-success. This masks the model misconfiguration from the professor and produces
  no documents. The gate must return sucesso=False so callers can surface a clear error.

Current broken behaviour:
  if not model.suporta_function_calling:
      ...
      return ResultadoExecucao(sucesso=True, ...)  # ← BUG: should be False

Expected behaviour after E-T1 is implemented:
  if tools_to_use and not model.suporta_function_calling:
      return ResultadoExecucao(
          sucesso=False,
          etapa="tools",
          erro="Este modelo não suporta geração de documentos. Selecione um modelo compatível com function calling."
      )

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_e_t1_tool_capability_gate.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, ResultadoExecucao


# ============================================================
# EXACT ERROR STRING (source of truth for tests)
# ============================================================

EXPECTED_ERROR_MESSAGE = (
    "Este modelo não suporta geração de documentos. "
    "Selecione um modelo compatível com function calling."
)


# ============================================================
# HELPERS
# ============================================================

def _make_mock_model(suporta_function_calling: bool, tipo_value: str = "anthropic"):
    """Build a minimal ModelConfig-like mock."""
    model = MagicMock()
    model.suporta_function_calling = suporta_function_calling
    model.tipo = MagicMock()
    model.tipo.value = tipo_value
    model.modelo = "test-model"
    model.api_key_id = ""
    return model


def _make_chat_service_module(model):
    """Build a mock chat_service module with model_manager + api_key_manager.

    IMPORTANT: We mock ChatClient so that:
    - client.chat() returns a proper dict (simulating a successful fallback)
    - client.chat_with_tools() also returns a proper dict (simulating tool success)

    This ensures the current fallback path (sucesso=True) reaches its return
    statement successfully, so our tests that assert sucesso=False will actually
    catch the real bug (returning True instead of False).
    """
    mock_module = MagicMock()

    mock_manager = MagicMock()
    mock_manager.get = MagicMock(return_value=model)
    mock_manager.get_default = MagicMock(return_value=model)
    mock_module.model_manager = mock_manager

    mock_key_manager = MagicMock()
    mock_key_manager.get = MagicMock(return_value=None)
    mock_key_manager.get_por_empresa = MagicMock(return_value=None)
    mock_module.api_key_manager = mock_key_manager

    # Expose ProviderType so the function can use it (needed for env_map lookup)
    from chat_service import ProviderType
    mock_module.ProviderType = ProviderType

    # Mock ChatClient so client.chat() returns a clean dict (no serialization error)
    # This lets the fallback path complete with sucesso=True so our tests can
    # catch the bug: the current code returns sucesso=True, we assert sucesso=False.
    mock_client_instance = MagicMock()
    mock_client_instance.chat = AsyncMock(return_value={
        "content": "Fallback response text",
        "tokens": 42,
        "modelo": "test-model",
        "provider": "anthropic",
    })
    mock_client_instance.chat_with_tools = AsyncMock(return_value={
        "content": "Tool response text",
        "tokens": 100,
        "modelo": "test-model",
        "provider": "anthropic",
        "tool_calls": [],
    })

    mock_chat_client_cls = MagicMock(return_value=mock_client_instance)
    mock_module.ChatClient = mock_chat_client_cls

    return mock_module


def _make_tools_module():
    """Build a minimal tools module mock so PIPELINE_TOOLS exists."""
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
    model,
    tools_to_use,
    provider_id=None,
    api_key_override="test-key",
):
    """
    Patch the lazy-imported modules inside executar_com_tools and call it.

    executar_com_tools imports at call-time:
        from chat_service import model_manager, api_key_manager, ChatClient, ProviderType
        from tools import ToolRegistry, CREATE_DOCUMENT, EXECUTE_PYTHON_CODE, PIPELINE_TOOLS
        from tool_handlers import TOOL_HANDLERS
        from tools import ToolExecutionContext

    We inject mocks for all of them so no real DB or API keys are needed.
    The api_key override avoids the "API key não encontrada" early return.
    """
    chat_service_mock = _make_chat_service_module(model)
    tools_mock = _make_tools_module()
    tool_handlers_mock = _make_tool_handlers_module()

    # Inject a working api_key so we pass the key-validation block
    api_key_config = MagicMock()
    api_key_config.api_key = api_key_override
    chat_service_mock.api_key_manager.get_por_empresa.return_value = api_key_config

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
            mensagem="Gere o relatório do aluno.",
            atividade_id="atividade_test_123",
            aluno_id="aluno_test_456",
            provider_id=provider_id,
            tools_to_use=tools_to_use,
        )

    return result


# ============================================================
# TEST: NON-TOOL MODEL BLOCKED WHEN TOOLS ARE REQUESTED
# ============================================================

class TestNonToolModelBlocked:
    """When suporta_function_calling=False and tools_to_use is non-empty,
    executar_com_tools must return sucesso=False (not sucesso=True)."""

    async def test_non_tool_model_returns_sucesso_false(self):
        """Non-tool model with create_document in tools_to_use → sucesso=False.

        Currently FAILS: current code returns sucesso=True (silent fallback).
        After E-T1 the gate must return sucesso=False.
        """
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        assert isinstance(result, ResultadoExecucao), (
            "executar_com_tools must always return a ResultadoExecucao instance"
        )
        assert result.sucesso is False, (
            f"Expected sucesso=False for non-tool model with tools_to_use=['create_document'], "
            f"but got sucesso={result.sucesso}. "
            f"Current code silently falls back and returns sucesso=True — this is the bug E-T1 must fix."
        )

    async def test_non_tool_model_with_multiple_tools_returns_sucesso_false(self):
        """Non-tool model + multiple tools → still sucesso=False."""
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert result.sucesso is False, (
            f"Expected sucesso=False for non-tool model with multiple tools, got sucesso={result.sucesso}"
        )

    async def test_non_tool_model_blocked_sets_etapa_tools(self):
        """Blocked result must use etapa='tools' to match existing ResultadoExecucao conventions."""
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        assert result.sucesso is False
        assert result.etapa == "tools", (
            f"Expected etapa='tools', got etapa={result.etapa!r}"
        )


# ============================================================
# TEST: EXACT PORTUGUESE ERROR MESSAGE
# ============================================================

class TestExactErrorMessage:
    """The error field must contain the exact Portuguese string specified in the plan."""

    async def test_error_message_is_exact_portuguese_string(self):
        """erro field must equal the exact Portuguese error message from the plan.

        Currently FAILS because the current code returns sucesso=True with no erro,
        or returns a different message in the alertas list.
        """
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        # Must fail first (gate not implemented)
        assert result.sucesso is False

        assert result.erro == EXPECTED_ERROR_MESSAGE, (
            f"Expected exact error message:\n  {EXPECTED_ERROR_MESSAGE!r}\n"
            f"Got:\n  {result.erro!r}\n"
            f"The error message must be preserved verbatim for the frontend to display it."
        )

    async def test_error_message_contains_function_calling_reference(self):
        """Error message must mention 'function calling' so professors understand what's needed."""
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        assert result.sucesso is False
        assert result.erro is not None, "erro field must not be None when sucesso=False"
        assert "function calling" in result.erro, (
            f"Error message must contain 'function calling'. Got: {result.erro!r}"
        )

    async def test_error_message_contains_model_selection_guidance(self):
        """Error message must mention selecting a different model (user-actionable)."""
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        assert result.sucesso is False
        assert result.erro is not None
        assert "Selecione" in result.erro, (
            f"Error message must contain 'Selecione' (action guidance). Got: {result.erro!r}"
        )


# ============================================================
# TEST: TOOL-CAPABLE MODEL PASSES GATE
# ============================================================

class TestToolCapableModelPassesGate:
    """When suporta_function_calling=True the gate must NOT block execution."""

    async def test_tool_capable_model_does_not_return_early_error(self):
        """suporta_function_calling=True → no early sucesso=False return from gate.

        The function may still fail downstream (no real tools in our mock), but it
        must not fail AT the capability gate. We detect gate-blocking by checking that
        if sucesso=False, the erro is not the gate's error message.
        """
        model = _make_mock_model(suporta_function_calling=True)

        # We expect either:
        # (a) sucesso=True (mock tools completed somehow), OR
        # (b) sucesso=False with a DIFFERENT error (downstream failure, not the gate)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        assert isinstance(result, ResultadoExecucao)

        # The gate error must NOT be triggered for a capable model
        if not result.sucesso:
            assert result.erro != EXPECTED_ERROR_MESSAGE, (
                "Tool-capable model (suporta_function_calling=True) must NOT hit the "
                "capability gate. The gate error message was returned even though the "
                "model supports function calling — this is a logic error in the gate condition."
            )

    async def test_gate_condition_checks_suporta_function_calling(self):
        """Verify gate uses suporta_function_calling flag (not provider type) as criterion."""
        # A model that claims to support tools should pass regardless of provider name
        model = _make_mock_model(suporta_function_calling=True, tipo_value="openai")
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=["create_document"],
        )

        # Gate must not block this model
        if not result.sucesso:
            assert result.erro != EXPECTED_ERROR_MESSAGE, (
                "Gate must rely on suporta_function_calling flag, not provider type. "
                "OpenAI model with suporta_function_calling=True must pass the gate."
            )


# ============================================================
# TEST: DEFAULT tools_to_use (None) WITH NON-TOOL MODEL
# ============================================================

class TestDefaultToolsWithNonToolModel:
    """When tools_to_use=None the function expands it to the default list.
    A non-tool model must still be blocked because the expanded list is non-empty."""

    async def test_none_tools_to_use_with_non_tool_model_is_blocked(self):
        """tools_to_use=None expands to ["create_document", "execute_python_code"].
        Non-tool model must be blocked because expanded list is non-empty.

        This tests that the gate checks AFTER the None→default expansion, not before.
        """
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=None,  # Will expand to default list inside function
        )

        assert result.sucesso is False, (
            f"Expected sucesso=False when tools_to_use=None (expands to default tools) "
            f"with non-tool model, got sucesso={result.sucesso}. "
            f"The gate must check after the None→default expansion."
        )


# ============================================================
# TEST: EXPLICITLY EMPTY tools_to_use BYPASSES GATE
# ============================================================

class TestEmptyToolsListBypassesGate:
    """When tools_to_use=[] (explicitly empty list), no tools are requested.
    The gate should NOT block even for non-tool models — there's nothing to block."""

    async def test_empty_tools_list_does_not_trigger_gate(self):
        """tools_to_use=[] → no tools requested → gate should not block.

        Even a non-tool model should be allowed to run without tools.
        The gate condition is: tools_to_use is non-empty AND model lacks function calling.
        """
        model = _make_mock_model(suporta_function_calling=False)
        result = await _call_executar_com_tools(
            model=model,
            tools_to_use=[],  # Explicitly empty — no tools requested
        )

        # Must NOT be blocked by the capability gate
        # (It may fail for other reasons with our minimal mock, but not the gate)
        if not result.sucesso:
            assert result.erro != EXPECTED_ERROR_MESSAGE, (
                "Non-tool model with tools_to_use=[] must NOT be blocked by the "
                "capability gate. The gate should only fire when tools are actually "
                "requested (non-empty tools_to_use). "
                f"Got erro: {result.erro!r}"
            )
