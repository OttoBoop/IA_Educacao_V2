"""
Tests for static page navigation robustness.

F2-T1: Navigation guards for file:// (back, reload).
F2-T2: DOM snapshot extraction on self-contained HTML.
"""

import pytest
from pathlib import Path

from tests.ui.investor_journey_agent.browser_interface import BrowserInterface
from tests.ui.investor_journey_agent.config import VIEWPORT_CONFIGS


VIEWPORT = VIEWPORT_CONFIGS["desktop"]

STATIC_HTML = """\
<html>
<head><title>Journey Report</title></head>
<body>
  <h1 id="title">Journey Report</h1>
  <nav>
    <a href="#section1">Section 1</a>
    <a href="#section2">Section 2</a>
  </nav>
  <div id="section1" style="margin-top: 800px;">
    <h2>Section 1</h2>
    <p>Content of section 1</p>
    <button onclick="this.textContent='Clicked!'">Expand</button>
  </div>
  <div id="section2" style="margin-top: 800px;">
    <h2>Section 2</h2>
    <p>Content of section 2</p>
  </div>
</body>
</html>
"""


@pytest.fixture
def static_page(tmp_path):
    """Create a static HTML file and return its file:// URL."""
    html_file = tmp_path / "report.html"
    html_file.write_text(STATIC_HTML)
    return html_file.resolve().as_uri()


# ============================================================
# F2-T1: Navigation guards for file:// (back, reload)
# ============================================================


class TestFileUrlBackNavigation:
    """F2-T1: back action on file:// should not crash."""

    @pytest.mark.asyncio
    async def test_go_back_on_file_url_does_not_crash(self, static_page):
        """go_back() on a file:// URL with no history should return False, not crash."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            # No navigation history - back should gracefully handle this
            result = await browser.go_back()
            # Should return False (no history) but NOT raise an exception
            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_reload_on_file_url_works(self, static_page):
        """reload() on a file:// URL should work."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            result = await browser.reload()
            assert result is True


class TestFileUrlScrolling:
    """F2-T1: Scrolling should work on static file:// pages."""

    @pytest.mark.asyncio
    async def test_scroll_down_on_static_page(self, static_page):
        """scroll() should work on a static HTML page."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            result = await browser.scroll("down")
            assert result is True

    @pytest.mark.asyncio
    async def test_scroll_up_on_static_page(self, static_page):
        """scroll() up should work on a static HTML page."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            await browser.scroll("down")
            result = await browser.scroll("up")
            assert result is True


class TestFileUrlClicking:
    """F2-T1: Clicking anchor links and buttons on static pages."""

    @pytest.mark.asyncio
    async def test_click_anchor_link(self, static_page):
        """Clicking an anchor link (#section) should work."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            result = await browser.click("a[href='#section1']")
            assert result is True

    @pytest.mark.asyncio
    async def test_click_button_on_static_page(self, static_page):
        """Clicking a button on a static page should work."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            result = await browser.click("button")
            assert result is True


# ============================================================
# F2-T2: DOM snapshot on self-contained HTML
# ============================================================


class TestDomSnapshotOnStaticHtml:
    """F2-T2: DOM snapshot should work on self-contained HTML."""

    @pytest.mark.asyncio
    async def test_dom_snapshot_returns_content(self, static_page):
        """DOM snapshot should return non-empty content for static HTML."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            snapshot = await browser.get_dom_snapshot()
            assert len(snapshot) > 0
            assert "Error" not in snapshot

    @pytest.mark.asyncio
    async def test_dom_snapshot_contains_interactive_elements(self, static_page):
        """DOM snapshot should detect buttons and links in static HTML."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            snapshot = await browser.get_dom_snapshot()
            # Should find anchor tags and button
            assert "<a" in snapshot.lower() or "section" in snapshot.lower()

    @pytest.mark.asyncio
    async def test_clickable_elements_found_on_static_page(self, static_page):
        """get_clickable_elements() should find links and buttons in static HTML."""
        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(static_page)
            elements = await browser.get_clickable_elements()
            assert len(elements) > 0
            # Should find at least the anchor links and button
            tags = [el.tag for el in elements]
            assert "a" in tags or "button" in tags


class TestDomSnapshotWithBase64Images:
    """F2-T2: DOM snapshot should handle pages with base64 embedded images."""

    @pytest.mark.asyncio
    async def test_dom_snapshot_handles_base64_images(self, tmp_path):
        """DOM snapshot should not be overwhelmed by base64 image data."""
        html_with_images = """\
<html><body>
  <h1>Report with Images</h1>
  <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" alt="screenshot">
  <button id="expand">Expand</button>
  <a href="#top">Back to top</a>
</body></html>
"""
        html_file = tmp_path / "report_images.html"
        html_file.write_text(html_with_images)
        file_url = html_file.resolve().as_uri()

        async with BrowserInterface(viewport_config=VIEWPORT) as browser:
            await browser.goto(file_url)
            snapshot = await browser.get_dom_snapshot()
            # Should not contain the full base64 data (truncated text content)
            assert len(snapshot) < 10000  # Reasonable size
            assert "Error" not in snapshot
