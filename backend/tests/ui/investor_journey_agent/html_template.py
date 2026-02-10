"""
HTML Report Template Engine for Investor Journey Agent.

Generates self-contained HTML reports with:
- Base64 embedded screenshots
- Dark theme CSS
- Visual frustration timeline
- Interactive lightbox and collapsible sections
- Executive summary with key metrics
"""

import base64
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .agent import JourneyReport
    from .llm_brain import JourneyStep, JourneyEvaluation, PainPoint
    from .personas import Persona


def encode_screenshot_base64(path: Path) -> str:
    """
    Encode a screenshot PNG file as a base64 data URI.

    Args:
        path: Path to the PNG file.

    Returns:
        Data URI string (data:image/png;base64,...) or placeholder if file missing.
    """
    try:
        data = Path(path).read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except (FileNotFoundError, OSError):
        # Return a 1x1 transparent PNG placeholder
        placeholder = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
            "2mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        return f"data:image/png;base64,{placeholder}"


def frustration_to_color(level: float) -> str:
    """
    Map frustration level (0.0-1.0) to a CSS color.

    0.0-0.4 = green shades
    0.4-0.7 = yellow/orange shades
    0.7-1.0 = red shades

    Args:
        level: Frustration level between 0.0 and 1.0.

    Returns:
        CSS color string (hex).
    """
    level = max(0.0, min(1.0, level))

    if level <= 0.4:
        # Green to yellow-green
        r = int(76 + (level / 0.4) * (230 - 76))
        g = 175
        b = 80
        return f"#{r:02x}{g:02x}{b:02x}"
    elif level <= 0.7:
        # Yellow to orange
        t = (level - 0.4) / 0.3
        r = 230
        g = int(175 - t * 85)
        b = int(80 - t * 40)
        return f"#{r:02x}{g:02x}{b:02x}"
    else:
        # Orange to red
        t = (level - 0.7) / 0.3
        r = int(230 + t * 25)
        g = int(90 - t * 50)
        b = int(40 - t * 10)
        return f"#{min(r, 255):02x}{max(g, 0):02x}{max(b, 0):02x}"


def _format_duration(seconds: float) -> str:
    """Format seconds into a human-readable duration string."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


class HTMLReportRenderer:
    """
    Renders a JourneyReport as a self-contained HTML file.

    All CSS is inline in <style> tags, all JS in <script> tags,
    and all screenshots embedded as base64 data URIs.
    """

    def render(self, report: "JourneyReport") -> str:
        """
        Render a complete HTML report.

        Args:
            report: The JourneyReport to render.

        Returns:
            Complete HTML string.
        """
        persona = report.persona
        steps = report.steps
        evaluation = report.evaluation
        duration = (report.end_time - report.start_time).total_seconds()
        success_rate = report.success_rate

        # Store persona name for step card rendering
        self._current_persona_name = persona.name

        # Check for incomplete flag (set when journey ends early due to errors)
        is_incomplete = getattr(report, "incomplete", False)
        incomplete_reason = getattr(report, "incomplete_reason", None)

        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Journey Report - {persona.name} | Prova AI</title>
    {self._render_css()}
</head>
<body>
    <div class="container">
        {self._render_incomplete_banner(is_incomplete, incomplete_reason)}
        {self._render_header(persona, report)}
        {self._render_summary(report, duration, success_rate)}
        {self._render_timeline(steps)}
        {self._render_steps(steps)}
        {self._render_pain_points(evaluation)}
        {self._render_recommendations(evaluation)}
        {self._render_footer()}
    </div>
    {self._render_lightbox()}
    <button class="back-to-top" id="back-to-top" onclick="scrollToTop()" title="Back to top">&uarr;</button>
    {self._render_js()}
</body>
</html>"""

    def _render_incomplete_banner(
        self, is_incomplete: bool, reason: Optional[str]
    ) -> str:
        """Render a warning banner for incomplete journeys."""
        if not is_incomplete:
            return ""

        reason_html = (
            f"<p>{_escape_html(reason)}</p>" if reason else ""
        )

        return f"""
    <div class="journey-incomplete" style="
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    ">
        <strong style="color: var(--accent-red); font-size: 1rem;">
            Incomplete Journey
        </strong>
        {reason_html}
    </div>"""

    def _render_css(self) -> str:
        """Render inline CSS for dark theme."""
        return """<style>
    :root {
        --bg-primary: #0f1117;
        --bg-secondary: #1a1d27;
        --bg-card: #1e2130;
        --bg-hover: #252838;
        --text-primary: #e4e6eb;
        --text-secondary: #9ca3af;
        --text-muted: #6b7280;
        --accent-blue: #3b82f6;
        --accent-green: #4caf50;
        --accent-red: #ef4444;
        --accent-yellow: #f59e0b;
        --accent-orange: #f97316;
        --border: #2d3148;
        --shadow: rgba(0, 0, 0, 0.4);
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: var(--bg-primary);
        color: var(--text-primary);
        line-height: 1.6;
    }

    .container {
        max-width: 900px;
        margin: 0 auto;
        padding: 2rem 1.5rem;
    }

    /* Header */
    .header {
        text-align: center;
        margin-bottom: 2.5rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
    }
    .header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, var(--accent-blue), #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .header .subtitle {
        color: var(--text-secondary);
        font-size: 0.95rem;
    }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-gave-up {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-completed {
        background: rgba(76, 175, 80, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(76, 175, 80, 0.3);
    }

    /* Summary Cards */
    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .summary-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .summary-card .label {
        font-size: 0.8rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.3rem;
    }
    .summary-card .value {
        font-size: 1.6rem;
        font-weight: 700;
    }
    .summary-card .detail {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.2rem;
    }

    /* Persona Card */
    .persona-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 2rem;
    }
    .persona-card h3 {
        color: var(--accent-blue);
        margin-bottom: 0.5rem;
    }
    .persona-card .description {
        color: var(--text-secondary);
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    .persona-stats {
        display: flex;
        gap: 2rem;
    }
    .stat-bar {
        flex: 1;
    }
    .stat-bar .stat-label {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.3rem;
    }
    .stat-bar .bar {
        height: 6px;
        background: var(--bg-hover);
        border-radius: 3px;
        overflow: hidden;
    }
    .stat-bar .bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s;
    }
    .stat-bar .stat-value {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.2rem;
    }

    /* Timeline */
    .timeline-section {
        margin-bottom: 2rem;
        position: sticky;
        top: 0;
        z-index: 100;
        background: var(--bg-primary);
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
    }
    .timeline-section h2 {
        font-size: 1.2rem;
        margin-bottom: 1rem;
        color: var(--text-primary);
    }
    .timeline-bar {
        display: flex;
        gap: 3px;
        height: 32px;
        margin-bottom: 0.5rem;
    }
    .timeline-step {
        flex: 1;
        border-radius: 4px;
        cursor: pointer;
        position: relative;
        transition: transform 0.15s, opacity 0.15s;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: 600;
        color: rgba(255,255,255,0.8);
    }
    .timeline-step:hover {
        transform: scaleY(1.3);
        opacity: 0.85;
    }
    .timeline-legend {
        display: flex;
        justify-content: space-between;
        font-size: 0.75rem;
        color: var(--text-muted);
    }

    /* Step Cards */
    .steps-section h2 {
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    .step-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        margin-bottom: 1rem;
        overflow: hidden;
    }
    .step-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.2rem;
        border-bottom: 1px solid var(--border);
    }
    .step-number {
        font-weight: 700;
        font-size: 0.9rem;
    }
    .step-meta {
        display: flex;
        align-items: center;
        gap: 0.8rem;
        font-size: 0.8rem;
    }
    .step-status {
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .step-status.success {
        background: rgba(76, 175, 80, 0.15);
        color: var(--accent-green);
    }
    .step-status.failed {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
    }
    .frustration-badge {
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .step-body {
        padding: 1.2rem;
    }
    .step-url {
        font-size: 0.8rem;
        color: var(--text-muted);
        margin-bottom: 0.8rem;
        word-break: break-all;
    }
    .step-action {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
        padding: 0.6rem 0.8rem;
        background: var(--bg-hover);
        border-radius: 8px;
        font-size: 0.85rem;
    }
    .action-type {
        font-weight: 600;
        color: var(--accent-blue);
        text-transform: uppercase;
        font-size: 0.75rem;
    }
    .action-target {
        color: var(--text-secondary);
        font-family: 'Menlo', 'Consolas', monospace;
        font-size: 0.8rem;
    }
    .step-error {
        padding: 0.6rem 0.8rem;
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.2);
        border-radius: 8px;
        color: var(--accent-red);
        font-size: 0.85rem;
        margin-bottom: 1rem;
    }

    .step-screenshot {
        margin-bottom: 1rem;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border);
        cursor: pointer;
    }
    .step-screenshot img {
        width: 100%;
        display: block;
    }

    /* Pain Points */
    .pain-points-section, .recommendations-section {
        margin-bottom: 2rem;
    }
    .pain-points-section h2, .recommendations-section h2 {
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    .pain-point {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid;
    }
    .pain-point.severity-high {
        border-left-color: var(--accent-red);
    }
    .pain-point.severity-medium {
        border-left-color: var(--accent-orange);
    }
    .pain-point.severity-low {
        border-left-color: var(--accent-yellow);
    }
    .pain-point .pp-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.4rem;
    }
    .pain-point .pp-description {
        font-size: 0.9rem;
    }
    .pain-point .pp-severity {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        padding: 0.1rem 0.5rem;
        border-radius: 6px;
    }
    .pain-point .pp-suggestion {
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 0.4rem;
    }

    .recommendation-item {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        font-size: 0.9rem;
    }
    .recommendation-item .rec-number {
        color: var(--accent-blue);
        font-weight: 700;
        margin-right: 0.5rem;
    }

    /* Rating */
    .rating-section {
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .rating-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--accent-blue);
    }
    .rating-label {
        font-size: 0.85rem;
        color: var(--text-muted);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding-top: 1.5rem;
        border-top: 1px solid var(--border);
        color: var(--text-muted);
        font-size: 0.8rem;
    }

    /* Lightbox */
    .lightbox-overlay {
        display: none;
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.9);
        z-index: 1000;
        cursor: pointer;
        align-items: center;
        justify-content: center;
    }
    .lightbox-overlay.active {
        display: flex;
    }
    .lightbox-overlay img {
        max-width: 95vw;
        max-height: 95vh;
        border-radius: 8px;
        box-shadow: 0 0 40px var(--shadow);
    }
    .lightbox-close {
        position: fixed;
        top: 1rem;
        right: 1rem;
        color: white;
        font-size: 2rem;
        cursor: pointer;
        z-index: 1001;
        background: none;
        border: none;
        line-height: 1;
    }

    /* Collapsible Screenshots */
    .screenshot-container {
        margin-bottom: 1rem;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border);
    }
    .screenshot-toggle-bar {
        width: 100%;
        padding: 0.7rem 1rem;
        background: var(--bg-hover);
        color: var(--text-secondary);
        font-size: 0.85rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: background 0.15s;
    }
    .screenshot-toggle-bar:hover {
        background: var(--bg-card);
    }
    .screenshot-toggle-bar .arrow {
        transition: transform 0.2s;
        font-size: 0.7rem;
    }
    .screenshot-container[data-state="expanded"] .screenshot-toggle-bar .arrow {
        transform: rotate(90deg);
    }
    .screenshot-content {
        overflow: hidden;
    }
    .controls-bar {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .controls-bar button {
        padding: 0.4rem 0.8rem;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text-secondary);
        font-size: 0.8rem;
        cursor: pointer;
        transition: background 0.15s;
    }
    .controls-bar button:hover {
        background: var(--bg-hover);
    }

    /* Collapsible Step Cards */
    .step-header {
        cursor: pointer;
    }
    .step-collapse-arrow {
        font-size: 0.7rem;
        transition: transform 0.2s;
    }
    .step-card[data-collapsed="true"] .step-collapse-arrow {
        transform: rotate(-90deg);
    }

    /* Chat-style Thought Bubble */
    .thought-bubble {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        margin-top: 0.5rem;
    }
    .thought-bubble-icon {
        font-size: 1.4rem;
        line-height: 1;
        flex-shrink: 0;
        margin-top: 0.3rem;
    }
    .thought-bubble-text {
        background: var(--bg-secondary);
        border-radius: 0 12px 12px 12px;
        padding: 0.8rem 1rem;
        color: var(--text-secondary);
        font-size: 0.85rem;
        line-height: 1.7;
        font-style: italic;
        flex: 1;
    }

    /* Back to Top */
    .back-to-top {
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: var(--accent-blue);
        color: white;
        border: none;
        font-size: 1.2rem;
        cursor: pointer;
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 99;
        box-shadow: 0 2px 8px var(--shadow);
        transition: opacity 0.2s;
    }
    .back-to-top.visible {
        display: flex;
    }
</style>"""

    def _render_header(self, persona: "Persona", report: "JourneyReport") -> str:
        """Render the report header."""
        gave_up = report.gave_up
        badge = (
            '<span class="badge badge-gave-up">Gave Up</span>'
            if gave_up
            else '<span class="badge badge-completed">Completed</span>'
        )
        generated = datetime.now().strftime("%Y-%m-%d %H:%M")

        return f"""
    <div class="header">
        <h1>Investor Journey Report</h1>
        <p class="subtitle">
            {persona.name} &middot; {report.viewport_name} &middot; {generated}
            &nbsp;{badge}
        </p>
    </div>"""

    def _render_summary(
        self, report: "JourneyReport", duration: float, success_rate: float
    ) -> str:
        """Render executive summary cards and persona details."""
        persona = report.persona
        steps = report.steps
        duration_str = _format_duration(duration)
        success_pct = f"{success_rate:.0%}"

        # Determine success color
        if success_rate >= 0.7:
            success_color = "var(--accent-green)"
        elif success_rate >= 0.4:
            success_color = "var(--accent-yellow)"
        else:
            success_color = "var(--accent-red)"

        gave_up_text = "Yes" if report.gave_up else "No"

        return f"""
    <div class="summary-grid">
        <div class="summary-card">
            <div class="label">Steps</div>
            <div class="value">{len(steps)}</div>
        </div>
        <div class="summary-card">
            <div class="label">Success Rate</div>
            <div class="value" style="color: {success_color}">{success_pct}</div>
        </div>
        <div class="summary-card">
            <div class="label">Duration</div>
            <div class="value">{duration_str}</div>
        </div>
        <div class="summary-card">
            <div class="label">Gave Up</div>
            <div class="value">{gave_up_text}</div>
        </div>
    </div>

    <div class="persona-card">
        <h3>{persona.name}</h3>
        <p class="description">{persona.description}</p>
        <div class="persona-stats">
            <div class="stat-bar">
                <div class="stat-label">Patience</div>
                <div class="bar"><div class="bar-fill" style="width: {persona.patience_level * 10}%; background: var(--accent-blue);"></div></div>
                <div class="stat-value">{persona.patience_level}/10</div>
            </div>
            <div class="stat-bar">
                <div class="stat-label">Tech Savviness</div>
                <div class="bar"><div class="bar-fill" style="width: {persona.tech_savviness * 10}%; background: var(--accent-blue);"></div></div>
                <div class="stat-value">{persona.tech_savviness}/10</div>
            </div>
        </div>
    </div>"""

    def _render_timeline(self, steps: list) -> str:
        """Render visual frustration timeline."""
        if not steps:
            return ""

        bars = []
        for step in steps:
            color = frustration_to_color(step.action.frustration_level)
            pct = f"{step.action.frustration_level:.0%}"
            status = "pass" if step.success else "fail"
            bars.append(
                f'<div class="timeline-step" '
                f'style="background: {color};" '
                f'title="Step {step.step_number}: {pct} frustration ({status})" '
                f'onclick="scrollToStep({step.step_number})">'
                f'{step.step_number}'
                f'</div>'
            )

        return f"""
    <div class="timeline-section">
        <h2>Frustration Timeline</h2>
        <div class="timeline-bar">
            {"".join(bars)}
        </div>
        <div class="timeline-legend">
            <span>Start</span>
            <span>Low frustration &rarr; High frustration</span>
            <span>End</span>
        </div>
    </div>"""

    def _render_steps(self, steps: list) -> str:
        """Render step detail cards."""
        if not steps:
            return ""

        cards = []
        for step in steps:
            cards.append(self._render_step_card(step))

        return f"""
    <div class="steps-section">
        <h2>Step-by-Step Journey</h2>
        <div class="controls-bar">
            <button onclick="expandAllScreenshots()">Expand All Screenshots</button>
            <button onclick="collapseAllScreenshots()">Collapse All Screenshots</button>
            <button onclick="expandAllSteps()">Expand All Steps</button>
            <button onclick="collapseAllSteps()">Collapse All Steps</button>
        </div>
        {"".join(cards)}
    </div>"""

    def _render_step_card(self, step: "JourneyStep") -> str:
        """Render a single step card."""
        action = step.action
        frustration_pct = f"{action.frustration_level * 100:.0f}%"
        frust_color = frustration_to_color(action.frustration_level)

        # Status badge
        if step.success:
            status_html = '<span class="step-status success">Success</span>'
        else:
            status_html = '<span class="step-status failed">Failed</span>'

        # Screenshot
        screenshot_src = encode_screenshot_base64(Path(step.screenshot_path))
        screenshot_html = f"""
        <div class="screenshot-container" data-state="collapsed">
            <div class="screenshot-toggle-bar" onclick="toggleScreenshot(this.parentElement)">
                <span>View Screenshot</span>
                <span class="arrow">&#9654;</span>
            </div>
            <div class="screenshot-content" style="display:none;">
                <div class="step-screenshot" onclick="openLightbox(this)">
                    <img src="{screenshot_src}" alt="Step {step.step_number} screenshot" loading="lazy">
                </div>
            </div>
        </div>"""

        # Error message
        error_html = ""
        if not step.success and step.error_message:
            error_html = f'<div class="step-error">{_escape_html(step.error_message)}</div>'

        # Action details
        action_html = f"""
        <div class="step-action">
            <span class="action-type">{action.action_type.value}</span>
            <span class="action-target">{_escape_html(action.target)}</span>
        </div>"""

        # Thought (chat bubble)
        persona_name = getattr(self, '_current_persona_name', 'User')
        emoji = _persona_emoji(persona_name)
        thought_html = f"""
        <div class="thought-bubble">
            <span class="thought-bubble-icon" title="{_escape_html(persona_name)}">{emoji}</span>
            <div class="thought-bubble-text">
                {_escape_html(action.thought)}
            </div>
        </div>"""

        return f"""
    <div class="step-card" id="step-{step.step_number}" data-collapsed="false">
        <div class="step-header" onclick="toggleStep(this.parentElement)">
            <span class="step-number">Step {step.step_number}</span>
            <div class="step-meta">
                <span class="frustration-badge" style="background: {frust_color}22; color: {frust_color};">
                    {frustration_pct}
                </span>
                {status_html}
                <span class="step-collapse-arrow">&#9660;</span>
            </div>
        </div>
        <div class="step-body">
            <div class="step-url">{_escape_html(step.url)}</div>
            {screenshot_html}
            {action_html}
            {error_html}
            {thought_html}
        </div>
    </div>"""

    def _render_pain_points(self, evaluation: "Optional[JourneyEvaluation]") -> str:
        """Render pain points section."""
        if not evaluation or not evaluation.pain_points:
            return ""

        items = []
        for pp in evaluation.pain_points:
            items.append(f"""
        <div class="pain-point severity-{pp.severity}">
            <div class="pp-header">
                <span class="pp-description">{_escape_html(pp.description)}</span>
                <span class="pp-severity">{pp.severity}</span>
            </div>
            {f'<div class="pp-suggestion">Suggestion: {_escape_html(pp.suggestion)}</div>' if pp.suggestion else ''}
        </div>""")

        return f"""
    <div class="pain-points-section">
        <h2>Pain Points</h2>
        {"".join(items)}
    </div>"""

    def _render_recommendations(
        self, evaluation: "Optional[JourneyEvaluation]"
    ) -> str:
        """Render recommendations section."""
        if not evaluation:
            return ""

        parts = []

        # Rating
        if evaluation.overall_rating:
            parts.append(f"""
    <div class="rating-section">
        <div class="rating-value">{evaluation.overall_rating}/5</div>
        <div class="rating-label">Overall Rating</div>
    </div>""")

        # Suggestions
        if evaluation.suggestions:
            items = []
            for i, suggestion in enumerate(evaluation.suggestions, 1):
                items.append(f"""
        <div class="recommendation-item">
            <span class="rec-number">#{i}</span>
            {_escape_html(suggestion)}
        </div>""")

            parts.append(f"""
    <div class="recommendations-section">
        <h2>Recommendations</h2>
        {"".join(items)}
    </div>""")

        return "".join(parts)

    def _render_footer(self) -> str:
        """Render the footer."""
        return """
    <div class="footer">
        <p>Generated by Investor Journey Agent &middot; Prova AI</p>
    </div>"""

    def _render_lightbox(self) -> str:
        """Render the lightbox overlay markup."""
        return """
    <div class="lightbox-overlay" id="lightbox" onclick="closeLightbox()">
        <button class="lightbox-close" onclick="closeLightbox()">&times;</button>
        <img id="lightbox-img" src="" alt="Screenshot">
    </div>"""

    def _render_js(self) -> str:
        """Render inline JavaScript for interactivity."""
        return """<script>
    function openLightbox(el) {
        var img = el.querySelector('img');
        if (!img) return;
        var overlay = document.getElementById('lightbox');
        var lbImg = document.getElementById('lightbox-img');
        lbImg.src = img.src;
        overlay.classList.add('active');
    }

    function closeLightbox() {
        document.getElementById('lightbox').classList.remove('active');
    }

    function scrollToStep(n) {
        var el = document.getElementById('step-' + n);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function toggleScreenshot(container) {
        var content = container.querySelector('.screenshot-content');
        var state = container.getAttribute('data-state');
        if (state === 'collapsed') {
            container.setAttribute('data-state', 'expanded');
            content.style.display = 'block';
        } else {
            container.setAttribute('data-state', 'collapsed');
            content.style.display = 'none';
        }
    }

    function setAllScreenshotsState(state, display) {
        var containers = document.querySelectorAll('.screenshot-container');
        containers.forEach(function(c) {
            c.setAttribute('data-state', state);
            c.querySelector('.screenshot-content').style.display = display;
        });
    }

    function expandAllScreenshots() {
        setAllScreenshotsState('expanded', 'block');
    }

    function collapseAllScreenshots() {
        setAllScreenshotsState('collapsed', 'none');
    }

    function toggleStep(card) {
        var body = card.querySelector('.step-body');
        var collapsed = card.getAttribute('data-collapsed') === 'true';
        if (collapsed) {
            card.setAttribute('data-collapsed', 'false');
            body.style.display = '';
        } else {
            card.setAttribute('data-collapsed', 'true');
            body.style.display = 'none';
        }
    }

    function setAllStepsState(collapsed) {
        var cards = document.querySelectorAll('.step-card');
        cards.forEach(function(c) {
            c.setAttribute('data-collapsed', collapsed ? 'true' : 'false');
            c.querySelector('.step-body').style.display = collapsed ? 'none' : '';
        });
    }

    function expandAllSteps() {
        setAllStepsState(false);
    }

    function collapseAllSteps() {
        setAllStepsState(true);
    }

    function scrollToTop() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    window.addEventListener('scroll', function() {
        var btn = document.getElementById('back-to-top');
        if (window.scrollY > 400) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeLightbox();
    });
</script>"""


def _persona_emoji(name: str) -> str:
    """Map persona name to an emoji icon for chat bubbles."""
    mapping = {
        "investor": "\U0001F4BC",       # briefcase
        "student": "\U0001F393",        # graduation cap
        "confused teacher": "\U0001F914", # thinking face
        "power user": "\u26A1",         # lightning
        "qa tester": "\U0001F50D",      # magnifying glass
    }
    return mapping.get(name.lower(), "\U0001F464")  # default: bust silhouette


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
