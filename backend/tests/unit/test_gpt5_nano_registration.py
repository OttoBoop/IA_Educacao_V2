"""
Test GPT-5 Nano registration in models.json

Verifies that gpt-5-nano is properly registered with correct
parameters for a reasoning model (no temperature, reasoning_effort).
"""

import json
from pathlib import Path

import pytest


MODELS_JSON = Path(__file__).parent.parent.parent / "data" / "models.json"


@pytest.fixture
def models():
    with open(MODELS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)["models"]


def find_model(models, modelo_id):
    return next((m for m in models if m["modelo"] == modelo_id), None)


def find_models(models, modelo_id):
    return [m for m in models if m["modelo"] == modelo_id]


class TestGPT5NanoRegistration:
    def test_gpt5_nano_exists_in_models(self, models):
        """gpt-5-nano must be present in models.json"""
        model = find_model(models, "gpt-5-nano")
        assert model is not None, "gpt-5-nano not found in models.json"

    def test_gpt5_nano_is_openai_type(self, models):
        """gpt-5-nano must be registered as openai provider"""
        model = find_model(models, "gpt-5-nano")
        assert model["tipo"] == "openai"

    def test_gpt5_nano_no_temperature(self, models):
        """Reasoning models must not support temperature"""
        model = find_model(models, "gpt-5-nano")
        assert model["suporta_temperature"] is False

    def test_gpt5_nano_has_reasoning_effort(self, models):
        """Reasoning models must have reasoning_effort in parametros"""
        model = find_model(models, "gpt-5-nano")
        assert "reasoning_effort" in model.get("parametros", {})

    def test_gpt5_nano_is_active(self, models):
        """Model must be active"""
        model = find_model(models, "gpt-5-nano")
        assert model["ativo"] is True


class TestGPT54MiniRegistration:
    def test_gpt54mini_exists_as_ocr_candidate(self, models):
        """gpt-5.4-mini candidate must survive deploys via models.json."""
        model = find_model(models, "gpt-5.4-mini")
        assert model is not None, "gpt-5.4-mini not found in models.json"
        assert model["id"] == "gpt54mini001"
        assert model["tipo"] == "openai"
        assert model["catalog_ref"] == "openai/gpt-5.4-mini"

    def test_gpt54mini_capabilities_match_smoke_candidate(self, models):
        """Candidate needs vision/tools and no temperature for reasoning calls."""
        model = find_model(models, "gpt-5.4-mini")
        assert model["suporta_vision"] is True
        assert model["suporta_function_calling"] is True
        assert model["suporta_temperature"] is False
        assert model["temperature"] is None
        assert model["parametros"]["reasoning_effort"] == "low"
        assert model["ativo"] is True

    def test_gpt54mini_is_default_while_anthropic_credit_is_blocked(self, models):
        """Default model must be an already-confirmed provider, not blocked Haiku."""
        defaults = [model for model in models if model.get("is_default")]
        assert len(defaults) == 1
        assert defaults[0]["id"] == "gpt54mini001"
        assert defaults[0]["modelo"] == "gpt-5.4-mini"


class TestOpenAIReasoningRegistration:
    def test_o3_mini_configs_support_tools_but_not_vision(self, models):
        """o3-mini API supports function calling, but not image input."""
        o3_models = find_models(models, "o3-mini")

        assert {model["id"] for model in o3_models} == {
            "58ff5dcdff67",
            "c489f094083c",
        }
        for model in o3_models:
            assert model["tipo"] == "openai"
            assert model["suporta_temperature"] is False
            assert model["temperature"] is None
            assert model["suporta_function_calling"] is True
            assert model["suporta_vision"] is False
            assert "reasoning_effort" in model["parametros"]

    def test_o4_mini_config_supports_tools_and_vision(self, models):
        """o4-mini API supports function calling and image input."""
        model = find_model(models, "o4-mini")

        assert model is not None
        assert model["id"] == "9f6b2b61b6c3"
        assert model["tipo"] == "openai"
        assert model["suporta_temperature"] is False
        assert model["temperature"] is None
        assert model["suporta_function_calling"] is True
        assert model["suporta_vision"] is True
        assert model["parametros"]["reasoning_effort"] == "high"
