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
            "O resultado deve ser um JSON parseavel que comeca com { e termina com }.\n"
            "Estrutura JSON esperada:\n"
            '{"questoes":[{"numero":1,"enunciado":"x","itens":[],'
            '"tipo":"dissertativa","pontuacao":1.0,"habilidades":["h"],'
            '"tipo_raciocinio":"aplicacao"}],'
            '"total_questoes":1,"pontuacao_total":1.0,'
            '"_avisos_documento":[],"_avisos_questao":[]}'
        ),
        anexos=[],
        system_prompt="Voce extrai questoes.",
        historico=[],
    )

    assert resultado.sucesso is True
    payload = _FakeAsyncClient.captured_payloads[-1]
    assert payload["output_config"]["format"]["type"] == "json_schema"
    schema = payload["output_config"]["format"]["schema"]
    assert schema["additionalProperties"] is False
    assert "questoes" in schema["required"]
    assert schema["properties"]["questoes"]["items"]["additionalProperties"] is False


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


@pytest.mark.asyncio
async def test_anthropic_unknown_json_prompt_does_not_use_generic_schema(monkeypatch):
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
        mensagem="Retorne APENAS JSON valido no formato que achar melhor.",
        anexos=[],
        system_prompt="Voce e um assistente.",
        historico=[],
    )

    payload = _FakeAsyncClient.captured_payloads[-1]
    assert "output_config" not in payload


def test_anthropic_gabarito_schema_wins_over_embedded_questoes_context():
    from anexos import ClienteAPIMultimodal

    cliente = ClienteAPIMultimodal(
        {
            "tipo": "anthropic",
            "api_key": "test-key",
            "modelo": "claude-haiku-4-5-20251001",
        }
    )

    schema = cliente._anthropic_json_schema_para_prompt(
        'Questões já identificadas: {"questoes":[{"tipo_raciocinio":"aplicacao"}]}\n'
        'Estrutura JSON esperada: {"respostas":[{"questao_numero":1,'
        '"resposta_correta":"x=5","justificativa":"","conceito_central":"Equacao",'
        '"criterios_parciais":[]}],"_avisos_documento":[],"_avisos_questao":[]}'
    )

    assert "respostas" in schema["required"]
    assert "questoes" not in schema["required"]


def test_anthropic_respostas_schema_wins_over_embedded_questoes_context():
    from anexos import ClienteAPIMultimodal

    cliente = ClienteAPIMultimodal(
        {
            "tipo": "anthropic",
            "api_key": "test-key",
            "modelo": "claude-haiku-4-5-20251001",
        }
    )

    schema = cliente._anthropic_json_schema_para_prompt(
        'Questões da prova: {"questoes":[{"tipo_raciocinio":"aplicacao"}]}\n'
        'Estrutura JSON esperada: {"aluno":"Ana","respostas":[{"questao_numero":1,'
        '"resposta_aluno":"x=5","em_branco":false,"ilegivel":false,'
        '"observacoes":"","raciocinio_parcial":null}],'
        '"questoes_respondidas":1,"questoes_em_branco":0,'
        '"_avisos_documento":[],"_avisos_questao":[]}'
    )

    assert "aluno" in schema["required"]
    assert "respostas" in schema["required"]
    assert "questoes" not in schema["required"]
