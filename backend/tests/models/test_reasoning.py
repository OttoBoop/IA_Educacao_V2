"""
Testes para modelos REASONING (o3, o4-mini, deepseek-reasoner, etc.)

Estes modelos NÃO suportam temperature e usam reasoning_effort.
"""

import pytest
from typing import List
from .base_model_test import BaseModelTest, ModelTestConfig


# Modelos reasoning conhecidos
REASONING_MODELS = ["o3", "o3-mini", "o3-pro", "o4-mini", "deepseek-reasoner"]


@pytest.mark.reasoning
class TestReasoningModels(BaseModelTest):
    """
    Testes para modelos de raciocínio.

    Características:
    - NÃO suportam temperature
    - Usam reasoning_effort (low/medium/high)
    - Usam max_completion_tokens ao invés de max_tokens
    """

    MODELS = REASONING_MODELS

    @property
    def model_config(self) -> ModelTestConfig:
        return ModelTestConfig(
            provider_type="openai",
            model_id="o3-mini",  # Default para testes
            supports_temperature=False,
            supports_vision=False,
            supports_tools=True,
            is_reasoning=True,
            max_tokens=8192,
            expected_latency_ms=60000  # Reasoning é mais lento
        )

    @pytest.mark.asyncio
    @pytest.mark.expensive
    async def test_reasoning_effort_low(self, selected_provider):
        """Testa reasoning_effort=low"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Modelo reasoning deve aceitar reasoning_effort
        response = await provider.complete(
            prompt="Quanto é 15 * 23?",
            max_tokens=100,
            reasoning_effort="low"
        )

        assert response is not None
        assert "345" in response.content or "trezentos" in response.content.lower()

    @pytest.mark.asyncio
    @pytest.mark.expensive
    async def test_reasoning_effort_high(self, selected_provider):
        """Testa reasoning_effort=high para problemas complexos"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        prompt = """
        Um trem parte da cidade A às 8h com velocidade de 60km/h.
        Outro trem parte da cidade B (300km de distância) às 9h com velocidade de 90km/h.
        A que horas os trens se encontram?
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=500,
            reasoning_effort="high"
        )

        assert response is not None
        assert len(response.content) > 50  # Deve ter explicação

    @pytest.mark.asyncio
    async def test_no_temperature_in_request(self, selected_provider):
        """Verifica que temperature NÃO causa erro em modelos reasoning"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Mesmo passando temperature, não deve causar erro
        # O provider deve ignorar ou remover o parâmetro
        try:
            response = await provider.complete(
                prompt="Diga olá",
                temperature=0.7,  # Será ignorado
                max_tokens=50
            )
            assert response is not None
        except Exception as e:
            # Se der erro, deve ser por outro motivo, não temperature
            if "temperature" in str(e).lower():
                pytest.fail("Erro relacionado a temperature não deveria ocorrer")
            raise

    @pytest.mark.asyncio
    async def test_max_completion_tokens(self, selected_provider):
        """Verifica uso de max_completion_tokens"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Escreva um poema curto sobre matemática",
            max_tokens=100  # Será convertido para max_completion_tokens
        )

        assert response is not None
        # Resposta não deve ser excessivamente longa
        assert len(response.content) < 2000

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complex_reasoning_task(self, selected_provider):
        """Testa tarefa que requer raciocínio complexo"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        prompt = """
        Analise este problema de lógica e resolva passo a passo:

        Três amigos (Ana, Bruno e Carla) têm profissões diferentes
        (médico, advogado, engenheiro).

        Dicas:
        1. Ana não é médica
        2. Bruno não é advogado
        3. O médico é amigo de Carla
        4. Ana é amiga do advogado

        Qual a profissão de cada um?

        Retorne um JSON: {"ana": "profissão", "bruno": "profissão", "carla": "profissão"}
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=1000,
            reasoning_effort="high"
        )

        assert response is not None
        # Deve conter as profissões mencionadas
        content_lower = response.content.lower()
        assert any(p in content_lower for p in ["médico", "advogado", "engenheiro", "medico"])
