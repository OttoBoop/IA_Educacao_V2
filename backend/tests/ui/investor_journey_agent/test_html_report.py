"""
Tests for HTML report generation (Feature 1: HTML Report Template).

Tests cover:
- F1-T1: Base HTML template structure (doctype, head, body, inline CSS/JS)
- F1-T2: Base64 screenshot embedding
- F1-T3: Executive summary section
- F1-T4: Visual timeline with frustration gradient
- F1-T5: Step detail cards
- F1-T6: Interactive JS (lightbox, collapsible)
- F1-T7: Pain points & recommendations section
"""

import base64
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


# ============================================================
# Test Fixtures
# ============================================================


def _make_step(
    step_number: int = 1,
    url: str = "http://test.com",
    screenshot_path: str = "/tmp/step_01.png",
    action_type: ActionType = ActionType.CLICK,
    target: str = "#button",
    thought: str = "I want to click this button",
    frustration: float = 0.2,
    confidence: float = 0.8,
    success: bool = True,
    error: str = None,
) -> JourneyStep:
    """Helper to create a JourneyStep for tests."""
    return JourneyStep(
        step_number=step_number,
        url=url,
        screenshot_path=screenshot_path,
        action=Action(
            action_type=action_type,
            target=target,
            thought=thought,
            frustration_level=frustration,
            confidence=confidence,
        ),
        success=success,
        error_message=error,
    )


def _make_mock_report(
    steps=None,
    evaluation=None,
    persona_name="investor",
    gave_up=False,
):
    """Helper to create a mock JourneyReport."""
    report = MagicMock()
    report.persona = get_persona(persona_name)
    report.goal = "Explore the application"
    report.url = "https://ia-educacao-v2.onrender.com"
    report.viewport_name = "iphone_14"
    report.start_time = datetime(2026, 2, 8, 21, 0, 0)
    report.end_time = datetime(2026, 2, 8, 21, 3, 30)
    report.steps = steps or [_make_step()]
    report.success_rate = sum(1 for s in report.steps if s.success) / max(len(report.steps), 1)
    report.gave_up = gave_up
    report.evaluation = evaluation
    return report


def _create_fake_screenshot(path: Path, width: int = 10, height: int = 10) -> Path:
    """Create a minimal valid PNG file for testing."""
    # Minimal valid 1x1 PNG (67 bytes)
    import struct
    import zlib

    def _minimal_png(w, h):
        """Generate a minimal valid PNG."""

        def chunk(chunk_type, data):
            c = chunk_type + data
            crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
            return struct.pack(">I", len(data)) + c + crc

        header = b"\x89PNG\r\n\x1a\n"
        ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        # Raw image data: filter byte + RGB pixels per row
        raw = b""
        for _ in range(h):
            raw += b"\x00" + b"\xff\x00\x00" * w  # Red pixels
        idat = chunk(b"IDAT", zlib.compress(raw))
        iend = chunk(b"IEND", b"")
        return header + ihdr + idat + iend

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_minimal_png(width, height))
    return path


# ============================================================
# F1-T1: Base HTML Template Structure
# ============================================================


class TestHTMLTemplateStructure:
    """F1-T1: Base HTML/CSS/JS template must produce valid self-contained HTML."""

    def test_html_template_module_exists(self):
        """html_template.py module should be importable."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        assert HTMLReportRenderer is not None

    def test_render_produces_html_with_doctype(self):
        """Rendered HTML should start with <!DOCTYPE html>."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        report = _make_mock_report()
        html = renderer.render(report)

        assert html.strip().startswith("<!DOCTYPE html>")

    def test_render_has_head_and_body(self):
        """Rendered HTML should have <head> and <body> tags."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        assert "<head>" in html
        assert "</head>" in html
        assert "<body" in html
        assert "</body>" in html

    def test_render_has_inline_css(self):
        """CSS should be inline in a <style> tag, not an external file."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        assert "<style>" in html
        assert "</style>" in html

    def test_render_is_self_contained(self):
        """HTML should not reference any external files (no external src/href)."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer
        import re

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        # Should not have external stylesheet links
        external_links = re.findall(r'<link[^>]+href=["\']https?://', html)
        assert len(external_links) == 0, f"Found external links: {external_links}"

        # Should not have external script sources
        external_scripts = re.findall(r'<script[^>]+src=["\']https?://', html)
        assert len(external_scripts) == 0, f"Found external scripts: {external_scripts}"

    def test_render_has_dark_theme(self):
        """CSS should include dark theme styling."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        # Dark theme: background should be dark, text should be light
        assert "background" in html.lower()
        # Check for dark color values (common dark theme patterns)
        assert any(c in html for c in ["#1a", "#0d", "#12", "#18", "#1e", "#11", "#0f", "rgb(1"])

    def test_render_has_title_with_persona(self):
        """HTML <title> should include the persona name."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report(persona_name="investor"))

        assert "<title>" in html
        assert "Investor" in html


# ============================================================
# F1-T2: Base64 Screenshot Embedding
# ============================================================


class TestBase64Embedding:
    """F1-T2: Screenshots should be embedded as base64 data URIs."""

    def test_encode_screenshot_to_base64(self):
        """Should convert a PNG file to a base64 data URI string."""
        from tests.ui.investor_journey_agent.html_template import encode_screenshot_base64

        with TemporaryDirectory() as tmpdir:
            png_path = Path(tmpdir) / "test.png"
            _create_fake_screenshot(png_path)

            data_uri = encode_screenshot_base64(png_path)

            assert data_uri.startswith("data:image/png;base64,")
            # The base64 part should be valid
            b64_part = data_uri.split(",", 1)[1]
            decoded = base64.b64decode(b64_part)
            assert decoded[:4] == b"\x89PNG"

    def test_missing_screenshot_returns_placeholder(self):
        """Should return a placeholder when screenshot file doesn't exist."""
        from tests.ui.investor_journey_agent.html_template import encode_screenshot_base64

        result = encode_screenshot_base64(Path("/nonexistent/path.png"))

        # Should return something usable, not crash
        assert result is not None
        assert isinstance(result, str)

    def test_html_embeds_screenshots_as_base64(self):
        """Full HTML render should embed screenshots as data URIs."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        with TemporaryDirectory() as tmpdir:
            screenshot_path = Path(tmpdir) / "screenshots" / "step_01.png"
            _create_fake_screenshot(screenshot_path)

            step = _make_step(screenshot_path=str(screenshot_path))
            report = _make_mock_report(steps=[step])

            renderer = HTMLReportRenderer()
            html = renderer.render(report)

            assert "data:image/png;base64," in html


# ============================================================
# F1-T3: Executive Summary Section
# ============================================================


class TestExecutiveSummary:
    """F1-T3: Report should have an executive summary with key metrics."""

    def test_summary_shows_persona_name(self):
        """Summary should display the persona name."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report(persona_name="investor"))

        assert "Investor" in html

    def test_summary_shows_success_rate(self):
        """Summary should display the success rate percentage."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        steps = [
            _make_step(step_number=1, success=True),
            _make_step(step_number=2, success=False, error="Timeout"),
            _make_step(step_number=3, success=True),
        ]
        report = _make_mock_report(steps=steps)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "67%" in html  # 2/3

    def test_summary_shows_total_steps(self):
        """Summary should display the total step count."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        steps = [_make_step(step_number=i) for i in range(1, 6)]
        report = _make_mock_report(steps=steps)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert ">5<" in html or ">5 " in html or "5 steps" in html.lower() or '"5"' in html

    def test_summary_shows_duration(self):
        """Summary should display the journey duration."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())  # 3m30s duration

        assert "3" in html and ("30" in html or "210" in html or "min" in html.lower())

    def test_summary_shows_gave_up_status(self):
        """Summary should indicate if the persona gave up."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report(gave_up=True))

        assert "gave up" in html.lower() or "abandoned" in html.lower() or "give up" in html.lower()

    def test_summary_shows_persona_details(self):
        """Summary should show patience and tech savviness."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report(persona_name="investor"))

        # Investor has patience 3/10 and tech 8/10
        assert "3" in html  # patience
        assert "8" in html  # tech savviness


# ============================================================
# F1-T4: Visual Timeline with Frustration Gradient
# ============================================================


class TestFrustrationTimeline:
    """F1-T4: Visual timeline should show frustration progression."""

    def test_timeline_has_color_coded_steps(self):
        """Each step in the timeline should have a color based on frustration."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        steps = [
            _make_step(step_number=1, frustration=0.2),  # Low = green
            _make_step(step_number=2, frustration=0.5),  # Med = yellow
            _make_step(step_number=3, frustration=0.9),  # High = red
        ]
        report = _make_mock_report(steps=steps)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        # Should contain color indicators for different frustration levels
        # At minimum, there should be distinct visual treatment
        assert "timeline" in html.lower() or "progress" in html.lower()

    def test_frustration_color_mapping(self):
        """Frustration levels should map to correct colors."""
        from tests.ui.investor_journey_agent.html_template import frustration_to_color

        # Low (0-40%) = greenish
        low_color = frustration_to_color(0.2)
        assert low_color is not None

        # Medium (40-70%) = yellowish/orange
        mid_color = frustration_to_color(0.5)
        assert mid_color != low_color

        # High (70%+) = reddish
        high_color = frustration_to_color(0.9)
        assert high_color != mid_color


# ============================================================
# F1-T5: Step Detail Cards
# ============================================================


class TestStepDetailCards:
    """F1-T5: Each step should render as a detailed card."""

    def test_step_card_shows_thought_process(self):
        """Step card should include the persona's thought process."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        step = _make_step(thought="I want to find my grades but the sidebar is confusing")
        report = _make_mock_report(steps=[step])

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "sidebar is confusing" in html

    def test_step_card_shows_action_type(self):
        """Step card should show what action was taken."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        step = _make_step(action_type=ActionType.CLICK, target="#submit-btn")
        report = _make_mock_report(steps=[step])

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "click" in html.lower()
        assert "#submit-btn" in html

    def test_step_card_shows_success_or_failure(self):
        """Step card should indicate if the action succeeded or failed."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        steps = [
            _make_step(step_number=1, success=True),
            _make_step(step_number=2, success=False, error="Element not found"),
        ]
        report = _make_mock_report(steps=steps)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "success" in html.lower() or "pass" in html.lower()
        assert "fail" in html.lower() or "error" in html.lower()
        assert "Element not found" in html

    def test_step_card_shows_frustration_level(self):
        """Step card should display the frustration percentage."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        step = _make_step(frustration=0.65)
        report = _make_mock_report(steps=[step])

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "65%" in html

    def test_step_card_shows_url(self):
        """Step card should show the URL at that step."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        step = _make_step(url="https://ia-educacao-v2.onrender.com/chat")
        report = _make_mock_report(steps=[step])

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "ia-educacao-v2.onrender.com/chat" in html

    def test_all_steps_rendered(self):
        """All steps from the journey should appear in the HTML."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        steps = [_make_step(step_number=i, thought=f"Thought for step {i}") for i in range(1, 8)]
        report = _make_mock_report(steps=steps)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        for i in range(1, 8):
            assert f"Thought for step {i}" in html


# ============================================================
# F1-T6: Interactive JS (Lightbox, Collapsible)
# ============================================================


class TestInteractiveJS:
    """F1-T6: HTML should have JS for screenshot lightbox and collapsible thoughts."""

    def test_html_has_script_tag(self):
        """HTML should include a <script> block."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        assert "<script>" in html
        assert "</script>" in html

    def test_lightbox_markup_exists(self):
        """HTML should have lightbox container markup for screenshot expansion."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        assert "lightbox" in html.lower()

    def test_collapsible_thought_markup(self):
        """Thought sections should have collapsible markup (details/summary or similar)."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(_make_mock_report())

        # Either <details>/<summary> or custom collapsible with toggle class
        has_details = "<details" in html.lower()
        has_toggle = "collapsible" in html.lower() or "toggle" in html.lower() or "expandable" in html.lower()
        assert has_details or has_toggle


# ============================================================
# F1-T7: Pain Points & Recommendations
# ============================================================


class TestPainPointsSection:
    """F1-T7: Pain points and recommendations from evaluation."""

    def test_pain_points_rendered_when_present(self):
        """Pain points should appear in HTML when evaluation has them."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        evaluation = JourneyEvaluation(
            success_rate=0.6,
            total_steps=10,
            give_up_points=[7],
            pain_points=[
                PainPoint(
                    description="Sidebar not accessible on mobile",
                    severity="high",
                    step_number=3,
                    suggestion="Fix mobile responsive layout",
                ),
                PainPoint(
                    description="Welcome modal blocks interaction",
                    severity="medium",
                    step_number=5,
                    suggestion="Add visible close button",
                ),
            ],
            suggestions=["Improve mobile nav", "Fix modal dismissal"],
            overall_rating=2.5,
        )
        report = _make_mock_report(evaluation=evaluation)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "Sidebar not accessible" in html
        assert "Welcome modal blocks" in html
        assert "high" in html.lower()

    def test_recommendations_rendered_when_present(self):
        """Recommendations should appear in HTML when evaluation has them."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        evaluation = JourneyEvaluation(
            success_rate=0.8,
            total_steps=5,
            give_up_points=[],
            pain_points=[],
            suggestions=["Add onboarding tutorial", "Improve loading speed"],
            overall_rating=4.0,
        )
        report = _make_mock_report(evaluation=evaluation)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "onboarding tutorial" in html
        assert "loading speed" in html

    def test_no_pain_points_section_when_no_evaluation(self):
        """When there's no evaluation, pain points section should not crash."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        report = _make_mock_report(evaluation=None)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        # Should still produce valid HTML without crashing
        assert "<!DOCTYPE html>" in html

    def test_overall_rating_displayed(self):
        """Overall rating should be displayed when evaluation exists."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        evaluation = JourneyEvaluation(
            success_rate=0.7,
            total_steps=10,
            give_up_points=[],
            pain_points=[],
            suggestions=[],
            overall_rating=3.5,
        )
        report = _make_mock_report(evaluation=evaluation)

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "3.5" in html or "3,5" in html


# ============================================================
# F2: Report Generator Integration
# ============================================================


class TestReportGeneratorHTML:
    """F2: ReportGenerator should produce HTML alongside markdown/JSON."""

    def test_generate_creates_html_file(self):
        """F2-T1/T3: generate() should create journey_report.html."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            # Create screenshots dir (agent normally does this)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(report)

            html_files = list(output_dir.glob("*.html"))
            assert len(html_files) == 1, f"Expected 1 HTML file, found {len(html_files)}"
            assert html_files[0].stat().st_size > 0

    def test_generation_result_has_html_path(self):
        """F2-T2: GenerationResult should include html_report_path."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(report)

            assert hasattr(result, "html_report_path")
            assert result.html_report_path is not None
            assert result.html_report_path.exists()
            assert result.html_report_path.suffix == ".html"

    def test_html_file_is_self_contained(self):
        """HTML file produced by generator should be self-contained."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator
        import re

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(report)

            html = result.html_report_path.read_text(encoding="utf-8")
            assert "<!DOCTYPE html>" in html
            external_links = re.findall(r'<link[^>]+href=["\']https?://', html)
            assert len(external_links) == 0

    def test_existing_outputs_still_generated(self):
        """F2 regression: markdown, JSON, and log still produced."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(report)

            assert result.journey_log_path.exists()
            assert result.journey_report_path.exists()
            assert result.summary_json_path.exists()

    def test_file_locations_summary_includes_html(self):
        """F2-T4: get_file_locations_summary() should mention HTML report."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(report)

            summary = result.get_file_locations_summary()
            assert ".html" in summary or "html" in summary.lower()

    def test_html_filename_contains_persona(self):
        """HTML filename should contain the persona name."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report(persona_name="investor")
            report.output_dir = output_dir

            generator = ReportGenerator()
            result = generator.generate(report)

            filename = result.html_report_path.name
            assert "investor" in filename.lower(), (
                f"HTML filename '{filename}' should contain persona name 'investor'"
            )

    def test_html_filename_contains_viewport(self):
        """HTML filename should contain the viewport/device name."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir
            report.viewport_name = "iphone_14"

            generator = ReportGenerator()
            result = generator.generate(report)

            filename = result.html_report_path.name
            assert "iphone_14" in filename.lower(), (
                f"HTML filename '{filename}' should contain viewport 'iphone_14'"
            )

    def test_html_filename_contains_timestamp(self):
        """HTML filename should contain a timestamp for uniqueness."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report()
            report.output_dir = output_dir
            # start_time is 2026-02-08 21:00:00

            generator = ReportGenerator()
            result = generator.generate(report)

            filename = result.html_report_path.name
            assert "2026" in filename, (
                f"HTML filename '{filename}' should contain year from timestamp"
            )

    def test_html_filename_persona_before_timestamp(self):
        """Persona and device should come before the timestamp in filename."""
        from tests.ui.investor_journey_agent.report_generator import ReportGenerator

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            (output_dir / "screenshots").mkdir()

            report = _make_mock_report(persona_name="investor")
            report.output_dir = output_dir
            report.viewport_name = "iphone_14"

            generator = ReportGenerator()
            result = generator.generate(report)

            filename = result.html_report_path.stem  # without .html
            persona_pos = filename.lower().find("investor")
            timestamp_pos = filename.find("2026")
            assert persona_pos < timestamp_pos, (
                f"In filename '{filename}', persona should come before timestamp"
            )


# ============================================================
# F3: Progress Narration
# ============================================================


class TestProgressNarrator:
    """F3: Periodic progress summaries during agent runs."""

    def test_narrator_module_exists(self):
        """ProgressNarrator class should be importable."""
        from tests.ui.investor_journey_agent.progress_narrator import ProgressNarrator

        assert ProgressNarrator is not None

    def test_narrator_produces_summary_at_interval(self):
        """Narrator should produce a summary string every N steps."""
        from tests.ui.investor_journey_agent.progress_narrator import ProgressNarrator

        narrator = ProgressNarrator(interval=3)

        # Steps 1 and 2 should return None (not at interval)
        assert narrator.on_step(_make_step(step_number=1, frustration=0.1, success=True)) is None
        assert narrator.on_step(_make_step(step_number=2, frustration=0.3, success=False, error="Timeout")) is None

        # Step 3 should return a summary
        result = narrator.on_step(_make_step(step_number=3, frustration=0.5, success=True))
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_narrator_summary_contains_key_info(self):
        """Summary should include step number, frustration, and success rate."""
        from tests.ui.investor_journey_agent.progress_narrator import ProgressNarrator

        narrator = ProgressNarrator(interval=2)
        narrator.on_step(_make_step(step_number=1, frustration=0.2, success=True))
        summary = narrator.on_step(_make_step(step_number=2, frustration=0.6, success=False, error="err"))

        assert summary is not None
        # Should mention step number or progress
        assert "2" in summary
        # Should mention frustration trend
        assert "frustration" in summary.lower() or "%" in summary
        # Should mention success rate
        assert "50%" in summary or "1/2" in summary or "success" in summary.lower()

    def test_narrator_no_summary_between_intervals(self):
        """Steps between intervals should not produce a summary."""
        from tests.ui.investor_journey_agent.progress_narrator import ProgressNarrator

        narrator = ProgressNarrator(interval=5)

        for i in range(1, 5):
            result = narrator.on_step(_make_step(step_number=i))
            assert result is None, f"Step {i} should not produce summary"

    def test_narrator_final_summary(self):
        """Narrator should have a method to produce a final summary."""
        from tests.ui.investor_journey_agent.progress_narrator import ProgressNarrator

        narrator = ProgressNarrator(interval=10)
        narrator.on_step(_make_step(step_number=1, frustration=0.1, success=True))
        narrator.on_step(_make_step(step_number=2, frustration=0.8, success=False, error="fail"))

        final = narrator.final_summary()
        assert final is not None
        assert isinstance(final, str)
        assert len(final) > 0


# ============================================================
# F4: Error Resilience - Incomplete Reports
# ============================================================


class TestIncompleteReports:
    """F4: HTML reports should indicate when journey ended early."""

    def test_incomplete_banner_shown_when_flagged(self):
        """HTML should show 'Incomplete' banner when report is marked incomplete."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        report = _make_mock_report()
        report.incomplete = True
        report.incomplete_reason = "Network timeout after step 3"

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "incomplete" in html.lower()
        assert "Network timeout" in html

    def test_no_incomplete_banner_for_normal_reports(self):
        """Normal reports should not show incomplete banner."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        report = _make_mock_report()
        report.incomplete = False

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        # Should not have the incomplete warning section
        # (the word "incomplete" might appear elsewhere, check for the banner specifically)
        assert "journey-incomplete" not in html

    def test_partial_report_preserves_completed_steps(self):
        """Even incomplete reports should show all steps that were completed."""
        from tests.ui.investor_journey_agent.html_template import HTMLReportRenderer

        steps = [
            _make_step(step_number=1, thought="First action", success=True),
            _make_step(step_number=2, thought="Second action", success=True),
            _make_step(step_number=3, thought="Third action failed", success=False, error="Connection lost"),
        ]
        report = _make_mock_report(steps=steps)
        report.incomplete = True
        report.incomplete_reason = "Connection lost"

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        assert "First action" in html
        assert "Second action" in html
        assert "Third action failed" in html


# ============================================================
# F3-T2/T3: Narrator Integration in Agent + CLI
# ============================================================


class TestNarratorIntegration:
    """F3-T2/T3: Narrator wired into agent and CLI."""

    def test_agent_accepts_narrator_parameter(self):
        """Agent should accept an optional narrator parameter."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.progress_narrator import ProgressNarrator

        narrator = ProgressNarrator(interval=3)
        # Should not raise - narrator is accepted as a parameter
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            narrator=narrator,
        )
        assert agent.narrator is narrator

    def test_agent_narrator_defaults_to_none(self):
        """Agent should work without a narrator (backwards compatible)."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent

        agent = InvestorJourneyAgent(persona="investor")
        assert agent.narrator is None

    def test_cli_has_narrate_flag(self):
        """CLI parser should have --no-narrate flag."""
        from tests.ui.investor_journey_agent.__main__ import parse_args
        import sys

        # Simulate --no-narrate flag
        old_argv = sys.argv
        try:
            sys.argv = ["prog", "--no-narrate"]
            args = parse_args()
            assert hasattr(args, "no_narrate")
            assert args.no_narrate is True
        finally:
            sys.argv = old_argv

    def test_cli_narrate_defaults_to_false(self):
        """--no-narrate should default to False (narration ON by default)."""
        from tests.ui.investor_journey_agent.__main__ import parse_args
        import sys

        old_argv = sys.argv
        try:
            sys.argv = ["prog"]
            args = parse_args()
            assert hasattr(args, "no_narrate")
            assert args.no_narrate is False
        finally:
            sys.argv = old_argv


# ============================================================
# F4-T1/T2: Error Resilience in Agent
# ============================================================


class TestAgentErrorResilience:
    """F4-T1/T2: Agent handles errors gracefully with partial reports."""

    def test_journey_report_has_incomplete_field(self):
        """JourneyReport should have incomplete and incomplete_reason fields."""
        from tests.ui.investor_journey_agent.agent import JourneyReport
        from tests.ui.investor_journey_agent.personas import get_persona

        report = JourneyReport(
            persona=get_persona("investor"),
            goal="test",
            url="http://test.com",
            viewport_name="iphone_14",
            start_time=datetime.now(),
            end_time=datetime.now(),
            steps=[],
            evaluation=None,
            output_dir=Path("/tmp"),
            incomplete=True,
            incomplete_reason="LLM API timeout",
        )

        assert report.incomplete is True
        assert report.incomplete_reason == "LLM API timeout"

    def test_journey_report_incomplete_defaults_to_false(self):
        """JourneyReport incomplete should default to False."""
        from tests.ui.investor_journey_agent.agent import JourneyReport
        from tests.ui.investor_journey_agent.personas import get_persona

        report = JourneyReport(
            persona=get_persona("investor"),
            goal="test",
            url="http://test.com",
            viewport_name="iphone_14",
            start_time=datetime.now(),
            end_time=datetime.now(),
            steps=[],
            evaluation=None,
            output_dir=Path("/tmp"),
        )

        assert report.incomplete is False
        assert report.incomplete_reason is None
