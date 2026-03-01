"""
NOVO CR - Classe Base para Testes de Modelos

Fornece uma classe abstrata com testes comuns que cada
implementação de modelo deve passar.

Uso:
    class TestOpenAIStandard(BaseModelTest):
        MODELS = ["gpt-4o", "gpt-4o-mini"]

        @property
        def model_config(self):
            return ModelTestConfig(
                provider_type="openai",
                supports_temperature=True,
                ...
            )
"""

import pytest
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import asyncio


@dataclass
class ModelTestConfig:
    """Configuração para teste de modelo"""
    provider_type: str          # "openai", "anthropic", "google"
    model_id: str               # ID do modelo atual sendo testado
    supports_temperature: bool  # Se suporta parâmetro temperature
    supports_vision: bool       # Se suporta imagens
    supports_tools: bool        # Se suporta function calling
    is_reasoning: bool          # Se é modelo de raciocínio (o1, o3)
    max_tokens: int = 4096      # Limite de tokens
    expected_latency_ms: int = 30000  # Latência esperada (para alertas)


class BaseModelTest(ABC):
    """
    Classe base abstrata para testes de modelos de IA.

    Cada subclasse implementa testes específicos para
    características do modelo (reasoning, vision, etc.)

    Testes Comuns:
    - test_basic_completion: Modelo responde a prompt simples
    - test_json_output: Modelo retorna JSON válido
    - test_pipeline_extract: Etapa de extração
    - test_pipeline_corrigir: Etapa de correção
    """

    # Subclasses devem definir lista de modelos a testar
    MODELS: List[str] = []

    @property
    @abstractmethod
    def model_config(self) -> ModelTestConfig:
        """Retorna configuração do modelo sendo testado"""
        pass

    def get_provider(self):
        """
        Obtém instância do provider para o modelo atual.
        Usa API keys do api_key_manager com path absoluto.
        """
        from pathlib import Path
        from chat_service import ApiKeyManager, ProviderType
        from ai_providers import OpenAIProvider, AnthropicProvider, GeminiProvider

        # Path absoluto para api_keys.json
        backend_dir = Path(__file__).parent.parent.parent
        api_keys_path = backend_dir / "data" / "api_keys.json"

        if not api_keys_path.exists():
            return None

        key_manager = ApiKeyManager(config_path=str(api_keys_path))
        if not key_manager.keys:
            return None

        config = self.model_config
        provider_type = config.provider_type.lower()

        if provider_type == "openai":
            key_config = key_manager.get_por_empresa(ProviderType.OPENAI)
            if key_config:
                return OpenAIProvider(api_key=key_config.api_key, model=config.model_id)

        elif provider_type == "anthropic":
            key_config = key_manager.get_por_empresa(ProviderType.ANTHROPIC)
            if key_config:
                return AnthropicProvider(api_key=key_config.api_key, model=config.model_id)

        elif provider_type == "google":
            key_config = key_manager.get_por_empresa(ProviderType.GOOGLE)
            if key_config:
                return GeminiProvider(api_key=key_config.api_key, model=config.model_id)

        return None

    # ============================================================
    # TESTES BÁSICOS
    # ============================================================

    @pytest.mark.asyncio
    async def test_basic_completion(self, selected_provider):
        """Teste básico: modelo responde a prompt simples"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Responda apenas: Olá, mundo!",
            max_tokens=50
        )

        assert response is not None
        assert response.content is not None
        assert len(response.content) > 0
        assert response.tokens_used > 0

    @pytest.mark.asyncio
    async def test_json_output(self, selected_provider, mock_json_response):
        """Teste: modelo retorna JSON válido"""
        import json

        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        prompt = """
        Retorne um JSON válido com a seguinte estrutura:
        {"resultado": "sucesso", "valor": 42}

        IMPORTANTE: Retorne APENAS o JSON, sem texto adicional.
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=100
        )

        assert response is not None

        # Tentar extrair JSON
        content = response.content.strip()

        # Remover blocos de código se presentes
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(content.strip())
            assert "resultado" in data or "valor" in data
        except json.JSONDecodeError:
            pytest.fail(f"Resposta não é JSON válido: {content[:200]}")

    # ============================================================
    # TESTES DE PARÂMETROS
    # ============================================================

    @pytest.mark.asyncio
    async def test_temperature_support(self, selected_provider):
        """Teste: verifica suporte a temperature"""
        config = self.model_config

        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        if config.supports_temperature:
            # Deve funcionar com temperature
            response = await provider.complete(
                prompt="Diga olá",
                temperature=0.5,
                max_tokens=20
            )
            assert response is not None
        else:
            # Modelos reasoning não suportam temperature
            # Verificar que não causa erro
            response = await provider.complete(
                prompt="Diga olá",
                max_tokens=20
            )
            assert response is not None

    @pytest.mark.asyncio
    async def test_max_tokens_respected(self, selected_provider):
        """Teste: max_tokens é respeitado"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        response = await provider.complete(
            prompt="Escreva um texto muito longo sobre qualquer assunto",
            max_tokens=50  # Limite baixo
        )

        assert response is not None
        # Verificar que resposta não é excessivamente longa
        # (tokens != caracteres, mas é uma aproximação)
        assert len(response.content) < 1000

    # ============================================================
    # TESTES DE PIPELINE
    # ============================================================

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_extract_questoes(self, selected_provider, test_scenario):
        """Teste etapa: extrair questões do enunciado"""
        import json

        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        enunciado = test_scenario["enunciado"]

        prompt = f"""
        Analise o documento de prova abaixo e extraia as questões.

        Retorne um JSON com a estrutura:
        {{
            "questoes": [
                {{"numero": 1, "enunciado": "...", "pontuacao": 2.0}},
                ...
            ],
            "total_questoes": N
        }}

        Documento:
        {enunciado.content}
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=2000
        )

        assert response is not None

        # Tentar parsear JSON
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(content.strip())
            assert "questoes" in data
            assert len(data["questoes"]) > 0
        except json.JSONDecodeError:
            pytest.fail(f"Extração não retornou JSON válido")

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_pipeline_corrigir(self, selected_provider, test_scenario):
        """Teste etapa: corrigir prova do aluno"""
        import json

        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        gabarito = test_scenario["gabarito"]
        aluno = test_scenario["alunos"][0]
        prova_aluno = aluno["prova"]

        prompt = f"""
        Compare a prova do aluno com o gabarito e faça a correção.

        GABARITO:
        {gabarito.content}

        PROVA DO ALUNO:
        {prova_aluno.content}

        Retorne um JSON com:
        {{
            "questoes": [
                {{
                    "numero": 1,
                    "nota": X.X,
                    "nota_maxima": Y.Y,
                    "feedback": "..."
                }},
                ...
            ],
            "nota_total": X.X,
            "nota_maxima": Y.Y
        }}
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=2000
        )

        assert response is not None

        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(content.strip())
            assert "questoes" in data or "nota_total" in data
        except json.JSONDecodeError:
            pytest.fail(f"Correção não retornou JSON válido")

    # ============================================================
    # TESTES DE ERRO
    # ============================================================

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_empty_prompt_handling(self, selected_provider):
        """Teste: como modelo lida com prompt vazio"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        # Prompt muito curto
        response = await provider.complete(
            prompt="",
            max_tokens=50
        )

        # Deve retornar algo (mesmo que seja erro ou resposta padrão)
        assert response is not None

    @pytest.mark.asyncio
    @pytest.mark.error_handling
    async def test_corrupted_input_handling(self, selected_provider, corrupted_document):
        """Teste: como modelo lida com entrada corrompida"""
        provider = self.get_provider()
        if not provider:
            pytest.skip("Provider não disponível")

        prompt = f"""
        Analise o seguinte documento e extraia informações:

        {corrupted_document.content}

        Retorne um JSON com as informações encontradas ou {{"erro": "descrição do problema"}}
        """

        response = await provider.complete(
            prompt=prompt,
            max_tokens=500
        )

        assert response is not None
        # Modelo deve retornar algo, mesmo que seja indicando erro


# ============================================================
# HELPERS PARA SUBCLASSES
# ============================================================

def skip_if_expensive(func):
    """Decorator para pular testes com modelos caros (async-aware)"""
    import functools
    import asyncio

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        config = self.model_config
        expensive_models = ["o3", "o1-pro", "gpt-5", "claude-opus-4-5", "gemini-3-ultra"]

        if any(m in config.model_id for m in expensive_models):
            if kwargs.get("skip_expensive", False):
                pytest.skip(f"Modelo caro: {config.model_id}")

        return await func(self, *args, **kwargs)

    return wrapper


def require_vision(func):
    """Decorator para testes que requerem vision (async-aware)"""
    import functools

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        config = self.model_config
        if not config.supports_vision:
            pytest.skip(f"Modelo não suporta vision: {config.model_id}")
        return await func(self, *args, **kwargs)

    return wrapper


def require_tools(func):
    """Decorator para testes que requerem function calling (async-aware)"""
    import functools

    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        config = self.model_config
        if not config.supports_tools:
            pytest.skip(f"Modelo não suporta tools: {config.model_id}")
        return await func(self, *args, **kwargs)

    return wrapper
