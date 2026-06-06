import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.asyncio
async def test_openai_analyze_document_reasoning_usa_max_completion_tokens(tmp_path):
    from ai_providers import OpenAIProvider

    arquivo = tmp_path / "doc.txt"
    arquivo.write_text("conteudo do documento", encoding="utf-8")

    provider = OpenAIProvider(api_key="test-key", model="gpt-5.4-mini")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {"content": "analise"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "total_tokens": 12,
            "prompt_tokens": 7,
            "completion_tokens": 5,
            "completion_tokens_details": {"reasoning_tokens": 1},
        },
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        result = await provider.analyze_document(str(arquivo), "Leia.")

    payload = mock_client.post.call_args.kwargs["json"]

    assert payload["model"] == "gpt-5.4-mini"
    assert payload["max_completion_tokens"] == 4096
    assert payload["reasoning_effort"] == "minimal"
    assert "max_tokens" not in payload
    assert result.content == "analise"
    assert result.metadata["is_reasoning_model"] is True


@pytest.mark.asyncio
async def test_openai_analyze_document_modelo_padrao_mantem_max_tokens(tmp_path):
    from ai_providers import OpenAIProvider

    arquivo = tmp_path / "doc.txt"
    arquivo.write_text("conteudo do documento", encoding="utf-8")

    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "choices": [
            {
                "message": {"content": "analise"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "total_tokens": 12,
            "prompt_tokens": 7,
            "completion_tokens": 5,
        },
    }

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)

        await provider.analyze_document(str(arquivo), "Leia.")

    payload = mock_client.post.call_args.kwargs["json"]

    assert payload["model"] == "gpt-4o"
    assert payload["max_tokens"] == 4096
    assert "max_completion_tokens" not in payload
    assert "reasoning_effort" not in payload
