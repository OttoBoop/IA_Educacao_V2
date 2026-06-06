"""Contrato comum de execucao de IA para pipelines e documentos.

Este modulo mantem `model_id` como referencia publica canonica. `provider_id`
continua aceito como alias legado, mas a resolucao sempre registra essa origem
para evitar troca silenciosa de modelo.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


CAPABILITY_DOCUMENT_READ = "document_read"
CAPABILITY_TOOL_USE = "tool_use"
CAPABILITY_MULTIMODAL = "multimodal"


@dataclass
class AIModelResolution:
    requested_model_id: Optional[str]
    legacy_provider_id: Optional[str]
    resolved_model_id: Optional[str]
    provider_type: str
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    source: str = "model_manager"
    warnings: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)

    @property
    def provider_ref(self) -> Optional[str]:
        return self.requested_model_id or self.legacy_provider_id or self.resolved_model_id

    def metadata(self) -> Dict[str, Any]:
        data = {
            "requested_model_id": self.requested_model_id,
            "legacy_provider_id": self.legacy_provider_id,
            "resolved_model_id": self.resolved_model_id,
            "resolved_provider": self.provider_type,
            "resolved_model": self.model_name,
            "provider_resolution_source": self.source,
        }
        if self.warnings:
            data["provider_warnings"] = list(self.warnings)
        return data


def _provider_type_from_legacy(provider) -> str:
    name = (getattr(provider, "name", "") or "").lower()
    model = (getattr(provider, "model", "") or "").lower()
    if "anthropic" in name or "claude" in model:
        return "anthropic"
    if "gemini" in name or "google" in name or "gemini" in model:
        return "google"
    if "local" in name or "ollama" in model:
        return "ollama"
    return "openai"


def resolve_ai_model(
    model_id: Optional[str] = None,
    provider_id: Optional[str] = None,
    required_capability: Optional[str] = None,
    allow_default: bool = True,
) -> AIModelResolution:
    """Resolve modelo sem fallback silencioso.

    Ordem:
    1. `model_id` explicito no model_manager;
    2. `provider_id` legado tratado como model_id, se existir no model_manager;
    3. `provider_id` legado no ai_registry;
    4. default do model_manager apenas quando nenhum id explicito foi informado.
    """
    from chat_service import model_manager, resolve_provider_config
    from ai_providers import ai_registry

    requested_model_id = model_id or None
    legacy_provider_id = provider_id or None
    lookup_id = requested_model_id or legacy_provider_id
    warnings: List[str] = []

    if legacy_provider_id and not requested_model_id:
        warnings.append("provider_id legado usado; prefira model_id")

    source = "model_manager"
    resolved_model_id: Optional[str] = lookup_id

    if lookup_id:
        model = model_manager.get(lookup_id)
        if model:
            config = resolve_provider_config(lookup_id)
            config["suporta_vision"] = getattr(model, "suporta_vision", None)
            config["suporta_function_calling"] = getattr(model, "suporta_function_calling", None)
            resolved_model_id = model.id
            provider_type = str(config.get("tipo") or model.tipo.value).lower()
            resolution = AIModelResolution(
                requested_model_id=requested_model_id,
                legacy_provider_id=legacy_provider_id,
                resolved_model_id=resolved_model_id,
                provider_type=provider_type,
                model_name=config.get("modelo") or model.get_model_id(),
                api_key=config.get("api_key") or "",
                base_url=config.get("base_url"),
                source=source,
                warnings=warnings,
                config=config,
            )
            validate_capability(resolution, required_capability)
            return resolution

        try:
            provider = ai_registry.get(lookup_id)
        except Exception as exc:
            raise ValueError(
                f"Modelo '{lookup_id}' nao encontrado. Nenhum fallback foi usado."
            ) from exc

        provider_type = _provider_type_from_legacy(provider)
        warnings.append("resolvido via ai_registry legado")
        resolution = AIModelResolution(
            requested_model_id=requested_model_id,
            legacy_provider_id=legacy_provider_id or lookup_id,
            resolved_model_id=lookup_id,
            provider_type=provider_type,
            model_name=getattr(provider, "model", "") or lookup_id,
            api_key=getattr(provider, "api_key", "") or "",
            base_url=getattr(provider, "base_url", None),
            source="ai_registry",
            warnings=warnings,
            config={
                "tipo": provider_type,
                "modelo": getattr(provider, "model", "") or lookup_id,
                "api_key": getattr(provider, "api_key", "") or "",
                "base_url": getattr(provider, "base_url", None),
            },
        )
        validate_capability(resolution, required_capability)
        return resolution

    if not allow_default:
        raise ValueError("model_id obrigatorio; default desabilitado para esta operacao")

    config = resolve_provider_config(None)
    default_model = model_manager.get_default()
    resolved_model_id = default_model.id if default_model else None
    resolution = AIModelResolution(
        requested_model_id=None,
        legacy_provider_id=None,
        resolved_model_id=resolved_model_id,
        provider_type=str(config.get("tipo") or "").lower(),
        model_name=config.get("modelo") or "",
        api_key=config.get("api_key") or "",
        base_url=config.get("base_url"),
        source="model_manager_default" if default_model else "ai_registry_default",
        warnings=[],
        config=config,
    )
    validate_capability(resolution, required_capability)
    return resolution


def validate_capability(resolution: AIModelResolution, capability: Optional[str]) -> None:
    if not capability:
        return

    provider_type = (resolution.provider_type or "").lower()

    if capability == CAPABILITY_DOCUMENT_READ:
        if provider_type not in {"openai", "anthropic", "google", "gemini", "ollama"}:
            raise ValueError(
                f"Modelo '{resolution.provider_ref}' nao suporta leitura direta de documento "
                f"neste backend (provider={provider_type})."
            )
        return

    if capability == CAPABILITY_TOOL_USE:
        if provider_type not in {"openai", "anthropic", "google", "gemini"}:
            raise ValueError(
                f"Modelo '{resolution.provider_ref}' nao suporta tool-use neste backend "
                f"(provider={provider_type})."
            )
        if resolution.config.get("suporta_function_calling") is False:
            raise ValueError(
                f"Modelo '{resolution.provider_ref}' nao declara suporte a tool-use."
            )
        return

    if capability == CAPABILITY_MULTIMODAL:
        if provider_type not in {"openai", "anthropic", "google", "gemini", "ollama"}:
            raise ValueError(
                f"Modelo '{resolution.provider_ref}' nao suporta multimodal neste backend "
                f"(provider={provider_type})."
            )
        if resolution.config.get("suporta_vision") is False:
            raise ValueError(
                f"Modelo '{resolution.provider_ref}' nao declara suporte multimodal/vision."
            )
        return

    raise ValueError(f"Capability desconhecida: {capability}")


def create_document_provider(resolution: AIModelResolution):
    """Cria adapter AIProvider para operacoes `analyze_document`."""
    from ai_providers import AnthropicProvider, GeminiProvider, LocalLLMProvider, OpenAIProvider

    provider_type = (resolution.provider_type or "").lower()
    model = resolution.model_name
    api_key = resolution.api_key or ""

    if provider_type == "openai":
        provider = OpenAIProvider(api_key=api_key, model=model)
        if resolution.base_url:
            provider.base_url = resolution.base_url.rstrip("/")
        return provider
    if provider_type == "anthropic":
        return AnthropicProvider(api_key=api_key, model=model)
    if provider_type in {"google", "gemini"}:
        return GeminiProvider(api_key=api_key, model=model)
    if provider_type == "ollama":
        return LocalLLMProvider(base_url=resolution.base_url or "http://localhost:11434", model=model or "llama3")

    raise ValueError(
        f"Provider '{provider_type}' nao possui adapter de leitura de documento"
    )


def parse_json_map(raw: Optional[str], field_name: str) -> Dict[str, str]:
    """Parse de mapas JSON usados em Forms; retorna dict string->string."""
    if not raw:
        return {}
    import json

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Formato invalido para {field_name}. Use JSON.") from exc

    if isinstance(parsed, list):
        return {str(item): str(item) for item in parsed if item}
    if not isinstance(parsed, dict):
        raise ValueError(f"{field_name} deve ser objeto JSON ou lista JSON.")
    return {str(k): str(v) for k, v in parsed.items() if v}


def parse_json_list(raw: Optional[str], field_name: str) -> List[str]:
    """Aceita lista JSON, string simples ou CSV pequeno."""
    if not raw:
        return []
    import json

    text = raw.strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Formato invalido para {field_name}. Use JSON array.") from exc
        if not isinstance(parsed, list):
            raise ValueError(f"{field_name} deve ser JSON array.")
        return [str(item) for item in parsed if item]
    if "," in text:
        return [part.strip() for part in text.split(",") if part.strip()]
    return [text]
