"""
Tests for the Investor Journey Agent.

These tests verify the agent can simulate user journeys
and generate meaningful reports.
"""

import pytest
import os
from pathlib import Path

# Skip all tests if UI tests are not enabled
pytestmark = [
    pytest.mark.ui,
    pytest.mark.skipif(
        os.getenv("RUN_UI_TESTS", "") != "1",
        reason="UI tests disabled. Set RUN_UI_TESTS=1 to enable",
    ),
    pytest.mark.skipif(
        not os.getenv("ANTHROPIC_API_KEY"),
        reason="ANTHROPIC_API_KEY not set",
    ),
]


@pytest.fixture
def agent_config():
    """Create agent configuration for tests."""
    from tests.ui.investor_journey_agent.config import AgentConfig

    return AgentConfig(
        ask_before_action=False,  # Automated testing
        max_steps=10,  # Limit steps for faster tests
    )


@pytest.mark.asyncio
async def test_investor_can_view_welcome(agent_config):
    """Test that an investor can see and interact with welcome modal."""
    from tests.ui.investor_journey_agent import InvestorJourneyAgent

    agent = InvestorJourneyAgent(
        persona="investor",
        viewport="iphone_14",
        mode="basic",
        config=agent_config,
    )

    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="View the welcome screen and understand what this app does",
        max_steps=5,
    )

    # Should have at least one step
    assert len(report.steps) >= 1

    # First step should have captured a screenshot
    assert Path(report.steps[0].screenshot_path).exists()


@pytest.mark.asyncio
async def test_student_navigation(agent_config):
    """Test that a student persona can navigate the app."""
    from tests.ui.investor_journey_agent import InvestorJourneyAgent

    agent = InvestorJourneyAgent(
        persona="student",
        viewport="desktop",
        mode="basic",
        config=agent_config,
    )

    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="Find where to view my graded assignments",
        max_steps=8,
    )

    # Should complete some steps
    assert len(report.steps) >= 1

    # Check report output was created
    assert report.output_dir.exists()
    assert (report.output_dir / "screenshots").exists()


@pytest.mark.asyncio
async def test_in_depth_analysis(agent_config):
    """Test in-depth mode generates evaluation."""
    from tests.ui.investor_journey_agent import InvestorJourneyAgent

    agent = InvestorJourneyAgent(
        persona="confused_teacher",
        viewport="iphone_14",
        mode="in_depth",
        config=agent_config,
    )

    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="Figure out how to use this platform",
        max_steps=5,
    )

    # In-depth mode should generate evaluation
    assert report.evaluation is not None
    assert report.evaluation.overall_rating >= 1
    assert report.evaluation.overall_rating <= 5


@pytest.mark.asyncio
async def test_report_generation(agent_config, tmp_path):
    """Test that report generator creates valid output."""
    from tests.ui.investor_journey_agent import InvestorJourneyAgent
    from tests.ui.investor_journey_agent.report_generator import ReportGenerator
    from tests.ui.investor_journey_agent.config import AgentConfig

    # Use temp directory for output
    config = AgentConfig(
        ask_before_action=False,
        max_steps=3,
        output_dir=tmp_path,
    )

    agent = InvestorJourneyAgent(
        persona="investor",
        viewport="iphone_14",
        mode="basic",
        config=config,
    )

    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="Quick look at the app",
        max_steps=3,
    )

    # Generate report
    generator = ReportGenerator()
    report_path = generator.generate(report)

    # Verify files created
    assert report_path.exists()
    assert report_path.suffix == ".md"
    assert (report.output_dir / "summary.json").exists()

    # Verify markdown content
    content = report_path.read_text()
    assert "# Investor Journey Report" in content
    assert "## Summary" in content
    assert report.persona.name in content


@pytest.mark.asyncio
async def test_frustration_detection(agent_config):
    """Test that agent can detect and report frustration."""
    from tests.ui.investor_journey_agent import InvestorJourneyAgent

    # Power user with low patience
    agent = InvestorJourneyAgent(
        persona="power_user",
        viewport="desktop",
        mode="in_depth",
        config=agent_config,
    )

    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="Quickly access advanced AI configuration",
        max_steps=10,
    )

    # Check that frustration was tracked
    frustration_levels = [step.action.frustration_level for step in report.steps]

    # At least one step should have been recorded
    assert len(frustration_levels) >= 1


# Manual test helper (not run by pytest)
async def _manual_test():
    """Run a manual test with visible browser."""
    from tests.ui.investor_journey_agent import InvestorJourneyAgent
    from tests.ui.investor_journey_agent.config import AgentConfig
    from tests.ui.investor_journey_agent.report_generator import ReportGenerator

    config = AgentConfig(
        ask_before_action=False,
        max_steps=15,
    )

    agent = InvestorJourneyAgent(
        persona="investor",
        viewport="iphone_14",
        mode="in_depth",
        config=config,
        headless=False,  # Show browser
    )

    report = await agent.run_journey(
        url="http://localhost:8000",
        goal="Evaluate if this product is worth investing in",
    )

    generator = ReportGenerator()
    report_path = generator.generate(report)

    print(f"\nReport saved to: {report_path}")
    return report


if __name__ == "__main__":
    import asyncio

    asyncio.run(_manual_test())
