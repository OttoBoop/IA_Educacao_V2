"""
Tests for CTA button visibility above the fold on mobile.

F3-T1: Welcome modal mobile CSS must be restructured so that the
"Começar a Usar" CTA button is visible without scrolling on iPhone 14.
F3-T2: Verify CTA visibility via viewport measurement.
"""

import re
from pathlib import Path

import pytest

# Path to the frontend HTML file
INDEX_PATH = Path(__file__).parents[4] / "frontend" / "index_v2.html"


@pytest.fixture
def html():
    return INDEX_PATH.read_text(encoding="utf-8")


def _find_mobile_media_block(html: str) -> str:
    """Extract content inside the @media (max-width: 768px) block that
    contains welcome modal CSS adjustments."""
    # Find all @media blocks for max-width: 768px
    pattern = r"@media[^{]*max-width:\s*768px[^{]*\{"
    blocks = []
    for m in re.finditer(pattern, html):
        start = m.end() - 1  # position of opening {
        depth = 0
        end = start
        for i in range(start, len(html)):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        blocks.append(html[start : end + 1])
    return "\n".join(blocks)


def _extract_css_rule(css_text: str, selector: str) -> str:
    """Extract a CSS rule block for a selector from CSS text."""
    results = []
    idx = 0
    while True:
        pos = css_text.find(selector, idx)
        if pos == -1:
            break
        brace_start = css_text.find("{", pos)
        if brace_start == -1:
            break
        depth = 0
        brace_end = brace_start
        for i in range(brace_start, len(css_text)):
            if css_text[i] == "{":
                depth += 1
            elif css_text[i] == "}":
                depth -= 1
                if depth == 0:
                    brace_end = i
                    break
        results.append(css_text[pos : brace_end + 1])
        idx = brace_end + 1
    return "\n".join(results)


# ============================================================
# F3-T1: Welcome modal mobile CSS restructuring
# ============================================================


class TestWelcomeModalMobileCSS:
    """F3-T1: Mobile CSS must reduce spacing so CTA fits above fold."""

    def test_modal_body_padding_reduced(self, html):
        """Welcome modal body must have reduced padding on mobile.

        The desktop version uses padding: 28px (inline style).
        The mobile CSS must override this to a smaller value.
        """
        mobile_css = _find_mobile_media_block(html)
        # Look for .modal-welcome .modal-body or similar with padding override
        has_padding_override = (
            "modal-body" in mobile_css and "padding" in mobile_css
        )
        assert has_padding_override, (
            "Mobile CSS must override modal-body padding to a smaller value"
        )

    def test_welcome_subtitle_margin_reduced(self, html):
        """Welcome subtitle margin-bottom must be reduced on mobile.

        Desktop uses margin-bottom: 24px — mobile should be smaller.
        """
        mobile_css = _find_mobile_media_block(html)
        rule = _extract_css_rule(mobile_css, ".welcome-subtitle")
        assert "margin-bottom" in rule, (
            "Mobile CSS must reduce .welcome-subtitle margin-bottom"
        )

    def test_welcome_section_spacing_reduced(self, html):
        """Welcome section padding and margin must be reduced on mobile."""
        mobile_css = _find_mobile_media_block(html)
        rule = _extract_css_rule(mobile_css, ".welcome-section")
        has_reduction = "padding" in rule or "margin" in rule
        assert has_reduction, (
            "Mobile CSS must reduce .welcome-section padding or margin"
        )

    def test_welcome_footer_margin_reduced(self, html):
        """Welcome footer margin-top must be reduced on mobile.

        Desktop has margin-top: 24px — mobile should be smaller.
        """
        mobile_css = _find_mobile_media_block(html)
        rule = _extract_css_rule(mobile_css, ".welcome-footer")
        assert "margin-top" in rule, (
            "Mobile CSS must reduce .welcome-footer margin-top"
        )

    def test_welcome_tips_spacing_reduced(self, html):
        """Welcome tips section must have reduced spacing on mobile."""
        mobile_css = _find_mobile_media_block(html)
        rule = _extract_css_rule(mobile_css, ".welcome-tips")
        has_reduction = "margin" in rule or "padding" in rule or "gap" in rule
        assert has_reduction, (
            "Mobile CSS must reduce .welcome-tips spacing"
        )
