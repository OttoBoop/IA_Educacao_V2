"""
NOVO CR - Testes de Unicidade de Modelo Padrao

Este arquivo testa que apenas UM modelo pode ser marcado como padrao (is_default).

===============================================================================
BUG DOCUMENTADO: Multiplos Modelos Padrao (2026-01-30)
===============================================================================

PROBLEMA DETECTADO:
    O arquivo models.json tinha DOIS modelos com is_default: true:
    - Linha 119: Claude Haiku 4.5 (is_default: true) - CORRETO
    - Linha 259: Llama 3.2 Local (is_default: true) - ERRO!

CAUSA RAIZ:
    O metodo ModelManager._load() carregava modelos do JSON sem validar
    a unicidade do campo is_default. Isso permitia que dados corrompidos
    (manualmente editados ou de migracoes antigas) persistissem.

    NAO foi causado por:
    - Sistemas legados ou endpoints duplicados
    - Multiplos endpoints para definir modelo padrao
    (Ha apenas um endpoint: POST /api/settings/models/{model_id}/default)

IMPACTO:
    - API /api/settings/models retornava dois modelos como default
    - get_default() retornava resultado imprevisivel (primeiro encontrado)
    - Comportamento nao-deterministico quando nenhum model_id era especificado

SOLUCAO IMPLEMENTADA:
    1. Adicionado metodo _ensure_single_default() em chat_service.py
    2. Chamado automaticamente no final de _load()
    3. Auto-corrige dados corrompidos, preferindo Haiku como default
    4. Persiste a correcao no arquivo JSON

VERIFICACAO:
    - Testes locais: pytest tests/unit/test_model_manager.py -v
    - Testes online: curl https://ia-educacao-v2.onrender.com/api/settings/models
      Deve retornar apenas UM modelo com is_default: true

===============================================================================

Uso:
    cd IA_Educacao_V2/backend
    pytest tests/unit/test_model_manager.py -v
"""

import os
import sys
import json
import pytest
import tempfile
from pathlib import Path

# Adicionar diretorio pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def model_manager_instance():
    """Cria instancia isolada do ModelManager com temp file"""
    from chat_service import ModelManager

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "models.json")
        manager = ModelManager(config_path=config_path)
        yield manager


@pytest.fixture
def model_manager_with_multiple_defaults():
    """Cria ModelManager com dados corrompidos (multiplos defaults)"""
    from chat_service import ModelManager

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "models.json")

        # Criar arquivo com BUG: dois modelos is_default: true
        corrupted_data = {
            "models": [
                {
                    "id": "haiku-123",
                    "nome": "Claude Haiku 4.5",
                    "tipo": "anthropic",
                    "modelo": "claude-haiku-4-5-20251001",
                    "ativo": True,
                    "is_default": True  # CORRETO
                },
                {
                    "id": "gpt-456",
                    "nome": "GPT-5 Mini",
                    "tipo": "openai",
                    "modelo": "gpt-5-mini",
                    "ativo": True,
                    "is_default": False
                },
                {
                    "id": "llama-789",
                    "nome": "Llama 3.2 (Local)",
                    "tipo": "ollama",
                    "modelo": "llama3.2:latest",
                    "ativo": True,
                    "is_default": True  # BUG! Segundo default
                }
            ]
        }

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(corrupted_data, f)

        # Carregar manager - deve corrigir automaticamente
        manager = ModelManager(config_path=config_path)
        yield manager


# ============================================================
# TESTES DE UNICIDADE
# ============================================================

class TestDefaultModelUniqueness:
    """Testes para garantir que apenas UM modelo e padrao"""

    def test_only_one_default_model_after_load(self, model_manager_with_multiple_defaults):
        """
        Garante que apenas UM modelo e padrao apos carregar dados corrompidos.

        Cenario: models.json tem dois modelos com is_default: true
        Esperado: _load() deve corrigir para apenas um
        """
        manager = model_manager_with_multiple_defaults

        # Contar quantos modelos sao default
        defaults = [m for m in manager.listar(apenas_ativos=False) if m.is_default]

        assert len(defaults) == 1, f"Deveria ter exatamente 1 modelo default, mas tem {len(defaults)}: {[m.nome for m in defaults]}"

    def test_haiku_preferred_as_default(self, model_manager_with_multiple_defaults):
        """
        Quando multiplos defaults existem, Haiku deve ser mantido.

        Regra de negocio: Haiku e o modelo preferido como default
        """
        manager = model_manager_with_multiple_defaults

        default = manager.get_default()

        assert default is not None, "Deve haver um modelo default"
        assert "haiku" in default.nome.lower(), f"Haiku deveria ser o default, mas e {default.nome}"

    def test_set_default_removes_previous_default(self, model_manager_instance):
        """
        Garante que set_default() remove o padrao anterior.

        Cenario: Mudar o modelo padrao via API
        Esperado: Apenas o novo modelo e default
        """
        from chat_service import ProviderType

        manager = model_manager_instance

        # Adicionar dois modelos
        model1 = manager.adicionar(
            nome="Modelo A",
            tipo=ProviderType.OPENAI,
            modelo="gpt-5-mini"
        )
        model2 = manager.adicionar(
            nome="Modelo B",
            tipo=ProviderType.ANTHROPIC,
            modelo="claude-haiku-4-5-20251001"
        )

        # Modelo1 deve ser default (primeiro adicionado)
        assert model1.is_default == True, "Primeiro modelo deveria ser default"

        # Mudar para modelo2
        result = manager.set_default(model2.id)
        assert result == True, "set_default deveria retornar True"

        # Verificar que apenas model2 e default agora
        defaults = [m for m in manager.listar(apenas_ativos=False) if m.is_default]
        assert len(defaults) == 1, f"Deveria ter 1 default, tem {len(defaults)}"
        assert defaults[0].id == model2.id, "Modelo B deveria ser o default"


class TestModelCapabilities:
    """Regressoes para cadastro de modelos por catalogo/settings."""

    @pytest.mark.parametrize(
        "model_id",
        [
            "gpt-5.5",
            "gpt-5.5-pro",
            "gpt-5.4",
            "gpt-5.4-mini",
            "gpt-5.4-nano",
            "gpt-5.4-pro",
            "gpt-5.2",
            "gpt-5.2-pro",
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5-pro",
        ],
    )
    def test_openai_reasoning_models_do_not_keep_temperature(self, model_manager_instance, model_id):
        """GPT-5 family models must be configured as reasoning models, not temperature models."""
        from chat_service import ProviderType

        model = model_manager_instance.adicionar(
            nome=model_id,
            tipo=ProviderType.OPENAI,
            modelo=model_id,
        )

        assert model.suporta_temperature is False
        assert model.temperature is None

    def test_adicionar_mescla_capabilities_sem_duplicar_kwargs(self, model_manager_instance):
        """Caller pode sobrescrever capabilities sugeridas sem TypeError."""
        from chat_service import ProviderType

        model = model_manager_instance.adicionar(
            nome="GPT-5.4 Mini OCR candidato",
            tipo=ProviderType.OPENAI,
            modelo="gpt-5.4-mini",
            max_tokens=16384,
            temperature=None,
            parametros={"reasoning_effort": "low"},
            suporta_vision=True,
            suporta_function_calling=True,
            suporta_streaming=True,
            suporta_temperature=False,
        )

        assert model.modelo == "gpt-5.4-mini"
        assert model.suporta_vision is True
        assert model.suporta_function_calling is True
        assert model.suporta_streaming is True
        assert model.suporta_temperature is False
        assert model.temperature is None

    def test_adicionar_usa_tools_do_modelo_sugerido_quando_existir(self, model_manager_instance):
        """Modelos sugeridos novos carregam tools/vision sem exigir PUT corretivo."""
        from chat_service import ProviderType

        model = model_manager_instance.adicionar(
            nome="GPT-5.4 Mini",
            tipo=ProviderType.OPENAI,
            modelo="gpt-5.4-mini",
        )

        assert model.suporta_vision is True
        assert model.suporta_function_calling is True


@pytest.mark.asyncio
async def test_criar_modelo_preserva_capabilities_no_create(monkeypatch):
    """POST /api/settings/models deve respeitar flags de capability no create."""
    import routes_chat

    captured = {}

    class FakeModel:
        def to_dict(self):
            return {"id": "fake-model", **captured}

    class FakeManager:
        def adicionar(self, **kwargs):
            captured.update(kwargs)
            return FakeModel()

    monkeypatch.setattr(routes_chat, "model_manager", FakeManager())

    data = routes_chat.ModelCreate(
        nome="GPT-5.4 Mini OCR candidato",
        tipo="openai",
        modelo="gpt-5.4-mini",
        max_tokens=16384,
        temperature=None,
        parametros={"reasoning_effort": "low"},
        suporta_vision=True,
        suporta_function_calling=True,
        suporta_streaming=True,
        suporta_temperature=False,
    )

    response = await routes_chat.criar_modelo(data)

    assert response["success"] is True
    assert captured["suporta_vision"] is True
    assert captured["suporta_function_calling"] is True
    assert captured["suporta_streaming"] is True
    assert captured["suporta_temperature"] is False


@pytest.mark.asyncio
async def test_criar_modelo_do_catalogo_nao_duplica_capabilities(monkeypatch, model_manager_instance):
    """POST /api/settings/models/from-catalog deve criar modelo sugerido sem 500."""
    import routes_chat

    monkeypatch.setattr(routes_chat, "model_manager", model_manager_instance)

    data = routes_chat.ModelFromCatalogCreate(
        catalog_ref="openai/gpt-5.4-mini",
        nome="GPT-5.4 Mini OCR candidato",
        max_tokens=16384,
    )

    response = await routes_chat.criar_modelo_do_catalogo(data)
    model = response["model"]

    assert response["success"] is True
    assert model["modelo"] == "gpt-5.4-mini"
    assert model["catalog_ref"] == "openai/gpt-5.4-mini"
    assert model["suporta_vision"] is True
    assert model["suporta_function_calling"] is True
    assert model["suporta_temperature"] is False


@pytest.mark.parametrize(
    "model_id",
    ["gpt-5.5-pro", "gpt-5.4-pro", "gpt-5.2-pro", "gpt-5-pro"],
)
def test_openai_pro_reasoning_build_params_sem_temperature(model_id):
    """OpenAI pro reasoning models cannot receive temperature/max_tokens."""
    from chat_service import ChatClient, ModelConfig, ProviderType

    client = ChatClient(
        ModelConfig(
            id=f"test-{model_id}",
            nome=model_id,
            tipo=ProviderType.OPENAI,
            modelo=model_id,
            max_tokens=1234,
            temperature=0.7,
        ),
        api_key="test-key",
    )

    params = client._build_params()

    assert client._is_reasoning_model() is True
    assert params["model"] == model_id
    assert params["max_completion_tokens"] == 1234
    assert "max_tokens" not in params
    assert "temperature" not in params


@pytest.mark.parametrize(
    "model_id",
    ["gpt-5.5-pro", "gpt-5.4-pro", "gpt-5.2-pro", "gpt-5-pro"],
)
def test_legacy_openai_provider_reconhece_pro_reasoning(model_id):
    """O provider legado tambem precisa tratar variantes pro como reasoning."""
    from ai_providers import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key", model=model_id)

    assert provider._is_reasoning_model() is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "catalog_ref",
    ["openai/gpt-5.5", "openai/gpt-5.2", "openai/gpt-5.2-pro", "openai/gpt-5-pro"],
)
async def test_criar_modelo_do_catalogo_openai_reasoning_sem_temperature(
    monkeypatch,
    model_manager_instance,
    catalog_ref,
):
    """Modelos GPT-5 do catalogo entram sem temperature, inclusive variantes pro."""
    import routes_chat

    monkeypatch.setattr(routes_chat, "model_manager", model_manager_instance)

    response = await routes_chat.criar_modelo_do_catalogo(
        routes_chat.ModelFromCatalogCreate(catalog_ref=catalog_ref)
    )
    model = response["model"]

    assert response["success"] is True
    assert model["catalog_ref"] == catalog_ref
    assert model["suporta_temperature"] is False
    assert model["temperature"] is None


@pytest.mark.parametrize(
    "model_id, expected_context, expected_max_output",
    [
        ("gpt-5.5", 1050000, 128000),
        ("gpt-5.5-pro", 1050000, 128000),
        ("gpt-5.4", 1050000, 128000),
        ("gpt-5.4-pro", 1050000, 128000),
        ("gpt-5.2", 400000, 128000),
        ("gpt-5.2-pro", 400000, 128000),
        ("gpt-5", 400000, 128000),
        ("gpt-5-mini", 400000, 128000),
        ("gpt-5-nano", 400000, 128000),
        ("gpt-5-pro", 400000, 272000),
    ],
)
def test_catalogo_openai_gpt5_contexto_e_saida_maxima_oficiais(
    model_id,
    expected_context,
    expected_max_output,
):
    """O catalogo nao pode ficar preso nos limites antigos de output/contexto."""
    from model_catalog import model_catalog

    metadata = model_catalog.get_model_info("openai", model_id)

    assert metadata is not None
    assert metadata.context_window == expected_context
    assert metadata.max_output == expected_max_output
    assert metadata.requires_temperature is False


@pytest.mark.parametrize(
    "model_id, expected_efforts",
    [
        ("gpt-5.4-pro", ["medium", "high", "xhigh"]),
        ("gpt-5.2-pro", ["medium", "high", "xhigh"]),
        ("gpt-5-pro", ["high"]),
    ],
)
def test_catalogo_openai_pro_reasoning_effort_restrito(model_id, expected_efforts):
    """Variantes pro nao devem anunciar niveis de reasoning que a doc oficial nao lista."""
    from model_catalog import model_catalog

    metadata = model_catalog.get_model_info("openai", model_id)

    assert metadata is not None
    assert metadata.special_params["reasoning_effort"] == expected_efforts


@pytest.mark.parametrize(
    "model_id, supports_json_mode, supports_streaming",
    [
        ("gpt-5.5-pro", True, False),
        ("gpt-5.4-pro", False, True),
        ("gpt-5.2-pro", False, True),
    ],
)
def test_catalogo_openai_pro_capabilities_oficiais(
    model_id,
    supports_json_mode,
    supports_streaming,
):
    """Capabilities de modelos pro precisam seguir a doc, nao herdar defaults."""
    from model_catalog import model_catalog

    metadata = model_catalog.get_model_info("openai", model_id)

    assert metadata is not None
    assert metadata.supports_json_mode is supports_json_mode
    assert metadata.supports_streaming is supports_streaming


def test_catalogo_nao_expoe_gpt5_image_slug_inexistente():
    """A lista oficial atual usa gpt-image-*, nao um slug textual gpt-5-image."""
    from model_catalog import model_catalog

    assert model_catalog.get_model_info("openai", "gpt-5-image") is None


# ============================================================
# TESTES DE MUDANCA DE PADRAO
# ============================================================

class TestDefaultModelChange:
    """Testes para mudanca de modelo padrao"""

    def test_can_change_default_model(self, model_manager_instance):
        """
        Verifica que conseguimos mudar o modelo padrao com sucesso.
        """
        from chat_service import ProviderType

        manager = model_manager_instance

        # Adicionar modelos
        manager.adicionar(nome="Modelo A", tipo=ProviderType.OPENAI, modelo="gpt-5-mini")
        model_b = manager.adicionar(nome="Modelo B", tipo=ProviderType.ANTHROPIC, modelo="claude-haiku-4-5-20251001")

        # Mudar para modelo B
        result = manager.set_default(model_b.id)
        assert result == True

        # Verificar que mudou
        new_default = manager.get_default()
        assert new_default.id == model_b.id

        # Verificar que so tem UM padrao
        defaults = [m for m in manager.listar(apenas_ativos=False) if m.is_default]
        assert len(defaults) == 1

    def test_set_default_nonexistent_model_fails(self, model_manager_instance):
        """
        Tentar definir modelo inexistente como padrao deve falhar.
        """
        manager = model_manager_instance

        result = manager.set_default("modelo-que-nao-existe")
        assert result == False


# ============================================================
# TESTES DE INICIALIZACAO
# ============================================================

class TestDefaultModelInitialization:
    """Testes de inicializacao do modelo padrao"""

    def test_first_model_becomes_default(self, model_manager_instance):
        """
        O primeiro modelo adicionado deve se tornar default automaticamente.
        """
        from chat_service import ProviderType

        manager = model_manager_instance

        # Manager vazio nao tem default
        assert manager.get_default() is None

        # Adicionar primeiro modelo
        model = manager.adicionar(
            nome="Primeiro Modelo",
            tipo=ProviderType.OPENAI,
            modelo="gpt-5-mini"
        )

        # Deve ser default
        assert model.is_default == True
        assert manager.get_default().id == model.id

    def test_second_model_not_default(self, model_manager_instance):
        """
        O segundo modelo adicionado NAO deve ser default.
        """
        from chat_service import ProviderType

        manager = model_manager_instance

        # Adicionar dois modelos
        model1 = manager.adicionar(nome="Primeiro", tipo=ProviderType.OPENAI, modelo="gpt-5-mini")
        model2 = manager.adicionar(nome="Segundo", tipo=ProviderType.ANTHROPIC, modelo="claude-haiku-4-5-20251001")

        # Apenas o primeiro deve ser default
        assert model1.is_default == True
        assert model2.is_default == False

    def test_no_default_without_models(self, model_manager_instance):
        """
        Sem modelos, get_default() retorna None.
        """
        manager = model_manager_instance

        assert manager.get_default() is None


# ============================================================
# TESTES DE PERSISTENCIA
# ============================================================

class TestDefaultModelPersistence:
    """Testes de persistencia do modelo padrao"""

    def test_default_persists_after_reload(self):
        """
        O modelo padrao deve persistir apos recarregar do arquivo.
        """
        from chat_service import ModelManager, ProviderType

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "models.json")

            # Criar e configurar
            manager1 = ModelManager(config_path=config_path)
            model = manager1.adicionar(
                nome="Modelo Persistente",
                tipo=ProviderType.OPENAI,
                modelo="gpt-5-mini"
            )
            model_id = model.id

            # Recarregar
            manager2 = ModelManager(config_path=config_path)

            # Verificar que o default persistiu
            default = manager2.get_default()
            assert default is not None
            assert default.id == model_id

    def test_corrupted_data_fixed_on_reload(self):
        """
        Dados corrompidos devem ser corrigidos ao recarregar.
        """
        from chat_service import ModelManager

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "models.json")

            # Criar arquivo corrompido
            corrupted_data = {
                "models": [
                    {"id": "a", "nome": "Haiku", "tipo": "anthropic", "modelo": "claude-haiku-4-5-20251001", "ativo": True, "is_default": True},
                    {"id": "b", "nome": "Llama", "tipo": "ollama", "modelo": "llama3.2", "ativo": True, "is_default": True}  # BUG
                ]
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(corrupted_data, f)

            # Carregar - deve corrigir
            manager = ModelManager(config_path=config_path)

            # Verificar correcao
            defaults = [m for m in manager.listar(apenas_ativos=False) if m.is_default]
            assert len(defaults) == 1, f"Deveria ter 1 default apos correcao, tem {len(defaults)}"

            # Verificar que foi salvo corrigido
            with open(config_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)

            saved_defaults = [m for m in saved_data["models"] if m.get("is_default", False)]
            assert len(saved_defaults) == 1, "Arquivo deveria ter sido salvo com apenas 1 default"


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
