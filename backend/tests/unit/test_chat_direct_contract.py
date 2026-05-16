import pytest


@pytest.mark.asyncio
async def test_chat_direto_nao_anexa_marcador_debug(monkeypatch):
    """POST /api/chat deve devolver exatamente o texto do modelo/processador."""

    import chat_service as chat_service_module
    import routes_chat
    from chat_service import ModelConfig, ProviderType

    class FakeModelManager:
        def get(self, model_id):
            assert model_id == "model-smoke"
            return ModelConfig(
                id="model-smoke",
                nome="Smoke Model",
                tipo=ProviderType.OPENAI,
                modelo="gpt-test",
            )

    class FakeApiKeyManager:
        def get(self, key_id):
            return None

        def get_por_empresa(self, empresa):
            return type("Key", (), {"api_key": "test-key"})()

    class FakeChatClient:
        def __init__(self, model_config, api_key):
            self.model_config = model_config
            self.api_key = api_key

        async def chat(self, user_message, historico, system_prompt):
            return {
                "content": '{"ok": true}',
                "modelo": self.model_config.modelo,
                "tokens": 12,
            }

    async def fake_processar_codigo_executavel(content, atividade_id=None, aluno_id=None):
        return content, []

    monkeypatch.setattr(routes_chat, "model_manager", FakeModelManager())
    monkeypatch.setattr(routes_chat, "api_key_manager", FakeApiKeyManager())
    monkeypatch.setattr(chat_service_module, "ChatClient", FakeChatClient)
    monkeypatch.setattr(
        chat_service_module.chat_service,
        "_processar_codigo_executavel",
        fake_processar_codigo_executavel,
    )

    response = await routes_chat.chat_direto(
        routes_chat.ChatRequest(
            messages=[
                routes_chat.ChatMessage(
                    role="user",
                    content="Responda apenas JSON.",
                )
            ],
            model_id="model-smoke",
        )
    )

    assert response["response"] == '{"ok": true}'
    assert "DEBUG_V3_MARKER_2026" not in response["response"]
