"""
Test Anthropic Tool Use with Claude Haiku
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


async def test_haiku_excel():
    """Test Haiku creating an Excel file via tool use."""
    from chat_service import ChatClient, ModelConfig, ProviderType, api_key_manager
    from tools import create_registry_with_handlers, ToolExecutionContext

    # Use Claude Haiku
    model_config = ModelConfig(
        id="test-haiku",
        nome="Claude Haiku Test",
        modelo="claude-haiku-4-5-20251001",  # Haiku 4.5
        tipo=ProviderType.ANTHROPIC,
        max_tokens=2048,
        suporta_temperature=True,
        temperature=0.5
    )

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        key_config = api_key_manager.get_por_empresa(ProviderType.ANTHROPIC)
        if key_config:
            api_key = key_config.api_key

    if not api_key:
        print("ERROR: No Anthropic API key found!")
        return

    # Create client and tool registry
    client = ChatClient(model_config, api_key)
    tool_registry = create_registry_with_handlers(["execute_python_code"])
    tools = tool_registry.get_anthropic_tools()

    print("=" * 60)
    print("CLAUDE HAIKU - EXCEL FILE GENERATION TEST")
    print("=" * 60)
    print(f"Model: {model_config.modelo}")
    print(f"Tools: {[t['name'] for t in tools]}")
    print()

    # Simple request to create an Excel file
    message = """
    Create an Excel file called 'grades.xlsx' with a simple table showing:
    - Column A: Student names (Alice, Bob, Carol, David)
    - Column B: Math grades (85, 92, 78, 95)
    - Column C: Science grades (90, 88, 82, 91)

    Use pandas and openpyxl to create the file.
    """

    print(f"User request:\n{message}\n")
    print("-" * 60)

    context = ToolExecutionContext()

    try:
        response = await client.chat_with_tools(
            mensagem=message,
            tools=tools,
            tool_registry=tool_registry,
            context=context,
            max_iterations=5
        )

        print(f"\nHaiku's response:\n{response.get('content', '')}\n")

        if response.get("tool_calls"):
            print("-" * 60)
            print(f"Tool calls made: {len(response['tool_calls'])}")
            for tc in response["tool_calls"]:
                print(f"  Tool: {tc['name']}")
                if 'code' in tc.get('input', {}):
                    code_preview = tc['input']['code'][:200] + "..." if len(tc['input'].get('code', '')) > 200 else tc['input'].get('code', '')
                    print(f"  Code preview:\n{code_preview}")

        print(f"\nTotal tokens: {response.get('tokens', 0)}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


async def test_haiku_pdf():
    """Test Haiku creating a PDF file via tool use."""
    from chat_service import ChatClient, ModelConfig, ProviderType, api_key_manager
    from tools import create_registry_with_handlers, ToolExecutionContext

    model_config = ModelConfig(
        id="test-haiku",
        nome="Claude Haiku Test",
        modelo="claude-haiku-4-5-20251001",
        tipo=ProviderType.ANTHROPIC,
        max_tokens=2048,
        suporta_temperature=True,
        temperature=0.5
    )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        key_config = api_key_manager.get_por_empresa(ProviderType.ANTHROPIC)
        if key_config:
            api_key = key_config.api_key

    if not api_key:
        print("ERROR: No Anthropic API key found!")
        return

    client = ChatClient(model_config, api_key)
    tool_registry = create_registry_with_handlers(["execute_python_code"])
    tools = tool_registry.get_anthropic_tools()

    print("\n" + "=" * 60)
    print("CLAUDE HAIKU - PDF FILE GENERATION TEST")
    print("=" * 60)
    print(f"Model: {model_config.modelo}")
    print()

    message = """
    Create a simple PDF file called 'report.pdf' with:
    - A title: "Student Progress Report"
    - A paragraph of text explaining this is a test report
    - Today's date

    Use reportlab to create the PDF.
    """

    print(f"User request:\n{message}\n")
    print("-" * 60)

    context = ToolExecutionContext()

    try:
        response = await client.chat_with_tools(
            mensagem=message,
            tools=tools,
            tool_registry=tool_registry,
            context=context,
            max_iterations=5
        )

        print(f"\nHaiku's response:\n{response.get('content', '')}\n")

        if response.get("tool_calls"):
            print("-" * 60)
            print(f"Tool calls made: {len(response['tool_calls'])}")

        print(f"\nTotal tokens: {response.get('tokens', 0)}")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print(" CLAUDE HAIKU TOOL USE TESTS ")
    print("=" * 60 + "\n")

    # Run Excel test
    asyncio.run(test_haiku_excel())

    # Run PDF test
    asyncio.run(test_haiku_pdf())
