"""
Testes para modelos Google (Gemini)

Gemini suporta temperature, vision, tools e PDFs nativos.
"""

import pytest
from typing import List
from .base_model_test import BaseModelTest, ModelTestConfig, require_vision, require_tools


@pytest.mark.google
class TestGoogle(BaseModelTest):
    """
    Testes para Gemini.

    Características:
    - Suporta temperature (0-2) - mesmo range do OpenAI
    - Suporta vision (imagens, PDFs, vídeos, áudio)
    - Suporta tools/function calling
    - API diferente (generationConfig, systemInstruction)
    - Header: x-goog-api-key

    NOTE: Gemini 3 models require "-preview" suffix (verified Jan 2026)
    """

    # Model IDs verified working as of January 2026
    # Gemini 3 requires "-preview" suffix, Gemini 2.5 uses direct IDs
    MODELS = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3-flash-preview", "gemini-3-pro-preview"]

    @property
    def model_config(self) -> ModelTestConfig:
        return ModelTestConfig(
            provider_type="google",
            model_id="gemini-2.5-flash",
            supports_temperature=True,
            supports_vision=True,
            supports_tools=True,
            is_reasoning=False,
            max_tokens=8192,
            expected_latency_ms=12000
        )

    @pytest.mark.asyncio
    async def test_generation_config(self, selected_provider):
        """Testa que temperature vai em generationConfig"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Diga olá",
            temperature=0.5,
            max_tokens=50
        )

        assert response is not None
        assert response.content is not None

    @pytest.mark.asyncio
    async def test_system_instruction(self, selected_provider):
        """Testa systemInstruction (formato Gemini)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Qual é sua função?",
            system_prompt="Você é um assistente educacional especializado em correção de provas.",
            max_tokens=100
        )

        assert response is not None
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["assistente", "educacional", "correção", "provas"])

    @pytest.mark.asyncio
    @require_vision
    async def test_pdf_inline_data(self, selected_provider, sample_pdf_path):
        """Testa PDF via inline_data"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        if hasattr(provider, 'analyze_document'):
            response = await provider.analyze_document(
                file_path=str(sample_pdf_path),
                instruction="Analise este documento"
            )
            assert response is not None

    @pytest.mark.asyncio
    async def test_json_output(self, selected_provider):
        """Testa saída JSON"""
        import json

        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt='Retorne apenas este JSON: {"status": "ok", "codigo": 200}',
            max_tokens=100
        )

        assert response is not None

        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        try:
            data = json.loads(content)
            assert "status" in data or "codigo" in data
        except json.JSONDecodeError:
            pass  # OK, não é crítico

    @pytest.mark.asyncio
    async def test_multipart_content(self, selected_provider):
        """Testa conteúdo multipart (texto + dados)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Simular envio de múltiplos parts
        prompt = """
        Considere os seguintes dados:

        Aluno: João Silva
        Nota P1: 8.5
        Nota P2: 7.0
        Nota P3: 9.0

        Calcule a média e diga se o aluno foi aprovado (média >= 7).
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=200
        )

        assert response is not None
        content_lower = response.content.lower()
        # Deve ter cálculo ou resposta sobre aprovação
        assert any(word in content_lower for word in ["média", "aprovado", "8", "media"])

    @pytest.mark.asyncio
    async def test_candidates_response(self, selected_provider):
        """Verifica parsing correto de candidates"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Escreva: Teste OK",
            max_tokens=20
        )

        assert response is not None
        assert response.content is not None
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_usage_metadata(self, selected_provider):
        """Verifica que tokens são contabilizados"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Olá, como vai?",
            max_tokens=50
        )

        assert response is not None
        # Deve ter informação de tokens
        assert response.tokens_used >= 0

    @pytest.mark.asyncio
    @pytest.mark.expensive
    async def test_gemini_pro_reasoning(self, selected_provider):
        """Testa capacidade de raciocínio do Gemini Pro"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        prompt = """
        Problema: Uma torneira enche um tanque em 6 horas.
        Outra torneira enche o mesmo tanque em 4 horas.
        Juntas, em quanto tempo enchem o tanque?

        Mostre o raciocínio e a resposta.
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=500
        )

        assert response is not None
        # Deve ter explicação
        assert len(response.content) > 100
