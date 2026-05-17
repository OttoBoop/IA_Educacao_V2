import pytest


class _FakeAnthropicResponse:
    status_code = 200
    headers = {}

    def json(self):
        return {
            "content": [{"type": "text", "text": '{"questoes": []}'}],
            "usage": {"input_tokens": 10, "output_tokens": 2},
        }


class _FakeAsyncClient:
    captured_payloads = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers, json):
        self.captured_payloads.append(json)
        return _FakeAnthropicResponse()


@pytest.mark.asyncio
async def test_anthropic_json_pipeline_prompt_uses_output_config(monkeypatch):
    from anexos import ClienteAPIMultimodal

    _FakeAsyncClient.captured_payloads.clear()
    monkeypatch.setattr("anexos.httpx.AsyncClient", _FakeAsyncClient)

    cliente = ClienteAPIMultimodal(
        {
            "tipo": "anthropic",
            "api_key": "test-key",
            "modelo": "claude-haiku-4-5-20251001",
            "max_tokens": 128,
        }
    )

    resultado = await cliente._enviar_anthropic(
        mensagem=(
            "INSTRUCAO CRITICA: Retorne APENAS o JSON valido. "
            "O resultado deve ser um JSON parseavel que comeca com { e termina com }."
        ),
        anexos=[],
        system_prompt="Voce extrai questoes.",
        historico=[],
    )

    assert resultado.sucesso is True
    payload = _FakeAsyncClient.captured_payloads[-1]
    assert payload["output_config"]["format"]["type"] == "json_schema"
    assert payload["output_config"]["format"]["schema"] == {
        "type": "object",
        "additionalProperties": True,
    }


@pytest.mark.asyncio
async def test_anthropic_free_text_prompt_does_not_use_output_config(monkeypatch):
    from anexos import ClienteAPIMultimodal

    _FakeAsyncClient.captured_payloads.clear()
    monkeypatch.setattr("anexos.httpx.AsyncClient", _FakeAsyncClient)

    cliente = ClienteAPIMultimodal(
        {
            "tipo": "anthropic",
            "api_key": "test-key",
            "modelo": "claude-haiku-4-5-20251001",
            "max_tokens": 128,
        }
    )

    await cliente._enviar_anthropic(
        mensagem="Escreva uma explicacao curta em Markdown.",
        anexos=[],
        system_prompt="Voce e um assistente.",
        historico=[],
    )

    payload = _FakeAsyncClient.captured_payloads[-1]
    assert "output_config" not in payload
