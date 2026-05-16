from pathlib import Path


FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


def _function_body(name: str, window: int = 2500) -> str:
    content = FRONTEND_HTML.read_text(encoding="utf-8")
    start = content.find(f"function {name}")
    assert start != -1, f"{name} must exist"
    return content[start:start + window]


def test_format_api_error_message_inclui_metadados_de_provider():
    body = _function_body("formatApiErrorMessage")

    assert "provider_status_code" in body
    assert "retryable" in body
    assert "rawMessage?.mensagem" in body
    assert "provider ${provider}" in body
    assert "código ${providerStatus}" in body


def test_render_stage_error_exibe_codigo_retry_e_provider():
    body = _function_body("renderTarefasTree", window=4500)

    assert "stageError.provider_status_code" in body
    assert "stageError.erro_codigo" in body
    assert "stageError.retryable === true" in body
    assert "Provider ' + stageError.provider" in body
