"""
F0-T1: GPT-5 Nano must have suporta_function_calling: true in models.json.

RED phase — this test should FAIL because the flag is currently false.
"""

import json
from pathlib import Path

import pytest


MODELS_JSON = Path(__file__).resolve().parents[2] / "data" / "models.json"


class TestF0T1_GPT5NanoFunctionCalling:
    """F0-T1: GPT-5 Nano must support function calling."""

    def test_gpt5_nano_exists_in_models(self):
        """models.json must contain an entry with id 'gpt5nano001'."""
        with open(MODELS_JSON, encoding="utf-8") as f:
            data = json.load(f)
        models = data["models"]
        ids = [m["id"] for m in models]
        assert "gpt5nano001" in ids, (
            "GPT-5 Nano (id=gpt5nano001) not found in models.json"
        )

    def test_gpt5_nano_supports_function_calling(self):
        """GPT-5 Nano must have suporta_function_calling set to true."""
        with open(MODELS_JSON, encoding="utf-8") as f:
            data = json.load(f)
        models = data["models"]
        nano = next(m for m in models if m["id"] == "gpt5nano001")
        assert nano["suporta_function_calling"] is True, (
            f"GPT-5 Nano suporta_function_calling is {nano['suporta_function_calling']!r}, "
            f"expected True. The E-T1 gate blocks models without function calling."
        )
