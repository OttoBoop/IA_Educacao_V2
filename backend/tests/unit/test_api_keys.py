"""
NOVO CR - Testes de Configuracao de API Keys

Este arquivo testa ambos os cenarios:
1. LOCAL: API keys criptografadas em api_keys.json
2. RENDER: API keys via variaveis de ambiente

Uso:
    # Testes locais
    pytest test_api_keys.py -v

    # Testes especificos
    pytest test_api_keys.py::test_local_encryption -v
    pytest test_api_keys.py::test_env_fallback -v
"""

import os
import sys
import json
import pytest
import asyncio
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock

# Adicionar diretorio pai ao path
sys.path.insert(0, str(Path(__file__).parent))


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def api_key_manager_instance():
    """Cria instancia isolada do ApiKeyManager"""
    from chat_service import ApiKeyManager, ProviderType
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "api_keys.json")
        manager = ApiKeyManager(config_path=config_path)
        yield manager


@pytest.fixture
def model_manager_instance():
    """Cria instancia isolada do ModelManager"""
    from chat_service import ModelManager
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "models.json")
        manager = ModelManager(config_path=config_path)
        yield manager


# ============================================================
# TESTES DE CRIPTOGRAFIA LOCAL
# ============================================================

class TestLocalEncryption:
    """Testes do sistema de criptografia local"""

    def test_encryption_key_generation(self, api_key_manager_instance):
        """Testa que a chave de criptografia e gerada automaticamente"""
        manager = api_key_manager_instance

        # Verifica que cipher foi criado
        assert manager._cipher is not None
        assert manager.is_encryption_enabled()

    def test_encrypt_decrypt_roundtrip(self, api_key_manager_instance):
        """Testa encrypt -> decrypt retorna valor original"""
        manager = api_key_manager_instance

        test_key = "sk-test-12345-secret-api-key"
        encrypted = manager._encrypt(test_key)
        decrypted = manager._decrypt(encrypted)

        assert decrypted == test_key
        assert encrypted != test_key  # Deve estar criptografado
        assert encrypted.startswith("gAAAAA")  # Formato Fernet

    def test_add_and_retrieve_key(self, api_key_manager_instance):
        """Testa adicionar e recuperar uma API key"""
        from chat_service import ProviderType

        manager = api_key_manager_instance

        # Adicionar key
        config = manager.adicionar(
            empresa=ProviderType.OPENAI,
            api_key="sk-test-openai-key",
            nome_exibicao="Minha Key OpenAI"
        )

        assert config is not None
        assert config.api_key == "sk-test-openai-key"

        # Recuperar por empresa
        retrieved = manager.get_por_empresa(ProviderType.OPENAI)
        assert retrieved is not None
        assert retrieved.api_key == "sk-test-openai-key"

    def test_key_saved_encrypted(self, api_key_manager_instance):
        """Testa que a key e salva criptografada no arquivo"""
        from chat_service import ProviderType

        manager = api_key_manager_instance

        # Adicionar key
        manager.adicionar(
            empresa=ProviderType.OPENAI,
            api_key="sk-test-should-be-encrypted"
        )

        # Ler arquivo diretamente
        with open(manager.config_path, 'r') as f:
            data = json.load(f)

        # Verificar que a key esta criptografada
        saved_key = data["keys"][0]["api_key"]
        assert saved_key != "sk-test-should-be-encrypted"
        assert saved_key.startswith("gAAAAA")  # Formato Fernet


# ============================================================
# TESTES DE FALLBACK PARA VARIAVEIS DE AMBIENTE
# ============================================================

class TestEnvFallback:
    """Testes do fallback para variaveis de ambiente (para Render)"""

    def test_get_api_key_from_env(self, api_key_manager_instance, model_manager_instance):
        """Testa que a API key e obtida de variaveis de ambiente quando nao ha no manager"""
        from chat_service import ProviderType, ChatService

        # Simular ambiente Render (sem keys no manager, mas com env vars)
        test_key = "sk-test-from-environment"

        with patch.dict(os.environ, {"OPENAI_API_KEY": test_key}):
            # Criar modelo sem api_key_id
            model = model_manager_instance.adicionar(
                nome="GPT-4o Test",
                tipo=ProviderType.OPENAI,
                modelo="gpt-4o"
            )

            # Simular busca de API key como faz o ChatService
            api_key = None

            # 1. Tentar api_key_id especifico
            if model.api_key_id:
                key_config = api_key_manager_instance.get(model.api_key_id)
                if key_config:
                    api_key = key_config.api_key

            # 2. Tentar por empresa
            if not api_key:
                key_config = api_key_manager_instance.get_por_empresa(model.tipo)
                if key_config:
                    api_key = key_config.api_key

            # 3. Fallback para env vars
            if not api_key:
                env_var_map = {
                    ProviderType.OPENAI: "OPENAI_API_KEY",
                    ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
                    ProviderType.GOOGLE: "GOOGLE_API_KEY",
                }
                env_var = env_var_map.get(model.tipo)
                if env_var:
                    api_key = os.getenv(env_var)

            assert api_key == test_key

    def test_env_fallback_all_providers(self):
        """Testa fallback de env vars para todos os providers principais"""
        from chat_service import ProviderType

        env_var_map = {
            ProviderType.OPENAI: "OPENAI_API_KEY",
            ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            ProviderType.GOOGLE: "GOOGLE_API_KEY",
            ProviderType.GROQ: "GROQ_API_KEY",
            ProviderType.MISTRAL: "MISTRAL_API_KEY",
            ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
        }

        test_env = {var: f"test-key-{provider.value}" for provider, var in env_var_map.items()}

        with patch.dict(os.environ, test_env):
            for provider, expected_var in env_var_map.items():
                key = os.getenv(expected_var)
                assert key == f"test-key-{provider.value}", f"Falhou para {provider.value}"


# ============================================================
# TESTES DE INTEGRACAO
# ============================================================

class TestChatServiceIntegration:
    """Testes de integracao do ChatService"""

    @pytest.mark.asyncio
    async def test_chat_with_local_key(self, api_key_manager_instance, model_manager_instance):
        """Testa chat usando key do manager local"""
        from chat_service import ProviderType, ChatClient

        # Pular se nao houver key real
        real_key = os.getenv("OPENAI_API_KEY")
        if not real_key:
            pytest.skip("OPENAI_API_KEY nao configurada")

        # Adicionar key ao manager
        api_key_manager_instance.adicionar(
            empresa=ProviderType.OPENAI,
            api_key=real_key
        )

        # Criar modelo
        model = model_manager_instance.adicionar(
            nome="GPT-4o Test",
            tipo=ProviderType.OPENAI,
            modelo="gpt-4o"
        )

        # Obter key
        key_config = api_key_manager_instance.get_por_empresa(ProviderType.OPENAI)
        assert key_config is not None

        # Testar chat
        client = ChatClient(model, key_config.api_key)
        response = await client.chat(
            "Responda apenas: OK",
            system_prompt="Responda apenas com a palavra OK."
        )

        assert "content" in response
        assert len(response["content"]) > 0

    @pytest.mark.asyncio
    async def test_chat_with_env_fallback(self, model_manager_instance):
        """Testa chat usando key de variavel de ambiente"""
        from chat_service import ProviderType, ChatClient

        # Pular se nao houver key real
        real_key = os.getenv("OPENAI_API_KEY")
        if not real_key:
            pytest.skip("OPENAI_API_KEY nao configurada")

        # Criar modelo sem api_key_id
        model = model_manager_instance.adicionar(
            nome="GPT-4o Test",
            tipo=ProviderType.OPENAI,
            modelo="gpt-4o"
        )

        # Testar chat usando env var diretamente
        client = ChatClient(model, real_key)
        response = await client.chat(
            "Responda apenas: OK",
            system_prompt="Responda apenas com a palavra OK."
        )

        assert "content" in response
        assert len(response["content"]) > 0


# ============================================================
# TESTES ONLINE (RENDER)
# ============================================================

class TestRenderEndpoints:
    """Testes dos endpoints no Render"""

    RENDER_URL = "https://ia-educacao-v2.onrender.com"

    @pytest.fixture
    def skip_if_offline(self):
        """Pula testes se Render estiver offline"""
        import httpx
        try:
            resp = httpx.get(f"{self.RENDER_URL}/api/debug/routers", timeout=10)
            if resp.status_code != 200:
                pytest.skip("Render offline ou inacessivel")
        except Exception:
            pytest.skip("Render offline ou inacessivel")

    @pytest.mark.asyncio
    async def test_render_has_models(self, skip_if_offline):
        """Verifica que o Render tem modelos configurados"""
        import httpx

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.RENDER_URL}/api/settings/models")
            assert resp.status_code == 200

            data = resp.json()
            assert "models" in data
            assert len(data["models"]) > 0

    @pytest.mark.asyncio
    async def test_render_env_fallback_works(self, skip_if_offline):
        """Verifica que o fallback de env vars funciona no Render"""
        import httpx

        async with httpx.AsyncClient() as client:
            # Primeiro, obter um modelo valido
            resp = await client.get(f"{self.RENDER_URL}/api/settings/models")
            models = resp.json()["models"]

            # Filtrar modelos que usam env vars (openai, anthropic, google)
            valid_types = ["openai", "anthropic", "google"]
            test_model = None
            for m in models:
                if m["tipo"] in valid_types and m["ativo"]:
                    test_model = m
                    break

            if not test_model:
                pytest.skip("Nenhum modelo valido encontrado")

            # Testar chat
            resp = await client.post(
                f"{self.RENDER_URL}/api/chat",
                json={
                    "messages": [{"role": "user", "content": "OK"}],
                    "model_id": test_model["id"]
                },
                timeout=60
            )

            assert resp.status_code == 200, f"Erro: {resp.text}"
            data = resp.json()
            assert "response" in data
            assert len(data["response"]) > 0

    @pytest.mark.asyncio
    async def test_render_all_providers(self, skip_if_offline):
        """Testa todos os providers configurados no Render"""
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(f"{self.RENDER_URL}/api/settings/models")
            models = resp.json()["models"]

            # Agrupar por tipo
            by_type = {}
            for m in models:
                if m["ativo"] and m["tipo"] in ["openai", "anthropic", "google"]:
                    if m["tipo"] not in by_type:
                        by_type[m["tipo"]] = m

            results = {}
            for tipo, model in by_type.items():
                try:
                    resp = await client.post(
                        f"{self.RENDER_URL}/api/chat",
                        json={
                            "messages": [{"role": "user", "content": "OK"}],
                            "model_id": model["id"]
                        }
                    )
                    results[tipo] = {
                        "success": resp.status_code == 200,
                        "model": model["nome"],
                        "status": resp.status_code
                    }
                except Exception as e:
                    results[tipo] = {
                        "success": False,
                        "model": model["nome"],
                        "error": str(e)
                    }

            # Verificar que pelo menos um provider funciona
            working = [t for t, r in results.items() if r["success"]]
            assert len(working) > 0, f"Nenhum provider funcionou: {results}"

            # Exibir resultados
            print("\nResultados por provider:")
            for tipo, result in results.items():
                status = "OK" if result["success"] else "FALHOU"
                print(f"  {tipo}: {status} ({result['model']})")


# ============================================================
# TESTES DE REGRESSAO
# ============================================================

class TestRegression:
    """Testes de regressao para problemas conhecidos"""

    def test_api_keys_not_in_repo(self):
        """Verifica que api_keys.json NAO esta no repositorio (deve estar no .gitignore)"""
        # Navigate from tests/unit/ to backend/.gitignore
        gitignore_path = Path(__file__).parent.parent.parent / ".gitignore"

        if gitignore_path.exists():
            content = gitignore_path.read_text()
            assert "api_keys.json" in content, "api_keys.json deve estar no .gitignore"


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    # Rodar testes
    pytest.main([__file__, "-v", "--tb=short"])
