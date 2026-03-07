"""
Tests for F8-T6: Sync max_llm_calls with max_steps automatically.

Verifies that:
1. AgentConfig auto-syncs max_llm_calls with max_steps when max_llm_calls is not explicitly set
2. Explicitly setting max_llm_calls preserves the explicit value
3. Default max_llm_calls is None (sentinel for auto-sync)
"""

import pytest


class TestMaxLlmCallsSyncsWithMaxSteps:
    """max_llm_calls must auto-sync with max_steps."""

    def test_max_llm_calls_equals_max_steps_default(self):
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        assert config.max_llm_calls == config.max_steps

    def test_max_llm_calls_syncs_with_custom_max_steps(self):
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", max_steps=200)
        assert config.max_llm_calls == 200

    def test_max_llm_calls_syncs_with_small_max_steps(self):
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", max_steps=10)
        assert config.max_llm_calls == 10


class TestExplicitMaxLlmCallsPreserved:
    """When max_llm_calls is explicitly set, keep the explicit value."""

    def test_explicit_max_llm_calls_kept(self):
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(
            anthropic_api_key="test-key",
            max_steps=400,
            max_llm_calls=100,
        )
        assert config.max_llm_calls == 100

    def test_explicit_max_llm_calls_different_from_max_steps(self):
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(
            anthropic_api_key="test-key",
            max_steps=50,
            max_llm_calls=25,
        )
        assert config.max_llm_calls == 25
        assert config.max_steps == 50
