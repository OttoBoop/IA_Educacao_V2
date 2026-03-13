"""
Tests for rate limiting and cost control in the Investor Journey Agent.

These tests verify that the agent has proper limits to prevent runaway costs.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestRateLimitingConfig:
    """Tests for rate limiting configuration."""

    def test_config_has_max_llm_calls(self):
        """Test that AgentConfig has max_llm_calls synced with max_steps by default."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig()

        assert hasattr(config, 'max_llm_calls')
        assert config.max_llm_calls == config.max_steps

    def test_config_max_llm_calls_is_configurable(self):
        """Test that max_llm_calls can be customized."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(max_llm_calls=25)

        assert config.max_llm_calls == 25

    def test_config_has_max_tokens_per_request(self):
        """Test that AgentConfig has max_tokens_per_request with default 2000."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig()

        assert hasattr(config, 'max_tokens_per_request')
        assert config.max_tokens_per_request == 2000

    def test_config_max_tokens_per_request_is_configurable(self):
        """Test that max_tokens_per_request can be customized."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(max_tokens_per_request=1000)

        assert config.max_tokens_per_request == 1000

    def test_config_has_journey_timeout_seconds(self):
        """Test that AgentConfig has journey_timeout_seconds with default 1200 (20 min)."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig()

        assert hasattr(config, 'journey_timeout_seconds')
        assert config.journey_timeout_seconds == 1200  # 20 minutes


class TestLLMCallCounter:
    """Tests for LLM call counter in the agent."""

    def test_llm_brain_tracks_call_count(self):
        """Test that LLMBrain tracks the number of API calls made."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)

        assert hasattr(brain, 'call_count')
        assert brain.call_count == 0

    @pytest.mark.asyncio
    async def test_llm_brain_increments_call_count(self):
        """Test that LLMBrain increments call_count after each API call."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)

        # Mock the API call
        with patch.object(brain, '_call_claude', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"action_type": "wait", "target": "", "thought": "test", "frustration_level": 0.1, "confidence": 0.9}'

            persona = get_persona("investor")
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="test",
            )

            assert brain.call_count == 1

    @pytest.mark.asyncio
    async def test_llm_brain_blocks_when_max_calls_is_exceeded(self):
        """Test that max_llm_calls exhaustion returns a blocking decision failure action."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona

        config = AgentConfig(max_llm_calls=2, anthropic_api_key="test-key")
        brain = LLMBrain(config)

        # Mock the API call
        with patch.object(brain, '_call_claude', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"action_type": "wait", "target": "", "thought": "test", "frustration_level": 0.1, "confidence": 0.9}'

            persona = get_persona("investor")

            # First two calls should work
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="test",
            )
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="test",
            )

            assert brain.call_count == 2

            # Third call should return a blocking failure action instead of pretending success
            action = await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="test",
            )

            assert action.action_type.value == "wait"
            assert action.decision_error_is_blocking is True
            assert action.decision_error is not None
            assert "Maximum LLM calls" in action.decision_error
