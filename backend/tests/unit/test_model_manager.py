"""
PROVA AI - Testes de Unicidade de Modelo Padrao

Este arquivo testa que apenas UM modelo pode ser marcado como padrao (is_default).

Problema resolvido:
- Bug onde models.json tinha dois modelos com is_default: true
- Haiku (correto) e Llama (erro)

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
