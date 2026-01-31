"""
Tests for BrowserInterface reload and back navigation actions.

These tests verify that the browser interface supports reload and back
actions that personas can use when encountering failures.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.ui.investor_journey_agent.browser_interface import BrowserInterface
from tests.ui.investor_journey_agent.config import VIEWPORT_CONFIGS


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
