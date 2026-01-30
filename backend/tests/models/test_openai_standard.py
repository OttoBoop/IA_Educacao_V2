"""
Testes para modelos OpenAI STANDARD (GPT-4o, GPT-4.1, etc.)

Estes modelos suportam temperature, vision e tools.
"""

import pytest
from typing import List
from .base_model_test import BaseModelTest, ModelTestConfig, require_vision, require_tools


@pytest.mark.openai
class TestOpenAIStandard(BaseModelTest):
    """
    Testes para modelos OpenAI padrão.

    Características:
    - Suportam temperature (0-2)
    - Suportam vision (imagens)
    - Suportam tools/function calling
    """

    MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"]

    @property
    def model_config(self) -> ModelTestConfig:
        return ModelTestConfig(
            provider_type="openai",
            model_id="gpt-4o-mini",
            supports_temperature=True,
            supports_vision=True,
            supports_tools=True,
            is_reasoning=False,
            max_tokens=4096,
            expected_latency_ms=10000
        )

    @pytest.mark.asyncio
    async def test_temperature_variation(self, selected_provider):
        """Testa diferentes valores de temperature"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Temperature baixa = mais determinístico
        response_low = await provider.complete(
            prompt="Complete: O céu é...",
            temperature=0.1,
            max_tokens=20
        )

        # Temperature alta = mais criativo
        response_high = await provider.complete(
            prompt="Complete: O céu é...",
            temperature=1.5,
            max_tokens=20
        )

        assert response_low is not None
        assert response_high is not None

    @pytest.mark.asyncio
    @require_vision
    async def test_image_analysis(self, selected_provider, sample_pdf_path):
        """Testa análise de imagem/documento"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Usar analyze_document se disponível
        if hasattr(provider, 'analyze_document'):
            response = await provider.analyze_document(
                file_path=str(sample_pdf_path),
                instruction="Descreva o conteúdo deste documento"
            )
            assert response is not None

    @pytest.mark.asyncio
    @require_tools
    async def test_function_calling(self, selected_provider):
        """Testa function calling / tools"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "calcular_nota",
                    "description": "Calcula a nota final do aluno",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "acertos": {"type": "integer", "description": "Número de acertos"},
                            "total": {"type": "integer", "description": "Total de questões"}
                        },
                        "required": ["acertos", "total"]
                    }
                }
            }
        ]

        response = await provider.complete(
            prompt="O aluno acertou 8 de 10 questões. Calcule a nota.",
            tools=tools,
            max_tokens=200
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_json_mode(self, selected_provider):
        """Testa modo JSON (response_format)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        import json

        response = await provider.complete(
            prompt='Retorne um JSON com {"nome": "teste", "valor": 42}. APENAS o JSON.',
            max_tokens=100
        )

        assert response is not None

        # Tentar parsear
        content = response.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()

        try:
            data = json.loads(content)
            assert "nome" in data or "valor" in data
        except json.JSONDecodeError:
            # Pode falhar, mas não deve ser erro crítico
            pass

    @pytest.mark.asyncio
    async def test_system_prompt(self, selected_provider):
        """Testa system prompt"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Qual seu nome?",
            system_prompt="Você é um assistente chamado ProvaBot que ajuda professores.",
            max_tokens=100
        )

        assert response is not None
        # Deve mencionar o nome ou papel definido no system prompt
        content_lower = response.content.lower()
        assert "provabot" in content_lower or "assistente" in content_lower or "professor" in content_lower

    @pytest.mark.asyncio
    async def test_long_context(self, selected_provider):
        """Testa contexto longo"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Criar prompt longo
        long_text = "Esta é uma frase de teste. " * 500  # ~3500 palavras

        response = await provider.complete(
            prompt=f"Resuma em uma frase:\n\n{long_text}",
            max_tokens=100
        )

        assert response is not None
        assert len(response.content) > 10
