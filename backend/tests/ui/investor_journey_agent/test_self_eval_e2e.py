"""
End-to-end smoke test: run the journey agent on a static HTML report fixture.

F3-T1: Verifies the full agent loop works on a file:// URL.
Uses a mock LLM brain to avoid API calls while testing the real browser.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent, JourneyReport
from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.llm_brain import Action, ActionType


# A minimal HTML report fixture that mimics a journey report
FIXTURE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Journey Report - Investor Persona</title>
    <style>
        body { font-family: sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
        h1 { color: #00d4ff; }
        .step { border: 1px solid #333; padding: 10px; margin: 10px 0; border-radius: 8px; }
        .step img { max-width: 100%; }
        .collapsible { cursor: pointer; background: #16213e; padding: 8px; border-radius: 4px; }
        .collapsible-content { display: none; padding: 10px; }
        nav a { color: #00d4ff; margin-right: 15px; }
    </style>
</head>
<body>
    <h1>Journey Report</h1>
    <nav>
        <a href="#summary">Summary</a>
        <a href="#steps">Steps</a>
        <a href="#findings">Findings</a>
    </nav>

    <section id="summary">
        <h2>Executive Summary</h2>
        <p>Persona: Investor | Steps: 15 | Success Rate: 73%</p>
        <p>The investor explored the application and found several UX issues.</p>
    </section>

    <section id="steps" style="margin-top: 200px;">
        <h2>Journey Steps</h2>
        <div class="step">
            <h3>Step 1: Landing Page</h3>
            <p>Thought: "Let me see what this app is about"</p>
            <div class="collapsible" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'block' ? 'none' : 'block'">
                Show Details
            </div>
            <div class="collapsible-content">
                <p>Action: scroll down</p>
                <p>Frustration: 0.1</p>
            </div>
        </div>
        <div class="step">
            <h3>Step 2: Navigation</h3>
            <p>Thought: "Where do I find the main features?"</p>
        </div>
    </section>

    <section id="findings" style="margin-top: 200px;">
        <h2>Key Findings</h2>
        <ul>
            <li>No clear call-to-action on landing page</li>
            <li>Mobile navigation is confusing</li>
            <li>Loading times feel slow</li>
        </ul>
    </section>
</body>
</html>
"""


@pytest.fixture
def report_html(tmp_path):
    """Create a static HTML report fixture and return its file:// URL."""
    html_file = tmp_path / "journey_report.html"
    html_file.write_text(FIXTURE_HTML)
    return html_file.resolve().as_uri()


@pytest.fixture
def output_dir(tmp_path):
    """Create an output directory for the agent."""
    out = tmp_path / "output"
    out.mkdir()
    return out


def make_scroll_action(step_num):
    """Create a scroll action."""
    return Action(
        action_type=ActionType.SCROLL,
        target="page",
        thought=f"Let me scroll to see more of this report (step {step_num})",
        frustration_level=0.1 * step_num,
        confidence=0.9,
        scroll_direction="down",
    )


def make_click_action(selector, thought="Let me click this"):
    """Create a click action."""
    return Action(
        action_type=ActionType.CLICK,
        target=selector,
        thought=thought,
        frustration_level=0.2,
        confidence=0.8,
    )


def make_done_action():
    """Create a done action."""
    return Action(
        action_type=ActionType.DONE,
        target="",
        thought="I have seen enough of this report to evaluate it.",
        frustration_level=0.3,
        confidence=0.9,
    )


class TestSelfEvalE2E:
    """F3-T1: End-to-end journey on a static HTML report."""

    @pytest.mark.asyncio
    async def test_journey_completes_on_static_html(self, report_html, output_dir):
        """Full journey on a static HTML file should complete without error."""
        # Sequence: scroll, scroll, click nav link, scroll, done
        actions = [
            make_scroll_action(1),
            make_scroll_action(2),
            make_click_action("a[href='#steps']", "Let me check the steps section"),
            make_scroll_action(3),
            make_done_action(),
        ]
        action_iter = iter(actions)

        config = AgentConfig(
            ask_before_action=False,
            max_steps=10,
            output_dir=output_dir,
        )

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="desktop",
            mode="basic",
            config=config,
            headless=True,
        )

        # Mock the LLM brain to return our scripted actions
        with patch.object(
            agent.__class__,
            "_InvestorJourneyAgent__init_brain",
            return_value=None,
            create=True,
        ):
            pass

        # Run journey with mocked LLM
        original_run = agent.run_journey

        async def patched_run(url, goal, max_steps=None):
            # We need to patch the brain AFTER it's created inside run_journey
            report = await original_run(url=url, goal=goal, max_steps=max_steps)
            return report

        # Patch decide_next_action on LLMBrain
        with patch(
            "tests.ui.investor_journey_agent.llm_brain.LLMBrain.decide_next_action",
            side_effect=actions,
        ):
            report = await agent.run_journey(
                url=report_html,
                goal="Evaluate this journey report's UX and design",
                max_steps=10,
            )

        # Verify results
        assert isinstance(report, JourneyReport)
        assert len(report.steps) == 5
        assert not report.gave_up
        assert report.output_dir.exists()

    @pytest.mark.asyncio
    async def test_journey_produces_screenshots(self, report_html, output_dir):
        """Journey should capture screenshots at each step."""
        actions = [
            make_scroll_action(1),
            make_done_action(),
        ]

        config = AgentConfig(
            ask_before_action=False,
            max_steps=5,
            output_dir=output_dir,
        )

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="desktop",
            mode="basic",
            config=config,
            headless=True,
        )

        with patch(
            "tests.ui.investor_journey_agent.llm_brain.LLMBrain.decide_next_action",
            side_effect=actions,
        ):
            report = await agent.run_journey(
                url=report_html,
                goal="Quick look at the report",
                max_steps=5,
            )

        # Check screenshots were saved
        screenshots_dir = report.output_dir / "screenshots"
        assert screenshots_dir.exists()
        screenshots = list(screenshots_dir.glob("*.png"))
        assert len(screenshots) >= 2  # At least one per step

    @pytest.mark.asyncio
    async def test_journey_does_not_crash_on_give_up(self, report_html, output_dir):
        """Journey should handle give_up action gracefully on static HTML."""
        actions = [
            make_scroll_action(1),
            Action(
                action_type=ActionType.GIVE_UP,
                target="",
                thought="This report is impossible to navigate on mobile!",
                frustration_level=0.9,
                confidence=0.95,
            ),
        ]

        config = AgentConfig(
            ask_before_action=False,
            max_steps=5,
            output_dir=output_dir,
        )

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            mode="basic",
            config=config,
            headless=True,
        )

        with patch(
            "tests.ui.investor_journey_agent.llm_brain.LLMBrain.decide_next_action",
            side_effect=actions,
        ):
            report = await agent.run_journey(
                url=report_html,
                goal="Evaluate report on mobile",
                max_steps=5,
            )

        assert report.gave_up
        assert len(report.steps) == 2
