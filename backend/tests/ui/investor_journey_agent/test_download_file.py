"""
Tests for F8-T2: download_file action type.

Verifies that:
1. DOWNLOAD_FILE exists in ActionType enum
2. LLM brain system prompt includes download_file
3. Browser interface has download_file() method
4. Agent _execute_action handles DOWNLOAD_FILE
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


class TestDownloadFileActionType:
    """DOWNLOAD_FILE must exist in ActionType enum."""

    def test_download_file_in_action_type(self):
        from tests.ui.investor_journey_agent.llm_brain import ActionType

        assert hasattr(ActionType, "DOWNLOAD_FILE")
        assert ActionType.DOWNLOAD_FILE.value == "download_file"


class TestDownloadFileInSystemPrompt:
    """System prompt must list download_file as available action."""

    def test_system_prompt_includes_download_file(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.personas import get_persona
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        persona = get_persona("investor")
        prompt = brain._build_decision_system_prompt(persona, "test goal")
        assert "download_file" in prompt


class TestBrowserDownloadFileMethod:
    """BrowserInterface must have a download_file method that returns a Path."""

    def test_browser_has_download_file_method(self):
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        assert hasattr(BrowserInterface, "download_file")
        assert callable(getattr(BrowserInterface, "download_file"))


class TestAgentExecuteDownloadFile:
    """Agent._execute_action must handle DOWNLOAD_FILE."""

    @pytest.mark.asyncio
    async def test_execute_download_file_calls_browser(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(
            anthropic_api_key="test-key",
            ask_before_action=False,
            downloads_dir=Path("/tmp/test_downloads"),
        )
        agent = InvestorJourneyAgent(
            persona="investor", viewport="desktop", mode="basic", config=config
        )

        # Mock the browser
        mock_browser = AsyncMock()
        mock_browser.download_file = AsyncMock(return_value=Path("/tmp/test_downloads/report.pdf"))
        agent._browser = mock_browser

        action = Action(
            action_type=ActionType.DOWNLOAD_FILE,
            target="download report button",
            thought="I want to download the report",
            frustration_level=0.1,
            confidence=0.9,
            element_index=5,
        )

        success, error = await agent._execute_action(action)
        assert success is True
        assert error is None
        mock_browser.download_file.assert_called_once()


class TestDownloadFileParsing:
    """LLM brain must parse download_file action type from JSON."""

    def test_parse_download_file_action(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain, ActionType
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        data = {
            "action_type": "download_file",
            "target": "download button",
            "thought": "downloading report",
            "frustration_level": 0.2,
            "confidence": 0.8,
            "element_index": 5,
        }
        action = brain._parse_action_response(data)
        assert action.action_type == ActionType.DOWNLOAD_FILE
