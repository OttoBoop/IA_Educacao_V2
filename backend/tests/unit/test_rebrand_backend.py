"""
Structural tests for NOVO CR backend branding.

C-T1: FastAPI title and root response must say "NOVO CR".
C-T2: OpenRouter headers must reference "NOVO CR".

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_backend.py -v
"""

from pathlib import Path

import pytest

MAIN_V2 = Path(__file__).parent.parent.parent / "main_v2.py"
CHAT_SERVICE = Path(__file__).parent.parent.parent / "chat_service.py"


@pytest.fixture
def main_v2_content():
    """Read the main_v2.py file."""
    assert MAIN_V2.exists(), f"File not found: {MAIN_V2}"
    return MAIN_V2.read_text(encoding="utf-8")


@pytest.fixture
def chat_service_content():
    """Read the chat_service.py file."""
    assert CHAT_SERVICE.exists(), f"File not found: {CHAT_SERVICE}"
    return CHAT_SERVICE.read_text(encoding="utf-8")


class TestFastAPITitle:
    """C-T1: FastAPI app title must say 'NOVO CR'."""

    def test_fastapi_title_contains_novo_cr(self, main_v2_content):
        """FastAPI title should say 'NOVO CR - Sistema de Correção v2.0'."""
        assert 'title="NOVO CR - Sistema de Corre' in main_v2_content

    def test_fastapi_title_no_old_brand(self, main_v2_content):
        """FastAPI title must not say 'Prova AI'."""
        # Check within the FastAPI() constructor area only
        assert 'title="Prova AI' not in main_v2_content


class TestRootEndpoint:
    """C-T1: Root endpoint response must say 'NOVO CR'."""

    def test_root_response_contains_novo_cr(self, main_v2_content):
        """Root endpoint message should say 'API NOVO CR v2.0'."""
        assert '"API NOVO CR v2.0"' in main_v2_content

    def test_root_response_no_old_brand(self, main_v2_content):
        """Root endpoint must not say 'Prova AI'."""
        assert '"API Prova AI v2.0"' not in main_v2_content


class TestOpenRouterHeaders:
    """C-T2: OpenRouter HTTP headers must reference 'NOVO CR'."""

    def test_x_title_contains_novo_cr(self, chat_service_content):
        """X-Title header should say 'NOVO CR'."""
        assert '"X-Title"] = "NOVO CR"' in chat_service_content

    def test_x_title_no_old_brand(self, chat_service_content):
        """X-Title must not say 'Prova AI'."""
        assert '"X-Title"] = "Prova AI"' not in chat_service_content

    def test_http_referer_updated(self, chat_service_content):
        """HTTP-Referer should reference novo-cr, not prova-ai."""
        assert "novo-cr" in chat_service_content or "novocr" in chat_service_content
        assert '"HTTP-Referer"] = "https://prova-ai' not in chat_service_content
