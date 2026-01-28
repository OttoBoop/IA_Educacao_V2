"""
Shared fixtures for Prova AI tests.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path BEFORE any other imports
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
import tempfile
import shutil
from typing import Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================
# ASYNC EVENT LOOP FIXTURE
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================
# TEMPORARY DATA DIRECTORY
# ============================================================

@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Creates a temporary directory for test data."""
    temp_dir = Path(tempfile.mkdtemp(prefix="prova_ai_test_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# ============================================================
# MOCK HTTP RESPONSES
# ============================================================

@pytest.fixture
def mock_httpx_response():
    """Factory fixture for creating mock httpx responses."""
    def _create_response(status_code: int, json_data: Dict[str, Any]):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data
        response.text = str(json_data)
        return response
    return _create_response


@pytest.fixture
def mock_openai_chat_response(mock_httpx_response):
    """Creates a mock OpenAI chat completion response."""
    return mock_httpx_response(200, {
        "choices": [{
            "message": {"content": "Test response from OpenAI"},
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 50,
            "total_tokens": 100
        }
    })


@pytest.fixture
def mock_anthropic_chat_response(mock_httpx_response):
    """Creates a mock Anthropic messages response."""
    return mock_httpx_response(200, {
        "content": [{"type": "text", "text": "Test response from Claude"}],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 50,
            "output_tokens": 50
        }
    })


@pytest.fixture
def mock_google_chat_response(mock_httpx_response):
    """Creates a mock Google Gemini response."""
    return mock_httpx_response(200, {
        "candidates": [{
            "content": {
                "parts": [{"text": "Test response from Gemini"}]
            }
        }],
        "usageMetadata": {
            "promptTokenCount": 50,
            "candidatesTokenCount": 50,
            "totalTokenCount": 100
        }
    })


# ============================================================
# SAMPLE FILES
# ============================================================

@pytest.fixture
def sample_pdf_path(temp_data_dir: Path) -> Path:
    """Creates a minimal test PDF file."""
    pdf_path = temp_data_dir / "test_prova.pdf"
    # Minimal PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_json_path(temp_data_dir: Path) -> Path:
    """Creates a test JSON file."""
    json_path = temp_data_dir / "test_data.json"
    json_path.write_text('{"questoes": [{"numero": 1, "enunciado": "Test"}]}', encoding='utf-8')
    return json_path
