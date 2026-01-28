"""
Integration tests for AI provider configurations.

These tests verify that the provider selection logic works correctly
and that API calls are made with the right parameters.
"""

import sys
from pathlib import Path

# Add the backend directory to Python path BEFORE any other imports
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestProviderConfiguration:
    """Tests for provider configuration and selection."""

    @pytest.mark.asyncio
    async def test_openai_chat_uses_correct_params(self, mock_openai_chat_response):
        """Test that OpenAI chat uses correct parameters."""
        from chat_service import ChatClient, ModelConfig, ProviderType

        config = ModelConfig(
            id="test-openai",
            nome="Test OpenAI",
            tipo=ProviderType.OPENAI,
            modelo="gpt-4o",
            max_tokens=4096,
            temperature=0.7,
            suporta_temperature=True,
            suporta_vision=True
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_openai_chat_response
            )

            client = ChatClient(config, "fake-api-key")
            result = await client.chat("Hello", [], "You are helpful")

            assert result["content"] == "Test response from OpenAI"
            assert result["provider"] == "openai"

            # Verify the call was made with correct parameters
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            assert "gpt-4o" in str(call_args)

    @pytest.mark.asyncio
    async def test_anthropic_chat_uses_correct_params(self, mock_anthropic_chat_response):
        """Test that Anthropic chat uses correct parameters."""
        from chat_service import ChatClient, ModelConfig, ProviderType

        config = ModelConfig(
            id="test-anthropic",
            nome="Test Anthropic",
            tipo=ProviderType.ANTHROPIC,
            modelo="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            temperature=0.7,
            suporta_temperature=True,
            suporta_vision=True
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_anthropic_chat_response
            )

            client = ChatClient(config, "fake-api-key")
            result = await client.chat("Hello", [], "You are helpful")

            assert result["content"] == "Test response from Claude"
            assert result["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_google_chat_uses_system_instruction(self, mock_google_chat_response):
        """Test that Google chat uses proper system_instruction parameter."""
        from chat_service import ChatClient, ModelConfig, ProviderType

        config = ModelConfig(
            id="test-google",
            nome="Test Google",
            tipo=ProviderType.GOOGLE,
            modelo="gemini-2.5-flash",
            max_tokens=4096,
            temperature=0.7,
            suporta_temperature=True,
            suporta_vision=True
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_google_chat_response
            )

            client = ChatClient(config, "fake-api-key")
            result = await client.chat("Hello", [], "You are a helpful assistant")

            assert result["content"] == "Test response from Gemini"
            assert result["provider"] == "google"

            # Verify system_instruction is in the request
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            json_body = call_args.kwargs.get('json', {})
            assert "system_instruction" in json_body

    @pytest.mark.asyncio
    async def test_reasoning_model_no_temperature(self, mock_openai_chat_response):
        """Test that reasoning models don't send temperature parameter."""
        from chat_service import ChatClient, ModelConfig, ProviderType

        config = ModelConfig(
            id="test-o1",
            nome="Test O1",
            tipo=ProviderType.OPENAI,
            modelo="o1",
            max_tokens=4096,
            temperature=None,
            suporta_temperature=False,
            suporta_vision=False
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_openai_chat_response
            )

            client = ChatClient(config, "fake-api-key")
            result = await client.chat("Hello", [], "You are helpful")

            # Verify temperature is NOT in the request
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            json_body = call_args.kwargs.get('json', {})
            assert "temperature" not in json_body


class TestModelNames:
    """Tests for correct model name configuration."""

    def test_anthropic_model_ids_are_correct(self):
        """Test that Anthropic model IDs match expected format."""
        from chat_service import MODELOS_SUGERIDOS, ProviderType

        anthropic_models = MODELOS_SUGERIDOS.get(ProviderType.ANTHROPIC, [])

        # Check Claude 4.5 models have correct date format
        for model in anthropic_models:
            if "4-5" in model["id"]:
                # Should have format like claude-sonnet-4-5-YYYYMMDD
                assert len(model["id"]) > 20, f"Model ID too short: {model['id']}"

        # Specific checks for known models with CORRECT release dates
        sonnet_45 = next((m for m in anthropic_models if "sonnet-4-5" in m["id"]), None)
        assert sonnet_45 is not None, "Claude Sonnet 4.5 not found"
        assert "20250929" in sonnet_45["id"], f"Wrong date for Sonnet 4.5: {sonnet_45['id']} (should be 20250929)"

        haiku_45 = next((m for m in anthropic_models if "haiku-4-5" in m["id"]), None)
        assert haiku_45 is not None, "Claude Haiku 4.5 not found"
        assert "20251015" in haiku_45["id"], f"Wrong date for Haiku 4.5: {haiku_45['id']} (should be 20251015)"

        opus_45 = next((m for m in anthropic_models if "opus-4-5" in m["id"]), None)
        assert opus_45 is not None, "Claude Opus 4.5 not found"
        assert "20251124" in opus_45["id"], f"Wrong date for Opus 4.5: {opus_45['id']} (should be 20251124)"

    def test_openai_model_ids_exist(self):
        """Test that OpenAI model IDs are valid."""
        from chat_service import MODELOS_SUGERIDOS, ProviderType

        openai_models = MODELOS_SUGERIDOS.get(ProviderType.OPENAI, [])

        valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "o1", "o3", "o3-mini", "o4-mini"]

        for model in openai_models:
            assert any(valid in model["id"] for valid in valid_models), \
                f"Possibly invalid OpenAI model: {model['id']}"


class TestSavedModelsConfiguration:
    """Tests for the actual saved models in data/models.json."""

    def test_saved_anthropic_models_have_correct_ids(self):
        """Test that saved Anthropic models use correct model IDs."""
        import json
        from pathlib import Path

        models_path = Path(__file__).parent.parent.parent / "data" / "models.json"
        if not models_path.exists():
            pytest.skip("models.json not found")

        with open(models_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Known correct Anthropic model IDs with release dates
        correct_anthropic_models = {
            "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5": "claude-haiku-4-5-20251015",
            "claude-opus-4-5": "claude-opus-4-5-20251124",
            "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku": "claude-3-5-haiku-20241022",
        }

        anthropic_models = [m for m in data.get("models", []) if m.get("tipo") == "anthropic"]

        for model in anthropic_models:
            modelo_id = model.get("modelo", "")

            # Check if this is a Claude 4.5 model with wrong date
            for prefix, correct_id in correct_anthropic_models.items():
                if modelo_id.startswith(prefix) and modelo_id != correct_id:
                    # Only fail if the date part is wrong
                    if prefix in modelo_id and correct_id.split("-")[-1] not in modelo_id:
                        pytest.fail(
                            f"Model '{model.get('nome')}' has wrong ID: {modelo_id}\n"
                            f"Expected: {correct_id}"
                        )

    def test_saved_openai_models_are_valid(self):
        """Test that saved OpenAI models use valid model names."""
        import json
        from pathlib import Path

        models_path = Path(__file__).parent.parent.parent / "data" / "models.json"
        if not models_path.exists():
            pytest.skip("models.json not found")

        with open(models_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Known valid OpenAI model patterns (updated Jan 2026)
        valid_patterns = [
            # GPT-5 series (released 2025-2026)
            "gpt-5.2", "gpt-5.2-pro", "gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-5-pro", "gpt-5-image",
            # GPT-4 series
            "gpt-4o", "gpt-4o-mini",
            "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano",
            # Reasoning models
            "o1", "o1-pro", "o3", "o3-mini", "o3-pro", "o4-mini",
        ]

        # Known INVALID models that don't exist
        invalid_models = ["gpt-6", "gpt-7"]

        openai_models = [m for m in data.get("models", []) if m.get("tipo") == "openai"]

        for model in openai_models:
            modelo_id = model.get("modelo", "")

            # Check for known invalid models
            if modelo_id in invalid_models:
                pytest.fail(
                    f"Model '{model.get('nome')}' uses invalid OpenAI model: {modelo_id}\n"
                    f"This model does not exist. Use one of: {valid_patterns}"
                )

    def test_saved_google_models_are_valid(self):
        """Test that saved Google models use valid model names."""
        import json
        from pathlib import Path

        models_path = Path(__file__).parent.parent.parent / "data" / "models.json"
        if not models_path.exists():
            pytest.skip("models.json not found")

        with open(models_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Known valid Google Gemini model patterns
        valid_patterns = [
            "gemini-3-pro", "gemini-3-flash", "gemini-3-ultra",
            "gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite",
            "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash",
        ]

        google_models = [m for m in data.get("models", []) if m.get("tipo") == "google"]

        for model in google_models:
            modelo_id = model.get("modelo", "")

            is_valid = any(pattern in modelo_id for pattern in valid_patterns)
            if not is_valid:
                pytest.fail(
                    f"Model '{model.get('nome')}' may use invalid Google model: {modelo_id}\n"
                    f"Expected patterns: {valid_patterns}"
                )

    def test_all_models_have_required_fields(self):
        """Test that all saved models have required fields."""
        import json
        from pathlib import Path

        models_path = Path(__file__).parent.parent.parent / "data" / "models.json"
        if not models_path.exists():
            pytest.skip("models.json not found")

        with open(models_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        required_fields = ["id", "nome", "tipo", "modelo", "max_tokens", "ativo"]

        for model in data.get("models", []):
            for field in required_fields:
                assert field in model, f"Model '{model.get('nome', 'unknown')}' missing field: {field}"
                assert model[field] is not None or field in ["api_key_id", "temperature"], \
                    f"Model '{model.get('nome')}' has None for required field: {field}"


class TestMultimodalProviders:
    """Tests for multimodal API calls with attachments."""

    @pytest.mark.asyncio
    async def test_google_multimodal_uses_system_instruction(self, mock_google_chat_response):
        """Test that Google multimodal uses system_instruction parameter."""
        from anexos import ClienteAPIMultimodal

        config = {
            "tipo": "google",
            "api_key": "fake-key",
            "modelo": "gemini-2.5-flash",
            "max_tokens": 4096,
            "temperature": 0.7,
            "suporta_temperature": True
        }

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_google_chat_response
            )

            client = ClienteAPIMultimodal(config)
            result = await client._enviar_google(
                "Test message",
                [],
                "System instruction here",
                []
            )

            assert result.sucesso is True
            assert result.resposta == "Test response from Gemini"

            # Verify system_instruction is in the request
            call_args = mock_client.return_value.__aenter__.return_value.post.call_args
            json_body = call_args.kwargs.get('json', {})
            assert "system_instruction" in json_body
            assert json_body["system_instruction"]["parts"][0]["text"] == "System instruction here"
