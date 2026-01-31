"""
Tests for roleplay failure reactions in the Investor Journey Agent.

These tests verify that personas react to failures realistically,
matching their personality (patience level, tech skill).
"""

import pytest
from unittest.mock import patch, AsyncMock

from tests.ui.investor_journey_agent.llm_brain import (
    LLMBrain,
    JourneyStep,
    Action,
    ActionType,
)
from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.personas import get_persona


class TestFailureContextPassing:
    """Tests for passing failure context to LLM decisions."""

    @pytest.mark.asyncio
    async def test_failure_context_included_in_prompt(self):
        """Test that when last action failed, failure details are sent to LLM."""
        config = AgentConfig()
        brain = LLMBrain(config)

        # Create a history with a failed action
        failed_step = JourneyStep(
            step_number=1,
            url="http://test.com",
            screenshot_path="/tmp/step1.png",
            action=Action(
                action_type=ActionType.CLICK,
                target="#submit-button",
                thought="Clicking submit",
                frustration_level=0.2,
                confidence=0.8,
            ),
            success=False,
            error_message="Element not found: #submit-button",
        )

        persona = get_persona("investor")
        captured_messages = []

        # Mock _call_claude to capture what's sent
        async def capture_call(messages, model, max_tokens, system):
            captured_messages.append({"messages": messages, "system": system})
            return '{"action_type": "wait", "target": "", "thought": "test", "frustration_level": 0.5, "confidence": 0.5}'

        with patch.object(brain, '_call_claude', side_effect=capture_call):
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="Submit form",
                history=[failed_step],
            )

        # Verify failure context is in the user message
        assert len(captured_messages) == 1
        user_content = captured_messages[0]["messages"][0]["content"]

        # Find the text content (not image)
        text_content = None
        for item in user_content:
            if item.get("type") == "text":
                text_content = item.get("text", "")
                break

        assert text_content is not None, "No text content found in message"

        # Check that failure details are prominently included
        assert "LAST ACTION FAILED" in text_content or "failed" in text_content.lower()
        assert "Element not found" in text_content

    @pytest.mark.asyncio
    async def test_failure_context_asks_persona_to_react(self):
        """Test that the system prompt guides persona to react to failure."""
        config = AgentConfig()
        brain = LLMBrain(config)

        failed_step = JourneyStep(
            step_number=1,
            url="http://test.com",
            screenshot_path="/tmp/step1.png",
            action=Action(
                action_type=ActionType.CLICK,
                target="#broken-button",
                thought="Trying to click",
                frustration_level=0.3,
                confidence=0.7,
            ),
            success=False,
            error_message="Button is not clickable",
        )

        persona = get_persona("investor")
        captured_messages = []

        async def capture_call(messages, model, max_tokens, system):
            captured_messages.append({"messages": messages, "system": system})
            return '{"action_type": "give_up", "target": "", "thought": "This is broken", "frustration_level": 0.9, "confidence": 0.9}'

        with patch.object(brain, '_call_claude', side_effect=capture_call):
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="Click button",
                history=[failed_step],
            )

        # Check that system prompt mentions reacting to failures
        system_prompt = captured_messages[0]["system"]

        # Should have guidance on failure reactions
        assert "fail" in system_prompt.lower() or "retry" in system_prompt.lower() or "give_up" in system_prompt.lower()


class TestReloadAndBackActions:
    """Tests for reload and back navigation actions."""

    def test_action_type_has_reload(self):
        """Test that ActionType enum includes RELOAD."""
        assert hasattr(ActionType, 'RELOAD')
        assert ActionType.RELOAD.value == "reload"

    def test_action_type_has_back(self):
        """Test that ActionType enum includes BACK."""
        assert hasattr(ActionType, 'BACK')
        assert ActionType.BACK.value == "back"

    @pytest.mark.asyncio
    async def test_system_prompt_mentions_reload_action(self):
        """Test that system prompt includes reload as an available action."""
        config = AgentConfig()
        brain = LLMBrain(config)

        persona = get_persona("investor")
        captured_messages = []

        async def capture_call(messages, model, max_tokens, system):
            captured_messages.append({"system": system})
            return '{"action_type": "wait", "target": "", "thought": "test", "frustration_level": 0.1, "confidence": 0.9}'

        with patch.object(brain, '_call_claude', side_effect=capture_call):
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="Test",
            )

        system_prompt = captured_messages[0]["system"]

        # Should mention reload as available action
        assert "reload" in system_prompt.lower()

    @pytest.mark.asyncio
    async def test_system_prompt_mentions_back_action(self):
        """Test that system prompt includes back as an available action."""
        config = AgentConfig()
        brain = LLMBrain(config)

        persona = get_persona("investor")
        captured_messages = []

        async def capture_call(messages, model, max_tokens, system):
            captured_messages.append({"system": system})
            return '{"action_type": "wait", "target": "", "thought": "test", "frustration_level": 0.1, "confidence": 0.9}'

        with patch.object(brain, '_call_claude', side_effect=capture_call):
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="Test",
            )

        system_prompt = captured_messages[0]["system"]

        # Should mention back as available action
        assert "back" in system_prompt.lower()
