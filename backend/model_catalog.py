"""
NOVO CR - Catálogo de Modelos de IA v1.0

Gerencia metadados completos de modelos de IA incluindo:
- Custos (input/output/cache por 1M tokens)
- Contexto (context window, max output)
- Capacidades (vision, tools, reasoning, etc.)
- Configurações de API (headers, autenticação)
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from enum import Enum
import json


# ============================================================
# MODELO DE DADOS
# ============================================================

@dataclass
class ModelMetadata:
    """Metadados completos de um modelo de IA"""
    id: str                           # "gpt-4o"
    provider: str                     # "openai"
    display_name: str                 # "GPT-4o"
    description: str = ""             # Descrição curta

    # Custos (por 1M tokens, USD)
    input_cost: float = 0.0           # $2.50
    output_cost: float = 0.0          # $10.00
    cached_input_cost: Optional[float] = None

    # Contexto
    context_window: int = 0           # 128000
    max_output: int = 0               # 16384

    # Capacidades principais
    supports_vision: bool = False
    supports_tools: bool = False      # Function calling
    supports_json_mode: bool = False
    supports_streaming: bool = True

    # Recursos especiais
    supports_reasoning: bool = False       # o1/o3, DeepSeek-R1
    supports_extended_thinking: bool = False  # Claude
    supports_search: bool = False          # Perplexity
    supports_code_exec: bool = False       # Gemini
    supports_rag: bool = False             # Cohere

    # Parâmetros especiais
    special_params: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"reasoning_effort": ["low","medium","high"]}

    requires_temperature: bool = True  # False para modelos reasoning

    # Datas
    release_date: Optional[str] = None
    deprecation_date: Optional[str] = None
    is_preview: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "display_name": self.display_name,
            "description": self.description,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "cached_input_cost": self.cached_input_cost,
            "context_window": self.context_window,
            "max_output": self.max_output,
            "supports_vision": self.supports_vision,
            "supports_tools": self.supports_tools,
            "supports_json_mode": self.supports_json_mode,
            "supports_streaming": self.supports_streaming,
            "supports_reasoning": self.supports_reasoning,
            "supports_extended_thinking": self.supports_extended_thinking,
            "supports_search": self.supports_search,
            "supports_code_exec": self.supports_code_exec,
            "supports_rag": self.supports_rag,
            "special_params": self.special_params,
            "requires_temperature": self.requires_temperature,
            "release_date": self.release_date,
            "deprecation_date": self.deprecation_date,
            "is_preview": self.is_preview
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], provider: str) -> 'ModelMetadata':
        return cls(
            id=data.get("id", ""),
            provider=provider,
            display_name=data.get("display_name", data.get("id", "")),
            description=data.get("description", ""),
            input_cost=data.get("input_cost", 0.0),
            output_cost=data.get("output_cost", 0.0),
            cached_input_cost=data.get("cached_input_cost"),
            context_window=data.get("context_window", 0),
            max_output=data.get("max_output", 0),
            supports_vision=data.get("supports_vision", False),
            supports_tools=data.get("supports_tools", False),
            supports_json_mode=data.get("supports_json_mode", False),
            supports_streaming=data.get("supports_streaming", True),
            supports_reasoning=data.get("supports_reasoning", False),
            supports_extended_thinking=data.get("supports_extended_thinking", False),
            supports_search=data.get("supports_search", False),
            supports_code_exec=data.get("supports_code_exec", False),
            supports_rag=data.get("supports_rag", False),
            special_params=data.get("special_params", {}),
            requires_temperature=data.get("requires_temperature", True),
            release_date=data.get("release_date"),
            deprecation_date=data.get("deprecation_date"),
            is_preview=data.get("is_preview", False)
        )


@dataclass
class ProviderInfo:
    """Informações de configuração de um provedor"""
    key: str                          # "openai"
    name: str                         # "OpenAI"
    base_url: str                     # "https://api.openai.com/v1"
    auth_header: str = "Authorization"  # Header de autenticação
    auth_prefix: str = "Bearer"       # Prefixo (vazio para Anthropic)
    extra_headers: Dict[str, str] = field(default_factory=dict)
    is_local: bool = False            # True para Ollama, vLLM, LM Studio
    models: List[ModelMetadata] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "base_url": self.base_url,
            "auth_header": self.auth_header,
            "auth_prefix": self.auth_prefix,
            "extra_headers": self.extra_headers,
            "is_local": self.is_local,
            "models": [m.to_dict() for m in self.models]
        }


# ============================================================
# GERENCIADOR DE CATÁLOGO
# ============================================================

class ModelCatalogManager:
    """Gerencia o catálogo de modelos de IA"""

    def __init__(self, catalog_path: str = "./data/model_catalog.json"):
        self.catalog_path = Path(catalog_path)
        self.providers: Dict[str, ProviderInfo] = {}
        self.version: str = ""
        self.last_updated: str = ""
        self._load()

    def _load(self):
        """Carrega o catálogo do arquivo JSON"""
        if not self.catalog_path.exists():
            return

        try:
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.version = data.get("version", "")
            self.last_updated = data.get("last_updated", "")

            for key, prov_data in data.get("providers", {}).items():
                models = [
                    ModelMetadata.from_dict(m, key)
                    for m in prov_data.get("models", [])
                ]

                self.providers[key] = ProviderInfo(
                    key=key,
                    name=prov_data.get("name", key.title()),
                    base_url=prov_data.get("base_url", ""),
                    auth_header=prov_data.get("auth_header", "Authorization"),
                    auth_prefix=prov_data.get("auth_prefix", "Bearer"),
                    extra_headers=prov_data.get("extra_headers", {}),
                    is_local=prov_data.get("is_local", False),
                    models=models
                )
        except Exception as e:
            print(f"Erro ao carregar catálogo: {e}")

    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Retorna todos os provedores com resumo"""
        return [
            {
                "key": p.key,
                "name": p.name,
                "is_local": p.is_local,
                "model_count": len(p.models),
                "base_url": p.base_url
            }
            for p in self.providers.values()
        ]

    def get_provider(self, provider_key: str) -> Optional[ProviderInfo]:
        """Retorna informações completas de um provedor"""
        return self.providers.get(provider_key)

    def get_provider_models(self, provider_key: str) -> List[ModelMetadata]:
        """Retorna todos os modelos de um provedor"""
        provider = self.providers.get(provider_key)
        return provider.models if provider else []

    def get_model_info(self, provider_key: str, model_id: str) -> Optional[ModelMetadata]:
        """Retorna informações detalhadas de um modelo específico"""
        provider = self.providers.get(provider_key)
        if not provider:
            return None

        for model in provider.models:
            if model.id == model_id:
                return model
        return None

    def search_models(
        self,
        supports_vision: Optional[bool] = None,
        supports_tools: Optional[bool] = None,
        supports_reasoning: Optional[bool] = None,
        supports_search: Optional[bool] = None,
        max_input_cost: Optional[float] = None,
        min_context_window: Optional[int] = None,
        provider: Optional[str] = None,
        is_local: Optional[bool] = None
    ) -> List[ModelMetadata]:
        """Busca modelos por capacidades e critérios"""
        results = []

        for prov_key, prov in self.providers.items():
            # Filtro por provedor
            if provider and prov_key != provider:
                continue

            # Filtro por local
            if is_local is not None and prov.is_local != is_local:
                continue

            for model in prov.models:
                # Filtros de capacidade
                if supports_vision is not None and model.supports_vision != supports_vision:
                    continue
                if supports_tools is not None and model.supports_tools != supports_tools:
                    continue
                if supports_reasoning is not None and model.supports_reasoning != supports_reasoning:
                    continue
                if supports_search is not None and model.supports_search != supports_search:
                    continue

                # Filtros numéricos
                if max_input_cost is not None and model.input_cost > max_input_cost:
                    continue
                if min_context_window is not None and model.context_window < min_context_window:
                    continue

                results.append(model)

        return results

    def get_cost_comparison(self, model_refs: List[str]) -> List[Dict[str, Any]]:
        """
        Compara custos entre modelos.
        model_refs no formato "provider/model_id"
        """
        results = []

        for ref in model_refs:
            if "/" not in ref:
                continue

            provider, model_id = ref.split("/", 1)
            model = self.get_model_info(provider, model_id)

            if model:
                results.append({
                    "ref": ref,
                    "display_name": model.display_name,
                    "provider": provider,
                    "input_cost": model.input_cost,
                    "output_cost": model.output_cost,
                    "cached_input_cost": model.cached_input_cost,
                    "context_window": model.context_window
                })

        return results

    def calculate_cost(
        self,
        model_ref: str,
        input_tokens: int,
        output_tokens: int,
        requests_per_day: int = 1,
        use_cache: bool = False
    ) -> Dict[str, float]:
        """Calcula custo estimado para um modelo"""
        if "/" not in model_ref:
            return {"error": "Formato inválido. Use provider/model_id"}

        provider, model_id = model_ref.split("/", 1)
        model = self.get_model_info(provider, model_id)

        if not model:
            return {"error": "Modelo não encontrado"}

        # Custo por requisição
        input_cost = model.cached_input_cost if use_cache and model.cached_input_cost else model.input_cost
        cost_per_request = (
            (input_tokens * input_cost / 1_000_000) +
            (output_tokens * model.output_cost / 1_000_000)
        )

        daily_cost = cost_per_request * requests_per_day
        monthly_cost = daily_cost * 30

        return {
            "model": model.display_name,
            "cost_per_request": round(cost_per_request, 6),
            "daily_cost": round(daily_cost, 4),
            "monthly_cost": round(monthly_cost, 2),
            "input_cost_used": input_cost,
            "output_cost_used": model.output_cost
        }

    def get_full_catalog(self) -> Dict[str, Any]:
        """Retorna catálogo completo para o frontend"""
        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "providers": {
                key: prov.to_dict()
                for key, prov in self.providers.items()
            }
        }

    def get_catalog_summary(self) -> Dict[str, Any]:
        """Retorna resumo do catálogo"""
        total_models = sum(len(p.models) for p in self.providers.values())
        cloud_providers = [p for p in self.providers.values() if not p.is_local]
        local_providers = [p for p in self.providers.values() if p.is_local]

        return {
            "version": self.version,
            "last_updated": self.last_updated,
            "total_providers": len(self.providers),
            "cloud_providers": len(cloud_providers),
            "local_providers": len(local_providers),
            "total_models": total_models,
            "providers": self.get_all_providers()
        }


# ============================================================
# INSTÂNCIA GLOBAL
# ============================================================

model_catalog = ModelCatalogManager()


def get_model_catalog() -> ModelCatalogManager:
    """Retorna a instância global do catálogo"""
    return model_catalog
