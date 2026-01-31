"""
Tests for two-document output in the Investor Journey Agent.

These tests verify that the agent creates two documents:
- journey_log.md - Raw steps, screenshots, thoughts (intermediate)
- analysis_report.md - Human-readable, story format (thorough)
"""

import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock

from tests.ui.investor_journey_agent.llm_brain import (
    JourneyStep,
    Action,
    ActionType,
    JourneyEvaluation,
    PainPoint,
)
from tests.ui.investor_journey_agent.personas import get_persona


class TestJourneyLogGenerator:
    """Tests for the intermediate journey log generator."""

    def test_journey_log_generator_exists(self):
        """Test that JourneyLogGenerator class exists."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        assert JourneyLogGenerator is not None

    def test_generate_log_creates_file(self):
        """Test that generate_log creates journey_log.md file."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = JourneyLogGenerator()

            # Create minimal mock report
            persona = get_persona("investor")
            steps = [
                JourneyStep(
                    step_number=1,
                    url="http://test.com",
                    screenshot_path="/tmp/step1.png",
                    action=Action(
                        action_type=ActionType.CLICK,
                        target="#button",
                        thought="Clicking the button",
                        frustration_level=0.2,
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

            assert log_path.exists()
            assert log_path.name == "journey_log.md"

    def test_journey_log_includes_step_details(self):
        """Test that journey_log.md includes raw step details."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = JourneyLogGenerator()

            persona = get_persona("investor")
            steps = [
                JourneyStep(
                    step_number=1,
                    url="http://test.com/page1",
                    screenshot_path="/tmp/step1.png",
                    action=Action(
                        action_type=ActionType.CLICK,
                        target="#submit-button",
                        thought="I want to submit this form",
                        frustration_level=0.3,
                        confidence=0.7,
                    ),
                    success=True,
                ),
                JourneyStep(
                    step_number=2,
                    url="http://test.com/page2",
                    screenshot_path="/tmp/step2.png",
                    action=Action(
                        action_type=ActionType.WAIT,
                        target="",
                        thought="Waiting for page to load",
                        frustration_level=0.5,
                        confidence=0.5,
                    ),
                    success=False,
                    error_message="Timeout waiting for element",
                ),
            ]

            log_path = generator.generate_log(
                output_dir=output_dir,
                persona=persona,
                goal="Complete registration",
                url="http://test.com",
                viewport_name="iphone_14",
                steps=steps,
                start_time=datetime.now(),
            )

            content = log_path.read_text(encoding="utf-8")

            # Should include step details
            assert "Step 1" in content
            assert "Step 2" in content
            assert "#submit-button" in content
            assert "I want to submit this form" in content
            assert "Timeout waiting for element" in content
            assert "investor" in content.lower()

    def test_journey_log_includes_screenshot_paths(self):
        """Test that journey_log includes screenshot paths for Claude Code."""
        from tests.ui.investor_journey_agent.report_generator import JourneyLogGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = JourneyLogGenerator()

            persona = get_persona("investor")
            steps = [
                JourneyStep(
                    step_number=1,
                    url="http://test.com",
                    screenshot_path=str(output_dir / "screenshots" / "step_001.png"),
                    action=Action(
                        action_type=ActionType.CLICK,
                        target="#button",
                        thought="Test thought",
                        frustration_level=0.1,
                        confidence=0.9,
                    ),
                    success=True,
                )
            ]

            log_path = generator.generate_log(
                output_dir=output_dir,
                persona=persona,
                goal="Test",
                url="http://test.com",
                viewport_name="desktop",
                steps=steps,
                start_time=datetime.now(),
            )

            content = log_path.read_text(encoding="utf-8")

            # Should reference screenshot for Claude Code to read
            assert "screenshot" in content.lower() or "step_001.png" in content


class TestFolderNaming:
    """Tests for folder naming convention."""

    def test_folder_name_has_correct_format(self):
        """Test that folder name follows YYYY-MM-DD_HH-MM_persona_viewport pattern."""
        from tests.ui.investor_journey_agent.report_generator import generate_output_folder_name

        folder_name = generate_output_folder_name(
            persona_name="investor",
            viewport_name="iphone_14",
            timestamp=datetime(2026, 1, 31, 14, 30, 45),
        )

        assert folder_name == "2026-01-31_14-30_investor_iphone_14"

    def test_folder_name_sanitizes_special_characters(self):
        """Test that folder name sanitizes special characters."""
        from tests.ui.investor_journey_agent.report_generator import generate_output_folder_name

        folder_name = generate_output_folder_name(
            persona_name="Confused Teacher",
            viewport_name="iPad Pro",
            timestamp=datetime(2026, 2, 15, 9, 5),
        )

        # Should not have spaces or special chars
        assert " " not in folder_name
        assert folder_name == "2026-02-15_09-05_confused_teacher_ipad_pro"


class TestReportGeneratorUpdates:
    """Tests for updated ReportGenerator with two-document output."""

    def test_report_generator_generates_both_files(self):
        """Test that ReportGenerator creates both journey_log.md and analysis_report.md."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        # Create a mock report
        mock_report = MagicMock()
        mock_report.persona = get_persona("investor")
        mock_report.goal = "Test goal"
        mock_report.url = "http://test.com"
        mock_report.viewport_name = "iphone_14"
        mock_report.start_time = datetime.now()
        mock_report.end_time = datetime.now()
        mock_report.success_rate = 0.8
        mock_report.gave_up = False
        mock_report.evaluation = None
        mock_report.steps = []

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mock_report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(mock_report)

            # Should create journey_log.md (intermediate)
            assert (output_dir / "journey_log.md").exists()

            # Should create analysis_report.md (thorough) OR journey_report.md
            # For now, accept either name as we're transitioning
            has_report = (
                (output_dir / "analysis_report.md").exists()
                or (output_dir / "journey_report.md").exists()
            )
            assert has_report


class TestFileLocationPrinting:
    """Tests for file location printing at end of journey (F4-T4)."""

    def test_report_generator_returns_all_paths(self):
        """Test that ReportGenerator.generate returns a result with all file paths."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator, GenerationResult

        # Create a mock report
        mock_report = MagicMock()
        mock_report.persona = get_persona("investor")
        mock_report.goal = "Test goal"
        mock_report.url = "http://test.com"
        mock_report.viewport_name = "iphone_14"
        mock_report.start_time = datetime.now()
        mock_report.end_time = datetime.now()
        mock_report.success_rate = 0.8
        mock_report.gave_up = False
        mock_report.evaluation = None
        mock_report.steps = []

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mock_report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(mock_report)

            # Result should be a GenerationResult with all paths
            assert isinstance(result, GenerationResult)
            assert result.journey_log_path.exists()
            assert result.journey_report_path.exists()
            assert result.summary_json_path.exists()
            assert result.screenshots_dir.exists() or result.screenshots_dir.parent.exists()

    def test_generation_result_has_printable_summary(self):
        """Test that GenerationResult can print a summary of file locations."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator, GenerationResult

        mock_report = MagicMock()
        mock_report.persona = get_persona("investor")
        mock_report.goal = "Test goal"
        mock_report.url = "http://test.com"
        mock_report.viewport_name = "iphone_14"
        mock_report.start_time = datetime.now()
        mock_report.end_time = datetime.now()
        mock_report.success_rate = 0.8
        mock_report.gave_up = False
        mock_report.evaluation = None
        mock_report.steps = []

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            mock_report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(mock_report)

            # Should have a method to get printable summary
            summary = result.get_file_locations_summary()

            assert "journey_log.md" in summary
            assert "journey_report.md" in summary
            assert "summary.json" in summary
