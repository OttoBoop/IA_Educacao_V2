"""
Tests for website context feature (F1: Context Plumbing, F4: Validation).

Verifies that website_context flows from CLI -> AgentConfig -> Agent -> LLM Brain system prompt.
Includes E2E test that verifies context reaches the system prompt during a real agent run.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# ── F1-T1: AgentConfig accepts website_context ──────────────────────


class TestAgentConfigWebsiteContext:
    """Tests for website_context field on AgentConfig."""

    def test_config_accepts_website_context(self):
        """AgentConfig should accept a website_context kwarg."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig(website_context="This is an exam grading platform")
        assert config.website_context == "This is an exam grading platform"

    def test_config_website_context_defaults_to_none(self):
        """AgentConfig.website_context should default to None."""
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig()
        assert config.website_context is None


# ── F1-T2: CLI --context flag ────────────────────────────────────────


class TestCLIContextFlag:
    """Tests for --context CLI argument."""

    def test_parser_accepts_context_flag(self):
        """CLI parser should recognize --context flag."""
        from tests.ui.investor_journey_agent.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args(["--context", "A test grading app"])
        assert args.context == "A test grading app"

    def test_parser_context_defaults_to_none(self):
        """--context should default to None when not provided."""
        from tests.ui.investor_journey_agent.__main__ import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.context is None


# ── F1-T4: System prompt injection ───────────────────────────────────


class TestSystemPromptContextInjection:
    """Tests for website_context injection into the LLM system prompt."""

    def test_system_prompt_includes_context_when_provided(self):
        """System prompt should contain the website context string."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona

        config = AgentConfig()
        brain = LLMBrain(config)
        persona = get_persona("investor")

        prompt = brain._build_decision_system_prompt(
            persona=persona,
            goal="Evaluate the product",
            website_context="This is an automated exam grading platform for teachers",
        )

        assert "automated exam grading platform" in prompt

    def test_system_prompt_frames_context_as_creator_pitch(self):
        """Context should be framed as 'the creator described this website as...'."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona

        config = AgentConfig()
        brain = LLMBrain(config)
        persona = get_persona("investor")

        prompt = brain._build_decision_system_prompt(
            persona=persona,
            goal="Evaluate",
            website_context="A cool app",
        )

        # Should be framed naturally, not just dumped in
        assert "creator" in prompt.lower() or "described" in prompt.lower()

    def test_system_prompt_works_without_context(self):
        """System prompt should work fine when website_context is None (backward compat)."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona

        config = AgentConfig()
        brain = LLMBrain(config)
        persona = get_persona("investor")

        # Should NOT raise - backward compat
        prompt = brain._build_decision_system_prompt(
            persona=persona,
            goal="Evaluate the product",
            website_context=None,
        )

        assert "Your current goal:" in prompt
        # Should not contain context framing when None
        assert "creator described" not in prompt.lower()


# ── F1-T3 + F1-T4: Integration — context flows through agent to brain ──


class TestContextFlowIntegration:
    """Integration tests: context flows from run_journey params to brain's system prompt."""

    def test_decide_next_action_accepts_website_context(self):
        """LLMBrain.decide_next_action should accept website_context param."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig

        config = AgentConfig()
        brain = LLMBrain(config)

        # Just verify the signature accepts the kwarg (don't actually call the API)
        import inspect
        sig = inspect.signature(brain.decide_next_action)
        assert "website_context" in sig.parameters

    def test_run_journey_accepts_website_context(self):
        """InvestorJourneyAgent.run_journey should accept website_context param."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent

        import inspect
        sig = inspect.signature(InvestorJourneyAgent.run_journey)
        assert "website_context" in sig.parameters


# ── F4-T1: E2E — website_context reaches system prompt in real agent run ──


FIXTURE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Test Page</title></head>
<body><h1>Test Website</h1><p>A simple page for testing context injection.</p></body>
</html>
"""


class TestWebsiteContextE2E:
    """F4-T1: E2E test that website_context actually reaches the LLM system prompt
    during a real agent run with mocked LLM."""

    @pytest.fixture
    def html_url(self, tmp_path):
        html_file = tmp_path / "test_page.html"
        html_file.write_text(FIXTURE_HTML)
        return html_file.resolve().as_uri()

    @pytest.fixture
    def output_dir(self, tmp_path):
        out = tmp_path / "output"
        out.mkdir()
        return out

    @pytest.mark.asyncio
    async def test_website_context_reaches_system_prompt_in_agent_run(self, html_url, output_dir):
        """When website_context is passed to run_journey, it must appear in the
        system prompt string passed to the LLM API call (_call_claude)."""
        import json as json_mod
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain

        captured_system_prompts = []

        # Mock _call_claude to capture the system prompt and return a done action JSON
        done_json = json_mod.dumps({
            "thought": "Done evaluating.",
            "frustration_level": 0.1,
            "action_type": "done",
            "target": "",
            "confidence": 0.9,
        })

        async def fake_call_claude(self, messages, model, max_tokens, system=None):
            if system:
                captured_system_prompts.append(system)
            return done_json

        config = AgentConfig(
            ask_before_action=False,
            max_steps=3,
            output_dir=output_dir,
        )

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="desktop",
            mode="basic",
            config=config,
            headless=True,
        )

        with patch.object(LLMBrain, "_call_claude", fake_call_claude):
            report = await agent.run_journey(
                url=html_url,
                goal="Evaluate this page",
                max_steps=3,
                website_context="An automated exam grading platform for teachers",
            )

        # The system prompt sent to the LLM should contain the website context
        assert len(captured_system_prompts) >= 1
        assert "automated exam grading platform" in captured_system_prompts[0]
        assert "creator" in captured_system_prompts[0].lower()
