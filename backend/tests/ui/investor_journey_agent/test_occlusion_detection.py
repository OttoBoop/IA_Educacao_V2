"""
Tests for occlusion detection in get_clickable_elements().

F1-T4: These tests load the mock HTML fixture in Playwright and verify
that the agent correctly classifies elements as visible, fully_occluded,
partially_occluded, or off_screen using elementFromPoint() sampling.

These tests require Playwright to be installed.
"""

from pathlib import Path

import pytest

from tests.ui.investor_journey_agent.browser_interface import (
    BrowserInterface,
    ClickableElement,
)
from tests.ui.investor_journey_agent.config import VIEWPORT_CONFIGS

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "occlusion_test.html"
FIXTURE_URL = FIXTURE_PATH.as_uri()


# ============================================================
# F1-T4: Occlusion detection unit tests
# ============================================================


def _find_element(elements: list, selector_fragment: str) -> ClickableElement:
    """Find an element by a fragment of its selector (e.g., 'btn-visible')."""
    for el in elements:
        if selector_fragment in el.selector or selector_fragment in el.text.lower():
            return el
    available = [f"{e.selector} ({e.text})" for e in elements]
    raise ValueError(
        f"Element matching '{selector_fragment}' not found. "
        f"Available: {available}"
    )


@pytest.fixture
async def browser():
    """Launch a Playwright browser and navigate to the occlusion fixture."""
    viewport = VIEWPORT_CONFIGS["desktop"]
    bi = BrowserInterface(viewport_config=viewport, headless=True)
    await bi.start()
    await bi.goto(FIXTURE_URL)
    yield bi
    await bi.close()


class TestOcclusionVisible:
    """A fully visible button (no overlay) should be marked 'visible'."""

    @pytest.mark.asyncio
    async def test_visible_button_is_in_list(self, browser):
        """btn-visible should appear in the clickable elements list."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-visible")
        assert el is not None

    @pytest.mark.asyncio
    async def test_visible_button_has_visible_status(self, browser):
        """btn-visible should have occlusion_status='visible'."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-visible")
        assert el.occlusion_status == "visible"


class TestOcclusionFullyOccluded:
    """A button behind a full overlay should be marked 'fully_occluded'."""

    @pytest.mark.asyncio
    async def test_occluded_button_is_in_list(self, browser):
        """btn-occluded should still appear in the list (not filtered out)."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-occluded")
        assert el is not None

    @pytest.mark.asyncio
    async def test_occluded_button_has_fully_occluded_status(self, browser):
        """btn-occluded should have occlusion_status='fully_occluded'."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-occluded")
        assert el.occlusion_status == "fully_occluded"


class TestOcclusionPartiallyOccluded:
    """A button partially behind an overlay should be marked 'partially_occluded'."""

    @pytest.mark.asyncio
    async def test_partial_button_is_in_list(self, browser):
        """btn-partial should appear in the clickable elements list."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-partial")
        assert el is not None

    @pytest.mark.asyncio
    async def test_partial_button_has_partially_occluded_status(self, browser):
        """btn-partial should have occlusion_status='partially_occluded'."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-partial")
        assert el.occlusion_status == "partially_occluded"


class TestOcclusionOffScreen:
    """An off-screen button should be marked 'off_screen' but still in the list."""

    @pytest.mark.asyncio
    async def test_offscreen_button_is_in_list(self, browser):
        """btn-offscreen should still appear in the list (not filtered out)."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-offscreen")
        assert el is not None

    @pytest.mark.asyncio
    async def test_offscreen_button_has_off_screen_status(self, browser):
        """btn-offscreen should have occlusion_status='off_screen'."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-offscreen")
        assert el.occlusion_status == "off_screen"


class TestOcclusionFivePointSampling:
    """Verify that 5-point sampling catches partial occlusion correctly."""

    @pytest.mark.asyncio
    async def test_center_visible_but_edges_occluded_is_partial(self, browser):
        """btn-partial has visible center but occluded right side → partially_occluded."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-partial")
        # The fixture places btn-partial at left=500, width=200
        # partial-overlay starts at left=600, so right half is covered
        # Center (x=600) is at the boundary, but right quadrant is covered
        assert el.occlusion_status == "partially_occluded"

    @pytest.mark.asyncio
    async def test_all_five_points_blocked_is_fully_occluded(self, browser):
        """btn-occluded is entirely behind the overlay → fully_occluded."""
        elements = await browser.get_clickable_elements()
        el = _find_element(elements, "btn-occluded")
        # overlay covers 150-450 x 150-450, button is at 200,200 with size 120x40
        # All 5 sample points should be behind the overlay
        assert el.occlusion_status == "fully_occluded"
