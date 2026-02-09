"""
Tests for F3: Partial report improvements.

Covers:
- F3-T1: HTML "Incomplete Journey" banner renders when report.incomplete=True
- F3-T2: KeyboardInterrupt during journey → still returns JourneyReport with incomplete=True
- F3-T3: EventEmitter.emit_stopped() called on KeyboardInterrupt
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

from tests.ui.investor_journey_agent.agent import JourneyReport, InvestorJourneyAgent
from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer
from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.personas import get_persona
from tests.ui.investor_journey_agent.llm_brain import Action, ActionType, JourneyStep


def _make_report(incomplete=False, incomplete_reason=None, steps=None):
    """Helper to create a JourneyReport for testing."""
    persona = get_persona("investor")
    if steps is None:
        action = Action(
            action_type=ActionType.CLICK,
            target="#btn",
            thought="Testing",
            frustration_level=0.3,
            confidence=0.8,
        )
        steps = [
            JourneyStep(
                step_number=1,
                url="https://example.com",
                screenshot_path="screenshots/step_01.png",
                action=action,
                success=True,
            )
        ]
    return JourneyReport(
        persona=persona,
        goal="Test the app",
        url="https://example.com",
        viewport_name="iphone_14",
        start_time=datetime(2026, 2, 9, 12, 0, 0),
        end_time=datetime(2026, 2, 9, 12, 1, 0),
        steps=steps,
        evaluation=None,
        output_dir=Path("/tmp/test"),
        incomplete=incomplete,
        incomplete_reason=incomplete_reason,
    )


class TestHTMLIncompleteBanner:
    """F3-T1: HTML report shows 'Incomplete Journey' banner."""

    def test_incomplete_report_shows_banner(self):
        """When report.incomplete=True, HTML contains 'Incomplete Journey'."""
        report = _make_report(incomplete=True)
        renderer = HTMLReportRenderer()
        html = renderer.render(report)
        assert "Incomplete Journey" in html

    def test_incomplete_reason_appears_in_banner(self):
        """When incomplete with a reason, the reason text appears in HTML."""
        report = _make_report(
            incomplete=True,
            incomplete_reason="Stopped by user request",
        )
        renderer = HTMLReportRenderer()
        html = renderer.render(report)
        assert "Stopped by user request" in html

    def test_complete_report_has_no_banner(self):
        """When report.incomplete=False, no incomplete banner appears."""
        report = _make_report(incomplete=False)
        renderer = HTMLReportRenderer()
        html = renderer.render(report)
        assert "Incomplete Journey" not in html
        assert "journey-incomplete" not in html


def _make_mock_browser(get_state_side_effect=None):
    """Create a properly configured mock BrowserInterface for testing.

    The mock is set up as an async context manager that returns itself,
    matching the agent's `async with BrowserInterface(...) as browser:` pattern.
    """
    mock_browser = AsyncMock()
    # Context manager returns itself
    mock_browser.__aenter__ = AsyncMock(return_value=mock_browser)
    mock_browser.__aexit__ = AsyncMock(return_value=False)
    mock_browser.goto = AsyncMock(return_value=True)
    mock_browser.wait_for_idle = AsyncMock()
    mock_browser.save_screenshot = AsyncMock()
    mock_browser._console_errors = []

    if get_state_side_effect is not None:
        mock_browser.get_state = AsyncMock(side_effect=get_state_side_effect)
    else:
        state = MagicMock()
        state.screenshot_base64 = "dGVzdA=="
        state.dom_snapshot = "<html></html>"
        state.url = "https://example.com"
        state.console_errors = []
        mock_browser.get_state = AsyncMock(return_value=state)

    return mock_browser


def _make_mock_state():
    """Create a mock browser state."""
    state = MagicMock()
    state.screenshot_base64 = "dGVzdA=="
    state.dom_snapshot = "<html></html>"
    state.url = "https://example.com"
    state.console_errors = []
    return state


def _make_mock_brain():
    """Create a mock LLMBrain that returns WAIT actions."""
    mock_brain = MagicMock()
    mock_brain.decide_next_action = AsyncMock(return_value=Action(
        action_type=ActionType.WAIT,
        target="",
        thought="Waiting",
        frustration_level=0.1,
        confidence=0.9,
    ))
    return mock_brain


class TestKeyboardInterruptHandling:
    """F3-T2: KeyboardInterrupt during journey returns partial report."""

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_returns_report_with_incomplete(self):
        """KeyboardInterrupt during journey loop → report with incomplete=True."""
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
        )

        state = _make_mock_state()
        # First get_state succeeds, second raises KeyboardInterrupt
        mock_browser = _make_mock_browser(
            get_state_side_effect=[state, KeyboardInterrupt()]
        )
        mock_brain = _make_mock_brain()

        try:
            with patch('tests.ui.investor_journey_agent.agent.BrowserInterface', return_value=mock_browser), \
                 patch('tests.ui.investor_journey_agent.agent.LLMBrain', return_value=mock_brain):
                report = await agent.run_journey(
                    url="https://example.com",
                    goal="Test",
                    max_steps=5,
                )
        except KeyboardInterrupt:
            pytest.fail("KeyboardInterrupt escaped run_journey() — it should be caught internally")

        assert report.incomplete is True
        assert report.incomplete_reason is not None
        assert "interrupt" in report.incomplete_reason.lower() or "keyboard" in report.incomplete_reason.lower()

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_emits_stopped_event(self):
        """KeyboardInterrupt triggers event_emitter.emit_stopped()."""
        mock_emitter = MagicMock()
        mock_emitter.emit_step = MagicMock()
        mock_emitter.emit_stopped = MagicMock()
        mock_emitter.emit_error = MagicMock()

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
            event_emitter=mock_emitter,
        )

        # Raise KeyboardInterrupt on first get_state
        mock_browser = _make_mock_browser(
            get_state_side_effect=KeyboardInterrupt()
        )
        mock_brain = _make_mock_brain()

        try:
            with patch('tests.ui.investor_journey_agent.agent.BrowserInterface', return_value=mock_browser), \
                 patch('tests.ui.investor_journey_agent.agent.LLMBrain', return_value=mock_brain):
                report = await agent.run_journey(
                    url="https://example.com",
                    goal="Test",
                    max_steps=5,
                )
        except KeyboardInterrupt:
            pytest.fail("KeyboardInterrupt escaped run_journey() — it should be caught internally")

        mock_emitter.emit_stopped.assert_called_once()
        call_kwargs = mock_emitter.emit_stopped.call_args
        reason = call_kwargs.kwargs.get("reason", "")
        assert "interrupt" in reason.lower()

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_preserves_completed_steps(self):
        """Steps completed before KeyboardInterrupt are preserved in report."""
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
        )

        state = _make_mock_state()
        # 2 successful states, then KeyboardInterrupt
        mock_browser = _make_mock_browser(
            get_state_side_effect=[state, state, KeyboardInterrupt()]
        )
        mock_brain = _make_mock_brain()

        try:
            with patch('tests.ui.investor_journey_agent.agent.BrowserInterface', return_value=mock_browser), \
                 patch('tests.ui.investor_journey_agent.agent.LLMBrain', return_value=mock_brain):
                report = await agent.run_journey(
                    url="https://example.com",
                    goal="Test",
                    max_steps=10,
                )
        except KeyboardInterrupt:
            pytest.fail("KeyboardInterrupt escaped run_journey() — it should be caught internally")

        assert report.incomplete is True
        assert len(report.steps) == 2  # 2 steps completed before interrupt
