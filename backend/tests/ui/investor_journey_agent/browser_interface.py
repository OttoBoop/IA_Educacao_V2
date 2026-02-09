"""
Browser Interface - Playwright wrapper for the Investor Journey Agent.

Provides a clean API for browser automation, screenshot capture,
and DOM analysis.
"""

import asyncio
import base64
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


@dataclass
class ClickableElement:
    """Represents a clickable element on the page."""

    selector: str
    tag: str
    text: str
    aria_label: Optional[str] = None
    role: Optional[str] = None
    is_visible: bool = True
    bounding_box: Optional[Dict[str, float]] = None
    occlusion_status: str = "visible"

    def to_description(self) -> str:
        """Human-readable description of the element."""
        parts = [f"<{self.tag}>"]
        if self.text:
            parts.append(f'"{self.text[:50]}"')
        if self.aria_label:
            parts.append(f"(aria: {self.aria_label})")
        if self.role:
            parts.append(f"[role={self.role}]")
        if self.occlusion_status != "visible":
            parts.append(f"[{self.occlusion_status}]")
        return " ".join(parts)


@dataclass
class PageState:
    """Current state of the page."""

    url: str
    title: str
    screenshot_base64: str
    dom_snapshot: str
    clickable_elements: List[ClickableElement] = field(default_factory=list)
    console_errors: List[str] = field(default_factory=list)
    is_loading: bool = False


class BrowserInterface:
    """
    Playwright wrapper providing agent-friendly browser automation.

    Usage:
        async with BrowserInterface(viewport="iphone_14") as browser:
            await browser.goto("http://localhost:8000")
            state = await browser.get_state()
            await browser.click("#some-button")
    """

    def __init__(
        self,
        viewport_config: Dict[str, Any],
        headless: bool = True,
        slow_mo: int = 0,
    ):
        self.viewport_config = viewport_config
        self.headless = headless
        self.slow_mo = slow_mo

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._console_errors: List[str] = []

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def start(self):
        """Start the browser."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
        )

        # Create context with viewport
        self._context = await self._browser.new_context(
            viewport={
                "width": self.viewport_config["width"],
                "height": self.viewport_config["height"],
            },
            device_scale_factor=self.viewport_config.get("device_scale_factor", 1),
            is_mobile=self.viewport_config.get("is_mobile", False),
            has_touch=self.viewport_config.get("has_touch", False),
        )

        self._page = await self._context.new_page()

        # Capture console errors
        self._page.on("console", self._on_console_message)

    def _on_console_message(self, msg):
        """Capture console errors."""
        if msg.type == "error":
            self._console_errors.append(msg.text)

    async def close(self):
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    @property
    def page(self) -> Page:
        """Get the current page."""
        if not self._page:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    async def goto(self, url: str, timeout: int = 60000) -> bool:
        """Navigate to a URL."""
        try:
            await self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            # Best-effort wait for network idle — don't fail if it times out
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass  # Page loaded fine, just has ongoing network activity
            return True
        except Exception as e:
            self._console_errors.append(f"Navigation error: {e}")
            return False

    async def get_screenshot(self) -> bytes:
        """Get a screenshot as bytes."""
        return await self.page.screenshot(type="png")

    async def get_screenshot_base64(self) -> str:
        """Get a screenshot as base64 string."""
        screenshot = await self.get_screenshot()
        return base64.b64encode(screenshot).decode("utf-8")

    async def save_screenshot(self, path: Path) -> bool:
        """Save a screenshot to a file."""
        try:
            await self.page.screenshot(path=str(path))
            return True
        except Exception:
            return False

    async def get_dom_snapshot(self, max_depth: int = 5, max_elements: int = 100) -> str:
        """
        Get a simplified DOM snapshot for LLM analysis.

        Returns a text representation focusing on interactive elements.
        """
        script = f"""
        () => {{
            function getSnapshot(element, depth, maxDepth) {{
                if (depth > maxDepth) return '';

                const tag = element.tagName?.toLowerCase() || '';
                const interactiveTags = ['button', 'a', 'input', 'select', 'textarea', 'label'];
                const hasRole = element.getAttribute('role');
                const hasClick = element.onclick || element.getAttribute('onclick');
                const isInteractive = interactiveTags.includes(tag) || hasRole || hasClick;

                let result = '';

                if (isInteractive || depth <= 2) {{
                    const id = element.id ? `#${{element.id}}` : '';
                    const classes = element.className && typeof element.className === 'string'
                        ? '.' + element.className.split(' ').filter(c => c).slice(0, 2).join('.')
                        : '';
                    const text = element.textContent?.trim().slice(0, 50) || '';
                    const ariaLabel = element.getAttribute('aria-label') || '';
                    const role = element.getAttribute('role') || '';

                    const indent = '  '.repeat(depth);
                    result = `${{indent}}<${{tag}}${{id}}${{classes}}>`;

                    if (ariaLabel) result += ` [aria-label="${{ariaLabel}}"]`;
                    if (role) result += ` [role="${{role}}"]`;
                    if (text && text.length < 50) result += ` "${{text}}"`;
                    result += '\\n';
                }}

                for (const child of element.children) {{
                    result += getSnapshot(child, depth + 1, maxDepth);
                }}

                return result;
            }}

            return getSnapshot(document.body, 0, {max_depth});
        }}
        """
        try:
            snapshot = await self.page.evaluate(script)
            # Limit output size
            lines = snapshot.split("\n")[:max_elements]
            return "\n".join(lines)
        except Exception as e:
            return f"Error getting DOM: {e}"

    async def get_clickable_elements(self) -> List[ClickableElement]:
        """Get all clickable elements on the page with occlusion detection."""
        script = """
        () => {
            const elements = [];
            const selectors = 'button, a, [role="button"], [onclick], input[type="submit"], input[type="button"]';

            // Check if an element at (x, y) belongs to the target element
            function isOwnElement(target, x, y) {
                const topEl = document.elementFromPoint(x, y);
                if (!topEl) return null; // point is outside viewport
                // Check if topEl is the target, or a descendant, or an ancestor
                return target.contains(topEl) || topEl.contains(target);
            }

            document.querySelectorAll(selectors).forEach((el) => {
                const rect = el.getBoundingClientRect();
                const hasSize = rect.width > 0 && rect.height > 0;
                if (!hasSize) return;

                const inViewport = rect.top < window.innerHeight && rect.bottom > 0 &&
                                   rect.left < window.innerWidth && rect.right > 0;

                // Determine occlusion status
                let occlusion_status;
                if (!inViewport) {
                    occlusion_status = 'off_screen';
                } else {
                    // 5-point sampling: center + 4 quadrant midpoints
                    const cx = rect.left + rect.width / 2;
                    const cy = rect.top + rect.height / 2;
                    const qw = rect.width / 4;
                    const qh = rect.height / 4;

                    const points = [
                        [cx, cy],             // center
                        [cx - qw, cy - qh],   // top-left quadrant
                        [cx + qw, cy - qh],   // top-right quadrant
                        [cx - qw, cy + qh],   // bottom-left quadrant
                        [cx + qw, cy + qh],   // bottom-right quadrant
                    ];

                    let visibleCount = 0;
                    for (const [px, py] of points) {
                        const owns = isOwnElement(el, px, py);
                        if (owns === true) visibleCount++;
                        // owns === null means outside viewport, treat as occluded
                    }

                    if (visibleCount === 5) {
                        occlusion_status = 'visible';
                    } else if (visibleCount === 0) {
                        occlusion_status = 'fully_occluded';
                    } else {
                        occlusion_status = 'partially_occluded';
                    }
                }

                // Build a reliable selector
                let selector;
                if (el.id) {
                    selector = `#${el.id}`;
                } else if (el.getAttribute('onclick')) {
                    const onclick = el.getAttribute('onclick').replace(/'/g, "\\'");
                    selector = `[onclick="${onclick}"]`;
                } else {
                    const parent = el.parentElement;
                    const siblings = parent ? Array.from(parent.children) : [];
                    const childIndex = siblings.indexOf(el) + 1;
                    const tag = el.tagName.toLowerCase();
                    const cls = el.className ? `.${el.className.trim().split(/\\s+/)[0]}` : '';
                    selector = cls
                        ? `${tag}${cls}:nth-child(${childIndex})`
                        : `${tag}:nth-child(${childIndex})`;
                }

                elements.push({
                    selector: selector,
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent?.trim().slice(0, 100) || '',
                    aria_label: el.getAttribute('aria-label'),
                    role: el.getAttribute('role'),
                    occlusion_status: occlusion_status,
                    bounding_box: {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height
                    }
                });
            });

            return elements;
        }
        """
        try:
            raw_elements = await self.page.evaluate(script)
            return [ClickableElement(**el) for el in raw_elements]
        except Exception:
            return []

    async def get_state(self) -> PageState:
        """Get the complete current state of the page."""
        screenshot_b64 = await self.get_screenshot_base64()
        dom_snapshot = await self.get_dom_snapshot()
        clickable = await self.get_clickable_elements()

        return PageState(
            url=self.page.url,
            title=await self.page.title(),
            screenshot_base64=screenshot_b64,
            dom_snapshot=dom_snapshot,
            clickable_elements=clickable,
            console_errors=self._console_errors.copy(),
            is_loading=False,
        )

    async def click(self, selector: str, timeout: int = 5000) -> bool:
        """Click an element."""
        try:
            await self.page.click(selector, timeout=timeout)
            await self.page.wait_for_timeout(500)  # Wait for animations
            return True
        except Exception as e:
            self._console_errors.append(f"Click failed on {selector}: {e}")
            return False

    async def type_text(self, selector: str, text: str, timeout: int = 5000) -> bool:
        """Type text into an element."""
        try:
            await self.page.fill(selector, text, timeout=timeout)
            return True
        except Exception as e:
            self._console_errors.append(f"Type failed on {selector}: {e}")
            return False

    async def scroll(self, direction: str = "down", amount: int = 300) -> bool:
        """Scroll the page."""
        try:
            delta = amount if direction == "down" else -amount
            await self.page.mouse.wheel(0, delta)
            await self.page.wait_for_timeout(300)
            return True
        except Exception:
            return False

    async def evaluate_js(self, script: str) -> Any:
        """Evaluate JavaScript on the page."""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            self._console_errors.append(f"JS evaluation failed: {e}")
            return None

    async def wait_for_idle(self, timeout: int = 5000):
        """Wait for network to be idle."""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
        except Exception:
            pass  # Timeout is acceptable

    async def reload(self, timeout: int = 30000) -> bool:
        """Reload the current page."""
        try:
            await self.page.reload(timeout=timeout)
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception as e:
            self._console_errors.append(f"Reload failed: {e}")
            return False

    async def go_back(self, timeout: int = 30000) -> bool:
        """Navigate back to the previous page."""
        try:
            await self.page.go_back(timeout=timeout)
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception as e:
            self._console_errors.append(f"Go back failed: {e}")
            return False

    def clear_errors(self):
        """Clear captured console errors."""
        self._console_errors.clear()
