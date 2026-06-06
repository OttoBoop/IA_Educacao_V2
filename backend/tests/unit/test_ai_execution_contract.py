import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def test_resolve_ai_model_usa_model_manager(monkeypatch):
    import ai_execution
    import chat_service

    model = SimpleNamespace(id="modelo-1", tipo=SimpleNamespace(value="openai"), get_model_id=lambda: "gpt-x")

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model if model_id == "modelo-1" else None)
    monkeypatch.setattr(
        chat_service,
        "resolve_provider_config",
        lambda model_id=None: {
            "tipo": "openai",
            "api_key": "key",
            "modelo": "gpt-x",
            "base_url": None,
        },
    )

    resolution = ai_execution.resolve_ai_model("modelo-1")

    assert resolution.requested_model_id == "modelo-1"
    assert resolution.resolved_model_id == "modelo-1"
    assert resolution.provider_type == "openai"
    assert resolution.source == "model_manager"
    assert resolution.warnings == []


def test_resolve_ai_model_provider_id_legado_fica_marcado(monkeypatch):
    import ai_execution
    import chat_service
    import ai_providers

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: None)
    monkeypatch.setattr(
        ai_providers.ai_registry,
        "get",
        lambda provider_id: SimpleNamespace(
            name="AnthropicProvider",
            model="claude-test",
            api_key="key",
        ),
    )

    resolution = ai_execution.resolve_ai_model(provider_id="claude-legado")

    assert resolution.legacy_provider_id == "claude-legado"
    assert resolution.resolved_model_id == "claude-legado"
    assert resolution.provider_type == "anthropic"
    assert resolution.source == "ai_registry"
    assert "provider_id legado usado; prefira model_id" in resolution.warnings
    assert "resolvido via ai_registry legado" in resolution.warnings


def test_resolve_ai_model_provider_id_legado_no_model_manager_nao_vira_model_id(monkeypatch):
    import ai_execution
    import chat_service

    model = SimpleNamespace(
        id="modelo-legado",
        tipo=SimpleNamespace(value="openai"),
        get_model_id=lambda: "gpt-x",
        suporta_vision=True,
        suporta_function_calling=True,
    )

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: model if model_id == "modelo-legado" else None)
    monkeypatch.setattr(
        chat_service,
        "resolve_provider_config",
        lambda model_id=None: {
            "tipo": "openai",
            "api_key": "key",
            "modelo": "gpt-x",
            "base_url": None,
        },
    )

    resolution = ai_execution.resolve_ai_model(provider_id="modelo-legado")

    assert resolution.requested_model_id is None
    assert resolution.legacy_provider_id == "modelo-legado"
    assert resolution.resolved_model_id == "modelo-legado"
    assert "provider_id legado usado; prefira model_id" in resolution.warnings


def test_resolve_ai_model_inexistente_nao_usa_default(monkeypatch):
    import ai_execution
    import chat_service
    import ai_providers

    monkeypatch.setattr(chat_service.model_manager, "get", lambda model_id: None)

    def missing(provider_id):
        raise ValueError("missing")

    monkeypatch.setattr(ai_providers.ai_registry, "get", missing)

    with pytest.raises(ValueError, match="Nenhum fallback foi usado"):
        ai_execution.resolve_ai_model("modelo-inexistente")


def test_validate_capability_bloqueia_provider_sem_adapter():
    import ai_execution

    resolution = ai_execution.AIModelResolution(
        requested_model_id="custom-1",
        legacy_provider_id=None,
        resolved_model_id="custom-1",
        provider_type="custom",
        model_name="custom-model",
        api_key="key",
    )

    with pytest.raises(ValueError, match="nao suporta leitura direta de documento"):
        ai_execution.validate_capability(
            resolution,
            ai_execution.CAPABILITY_DOCUMENT_READ,
        )


def test_validate_capability_bloqueia_tool_use_sem_flag_do_model_manager():
    import ai_execution

    resolution = ai_execution.AIModelResolution(
        requested_model_id="modelo-sem-tools",
        legacy_provider_id=None,
        resolved_model_id="modelo-sem-tools",
        provider_type="openai",
        model_name="gpt-x",
        api_key="key",
        config={"suporta_function_calling": False},
    )

    with pytest.raises(ValueError, match="nao declara suporte a tool-use"):
        ai_execution.validate_capability(
            resolution,
            ai_execution.CAPABILITY_TOOL_USE,
        )
