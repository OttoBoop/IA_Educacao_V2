"""
Tests for F8-T4: read_page_text action type.

Verifies that:
1. READ_PAGE_TEXT exists in ActionType enum
2. LLM brain system prompt includes read_page_text
3. Browser interface has read_page_text() method
4. Agent _execute_action handles READ_PAGE_TEXT
5. LLM brain parses read_page_text action type from JSON
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestReadPageTextActionType:
    """READ_PAGE_TEXT must exist in ActionType enum."""

    def test_read_page_text_in_action_type(self):
        from tests.ui.investor_journey_agent.llm_brain import ActionType

        assert hasattr(ActionType, "READ_PAGE_TEXT")
        assert ActionType.READ_PAGE_TEXT.value == "read_page_text"


class TestReadPageTextInSystemPrompt:
    """System prompt must list read_page_text as available action."""

    def test_system_prompt_includes_read_page_text(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.personas import get_persona
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        persona = get_persona("investor")
        prompt = brain._build_decision_system_prompt(persona, "test goal")
        assert "read_page_text" in prompt


class TestBrowserReadPageTextMethod:
    """BrowserInterface must have a read_page_text method."""

    def test_browser_has_read_page_text_method(self):
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        assert hasattr(BrowserInterface, "read_page_text")
        assert callable(getattr(BrowserInterface, "read_page_text"))


class TestAgentExecuteReadPageText:
    """Agent._execute_action must handle READ_PAGE_TEXT."""

    @pytest.mark.asyncio
    async def test_execute_read_page_text_calls_browser(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", ask_before_action=False)
        agent = InvestorJourneyAgent(
            persona="investor", viewport="desktop", mode="basic", config=config
        )

        mock_browser = AsyncMock()
        mock_browser.read_page_text = AsyncMock(return_value="Welcome to the dashboard")
        agent._browser = mock_browser

        action = Action(
            action_type=ActionType.READ_PAGE_TEXT,
            target="main heading",
            thought="I want to read the heading text",
            frustration_level=0.0,
            confidence=0.9,
            element_index=1,
        )

        success, error = await agent._execute_action(action)
        assert success is True
        assert error is None
        mock_browser.read_page_text.assert_called_once()


class TestReadPageTextParsing:
    """LLM brain must parse read_page_text action type from JSON."""

    def test_parse_read_page_text_action(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain, ActionType
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        data = {
            "action_type": "read_page_text",
            "target": "page title",
            "thought": "reading the title",
            "frustration_level": 0.1,
            "confidence": 0.8,
            "element_index": 1,
        }
        action = brain._parse_action_response(data)
        assert action.action_type == ActionType.READ_PAGE_TEXT
