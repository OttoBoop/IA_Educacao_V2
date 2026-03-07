"""
Tests for F8-T1: select_option action type.

Verifies that:
1. SELECT_OPTION exists in ActionType enum
2. Action dataclass has select_value field
3. LLM brain system prompt includes select_option
4. LLM brain parses select_value from response JSON
5. Browser interface get_clickable_elements detects <select> elements
6. Browser interface has select_option() method
7. Agent _execute_action handles SELECT_OPTION
8. Intent resolver handles SELECT_OPTION actions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSelectOptionActionType:
    """SELECT_OPTION must exist in ActionType enum."""

    def test_select_option_in_action_type(self):
        from tests.ui.investor_journey_agent.llm_brain import ActionType

        assert hasattr(ActionType, "SELECT_OPTION")
        assert ActionType.SELECT_OPTION.value == "select_option"


class TestSelectOptionActionDataclass:
    """Action dataclass must have select_value field."""

    def test_action_has_select_value_field(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType

        action = Action(
            action_type=ActionType.SELECT_OPTION,
            target="model dropdown",
            thought="I want to select a model",
            frustration_level=0.1,
            confidence=0.9,
            select_value="gpt-4o",
        )
        assert action.select_value == "gpt-4o"

    def test_select_value_defaults_to_none(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType

        action = Action(
            action_type=ActionType.CLICK,
            target="button",
            thought="clicking",
            frustration_level=0.0,
            confidence=0.5,
        )
        assert action.select_value is None


class TestSelectOptionInSystemPrompt:
    """System prompt must list select_option as available action."""

    def test_system_prompt_includes_select_option(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.personas import get_persona
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        persona = get_persona("investor")
        prompt = brain._build_decision_system_prompt(persona, "test goal")
        assert "select_option" in prompt
        assert "select_value" in prompt


class TestSelectOptionParsing:
    """LLM brain must parse select_value from response JSON."""

    def test_parse_action_with_select_value(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain, ActionType
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        data = {
            "action_type": "select_option",
            "target": "model selector",
            "thought": "selecting model",
            "frustration_level": 0.1,
            "confidence": 0.9,
            "select_value": "gpt-4o",
            "element_index": 3,
        }
        action = brain._parse_action_response(data)
        assert action.action_type == ActionType.SELECT_OPTION
        assert action.select_value == "gpt-4o"


class TestSelectElementDetection:
    """get_clickable_elements JS query must include <select> elements."""

    def test_clickable_elements_query_includes_select(self):
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        # Read the JS source from get_clickable_elements
        import inspect
        source = inspect.getsource(BrowserInterface.get_clickable_elements)
        assert "select" in source.lower()
        # Must be in the CSS selector query string
        assert "'select'" in source or '"select"' in source or ", select" in source


class TestBrowserSelectOptionMethod:
    """BrowserInterface must have a select_option method."""

    def test_browser_has_select_option_method(self):
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        assert hasattr(BrowserInterface, "select_option")
        assert callable(getattr(BrowserInterface, "select_option"))


class TestAgentExecuteSelectOption:
    """Agent._execute_action must handle SELECT_OPTION."""

    @pytest.mark.asyncio
    async def test_execute_select_option_calls_browser(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", ask_before_action=False)
        agent = InvestorJourneyAgent(
            persona="investor", viewport="desktop", mode="basic", config=config
        )

        # Mock the browser
        mock_browser = AsyncMock()
        mock_browser.select_option = AsyncMock(return_value=True)
        agent._browser = mock_browser

        action = Action(
            action_type=ActionType.SELECT_OPTION,
            target="model dropdown",
            thought="selecting model",
            frustration_level=0.1,
            confidence=0.9,
            select_value="gpt-4o",
            element_index=3,
        )

        success, error = await agent._execute_action(action)
        assert success is True
        assert error is None


class TestIntentResolverSelectOption:
    """IntentResolver.execute_with_retry must handle SELECT_OPTION."""

    @pytest.mark.asyncio
    async def test_intent_resolver_handles_select_option(self):
        from tests.ui.investor_journey_agent.intent_resolver import IntentResolver
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.browser_interface import ClickableElement

        resolver = IntentResolver()
        mock_browser = AsyncMock()
        mock_browser.select_option = AsyncMock(return_value=True)

        elements = [
            ClickableElement(
                selector="select#model",
                tag="select",
                text="gpt-4o",
                occlusion_status="visible",
            )
        ]

        action = Action(
            action_type=ActionType.SELECT_OPTION,
            target="model dropdown",
            thought="selecting",
            frustration_level=0.0,
            confidence=0.9,
            select_value="gpt-4o",
            element_index=1,
        )

        result = await resolver.execute_with_retry(action, elements, mock_browser)
        # Should NOT return None (which means "not my job")
        assert result is not None
        success, error = result
        assert success is True
