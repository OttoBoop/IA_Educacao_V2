"""
Report Generator - Creates markdown reports from journey data.

Generates human-readable reports with embedded screenshots
and actionable insights.

Produces two documents:
- journey_log.md - Raw steps for Claude Code analysis (intermediate)
- journey_report.md - Human-readable report (thorough)
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .agent import JourneyReport
    from .llm_brain import JourneyStep, JourneyEvaluation
    from .personas import Persona


@dataclass
class GenerationResult:
    """Result of report generation with all file paths."""

    journey_log_path: Path
    journey_report_path: Path
    summary_json_path: Path
    screenshots_dir: Path
    html_report_path: Optional[Path] = None

    def get_file_locations_summary(self) -> str:
        """Get a printable summary of all generated file locations."""
        output_dir = self.journey_log_path.parent.resolve()
        lines = [
            f"Output folder: {output_dir}",
            "",
            "Generated files:",
            f"  - Journey log:    {self.journey_log_path.resolve()}",
            f"  - Journey report: {self.journey_report_path.resolve()}",
            f"  - Summary JSON:   {self.summary_json_path.resolve()}",
            f"  - Screenshots:    {self.screenshots_dir.resolve()}/",
        ]
        if self.html_report_path:
            lines.append(f"  - HTML report:    {self.html_report_path.resolve()}")
        return "\n".join(lines)


def generate_output_folder_name(
    persona_name: str,
    viewport_name: str,
    timestamp: Optional[datetime] = None,
) -> str:
    """
    Generate folder name following YYYY-MM-DD_HH-MM_persona_viewport pattern.

    Args:
        persona_name: Name of the persona (e.g., "Investor", "Confused Teacher")
        viewport_name: Name of the viewport (e.g., "iphone_14", "iPad Pro")
        timestamp: Timestamp to use. If None, uses current time.

    Returns:
        Sanitized folder name (e.g., "2026-01-31_14-30_investor_iphone_14")
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Format timestamp
    time_str = timestamp.strftime("%Y-%m-%d_%H-%M")

    # Sanitize persona and viewport names
    def sanitize(name: str) -> str:
        # Convert to lowercase, replace spaces with underscores
        name = name.lower().replace(" ", "_")
        # Remove any non-alphanumeric characters except underscore
        name = re.sub(r"[^a-z0-9_]", "", name)
        return name

    persona_clean = sanitize(persona_name)
    viewport_clean = sanitize(viewport_name)

    return f"{time_str}_{persona_clean}_{viewport_clean}"


class JourneyLogGenerator:
    """
    Generates the intermediate journey log for Claude Code analysis.

    Creates journey_log.md with raw step data, suitable for AI analysis.
    """

    def generate_log(
        self,
        output_dir: Path,
        persona: "Persona",
        goal: str,
        url: str,
        viewport_name: str,
        steps: List["JourneyStep"],
        start_time: datetime,
    ) -> Path:
        """
        Generate the journey log file.

        Args:
            output_dir: Directory to save the log
            persona: The persona used for the journey
            goal: The goal of the journey
            url: Starting URL
            viewport_name: Name of the viewport used
            steps: List of journey steps
            start_time: When the journey started

        Returns:
            Path to the generated journey_log.md file
        """
        log_path = output_dir / "journey_log.md"

        lines = []

        # Header
        lines.append("# Journey Log\n")
        lines.append("*Intermediate log for Claude Code analysis*\n")
        lines.append("---\n")

        # Metadata
        lines.append("## Journey Metadata\n")
        lines.append(f"- **Persona:** {persona.name}")
        lines.append(f"- **Goal:** {goal}")
        lines.append(f"- **URL:** {url}")
        lines.append(f"- **Viewport:** {viewport_name}")
        lines.append(f"- **Start Time:** {start_time.isoformat()}")
        lines.append(f"- **Total Steps:** {len(steps)}")
        lines.append("")

        # Persona details
        lines.append("## Persona Profile\n")
        lines.append(f"**{persona.name}:** {persona.description}\n")
        lines.append(f"- Patience: {persona.patience_level}/10")
        lines.append(f"- Tech Savviness: {persona.tech_savviness}/10")
        lines.append("")

        # Steps
        lines.append("## Steps\n")

        for step in steps:
            lines.append(f"### Step {step.step_number}\n")

            # Screenshot reference
            screenshot_name = Path(step.screenshot_path).name
            lines.append(f"**Screenshot:** `{screenshot_name}`\n")

            # URL
            lines.append(f"**URL:** `{step.url}`\n")

            # Action details
            lines.append("**Action:**")
            lines.append(f"- Type: `{step.action.action_type.value}`")
            lines.append(f"- Target: `{step.action.target}`")
            if step.action.text_to_type:
                lines.append(f"- Text: `{step.action.text_to_type}`")
            if step.action.scroll_direction:
                lines.append(f"- Direction: `{step.action.scroll_direction}`")
            lines.append("")

            # Thought process
            lines.append("**Thought:**")
            lines.append(f"> {step.action.thought}\n")

            # Metrics
            lines.append("**Metrics:**")
            lines.append(f"- Frustration: {step.action.frustration_level:.0%}")
            lines.append(f"- Confidence: {step.action.confidence:.0%}")
            lines.append("")

            # Result
            if step.success:
                lines.append("**Result:** SUCCESS\n")
            else:
                lines.append("**Result:** FAILED")
                if step.error_message:
                    lines.append(f"- Error: {step.error_message}")
                lines.append("")

            lines.append("---\n")

        # Footer
        lines.append("\n*End of journey log*")

        # Write file
        log_path.write_text("\n".join(lines), encoding="utf-8")

        return log_path


class ReportGenerator:
    """
    Generates reports from journey data.

    Creates:
    - journey_log.md - Intermediate log for Claude Code analysis
    - journey_report.md - Human-readable markdown report
    - summary.json - Machine-readable data
    - journey_report.html - Self-contained HTML report for sharing
    """

    def __init__(self):
        self._log_generator = JourneyLogGenerator()

    def generate(self, report: "JourneyReport") -> GenerationResult:
        """
        Generate a complete report.

        Args:
            report: JourneyReport from the agent

        Returns:
            GenerationResult with paths to all generated files
        """
        report_path = report.output_dir / "journey_report.md"
        json_path = report.output_dir / "summary.json"
        screenshots_dir = report.output_dir / "screenshots"

        # Generate intermediate journey log first
        log_path = self._log_generator.generate_log(
            output_dir=report.output_dir,
            persona=report.persona,
            goal=report.goal,
            url=report.url,
            viewport_name=report.viewport_name,
            steps=report.steps,
            start_time=report.start_time,
        )

        # Generate markdown
        markdown = self._generate_markdown(report)
        report_path.write_text(markdown, encoding="utf-8")

        # Generate JSON summary
        json_data = self._generate_json(report)
        json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Generate HTML report
        html_path = self._generate_html(report)

        return GenerationResult(
            journey_log_path=log_path,
            journey_report_path=report_path,
            summary_json_path=json_path,
            screenshots_dir=screenshots_dir,
            html_report_path=html_path,
        )

    def _generate_html(self, report: "JourneyReport") -> Path:
        """Generate self-contained HTML report with descriptive filename."""
        from .html_template import HTMLReportRenderer

        renderer = HTMLReportRenderer()
        html = renderer.render(report)

        # Build descriptive filename: persona_viewport_YYYYMMDD_HHMM.html
        persona_clean = re.sub(r"[^a-z0-9_]", "", report.persona.name.lower().replace(" ", "_"))
        viewport_clean = re.sub(r"[^a-z0-9_]", "", report.viewport_name.lower().replace(" ", "_"))
        time_str = report.start_time.strftime("%Y%m%d_%H%M")
        html_filename = f"{persona_clean}_{viewport_clean}_{time_str}.html"

        html_path = report.output_dir / html_filename
        html_path.write_text(html, encoding="utf-8")

        return html_path

    def _generate_markdown(self, report: "JourneyReport") -> str:
        """Generate the markdown report."""
        lines = []

        # Header
        lines.append("# Investor Journey Report\n")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Summary table
        lines.append("## Summary\n")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **Persona** | {report.persona.name} |")
        lines.append(f"| **Goal** | {report.goal} |")
        lines.append(f"| **URL** | {report.url} |")
        lines.append(f"| **Viewport** | {report.viewport_name} |")
        lines.append(f"| **Duration** | {(report.end_time - report.start_time).total_seconds():.1f}s |")
        lines.append(f"| **Total Steps** | {len(report.steps)} |")
        lines.append(f"| **Success Rate** | {report.success_rate:.0%} |")
        lines.append(f"| **Gave Up** | {'Yes' if report.gave_up else 'No'} |")
        lines.append("")

        # Persona details
        lines.append("## Persona Details\n")
        lines.append(f"**{report.persona.name}:** {report.persona.description}\n")
        lines.append(f"- Patience: {report.persona.patience_level}/10")
        lines.append(f"- Tech Savviness: {report.persona.tech_savviness}/10")
        lines.append("")

        # Metrics summary
        if report.evaluation:
            lines.append("## Evaluation Metrics\n")
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Overall Rating | {'*' * int(report.evaluation.overall_rating)}/5 |")
            lines.append(f"| Success Rate | {report.evaluation.success_rate:.0%} |")
            lines.append(f"| Pain Points | {len(report.evaluation.pain_points)} |")
            lines.append(f"| Give-up Moments | {len(report.evaluation.give_up_points)} |")
            lines.append("")

        # Step-by-step journey
        lines.append("## Step-by-Step Journey\n")

        for step in report.steps:
            lines.append(f"### Step {step.step_number}\n")

            # Screenshot (relative path)
            screenshot_rel = Path(step.screenshot_path).name
            lines.append(f"![Step {step.step_number}](screenshots/{screenshot_rel})\n")

            # Step details
            lines.append(f"**URL:** `{step.url}`\n")

            # Thought process (blockquote)
            lines.append("**Thought Process:**")
            lines.append(f"> {step.action.thought}\n")

            # Action and result
            action_emoji = self._get_action_emoji(step.action.action_type.value)
            lines.append(f"**Action:** {action_emoji} `{step.action.action_type.value}` on `{step.action.target}`\n")

            # Frustration meter
            frustration_pct = step.action.frustration_level * 100
            if frustration_pct > 70:
                frustration_emoji = "**HIGH**"
            elif frustration_pct > 40:
                frustration_emoji = "MEDIUM"
            else:
                frustration_emoji = "low"
            lines.append(f"**Frustration:** {frustration_pct:.0f}% ({frustration_emoji})\n")

            # Result
            if step.success:
                lines.append("**Result:** Success\n")
            else:
                lines.append(f"**Result:** Failed - {step.error_message}\n")

            lines.append("---\n")

        # Pain Points section
        if report.evaluation and report.evaluation.pain_points:
            lines.append("## Pain Points\n")
            lines.append("| # | Issue | Severity | Step | Suggestion |")
            lines.append("|---|-------|----------|------|------------|")

            for i, pp in enumerate(report.evaluation.pain_points, 1):
                severity_emoji = {"high": "**HIGH**", "medium": "MEDIUM", "low": "low"}.get(pp.severity, pp.severity)
                suggestion = pp.suggestion or "-"
                lines.append(f"| {i} | {pp.description} | {severity_emoji} | {pp.step_number} | {suggestion} |")

            lines.append("")

        # Suggestions section
        if report.evaluation and report.evaluation.suggestions:
            lines.append("## Recommendations\n")
            for i, suggestion in enumerate(report.evaluation.suggestions, 1):
                lines.append(f"{i}. {suggestion}")
            lines.append("")

        # Footer
        lines.append("---\n")
        lines.append("*Generated by Investor Journey Agent - Prova AI*")

        return "\n".join(lines)

    def _generate_json(self, report: "JourneyReport") -> dict:
        """Generate JSON summary."""
        return {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "persona": report.persona.name,
                "goal": report.goal,
                "url": report.url,
                "viewport": report.viewport_name,
            },
            "summary": {
                "total_steps": len(report.steps),
                "success_rate": report.success_rate,
                "gave_up": report.gave_up,
                "duration_seconds": (report.end_time - report.start_time).total_seconds(),
            },
            "evaluation": {
                "overall_rating": report.evaluation.overall_rating if report.evaluation else None,
                "success_rate": report.evaluation.success_rate if report.evaluation else None,
                "pain_points_count": len(report.evaluation.pain_points) if report.evaluation else 0,
                "give_up_points": report.evaluation.give_up_points if report.evaluation else [],
            } if report.evaluation else None,
            "steps": [
                {
                    "step_number": step.step_number,
                    "url": step.url,
                    "action_type": step.action.action_type.value,
                    "target": step.action.target,
                    "thought": step.action.thought,
                    "frustration_level": step.action.frustration_level,
                    "confidence": step.action.confidence,
                    "success": step.success,
                    "error": step.error_message,
                }
                for step in report.steps
            ],
            "pain_points": [
                {
                    "description": pp.description,
                    "severity": pp.severity,
                    "step_number": pp.step_number,
                    "suggestion": pp.suggestion,
                }
                for pp in (report.evaluation.pain_points if report.evaluation else [])
            ],
            "suggestions": report.evaluation.suggestions if report.evaluation else [],
        }

    def _get_action_emoji(self, action_type: str) -> str:
        """Get emoji for action type."""
        emojis = {
            "click": "click",
            "type": "type",
            "scroll": "scroll",
            "wait": "wait",
            "give_up": "GAVE UP",
            "done": "DONE",
        }
        return emojis.get(action_type, action_type)
