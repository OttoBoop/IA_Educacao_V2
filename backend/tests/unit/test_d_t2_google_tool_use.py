"""
Test D-T2: Google _chat_google_with_tools() implementation

Tests:
- chat_with_tools() dispatcher routes to _chat_google_with_tools() for GOOGLE provider
- _chat_google_with_tools() parses Google Gemini functionCall format
- Tool execution loop (functionCall → execute → functionResponse → next)
- Stops when no functionCall parts in response
- Handles max_iterations
- Converts Anthropic tool format to Google function_declarations format
- Token tracking across iterations

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_d_t2_google_tool_use.py -v
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from chat_service import ChatClient, ModelConfig, ProviderType
from tools import ToolCall, ToolResult, ToolRegistry, ToolDefinition, ToolParameter, ToolExecutionContext


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def google_config():
    """ModelConfig for Google provider"""
    return ModelConfig(
        id="test-google",
        nome="Test Gemini",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-2.0-flash",
        max_tokens=4096,
        temperature=0.7,
        suporta_function_calling=True
    )


@pytest.fixture
def google_client(google_config):
    """ChatClient configured for Google"""
    return ChatClient(model_config=google_config, api_key="test-key")


@pytest.fixture
def mock_tool_registry():
    """Tool registry with a mock tool"""
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="create_document",
        description="Create a document",
        parameters=[
            ToolParameter(name="title", type="string", description="Document title", required=True),
            ToolParameter(name="content", type="string", description="Document content", required=True)
        ]
    )
    registry.register(tool)
    return registry


@pytest.fixture
def anthropic_format_tools(mock_tool_registry):
    """Tools in Anthropic format (as passed to chat_with_tools)"""
    return mock_tool_registry.get_anthropic_tools()


def make_google_function_call_response(function_calls, usage=None):
    """Helper: create a mock Google Gemini response with functionCall parts"""
    parts = [
        {"functionCall": {"name": fc["name"], "args": fc["args"]}}
        for fc in function_calls
    ]
    return {
        "candidates": [{
            "content": {"parts": parts, "role": "model"},
            "finishReason": "STOP"
        }],
        "usageMetadata": usage or {
            "promptTokenCount": 100,
            "candidatesTokenCount": 50,
            "totalTokenCount": 150
        }
    }


def make_google_final_response(text="Done!", usage=None):
    """Helper: create a mock Google Gemini response with final text"""
    return {
        "candidates": [{
            "content": {"parts": [{"text": text}], "role": "model"},
            "finishReason": "STOP"
        }],
        "usageMetadata": usage or {
            "promptTokenCount": 200,
            "candidatesTokenCount": 100,
            "totalTokenCount": 300
        }
    }


# ============================================================
# TEST: DISPATCHER ROUTING
# ============================================================

class TestGoogleDispatcherRouting:
    """chat_with_tools() routes to _chat_google_with_tools() for Google"""

    @pytest.mark.asyncio
    async def test_google_provider_routes_to_google_handler(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Dispatcher calls _chat_google_with_tools for ProviderType.GOOGLE"""
        with patch.object(google_client, '_chat_google_with_tools', new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {"content": "test", "tokens": 0, "modelo": "gemini-2.0-flash", "provider": "google", "tool_calls": []}

            await google_client.chat_with_tools(
                mensagem="test message",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                system_prompt="You are a helper"
            )

            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_google_provider_does_not_fallback_to_regular_chat(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Google provider should NOT fall back to regular chat()"""
        with patch.object(google_client, '_chat_google_with_tools', new_callable=AsyncMock) as mock_tool_handler, \
             patch.object(google_client, 'chat', new_callable=AsyncMock) as mock_regular_chat:
            mock_tool_handler.return_value = {"content": "test", "tokens": 0, "modelo": "gemini-2.0-flash", "provider": "google", "tool_calls": []}

            await google_client.chat_with_tools(
                mensagem="test",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry
            )

            mock_regular_chat.assert_not_called()


# ============================================================
# TEST: FUNCTION CALL PARSING
# ============================================================

class TestGoogleFunctionCallParsing:
    """_chat_google_with_tools() correctly parses Google functionCall format"""

    @pytest.mark.asyncio
    async def test_parses_single_function_call(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Parses a single functionCall from Google response"""
        fc_response = make_google_function_call_response([
            {"name": "create_document", "args": {"title": "Test", "content": "Hello"}}
        ])
        final_response = make_google_final_response("Document created!")

        mock_execute = AsyncMock(return_value=ToolResult(
            tool_use_id="google_call_0",
            content="Document created successfully",
            is_error=False
        ))
        mock_tool_registry.execute = mock_execute

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_r1 = MagicMock(status_code=200)
            mock_r1.json.return_value = fc_response
            mock_r2 = MagicMock(status_code=200)
            mock_r2.json.return_value = final_response
            mock_client.post = AsyncMock(side_effect=[mock_r1, mock_r2])

            result = await google_client._chat_google_with_tools(
                mensagem="Create a document",
                historico=[],
                system="You are a helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        # Tool was executed
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args.kwargs if mock_execute.call_args.kwargs else {}
        if not call_kwargs:
            call_args = mock_execute.call_args[1] if len(mock_execute.call_args) > 1 else {}
            call_kwargs = call_args
        assert call_kwargs.get("tool_name") or mock_execute.call_args[1].get("tool_name") == "create_document"

        assert result["content"] == "Document created!"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "create_document"

    @pytest.mark.asyncio
    async def test_parses_multiple_function_calls(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Parses multiple functionCalls from a single Google response"""
        fc_response = make_google_function_call_response([
            {"name": "create_document", "args": {"title": "Doc1", "content": "A"}},
            {"name": "create_document", "args": {"title": "Doc2", "content": "B"}}
        ])
        final_response = make_google_final_response("Both done!")

        async def mock_exec(tool_name, tool_input, tool_use_id, context=None):
            return ToolResult(tool_use_id=tool_use_id, content="OK", is_error=False)

        mock_tool_registry.execute = mock_exec

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_r1 = MagicMock(status_code=200)
            mock_r1.json.return_value = fc_response
            mock_r2 = MagicMock(status_code=200)
            mock_r2.json.return_value = final_response
            mock_client.post = AsyncMock(side_effect=[mock_r1, mock_r2])

            result = await google_client._chat_google_with_tools(
                mensagem="Create two docs",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        assert len(result["tool_calls"]) == 2


# ============================================================
# TEST: TOOL FORMAT CONVERSION
# ============================================================

class TestGoogleToolFormatConversion:
    """Anthropic tools converted to Google function_declarations format"""

    @pytest.mark.asyncio
    async def test_tools_sent_in_google_format(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Tools converted to function_declarations in API request"""
        final_response = make_google_final_response("No tools needed")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = final_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            await google_client._chat_google_with_tools(
                mensagem="Hello",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

            call_args = mock_client.post.call_args
            request_body = call_args.kwargs.get("json") or call_args[1].get("json")

            # Google format: tools[].function_declarations[].name
            assert "tools" in request_body
            tool_block = request_body["tools"][0]
            assert "function_declarations" in tool_block
            func_decl = tool_block["function_declarations"][0]
            assert func_decl["name"] == "create_document"
            assert "parameters" in func_decl


# ============================================================
# TEST: ITERATION & STOP CONDITIONS
# ============================================================

class TestGoogleIterationAndStop:
    """Loop stops correctly based on response content"""

    @pytest.mark.asyncio
    async def test_stops_when_no_function_calls_in_response(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Loop exits when response has text parts only (no functionCall)"""
        final_response = make_google_final_response("All done", {
            "promptTokenCount": 50, "candidatesTokenCount": 25, "totalTokenCount": 75
        })

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = final_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            result = await google_client._chat_google_with_tools(
                mensagem="Hello",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        assert result["content"] == "All done"
        assert result["tokens"] == 75
        assert result["provider"] == "google"

    @pytest.mark.asyncio
    async def test_max_iterations_exceeded(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Returns error when max iterations exceeded"""
        infinite_fc = make_google_function_call_response([
            {"name": "create_document", "args": {"title": "X", "content": "Y"}}
        ])

        async def mock_exec(tool_name, tool_input, tool_use_id, context=None):
            return ToolResult(tool_use_id=tool_use_id, content="OK", is_error=False)

        mock_tool_registry.execute = mock_exec

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = infinite_fc
            mock_client.post = AsyncMock(return_value=mock_resp)

            result = await google_client._chat_google_with_tools(
                mensagem="Infinite loop",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=2
            )

        assert "error" in result
        assert result["error"] == "max_iterations_exceeded"


# ============================================================
# TEST: TOKEN TRACKING
# ============================================================

class TestGoogleTokenTracking:
    """Tokens accumulated across iterations using Google usageMetadata"""

    @pytest.mark.asyncio
    async def test_tokens_accumulated(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Total tokens = sum of all iteration tokens"""
        fc_response = make_google_function_call_response(
            [{"name": "create_document", "args": {"title": "T", "content": "C"}}],
            usage={"promptTokenCount": 100, "candidatesTokenCount": 50, "totalTokenCount": 150}
        )
        final_response = make_google_final_response(
            "Done",
            usage={"promptTokenCount": 200, "candidatesTokenCount": 80, "totalTokenCount": 280}
        )

        async def mock_exec(tool_name, tool_input, tool_use_id, context=None):
            return ToolResult(tool_use_id=tool_use_id, content="OK", is_error=False)

        mock_tool_registry.execute = mock_exec

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_r1 = MagicMock(status_code=200)
            mock_r1.json.return_value = fc_response
            mock_r2 = MagicMock(status_code=200)
            mock_r2.json.return_value = final_response
            mock_client.post = AsyncMock(side_effect=[mock_r1, mock_r2])

            result = await google_client._chat_google_with_tools(
                mensagem="Create doc",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        assert result["tokens"] == 430


# ============================================================
# TEST: RESPONSE STRUCTURE
# ============================================================

class TestGoogleResponseStructure:
    """Response has required keys matching normalized format"""

    @pytest.mark.asyncio
    async def test_response_has_required_keys(self, google_client, mock_tool_registry, anthropic_format_tools):
        """Response contains content, tokens, modelo, provider, tool_calls"""
        final_response = make_google_final_response("Hello")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = final_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            result = await google_client._chat_google_with_tools(
                mensagem="Hi",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        assert "content" in result
        assert "tokens" in result
        assert "modelo" in result
        assert "provider" in result
        assert "tool_calls" in result
