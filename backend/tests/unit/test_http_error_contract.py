import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_http_exception_handler_preserva_detail_estruturado():
    import main_v2

    request = SimpleNamespace(state=SimpleNamespace(trace_id="trace-123"))
    response = await main_v2.http_exception_handler(
        request,
        HTTPException(
            status_code=429,
            detail={
                "erro": "provider_api_error",
                "provider": "Google",
                "provider_status_code": 429,
                "retryable": True,
                "mensagem": "Erro API Google: 429 - Limite atingido.",
            },
        ),
    )

    data = json.loads(response.body)

    assert response.status_code == 429
    assert data["error"]["message"] == "Erro API Google: 429 - Limite atingido."
    assert data["error"]["erro"] == "provider_api_error"
    assert data["error"]["provider"] == "Google"
    assert data["error"]["provider_status_code"] == 429
    assert data["error"]["retryable"] is True
    assert data["error"]["status_code"] == 429
    assert data["error"]["trace_id"] == "trace-123"
