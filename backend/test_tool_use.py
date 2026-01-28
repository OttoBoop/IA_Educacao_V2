"""
Example script demonstrating Anthropic Tool Use integration.

This script shows how to use the ChatClient with tools to generate files via code execution.
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_tool_use():
    """Test the tool use integration with a simple code execution example."""
    from chat_service import ChatClient, ModelConfig, ProviderType, model_manager
    from tools import create_registry_with_handlers, ToolExecutionContext

    # Get or create a model config for Anthropic
    model_config = ModelConfig(
        id="test-claude-sonnet",
        nome="Claude Sonnet Test",
        modelo="claude-sonnet-4-20250514",
        tipo=ProviderType.ANTHROPIC,
        max_tokens=4096,
        suporta_temperature=True,
        temperature=0.7
    )

    # Get API key (from environment or api_key_manager)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        from chat_service import api_key_manager
        key_config = api_key_manager.get_por_empresa(ProviderType.ANTHROPIC)
        if key_config:
            api_key = key_config.api_key

    if not api_key:
        print("ERROR: No Anthropic API key found!")
        print("Set ANTHROPIC_API_KEY environment variable or add key via the UI")
        return

    # Create client and tool registry
    client = ChatClient(model_config, api_key)
    tool_registry = create_registry_with_handlers(["execute_python_code"])

    # Get tools in Anthropic format
    tools = tool_registry.get_anthropic_tools()

    print("=" * 60)
    print("Tool Use Test - Code Execution")
    print("=" * 60)
    print(f"\nModel: {model_config.modelo}")
    print(f"Tools available: {[t['name'] for t in tools]}")
    print()

    # Test message that should trigger tool use
    test_message = """
    Please create a simple Python script that generates a chart showing
    the fibonacci sequence (first 10 numbers) and saves it as 'fibonacci_chart.png'.
    Use matplotlib for the visualization.
    """

    print(f"User message:\n{test_message}\n")
    print("-" * 60)

    # Call chat with tools
    context = ToolExecutionContext()

    try:
        response = await client.chat_with_tools(
            mensagem=test_message,
            tools=tools,
            tool_registry=tool_registry,
            context=context,
            max_iterations=5
        )

        print(f"\nClaude's response:\n{response.get('content', '')}\n")

        if response.get("tool_calls"):
            print("-" * 60)
            print(f"Tool calls made: {len(response['tool_calls'])}")
            for tc in response["tool_calls"]:
                print(f"  - {tc['name']}: {tc['input'].get('description', 'No description')}")

        print(f"\nTotal tokens used: {response.get('tokens', 0)}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


async def test_simple_chat():
    """Test that regular chat still works without tools."""
    from chat_service import ChatClient, ModelConfig, ProviderType

    model_config = ModelConfig(
        id="test-claude-sonnet",
        nome="Claude Sonnet Test",
        modelo="claude-sonnet-4-20250514",
        tipo=ProviderType.ANTHROPIC,
        max_tokens=1024,
        suporta_temperature=True,
        temperature=0.7
    )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        from chat_service import api_key_manager
        key_config = api_key_manager.get_por_empresa(ProviderType.ANTHROPIC)
        if key_config:
            api_key = key_config.api_key

    if not api_key:
        print("ERROR: No Anthropic API key found!")
        return

    client = ChatClient(model_config, api_key)

    print("=" * 60)
    print("Simple Chat Test (no tools)")
    print("=" * 60)

    response = await client.chat(
        mensagem="What is 2 + 2? Answer in one word.",
        system_prompt="You are a helpful assistant."
    )

    print(f"Response: {response.get('content', '')}")
    print(f"Tokens: {response.get('tokens', 0)}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" ANTHROPIC TOOL USE TEST SUITE ")
    print("=" * 60 + "\n")

    # Run tests
    asyncio.run(test_simple_chat())
    print("\n")
    asyncio.run(test_tool_use())
