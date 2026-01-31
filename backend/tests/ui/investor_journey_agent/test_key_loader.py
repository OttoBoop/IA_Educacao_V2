"""
Tests for the Investor Journey Agent API Key Loader.

These tests verify that the agent can load API keys from
the app's encrypted key store (data/api_keys.json).
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestKeyLoader:
    """Tests for the investor journey agent key loader."""

    def test_load_anthropic_key_from_api_keys_json(self):
        """Test that the key loader finds Anthropic key from api_keys.json."""
        # This test should FAIL because the key_loader module doesn't exist yet
        from tests.ui.investor_journey_agent.key_loader import load_anthropic_key

        # Create a temporary api_keys.json with a mock Anthropic key
        with tempfile.TemporaryDirectory() as tmpdir:
            # We need to mock the encryption system
            # For this test, we'll use unencrypted keys
            api_keys_path = Path(tmpdir) / "api_keys.json"
            api_keys_path.write_text(json.dumps({
                "keys": [
                    {
                        "id": "test123",
                        "empresa": "anthropic",
                        "nome_exibicao": "Test Anthropic Key",
                        "api_key": "sk-ant-test-key-12345",
                        "ativo": True
                    }
                ],
                "encrypted": False
            }))

            # Load key from the temporary path
            key = load_anthropic_key(config_path=str(api_keys_path))

            assert key is not None
            assert key == "sk-ant-test-key-12345"

    def test_fallback_to_env_var_when_file_missing(self):
        """Test that loader falls back to ANTHROPIC_API_KEY env var when file is missing."""
        from tests.ui.investor_journey_agent.key_loader import load_anthropic_key

        test_key = "sk-ant-from-env-var"

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": test_key}):
            # Use a path that doesn't exist
            key = load_anthropic_key(config_path="/nonexistent/path/api_keys.json")

            assert key == test_key

    def test_fallback_to_env_var_when_no_anthropic_key(self):
        """Test fallback to env var when file exists but has no Anthropic key."""
        from tests.ui.investor_journey_agent.key_loader import load_anthropic_key

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create api_keys.json with only OpenAI key
            api_keys_path = Path(tmpdir) / "api_keys.json"
            api_keys_path.write_text(json.dumps({
                "keys": [
                    {
                        "id": "openai123",
                        "empresa": "openai",
                        "nome_exibicao": "OpenAI Key",
                        "api_key": "sk-openai-key",
                        "ativo": True
                    }
                ],
                "encrypted": False
            }))

            test_key = "sk-ant-fallback-env"

            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": test_key}):
                key = load_anthropic_key(config_path=str(api_keys_path))

                assert key == test_key

    def test_returns_none_when_no_key_available(self):
        """Test that loader returns None when no key is available anywhere."""
        from tests.ui.investor_journey_agent.key_loader import load_anthropic_key

        # Clear the env var
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            # Remove the env var completely if it exists
            os.environ.pop("ANTHROPIC_API_KEY", None)

            key = load_anthropic_key(config_path="/nonexistent/path/api_keys.json")

            assert key is None

    def test_loads_from_default_path_when_not_specified(self):
        """Test that loader uses default path (data/api_keys.json) when not specified."""
        from tests.ui.investor_journey_agent.key_loader import load_anthropic_key, DEFAULT_API_KEYS_PATH

        # This test verifies the default path constant exists
        assert DEFAULT_API_KEYS_PATH is not None
        assert "api_keys.json" in str(DEFAULT_API_KEYS_PATH)


class TestAgentConfigWithKeyLoader:
    """Tests for AgentConfig integration with key loader."""

    def test_agent_config_uses_key_loader(self):
        """Test that AgentConfig uses the key loader instead of just env var."""
        from tests.ui.investor_journey_agent.key_loader import load_anthropic_key
        from tests.ui.investor_journey_agent.config import AgentConfig

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create api_keys.json with Anthropic key
            api_keys_path = Path(tmpdir) / "api_keys.json"
            api_keys_path.write_text(json.dumps({
                "keys": [
                    {
                        "id": "test123",
                        "empresa": "anthropic",
                        "nome_exibicao": "Test Key",
                        "api_key": "sk-ant-from-file",
                        "ativo": True
                    }
                ],
                "encrypted": False
            }))

            # Create config with custom path
            config = AgentConfig(api_keys_path=str(api_keys_path))

            # Should load from file, not env var
            assert config.anthropic_api_key == "sk-ant-from-file"
