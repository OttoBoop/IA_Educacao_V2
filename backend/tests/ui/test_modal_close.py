"""
test_modal_close.py — RED Tests: Modal Close Reliability

F2-T2: Unit-level Playwright tests
  - closeModal(validId) removes .active class from modal element
  - closeModal(nonexistentId) does NOT throw — fails gracefully
  - closeModal(nonexistentId) logs console.warn with the invalid ID

F2-T3: Integration + Mobile Playwright tests
  - Click x on modal -> modal hidden (desktop 1400x900)
  - Click x on modal -> modal hidden (iPhone 14 393x852, touch events)
  - Parametrized across 8 representative modals

These tests CURRENTLY FAIL (RED phase) because closeModal() (line 7147 of index_v2.html)
has no null-check and throws TypeError on nonexistent IDs.

They will PASS after F2-T4 implements the fix.

Run:
    cd IA_Educacao_V2/backend
    RUN_UI_TESTS=1 pytest tests/ui/test_modal_close.py -v

Requires: local server at http://localhost:8000
    python -m uvicorn main_v2:app --port 8000 --reload
"""

import os
import pytest
from typing import List

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, expect, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

LOCAL_URL = "http://localhost:8000"

# iPhone 14 viewport
IPHONE_14 = {"width": 393, "height": 852}

# Representative subset of modals with x close buttons.
# All 16 modals with closeModal() x buttons are structurally identical;
# testing 8 covers variety without excessive test runtime.
TESTABLE_MODALS = [
    "modal-settings",
    "modal-upload",
    "modal-materia",
    "modal-turma",
    "modal-busca",
    "modal-comparacao",
    "modal-add-apikey",
    "modal-prompt-preview",
]


# -- Fixtures -----------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
async def check_server():
    """Verify local server is running before tests."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed. Run: pip install playwright && playwright install chromium")

    if not os.getenv("RUN_UI_TESTS"):
        pytest.skip("UI tests disabled. Set RUN_UI_TESTS=1 to enable")

    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(LOCAL_URL, timeout=5.0)
            if response.status_code != 200:
                pytest.exit(
                    f"Server at {LOCAL_URL} returned {response.status_code}.\n"
                    f"Start with: cd IA_Educacao_V2/backend && python -m uvicorn main_v2:app --port 8000"
                )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.exit(
            f"Cannot connect to {LOCAL_URL}. Start server first.\n"
            f"  cd IA_Educacao_V2/backend && python -m uvicorn main_v2:app --port 8000\n"
            f"Error: {e}"
        )


@pytest.fixture(scope="function")
async def browser():
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        yield b
        await b.close()


@pytest.fixture(scope="function")
async def page(browser: Browser):
    """Desktop page (1400x900)."""
    p = await browser.new_page(viewport={"width": 1400, "height": 900})
    yield p
    await p.close()


@pytest.fixture(scope="function")
async def mobile_page(browser: Browser):
    """iPhone 14 page (393x852) with touch enabled."""
    p = await browser.new_page(viewport=IPHONE_14, has_touch=True)
    yield p
    await p.close()


# -- Helpers ------------------------------------------------------------------

async def dismiss_all_modals(page: Page):
    """
    Force-close all active modal overlays.

    Uses evaluate() to directly remove .active from all overlays — same
    operation closeModal() performs. Safe for test setup.
    """
    await page.evaluate("""
        () => {
            document.querySelectorAll('.modal-overlay.active').forEach(el => {
                el.classList.remove('active');
            });
        }
    """)
    await page.wait_for_timeout(150)


async def open_modal_and_verify(page: Page, modal_id: str):
    """Open a modal via JS openModal() and verify it has .active class."""
    await page.evaluate(f"openModal('{modal_id}')")
    await page.wait_for_timeout(100)

    is_active = await page.evaluate(f"""
        () => {{
            const el = document.getElementById('{modal_id}');
            return el && el.classList.contains('active');
        }}
    """)
    assert is_active, f"Failed to open {modal_id} — .active class not found after openModal()"


# -- F2-T2: Unit-level closeModal() Tests ------------------------------------

class TestCloseModalUnit:
    """
    F2-T2: Unit-level tests for closeModal() function.

    RED: test_nonexistent_id_* tests FAIL because closeModal() (index_v2.html:7147)
    has no null-check — document.getElementById(id) returns null and
    .classList.remove('active') throws TypeError.

    GREEN: Will PASS after F2-T4 adds null-check + console.warn.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_closeModal_removes_active_from_valid_modal(self, page: Page):
        """
        Regression guard: closeModal(validId) removes .active class.

        Currently PASSES — closeModal() works for valid IDs.
        Kept as guard to ensure F2-T4 doesn't break existing behavior.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_all_modals(page)

        # Open modal-settings, then close it via closeModal()
        await open_modal_and_verify(page, "modal-settings")

        await page.evaluate("closeModal('modal-settings')")
        await page.wait_for_timeout(100)

        is_still_active = await page.evaluate("""
            () => {
                const el = document.getElementById('modal-settings');
                return el && el.classList.contains('active');
            }
        """)

        assert not is_still_active, (
            "closeModal('modal-settings') should remove .active class from the modal. "
            "After calling closeModal(), the modal must not have .active."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_closeModal_nonexistent_id_does_not_throw(self, page: Page):
        """
        RED: closeModal('nonexistent-xyz') must NOT throw a JavaScript error.

        Currently FAILS: closeModal() calls getElementById('nonexistent-xyz')
        which returns null, then .classList.remove('active') throws:
        TypeError: Cannot read properties of null (reading 'classList')

        Fix: Add null-check before accessing classList.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_all_modals(page)

        result = await page.evaluate("""
            () => {
                try {
                    closeModal('nonexistent-xyz');
                    return { threw: false };
                } catch (e) {
                    return { threw: true, error: e.message, name: e.name };
                }
            }
        """)

        assert not result['threw'], (
            f"closeModal('nonexistent-xyz') must not throw, but threw "
            f"{result.get('name')}: {result.get('error')}. "
            f"Currently closeModal() (index_v2.html:7147) has no null-check. "
            f"Fix: check getElementById result before accessing classList."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_closeModal_nonexistent_id_logs_warning(self, page: Page):
        """
        RED: closeModal('nonexistent-xyz') must log a console.warn.

        Currently FAILS: closeModal() has no warning logic — it just throws
        TypeError. After F2-T4: should log console.warn mentioning the ID.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_all_modals(page)

        warnings: List[str] = []
        page.on("console", lambda msg: warnings.append(msg.text) if msg.type == "warning" else None)

        # Call closeModal with nonexistent ID (catch throw to prevent crash)
        await page.evaluate("""
            () => {
                try {
                    closeModal('nonexistent-xyz');
                } catch (e) {
                    // swallow — the throw is tested separately
                }
            }
        """)
        await page.wait_for_timeout(100)

        has_warning = any("nonexistent-xyz" in w for w in warnings)

        assert has_warning, (
            f"closeModal('nonexistent-xyz') must log a console.warn mentioning "
            f"the invalid ID. Got warnings: {warnings}. "
            f"Currently closeModal() (index_v2.html:7147) has no warning logic. "
            f"Fix: add console.warn when getElementById returns null."
        )


# -- F2-T3: Integration — Desktop x Click ------------------------------------

class TestModalCloseDesktop:
    """
    F2-T3: Integration tests — click x button on desktop viewport (1400x900).

    Opens each modal via openModal(), clicks the x close button, asserts
    the modal is no longer active.

    Currently expected to PASS on desktop (x click fires closeModal correctly).
    Serves as regression guard for F2-T4.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    @pytest.mark.parametrize("modal_id", TESTABLE_MODALS)
    async def test_close_button_hides_modal(self, page: Page, modal_id: str):
        """Click x on {modal_id} (desktop) — modal must become hidden."""
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_all_modals(page)

        # Open the modal
        await open_modal_and_verify(page, modal_id)

        # Find and click the x close button inside this specific modal
        close_btn = page.locator(f"#{modal_id} .modal-close")
        btn_count = await close_btn.count()

        assert btn_count > 0, (
            f"No .modal-close button found inside #{modal_id}. "
            f"Expected a <button class='modal-close'> element."
        )

        await close_btn.first.click()
        await page.wait_for_timeout(200)

        # Assert modal is no longer active
        is_active = await page.evaluate(f"""
            () => {{
                const el = document.getElementById('{modal_id}');
                return el && el.classList.contains('active');
            }}
        """)

        assert not is_active, (
            f"After clicking x on #{modal_id}, the modal must not have .active class. "
            f"The x button's onclick=closeModal('{modal_id}') should remove .active."
        )


# -- F2-T3: Integration — Mobile x Click (iPhone 14) -------------------------

class TestModalCloseMobile:
    """
    F2-T3: Mobile integration tests — click x on iPhone 14 viewport (393x852).

    Same as desktop tests but on mobile viewport with touch events.
    The journey agent observed x click not closing modals on iPhone 14 —
    these tests attempt to reproduce the bug.

    Uses page.tap() (touch event) instead of page.click() for realistic
    mobile interaction.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    @pytest.mark.parametrize("modal_id", TESTABLE_MODALS)
    async def test_close_button_hides_modal_mobile(self, mobile_page: Page, modal_id: str):
        """Tap x on {modal_id} (iPhone 14) — modal must become hidden."""
        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")
        await dismiss_all_modals(mobile_page)

        # Open the modal
        await open_modal_and_verify(mobile_page, modal_id)

        # Find and tap the x close button (touch event for mobile realism)
        close_btn = mobile_page.locator(f"#{modal_id} .modal-close")
        btn_count = await close_btn.count()

        assert btn_count > 0, (
            f"No .modal-close button found inside #{modal_id} on mobile viewport."
        )

        await close_btn.first.tap()
        await mobile_page.wait_for_timeout(200)

        # Assert modal is no longer active
        is_active = await mobile_page.evaluate(f"""
            () => {{
                const el = document.getElementById('{modal_id}');
                return el && el.classList.contains('active');
            }}
        """)

        assert not is_active, (
            f"After tapping x on #{modal_id} (iPhone 14 393x852), the modal must "
            f"not have .active class. Journey agent observed x click not closing modals "
            f"on mobile viewport."
        )


# -- pytest configuration -----------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "ui: UI tests using Playwright (requires local server)")
