"""
Tests for F8-T3: checkbox_toggle action type.

Verifies that:
1. CHECKBOX_TOGGLE exists in ActionType enum
2. LLM brain system prompt includes checkbox_toggle
3. Browser interface get_clickable_elements detects checkbox inputs
4. Browser interface has checkbox_toggle() method
5. Agent _execute_action handles CHECKBOX_TOGGLE
6. LLM brain parses checkbox_toggle action type from JSON
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCheckboxToggleActionType:
    """CHECKBOX_TOGGLE must exist in ActionType enum."""

    def test_checkbox_toggle_in_action_type(self):
        from tests.ui.investor_journey_agent.llm_brain import ActionType

        assert hasattr(ActionType, "CHECKBOX_TOGGLE")
        assert ActionType.CHECKBOX_TOGGLE.value == "checkbox_toggle"


class TestCheckboxToggleInSystemPrompt:
    """System prompt must list checkbox_toggle as available action."""

    def test_system_prompt_includes_checkbox_toggle(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.personas import get_persona
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        persona = get_persona("investor")
        prompt = brain._build_decision_system_prompt(persona, "test goal")
        assert "checkbox_toggle" in prompt


class TestCheckboxElementDetection:
    """get_clickable_elements JS query must include checkbox inputs."""

    def test_clickable_elements_query_includes_checkbox(self):
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        import inspect
        source = inspect.getsource(BrowserInterface.get_clickable_elements)
        assert "checkbox" in source.lower()


class TestBrowserCheckboxToggleMethod:
    """BrowserInterface must have a checkbox_toggle method."""

    def test_browser_has_checkbox_toggle_method(self):
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        assert hasattr(BrowserInterface, "checkbox_toggle")
        assert callable(getattr(BrowserInterface, "checkbox_toggle"))


class TestAgentExecuteCheckboxToggle:
    """Agent._execute_action must handle CHECKBOX_TOGGLE."""

    @pytest.mark.asyncio
    async def test_execute_checkbox_toggle_calls_browser(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", ask_before_action=False)
        agent = InvestorJourneyAgent(
            persona="investor", viewport="desktop", mode="basic", config=config
        )

        mock_browser = AsyncMock()
        mock_browser.checkbox_toggle = AsyncMock(return_value=True)
        agent._browser = mock_browser

        action = Action(
            action_type=ActionType.CHECKBOX_TOGGLE,
            target="agree to terms checkbox",
            thought="I need to accept the terms",
            frustration_level=0.1,
            confidence=0.9,
            element_index=3,
        )

        success, error = await agent._execute_action(action)
        assert success is True
        assert error is None
        mock_browser.checkbox_toggle.assert_called_once()


class TestCheckboxToggleParsing:
    """LLM brain must parse checkbox_toggle action type from JSON."""

    def test_parse_checkbox_toggle_action(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain, ActionType
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        data = {
            "action_type": "checkbox_toggle",
            "target": "terms checkbox",
            "thought": "toggling checkbox",
            "frustration_level": 0.2,
            "confidence": 0.8,
            "element_index": 3,
        }
        action = brain._parse_action_response(data)
        assert action.action_type == ActionType.CHECKBOX_TOGGLE
