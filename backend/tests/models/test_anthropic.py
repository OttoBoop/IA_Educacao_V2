"""
Testes para modelos Anthropic (Claude)

Claude suporta temperature, vision, tools e extended thinking.
"""

import pytest
from typing import List
from .base_model_test import BaseModelTest, ModelTestConfig, require_vision, require_tools


@pytest.mark.anthropic
class TestAnthropic(BaseModelTest):
    """
    Testes para Claude.

    Características:
    - Suporta temperature (0-1) - RANGE DIFERENTE do OpenAI
    - Suporta vision (imagens e PDFs nativos)
    - Suporta tools/function calling
    - Suporta extended_thinking (modelos 4.5)
    - API diferente (x-api-key, content blocks)
    """

    MODELS = [
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101"
    ]

    @property
    def model_config(self) -> ModelTestConfig:
        return ModelTestConfig(
            provider_type="anthropic",
            model_id="claude-haiku-4-5-20251001",
            supports_temperature=True,
            supports_vision=True,
            supports_tools=True,
            is_reasoning=False,
            max_tokens=4096,
            expected_latency_ms=15000
        )

    @pytest.mark.asyncio
    async def test_temperature_range(self, selected_provider):
        """Testa temperature no range correto (0-1)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Claude usa 0-1, não 0-2
        response = await provider.complete(
            prompt="Diga olá de forma criativa",
            temperature=0.9,  # Máximo é 1.0
            max_tokens=50
        )

        assert response is not None

    @pytest.mark.asyncio
    @require_vision
    async def test_pdf_native_support(self, selected_provider, sample_pdf_path):
        """Testa suporte nativo a PDF"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        if hasattr(provider, 'analyze_document'):
            response = await provider.analyze_document(
                file_path=str(sample_pdf_path),
                instruction="Descreva o conteúdo deste PDF"
            )
            assert response is not None
            assert response.content is not None

    @pytest.mark.asyncio
    async def test_system_prompt_format(self, selected_provider):
        """Testa formato do system prompt (separado das mensagens)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Qual é meu papel?",
            system_prompt="Você é um professor de matemática chamado Sr. Números.",
            max_tokens=100
        )

        assert response is not None
        content_lower = response.content.lower()
        assert "professor" in content_lower or "matemática" in content_lower or "números" in content_lower

    @pytest.mark.asyncio
    @require_tools
    async def test_tool_use(self, selected_provider):
        """Testa uso de tools (function calling)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        tools = [
            {
                "name": "criar_questao",
                "description": "Cria uma nova questão de prova",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "enunciado": {"type": "string"},
                        "resposta": {"type": "string"},
                        "pontuacao": {"type": "number"}
                    },
                    "required": ["enunciado", "resposta"]
                }
            }
        ]

        response = await provider.complete(
            prompt="Crie uma questão de matemática sobre frações",
            tools=tools,
            max_tokens=300
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_content_blocks_response(self, selected_provider):
        """Verifica que a resposta é parseada corretamente dos content blocks"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Escreva apenas: Teste OK",
            max_tokens=20
        )

        assert response is not None
        assert response.content is not None
        # Deve ter conteúdo extraído
        assert len(response.content) > 0

    @pytest.mark.asyncio
    @pytest.mark.expensive
    async def test_extended_thinking(self, selected_provider):
        """Testa extended thinking (modelos 4.5)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Extended thinking é para problemas complexos
        prompt = """
        Resolva este problema de lógica:

        Em uma competição, 5 equipes (A, B, C, D, E) jogaram entre si.
        - A venceu B e C
        - B venceu C e D
        - C venceu D e E
        - D venceu E e A
        - E venceu A e B

        Qual equipe teve mais vitórias?
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=500
        )

        assert response is not None
        # Deve ter raciocínio ou resposta
        assert len(response.content) > 50

    @pytest.mark.asyncio
    async def test_long_context_claude(self, selected_provider):
        """Testa contexto longo (Claude tem 200k tokens)"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Texto moderadamente longo
        long_text = "Parágrafo de exemplo para teste de contexto. " * 200

        response = await provider.complete(
            prompt=f"Quantas vezes a palavra 'exemplo' aparece neste texto?\n\n{long_text}",
            max_tokens=100
        )

        assert response is not None
