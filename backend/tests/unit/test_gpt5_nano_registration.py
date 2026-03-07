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
