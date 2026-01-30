"""
Shared fixtures for Prova AI tests.
"""

import os

# Avoid hanging tests when local LLM is not running.
os.environ.setdefault("PROVA_AI_DISABLE_LOCAL_LLM", "1")
os.environ.setdefault("PROVA_AI_TESTING", "1")

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


# ============================================================
# COMMAND LINE OPTIONS
# ============================================================

# Configuração de modelos por modo (sync com test_runner.py)
# Model IDs verified working as of January 2026
# NOTE: Gemini 3 requires "-preview" suffix. Gemini 2.0 deprecated (EOL March 2026)
MODEL_CONFIGS = {
    "cheap": {
        "openai": "gpt-5-mini",
        "anthropic": "claude-haiku-4-5-20251001",
        "google": "gemini-3-flash-preview",  # Gemini 3 requires -preview suffix
    },
    "full": {
        "openai": "gpt-5",
        "anthropic": "claude-sonnet-4-5-20250929",
        "google": "gemini-3-pro-preview",  # Gemini 3 requires -preview suffix
    },
    "reasoning": {
        "openai": "o3-mini",
        "anthropic": "claude-sonnet-4-5-20250929",
        "google": "gemini-3-pro-preview",  # Gemini 3 requires -preview suffix
    },
    "legacy": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "google": "gemini-2.5-flash",  # 2.0 deprecated, use 2.5
    }
}


def pytest_addoption(parser):
    """Adiciona opções de linha de comando para testes."""
    parser.addoption(
        "--provider",
        action="store",
        default=None,
        help="Provider para testar: openai, anthropic, google"
    )
    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="Modelo específico para testar: gpt-5-mini, claude-haiku-4-5-20251001"
    )
    parser.addoption(
        "--model-mode",
        action="store",
        default="cheap",
        choices=["cheap", "full", "reasoning", "legacy"],
        help="Modo de seleção de modelos: cheap (padrão), full, reasoning, legacy"
    )
    parser.addoption(
        "--reasoning",
        action="store_true",
        default=False,
        help="Testar apenas modelos reasoning (o1, o3, etc.)"
    )
    parser.addoption(
        "--skip-expensive",
        action="store_true",
        default=False,
        help="Pular modelos caros (opus, o3, gpt-5, etc.)"
    )
    parser.addoption(
        "--timeout",
        action="store",
        default=60,
        type=int,
        help="Timeout em segundos para requisições de IA"
    )


# ============================================================
# PROVIDER SELECTION FIXTURES
# ============================================================

@pytest.fixture
def selected_provider(request) -> str:
    """Retorna o provider/modelo selecionado via CLI ou default."""
    model = request.config.getoption("--model")
    provider = request.config.getoption("--provider")
    model_mode = request.config.getoption("--model-mode")

    # Modelo específico tem prioridade
    if model:
        return model

    # Obter config do modo
    mode_config = MODEL_CONFIGS.get(model_mode, MODEL_CONFIGS["cheap"])

    # Se provider especificado, usar modelo do modo atual
    if provider:
        return mode_config.get(provider, mode_config["openai"])

    # Default: modelo OpenAI do modo atual
    return mode_config["openai"]


@pytest.fixture
def skip_expensive(request) -> bool:
    """Verifica se deve pular modelos caros."""
    return request.config.getoption("--skip-expensive")


@pytest.fixture
def test_timeout(request) -> int:
    """Timeout para requisições de IA."""
    return request.config.getoption("--timeout")


@pytest.fixture
def is_reasoning_only(request) -> bool:
    """Verifica se deve testar apenas modelos reasoning."""
    return request.config.getoption("--reasoning")


@pytest.fixture
def model_mode(request) -> str:
    """Retorna o modo de modelo atual (cheap, full, reasoning, legacy)."""
    return request.config.getoption("--model-mode")


@pytest.fixture
def model_config(model_mode) -> Dict[str, str]:
    """Retorna a configuração de modelos do modo atual."""
    return MODEL_CONFIGS.get(model_mode, MODEL_CONFIGS["cheap"])


# ============================================================
# DOCUMENT FACTORY FIXTURES
# ============================================================

@pytest.fixture
def document_factory(temp_data_dir: Path):
    """Fábrica de documentos de teste."""
    from tests.fixtures.document_factory import DocumentFactory
    return DocumentFactory(temp_data_dir / "documents")


@pytest.fixture
def test_scenario(document_factory):
    """Cenário de teste completo com 2 alunos."""
    return document_factory.criar_cenario_completo(
        materia="Matemática",
        num_alunos=2,
        qualidades=["excelente", "medio"]
    )


@pytest.fixture
def corrupted_document(document_factory):
    """Documento corrompido para testes de erro."""
    return document_factory.criar_documento_corrompido("json_invalido")


@pytest.fixture
def empty_document(document_factory):
    """Documento vazio para testes."""
    return document_factory.criar_documento_corrompido("arquivo_vazio")


# ============================================================
# ENVIRONMENT DETECTION
# ============================================================

@pytest.fixture
def is_render_environment() -> bool:
    """Detecta se está rodando no Render."""
    import os
    return os.getenv("RENDER") == "true"


@pytest.fixture
def api_keys_available() -> Dict[str, bool]:
    """Verifica quais API keys estão disponíveis (env vars OU api_key_manager com path correto)."""
    import os
    from chat_service import ApiKeyManager, ProviderType

    # Usar path absoluto para api_keys.json
    api_keys_path = backend_dir / "data" / "api_keys.json"
    key_manager = ApiKeyManager(config_path=str(api_keys_path)) if api_keys_path.exists() else None

    return {
        "openai": bool(os.getenv("OPENAI_API_KEY")) or (key_manager and key_manager.get_por_empresa(ProviderType.OPENAI) is not None),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")) or (key_manager and key_manager.get_por_empresa(ProviderType.ANTHROPIC) is not None),
        "google": bool(os.getenv("GOOGLE_API_KEY")) or (key_manager and key_manager.get_por_empresa(ProviderType.GOOGLE) is not None),
        "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
        "mistral": bool(os.getenv("MISTRAL_API_KEY")),
    }


# ============================================================
# AI PROVIDER FIXTURES
# ============================================================

@pytest.fixture
def ai_provider(selected_provider):
    """
    Retorna um provider de IA configurado.
    Usa ApiKeyManager com path absoluto para garantir que encontra as keys.
    """
    from chat_service import ApiKeyManager, ProviderType
    from ai_providers import OpenAIProvider, AnthropicProvider, GeminiProvider

    # Usar path absoluto para o arquivo de API keys
    api_keys_path = backend_dir / "data" / "api_keys.json"

    if not api_keys_path.exists():
        pytest.fail(f"Arquivo de API keys não encontrado: {api_keys_path}")

    # Criar manager com path correto
    key_manager = ApiKeyManager(config_path=str(api_keys_path))

    if not key_manager.keys:
        pytest.fail(f"Nenhuma API key carregada de {api_keys_path}. Verifique se o arquivo .encryption_key existe em data/")

    # Determinar provider baseado no modelo selecionado
    model = selected_provider.lower()

    if "gpt" in model or "o1" in model or "o3" in model or "o4" in model:
        key_config = key_manager.get_por_empresa(ProviderType.OPENAI)
        if key_config:
            return OpenAIProvider(api_key=key_config.api_key, model=selected_provider)
        pytest.fail("API key OpenAI não encontrada ou inativa")

    elif "claude" in model:
        key_config = key_manager.get_por_empresa(ProviderType.ANTHROPIC)
        if key_config:
            return AnthropicProvider(api_key=key_config.api_key, model=selected_provider)
        pytest.fail("API key Anthropic não encontrada ou inativa")

    elif "gemini" in model:
        key_config = key_manager.get_por_empresa(ProviderType.GOOGLE)
        if key_config:
            return GeminiProvider(api_key=key_config.api_key, model=selected_provider)
        pytest.fail("API key Google não encontrada ou inativa")

    # Fallback: tentar OpenAI
    key_config = key_manager.get_por_empresa(ProviderType.OPENAI)
    if key_config:
        return OpenAIProvider(api_key=key_config.api_key, model="gpt-4o-mini")

    pytest.fail(f"Nenhum provider disponível para modelo: {selected_provider}")


# ============================================================
# MOCK AI RESPONSES
# ============================================================

@pytest.fixture
def mock_json_response():
    """Resposta JSON válida mockada."""
    return {
        "questoes": [
            {
                "numero": 1,
                "enunciado": "Resolva: 2+2",
                "resposta": "4",
                "pontuacao": 2.0
            }
        ],
        "total_questoes": 1,
        "pontuacao_total": 2.0
    }


@pytest.fixture
def mock_empty_json_response():
    """Resposta JSON vazia mockada."""
    return {}


@pytest.fixture
def mock_invalid_json_response():
    """Resposta com JSON inválido mockada."""
    return "Aqui está a resposta: {questoes: [invalido]}"


@pytest.fixture
def mock_correcao_response():
    """Resposta de correção mockada."""
    return {
        "questoes": [
            {
                "numero": 1,
                "nota": 1.8,
                "nota_maxima": 2.0,
                "feedback": "Resposta parcialmente correta",
                "erros": ["Faltou mostrar o cálculo"]
            }
        ],
        "nota_total": 1.8,
        "nota_maxima": 2.0,
        "observacoes": "Bom trabalho, mas mostre os cálculos"
    }


# ============================================================
# SKIP MARKERS
# ============================================================

@pytest.fixture(autouse=True)
def skip_if_no_api_key(request, api_keys_available):
    """Pula testes automaticamente se API key não disponível."""
    markers = list(request.node.iter_markers())

    for marker in markers:
        if marker.name == "openai" and not api_keys_available["openai"]:
            pytest.skip("OPENAI_API_KEY não disponível")
        elif marker.name == "anthropic" and not api_keys_available["anthropic"]:
            pytest.skip("ANTHROPIC_API_KEY não disponível")
        elif marker.name == "google" and not api_keys_available["google"]:
            pytest.skip("GOOGLE_API_KEY não disponível")


@pytest.fixture(autouse=True)
def skip_expensive_if_requested(request, skip_expensive):
    """Pula testes marcados como expensive se solicitado."""
    if skip_expensive:
        markers = list(request.node.iter_markers())
        for marker in markers:
            if marker.name == "expensive":
                pytest.skip("Modelo caro pulado (--skip-expensive)")


# ============================================================
# LOGGING SETUP
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Configura logging para testes."""
    try:
        from logging_config import setup_logging
        setup_logging(
            level="DEBUG",
            log_dir=Path(__file__).parent.parent / "logs",
            console_output=False,
            file_output=True
        )
    except ImportError:
        pass
