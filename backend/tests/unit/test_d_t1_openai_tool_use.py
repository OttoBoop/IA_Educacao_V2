"""
Test D-T1: OpenAI _chat_openai_with_tools() implementation

Tests:
- chat_with_tools() dispatcher routes to _chat_openai_with_tools() for OPENAI provider
- _chat_openai_with_tools() parses OpenAI tool_calls response format
- Tool execution loop works (tool_calls → execute → tool response → next iteration)
- Stops when finish_reason == "stop"
- Handles max_iterations
- Converts Anthropic tool format to OpenAI format
- Token tracking across iterations

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_d_t1_openai_tool_use.py -v
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
def openai_config():
    """ModelConfig for OpenAI provider"""
    return ModelConfig(
        id="test-openai",
        nome="Test GPT-4o",
        tipo=ProviderType.OPENAI,
        modelo="gpt-4o",
        max_tokens=4096,
        temperature=0.7,
        suporta_function_calling=True
    )


@pytest.fixture
def openai_client(openai_config):
    """ChatClient configured for OpenAI"""
    return ChatClient(model_config=openai_config, api_key="test-key")


@pytest.fixture
def mock_tool_registry():
    """Tool registry with a mock tool"""
    registry = ToolRegistry()
    tool = ToolDefinition(
        name="create_document",
        description="Create a document",
        parameters=[
            ToolParameter(
                name="title",
                type="string",
                description="Document title",
                required=True
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Document content",
                required=True
            )
        ]
    )
    registry.register(tool)
    return registry


@pytest.fixture
def anthropic_format_tools(mock_tool_registry):
    """Tools in Anthropic format (as passed to chat_with_tools)"""
    return mock_tool_registry.get_anthropic_tools()


def make_openai_tool_call_response(tool_calls, usage=None):
    """Helper: create a mock OpenAI response with tool_calls"""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"])
                        }
                    }
                    for tc in tool_calls
                ]
            },
            "finish_reason": "tool_calls"
        }],
        "usage": usage or {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    }


def make_openai_final_response(content="Done!", usage=None):
    """Helper: create a mock OpenAI response with final text"""
    return {
        "id": "chatcmpl-test-final",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "finish_reason": "stop"
        }],
        "usage": usage or {"prompt_tokens": 200, "completion_tokens": 100, "total_tokens": 300}
    }


# ============================================================
# TEST: DISPATCHER ROUTING
# ============================================================

class TestDispatcherRouting:
    """chat_with_tools() routes to _chat_openai_with_tools() for OpenAI"""

    @pytest.mark.asyncio
    async def test_openai_provider_routes_to_openai_handler(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Dispatcher calls _chat_openai_with_tools for ProviderType.OPENAI"""
        with patch.object(openai_client, '_chat_openai_with_tools', new_callable=AsyncMock) as mock_handler:
            mock_handler.return_value = {"content": "test", "tokens": 0, "modelo": "gpt-4o", "provider": "openai", "tool_calls": []}

            await openai_client.chat_with_tools(
                mensagem="test message",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                system_prompt="You are a helper"
            )

            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_provider_does_not_fallback_to_regular_chat(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """OpenAI provider should NOT fall back to regular chat()"""
        with patch.object(openai_client, '_chat_openai_with_tools', new_callable=AsyncMock) as mock_tool_handler, \
             patch.object(openai_client, 'chat', new_callable=AsyncMock) as mock_regular_chat:
            mock_tool_handler.return_value = {"content": "test", "tokens": 0, "modelo": "gpt-4o", "provider": "openai", "tool_calls": []}

            await openai_client.chat_with_tools(
                mensagem="test",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry
            )

            mock_regular_chat.assert_not_called()


# ============================================================
# TEST: TOOL CALL PARSING
# ============================================================

class TestOpenAIToolCallParsing:
    """_chat_openai_with_tools() correctly parses OpenAI tool_calls format"""

    @pytest.mark.asyncio
    async def test_parses_single_tool_call(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Parses a single tool call from OpenAI response"""
        tool_call_response = make_openai_tool_call_response([
            {"id": "call_123", "name": "create_document", "arguments": {"title": "Test", "content": "Hello"}}
        ])
        final_response = make_openai_final_response("Document created!")

        mock_execute = AsyncMock(return_value=ToolResult(
            tool_use_id="call_123",
            content="Document created successfully",
            is_error=False
        ))
        mock_tool_registry.execute = mock_execute

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            # First call returns tool_calls, second returns final
            mock_response_1 = MagicMock(status_code=200)
            mock_response_1.json.return_value = tool_call_response
            mock_response_2 = MagicMock(status_code=200)
            mock_response_2.json.return_value = final_response
            mock_client.post = AsyncMock(side_effect=[mock_response_1, mock_response_2])

            result = await openai_client._chat_openai_with_tools(
                mensagem="Create a document",
                historico=[],
                system="You are a helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        # Tool was executed with correct args
        mock_execute.assert_called_once_with(
            tool_name="create_document",
            tool_input={"title": "Test", "content": "Hello"},
            tool_use_id="call_123",
            context=None
        )

        assert result["content"] == "Document created!"
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "create_document"

    @pytest.mark.asyncio
    async def test_parses_multiple_tool_calls_in_one_response(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Parses multiple tool calls from a single OpenAI response"""
        tool_call_response = make_openai_tool_call_response([
            {"id": "call_1", "name": "create_document", "arguments": {"title": "Doc1", "content": "A"}},
            {"id": "call_2", "name": "create_document", "arguments": {"title": "Doc2", "content": "B"}}
        ])
        final_response = make_openai_final_response("Both documents created!")

        call_count = 0
        async def mock_exec(tool_name, tool_input, tool_use_id, context=None):
            return ToolResult(tool_use_id=tool_use_id, content="OK", is_error=False)

        mock_tool_registry.execute = mock_exec

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_r1 = MagicMock(status_code=200)
            mock_r1.json.return_value = tool_call_response
            mock_r2 = MagicMock(status_code=200)
            mock_r2.json.return_value = final_response
            mock_client.post = AsyncMock(side_effect=[mock_r1, mock_r2])

            result = await openai_client._chat_openai_with_tools(
                mensagem="Create two documents",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        assert len(result["tool_calls"]) == 2
        assert result["tool_calls"][0]["id"] == "call_1"
        assert result["tool_calls"][1]["id"] == "call_2"


# ============================================================
# TEST: TOOL FORMAT CONVERSION
# ============================================================

class TestToolFormatConversion:
    """Anthropic tool format is converted to OpenAI format for API calls"""

    @pytest.mark.asyncio
    async def test_tools_sent_in_openai_format(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Tools are converted from Anthropic format to OpenAI format in the API request"""
        final_response = make_openai_final_response("No tools needed")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = final_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            await openai_client._chat_openai_with_tools(
                mensagem="Hello",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

            # Check the request body
            call_args = mock_client.post.call_args
            request_body = call_args.kwargs.get("json") or call_args[1].get("json")

            # OpenAI format: tools[].type == "function" with function.name/description/parameters
            assert "tools" in request_body
            tool = request_body["tools"][0]
            assert tool["type"] == "function"
            assert "function" in tool
            assert tool["function"]["name"] == "create_document"
            assert "parameters" in tool["function"]


# ============================================================
# TEST: ITERATION & STOP CONDITIONS
# ============================================================

class TestIterationAndStopConditions:
    """Loop stops correctly on finish_reason and max_iterations"""

    @pytest.mark.asyncio
    async def test_stops_on_finish_reason_stop(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Loop exits when finish_reason == 'stop'"""
        final_response = make_openai_final_response("All done", {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = final_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            result = await openai_client._chat_openai_with_tools(
                mensagem="Hello",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        assert result["content"] == "All done"
        assert result["tokens"] == 75
        assert result["provider"] == "openai"
        assert result["modelo"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_max_iterations_exceeded(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Returns error when max iterations exceeded"""
        # Every response is a tool call — never stops
        infinite_tool_response = make_openai_tool_call_response([
            {"id": "call_inf", "name": "create_document", "arguments": {"title": "X", "content": "Y"}}
        ])

        async def mock_exec(tool_name, tool_input, tool_use_id, context=None):
            return ToolResult(tool_use_id=tool_use_id, content="OK", is_error=False)

        mock_tool_registry.execute = mock_exec

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = infinite_tool_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            result = await openai_client._chat_openai_with_tools(
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

class TestTokenTracking:
    """Tokens are accumulated across iterations"""

    @pytest.mark.asyncio
    async def test_tokens_accumulated_across_iterations(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Total tokens = sum of all iteration tokens"""
        tool_response = make_openai_tool_call_response(
            [{"id": "call_1", "name": "create_document", "arguments": {"title": "T", "content": "C"}}],
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        )
        final_response = make_openai_final_response(
            "Done",
            usage={"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280}
        )

        async def mock_exec(tool_name, tool_input, tool_use_id, context=None):
            return ToolResult(tool_use_id=tool_use_id, content="OK", is_error=False)

        mock_tool_registry.execute = mock_exec

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_r1 = MagicMock(status_code=200)
            mock_r1.json.return_value = tool_response
            mock_r2 = MagicMock(status_code=200)
            mock_r2.json.return_value = final_response
            mock_client.post = AsyncMock(side_effect=[mock_r1, mock_r2])

            result = await openai_client._chat_openai_with_tools(
                mensagem="Create doc",
                historico=[],
                system="Helper",
                tools=anthropic_format_tools,
                tool_registry=mock_tool_registry,
                max_iterations=10
            )

        # 150 + 280 = 430 total tokens
        assert result["tokens"] == 430


# ============================================================
# TEST: RESPONSE STRUCTURE
# ============================================================

class TestResponseStructure:
    """Response dict has required keys matching Anthropic handler pattern"""

    @pytest.mark.asyncio
    async def test_response_has_required_keys(self, openai_client, mock_tool_registry, anthropic_format_tools):
        """Response contains content, tokens, modelo, provider, tool_calls"""
        final_response = make_openai_final_response("Hello")

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            mock_resp = MagicMock(status_code=200)
            mock_resp.json.return_value = final_response
            mock_client.post = AsyncMock(return_value=mock_resp)

            result = await openai_client._chat_openai_with_tools(
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
