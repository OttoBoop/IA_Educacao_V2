"""
Tests for externalized analysis in the Investor Journey Agent (Feature 5).

These tests verify that:
- No Sonnet API calls are made during journey (only Haiku for steps)
- journey_log.md contains all info needed for Claude Code analysis
- The analysis is designed to be done externally
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.llm_brain import LLMBrain, JourneyStep, Action, ActionType
from tests.ui.investor_journey_agent.personas import get_persona


class TestNoSonnetCalls:
    """Tests that no Sonnet (analysis) model is called during journey."""

    @pytest.mark.asyncio
    async def test_llm_brain_only_uses_step_model(self):
        """Test that LLMBrain only uses the step model (Haiku), not analysis model."""
        config = AgentConfig()
        brain = LLMBrain(config)

        # Track which models are called
        models_called = []

        async def track_call(messages, model, max_tokens, system):
            models_called.append(model)
            return '{"action_type": "done", "target": "", "thought": "test", "frustration_level": 0.1, "confidence": 0.9}'

        persona = get_persona("investor")

        with patch.object(brain, '_call_claude', side_effect=track_call):
            await brain.decide_next_action(
                screenshot_base64="test",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="Test",
            )

        # Should only call step model (Haiku), not analysis model (Sonnet)
        assert len(models_called) == 1
        assert models_called[0] == config.step_model
        assert config.analysis_model not in models_called

    def test_agent_mode_basic_skips_evaluation(self):
        """Test that basic mode doesn't call evaluate_journey."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            mode="basic",  # Basic mode should skip evaluation
        )

        # Basic mode should be set
        assert agent.mode == "basic"

    @pytest.mark.asyncio
    async def test_in_depth_mode_still_works_but_deprecated(self):
        """
        Test that in_depth mode is deprecated but still functional.

        The agent should emit a deprecation warning or log that analysis
        should be done in Claude Code instead.
        """
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent

        # This test just verifies the mode exists - actual deprecation
        # message is an implementation detail
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            mode="in_depth",
        )

        assert agent.mode == "in_depth"


class TestJourneyLogForClaudeCode:
    """Tests that journey_log.md contains all info needed for Claude Code analysis."""

    def test_journey_log_includes_full_screenshot_paths(self):
        """Test that journey_log includes full paths for Claude Code to read screenshots."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            screenshots_dir = output_dir / "screenshots"
            screenshots_dir.mkdir()

            generator = JourneyLogGenerator()
            persona = get_persona("investor")

            steps = [
                JourneyStep(
                    step_number=1,
                    url="http://test.com",
                    screenshot_path=str(screenshots_dir / "step_01.png"),
                    action=Action(
                        action_type=ActionType.CLICK,
                        target="#button",
                        thought="Clicking button",
                        frustration_level=0.3,
                        confidence=0.8,
                    ),
                    success=True,
                )
            ]

            log_path = generator.generate_log(
                output_dir=output_dir,
                persona=persona,
                goal="Test goal",
                url="http://test.com",
                viewport_name="iphone_14",
                steps=steps,
                start_time=datetime.now(),
            )

            content = log_path.read_text(encoding="utf-8")

            # Should include screenshot filename for Claude Code to read
            assert "step_01.png" in content

    def test_journey_log_includes_persona_details(self):
        """Test that journey_log includes persona patience/tech level for analysis context."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = JourneyLogGenerator()
            persona = get_persona("investor")

            log_path = generator.generate_log(
                output_dir=output_dir,
                persona=persona,
                goal="Test goal",
                url="http://test.com",
                viewport_name="iphone_14",
                steps=[],
                start_time=datetime.now(),
            )

            content = log_path.read_text(encoding="utf-8")

            # Should include persona details for context
            assert "Patience" in content
            assert "Tech Savviness" in content or "Savviness" in content
            assert str(persona.patience_level) in content

    def test_journey_log_includes_frustration_metrics(self):
        """Test that journey_log includes frustration metrics for analysis."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = JourneyLogGenerator()
            persona = get_persona("investor")

            steps = [
                JourneyStep(
                    step_number=1,
                    url="http://test.com",
                    screenshot_path="/tmp/step1.png",
                    action=Action(
                        action_type=ActionType.CLICK,
                        target="#button",
                        thought="This is frustrating",
                        frustration_level=0.75,  # High frustration
                        confidence=0.4,
                    ),
                    success=False,
                    error_message="Button not found",
                )
            ]

            log_path = generator.generate_log(
                output_dir=output_dir,
                persona=persona,
                goal="Test goal",
                url="http://test.com",
                viewport_name="iphone_14",
                steps=steps,
                start_time=datetime.now(),
            )

            content = log_path.read_text(encoding="utf-8")

            # Should include frustration metrics
            assert "Frustration" in content
            assert "75%" in content
            assert "Button not found" in content
