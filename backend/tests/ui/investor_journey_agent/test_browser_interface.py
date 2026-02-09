"""
Tests for BrowserInterface reload and back navigation actions,
and ClickableElement dataclass fields.

These tests verify that the browser interface supports reload and back
actions that personas can use when encountering failures, and that
ClickableElement includes occlusion status tracking.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.ui.investor_journey_agent.browser_interface import (
    BrowserInterface,
    ClickableElement,
)
from tests.ui.investor_journey_agent.config import VIEWPORT_CONFIGS


# ============================================================
# F1-T1: ClickableElement occlusion_status field
# ============================================================


class TestClickableElementOcclusionStatus:
    """F1-T1: ClickableElement must have an occlusion_status field."""

    def test_has_occlusion_status_field(self):
        """ClickableElement should have an occlusion_status attribute."""
        el = ClickableElement(selector="#btn", tag="button", text="Click me")
        assert hasattr(el, "occlusion_status")

    def test_default_occlusion_status_is_visible(self):
        """occlusion_status should default to 'visible' when not specified."""
        el = ClickableElement(selector="#btn", tag="button", text="Click me")
        assert el.occlusion_status == "visible"

    def test_occlusion_status_accepts_fully_occluded(self):
        """Should accept 'fully_occluded' as a valid status."""
        el = ClickableElement(
            selector="#btn", tag="button", text="Click me",
            occlusion_status="fully_occluded",
        )
        assert el.occlusion_status == "fully_occluded"

    def test_occlusion_status_accepts_partially_occluded(self):
        """Should accept 'partially_occluded' as a valid status."""
        el = ClickableElement(
            selector="#btn", tag="button", text="Click me",
            occlusion_status="partially_occluded",
        )
        assert el.occlusion_status == "partially_occluded"

    def test_occlusion_status_accepts_off_screen(self):
        """Should accept 'off_screen' as a valid status."""
        el = ClickableElement(
            selector="#btn", tag="button", text="Click me",
            occlusion_status="off_screen",
        )
        assert el.occlusion_status == "off_screen"

    def test_to_description_includes_occlusion_when_not_visible(self):
        """to_description() should mention occlusion status when element is not visible."""
        el = ClickableElement(
            selector="#btn", tag="button", text="Click me",
            occlusion_status="fully_occluded",
        )
        desc = el.to_description()
        assert "occluded" in desc.lower()

    def test_to_description_omits_occlusion_when_visible(self):
        """to_description() should NOT mention occlusion when element is visible."""
        el = ClickableElement(
            selector="#btn", tag="button", text="Click me",
            occlusion_status="visible",
        )
        desc = el.to_description()
        assert "occluded" not in desc.lower()
        assert "off_screen" not in desc.lower()


class TestBrowserInterfaceReload:
    """Tests for page reload functionality."""

    def test_browser_interface_has_reload_method(self):
        """Test that BrowserInterface has a reload method."""
        viewport = VIEWPORT_CONFIGS["iphone_14"]
        browser = BrowserInterface(viewport_config=viewport)

        assert hasattr(browser, 'reload')
        assert callable(browser.reload)

    @pytest.mark.asyncio
    async def test_reload_calls_page_reload(self):
        """Test that reload() calls the Playwright page.reload()."""
        viewport = VIEWPORT_CONFIGS["iphone_14"]
        browser = BrowserInterface(viewport_config=viewport)

        # Mock the page
        mock_page = MagicMock()
        mock_page.reload = AsyncMock(return_value=None)
        mock_page.wait_for_load_state = AsyncMock(return_value=None)
        browser._page = mock_page

        result = await browser.reload()

        assert result is True
        mock_page.reload.assert_called_once()

    @pytest.mark.asyncio
    async def test_reload_returns_false_on_error(self):
        """Test that reload() returns False when an error occurs."""
        viewport = VIEWPORT_CONFIGS["iphone_14"]
        browser = BrowserInterface(viewport_config=viewport)

        # Mock the page to raise an error
        mock_page = MagicMock()
        mock_page.reload = AsyncMock(side_effect=Exception("Reload failed"))
        browser._page = mock_page

        result = await browser.reload()

        assert result is False


class TestBrowserInterfaceBack:
    """Tests for back navigation functionality."""

    def test_browser_interface_has_go_back_method(self):
        """Test that BrowserInterface has a go_back method."""
        viewport = VIEWPORT_CONFIGS["iphone_14"]
        browser = BrowserInterface(viewport_config=viewport)

        assert hasattr(browser, 'go_back')
        assert callable(browser.go_back)

    @pytest.mark.asyncio
    async def test_go_back_calls_page_go_back(self):
        """Test that go_back() calls the Playwright page.go_back()."""
        viewport = VIEWPORT_CONFIGS["iphone_14"]
        browser = BrowserInterface(viewport_config=viewport)

        # Mock the page
        mock_page = MagicMock()
        mock_page.go_back = AsyncMock(return_value=None)
        mock_page.wait_for_load_state = AsyncMock(return_value=None)
        browser._page = mock_page

        result = await browser.go_back()

        assert result is True
        mock_page.go_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_back_returns_false_on_error(self):
        """Test that go_back() returns False when an error occurs."""
        viewport = VIEWPORT_CONFIGS["iphone_14"]
        browser = BrowserInterface(viewport_config=viewport)

        # Mock the page to raise an error
        mock_page = MagicMock()
        mock_page.go_back = AsyncMock(side_effect=Exception("Go back failed"))
        browser._page = mock_page

        result = await browser.go_back()

        assert result is False
