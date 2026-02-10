"""
Tests for file:// URL support in the Investor Journey Agent.

F1-T1: File path detection and file:// URL conversion in CLI.
F1-T2: Browser interface handling of file:// navigation.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from tests.ui.investor_journey_agent.config import VIEWPORT_CONFIGS


# ============================================================
# F1-T1: URL resolution logic
# ============================================================


class TestResolveUrl:
    """F1-T1: URL resolution should detect file paths and convert to file:// URLs."""

    def test_http_url_passes_through(self):
        """HTTP URLs should be returned unchanged."""
        from tests.ui.investor_journey_agent.url_utils import resolve_url
        result = resolve_url("http://localhost:8000")
        assert result == "http://localhost:8000"

    def test_https_url_passes_through(self):
        """HTTPS URLs should be returned unchanged."""
        from tests.ui.investor_journey_agent.url_utils import resolve_url
        result = resolve_url("https://example.com")
        assert result == "https://example.com"

    def test_file_url_passes_through(self):
        """file:// URLs should be returned unchanged."""
        from tests.ui.investor_journey_agent.url_utils import resolve_url
        result = resolve_url("file:///home/user/report.html")
        assert result == "file:///home/user/report.html"

    def test_absolute_path_converted_to_file_url(self, tmp_path):
        """An absolute path to an existing file should be converted to a file:// URL."""
        from tests.ui.investor_journey_agent.url_utils import resolve_url
        # Create a temp HTML file
        html_file = tmp_path / "report.html"
        html_file.write_text("<html><body>test</body></html>")

        result = resolve_url(str(html_file))
        assert result.startswith("file:///")
        assert "report.html" in result

    def test_absolute_path_nonexistent_raises(self):
        """An absolute path to a non-existent file should raise FileNotFoundError."""
        from tests.ui.investor_journey_agent.url_utils import resolve_url
        with pytest.raises(FileNotFoundError):
            resolve_url("/nonexistent/path/report.html")

    def test_windows_path_converted_to_file_url(self, tmp_path):
        """A Windows-style path should be converted to a proper file:// URL."""
        from tests.ui.investor_journey_agent.url_utils import resolve_url
        html_file = tmp_path / "report.html"
        html_file.write_text("<html><body>test</body></html>")

        result = resolve_url(str(html_file))
        assert result.startswith("file:///")
        # Should not have backslashes in URL
        assert "\\" not in result


# ============================================================
# F1-T2: Browser interface with file:// URLs
# ============================================================


class TestBrowserInterfaceFileUrl:
    """F1-T2: Browser interface should handle file:// URLs."""

    @pytest.mark.asyncio
    async def test_goto_file_url_succeeds(self, tmp_path):
        """Browser should be able to navigate to a file:// URL."""
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        html_file = tmp_path / "test_page.html"
        html_file.write_text("<html><body><h1>Test</h1></body></html>")
        file_url = html_file.resolve().as_uri()

        viewport = VIEWPORT_CONFIGS["desktop"]
        async with BrowserInterface(viewport_config=viewport) as browser:
            success = await browser.goto(file_url)
            assert success is True

    @pytest.mark.asyncio
    async def test_get_state_works_on_file_url(self, tmp_path):
        """get_state() should work on a file:// page."""
        from tests.ui.investor_journey_agent.browser_interface import BrowserInterface

        html_file = tmp_path / "test_page.html"
        html_file.write_text("<html><head><title>Test Page</title></head><body><h1>Hello</h1></body></html>")
        file_url = html_file.resolve().as_uri()

        viewport = VIEWPORT_CONFIGS["desktop"]
        async with BrowserInterface(viewport_config=viewport) as browser:
            await browser.goto(file_url)
            state = await browser.get_state()
            assert state.title == "Test Page"
            assert state.screenshot_base64  # Should have a screenshot
            assert len(state.dom_snapshot) > 0  # Should have DOM content
