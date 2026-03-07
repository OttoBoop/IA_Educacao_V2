"""
Tests for F10-T1 (partial): evaluate_js action type.

Verifies that:
1. EVALUATE_JS exists in ActionType enum
2. Action dataclass has eval_script field
3. LLM brain system prompt includes evaluate_js
4. LLM brain parses evaluate_js action type from JSON (including eval_script)
5. Agent _execute_action handles EVALUATE_JS
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestEvaluateJsActionType:
    """EVALUATE_JS must exist in ActionType enum."""

    def test_evaluate_js_in_action_type(self):
        from tests.ui.investor_journey_agent.llm_brain import ActionType

        assert hasattr(ActionType, "EVALUATE_JS")
        assert ActionType.EVALUATE_JS.value == "evaluate_js"


class TestEvalScriptField:
    """Action dataclass must have eval_script field."""

    def test_action_has_eval_script_field(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType

        action = Action(
            action_type=ActionType.EVALUATE_JS,
            target="showTurma JS call",
            thought="navigating via JS",
            frustration_level=0.0,
            confidence=0.9,
            eval_script="showTurma('abc123')",
        )
        assert action.eval_script == "showTurma('abc123')"


class TestEvaluateJsInSystemPrompt:
    """System prompt must list evaluate_js as available action."""

    def test_system_prompt_includes_evaluate_js(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.personas import get_persona
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        persona = get_persona("tester")
        prompt = brain._build_decision_system_prompt(persona, "test goal")
        assert "evaluate_js" in prompt
        assert "eval_script" in prompt


class TestEvaluateJsParsing:
    """LLM brain must parse evaluate_js action type from JSON, extracting eval_script."""

    def test_parse_evaluate_js_action(self):
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain, ActionType
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key")
        brain = LLMBrain(config)
        data = {
            "action_type": "evaluate_js",
            "target": "navigate to turma via JS",
            "thought": "I will call showTurma directly",
            "frustration_level": 0.0,
            "confidence": 0.95,
            "eval_script": "showTurma('6b5dc44c08aaf375')",
        }
        action = brain._parse_action_response(data)
        assert action.action_type == ActionType.EVALUATE_JS
        assert action.eval_script == "showTurma('6b5dc44c08aaf375')"


class TestAgentExecuteEvaluateJs:
    """Agent._execute_action must handle EVALUATE_JS by calling browser.evaluate_js."""

    @pytest.mark.asyncio
    async def test_execute_evaluate_js_calls_browser(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", ask_before_action=False)
        agent = InvestorJourneyAgent(
            persona="tester", viewport="desktop", mode="basic", config=config
        )

        mock_browser = AsyncMock()
        mock_browser.evaluate_js = AsyncMock(return_value=None)
        agent._browser = mock_browser

        action = Action(
            action_type=ActionType.EVALUATE_JS,
            target="navigate to turma",
            thought="calling showTurma via JS",
            frustration_level=0.0,
            confidence=0.95,
            eval_script="showTurma('6b5dc44c08aaf375')",
        )

        success, error = await agent._execute_action(action)
        assert success is True
        assert error is None
        mock_browser.evaluate_js.assert_called_once_with("showTurma('6b5dc44c08aaf375')")

    @pytest.mark.asyncio
    async def test_execute_evaluate_js_missing_script_returns_false(self):
        from tests.ui.investor_journey_agent.llm_brain import Action, ActionType
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(anthropic_api_key="test-key", ask_before_action=False)
        agent = InvestorJourneyAgent(
            persona="tester", viewport="desktop", mode="basic", config=config
        )

        mock_browser = AsyncMock()
        agent._browser = mock_browser

        action = Action(
            action_type=ActionType.EVALUATE_JS,
            target="some target",
            thought="oops no script",
            frustration_level=0.0,
            confidence=0.5,
            eval_script=None,
        )

        success, error = await agent._execute_action(action)
        assert success is False
        assert "eval_script" in error
