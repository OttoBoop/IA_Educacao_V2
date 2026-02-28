"""
test_modal_backdrop.py — RED Tests: Modal Backdrop Click-to-Close (F3-T2)

Plan: docs/PLAN_Journey_UI_Fixes_Batch_2.md, task F3-T2

Investigation findings (F3-T1) showed three potential failure modes:
  1. Simple backdrop click works (handler at line 6082-6095 in index_v2.html)
  2. Task panel z-index (150) HIGHER than modal overlay (100) — if open, intercepts clicks
  3. Some modals may be opened by directly adding .active, bypassing openModal() auto-close

Tests written BEFORE implementation (RED phase).  Some tests are expected to
PASS (regression guards) and some are expected to FAIL (new broken behaviors).

Expected FAIL in RED:
  - test_task_panel_open_backdrop_click_still_closes_modal
    Task panel z-index 150 > modal overlay z-index 100; clicking where task panel
    overlaps the overlay area hits the task panel, not the overlay.
  - test_mobile_tap_on_backdrop_closes_modal (touch events not firing click handler)

Expected PASS already (regression guards):
  - test_simple_backdrop_click_closes_modal
  - test_backdrop_click_closes_all_testable_modals (parametrized)

Run:
    cd IA_Educacao_V2/backend
    RUN_UI_TESTS=1 pytest tests/ui/test_modal_backdrop.py -v

Requires: local server at http://localhost:8000
    python -m uvicorn main_v2:app --port 8000 --reload
"""

import os
import pytest
from typing import Optional

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

LOCAL_URL = "http://localhost:8000"

# iPhone 14 viewport
IPHONE_14 = {"width": 393, "height": 852}

# Modals that can be opened safely via openModal() without requiring pre-filled
# form data or authenticated context.  These are the "clean open" modals.
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

# Extended set — modals with modal-overlay wrappers that use openModal() flow
EXTENDED_MODALS = [
    "modal-settings",
    "modal-upload",
    "modal-materia",
    "modal-turma",
    "modal-busca",
    "modal-comparacao",
    "modal-add-apikey",
    "modal-prompt-preview",
    "modal-atividade",
    "modal-importar-csv",
]


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #

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
            response = await client.get(LOCAL_URL, timeout=30.0)
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
    """Creates and closes a Chromium browser instance."""
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


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #

async def dismiss_all_modals(page: Page):
    """
    Force-close all active modal overlays by directly removing .active.

    Used for test setup / cleanup only — not the user-facing close mechanism.
    """
    await page.evaluate("""
        () => {
            document.querySelectorAll('.modal-overlay.active').forEach(el => {
                el.classList.remove('active');
            });
        }
    """)
    await page.wait_for_timeout(150)


async def dismiss_welcome_modal(page: Page):
    """Dismiss the welcome modal if it is shown, so it doesn't block tests."""
    await page.evaluate("""
        () => {
            const welcome = document.getElementById('modal-welcome');
            if (welcome) welcome.classList.remove('active');
            const tutorial = document.getElementById('modal-tutorial');
            if (tutorial) tutorial.classList.remove('active');
        }
    """)
    await page.wait_for_timeout(150)


async def load_page_clean(page: Page):
    """Navigate to LOCAL_URL, wait for network idle, dismiss welcome modal."""
    await page.goto(LOCAL_URL)
    await page.wait_for_load_state("networkidle")
    await dismiss_welcome_modal(page)
    await dismiss_all_modals(page)


async def open_modal_and_verify(page: Page, modal_id: str):
    """Open a modal via JS openModal() and assert it received .active class."""
    await page.evaluate(f"openModal('{modal_id}')")
    await page.wait_for_timeout(100)

    is_active = await page.evaluate(f"""
        () => {{
            const el = document.getElementById('{modal_id}');
            return el && el.classList.contains('active');
        }}
    """)
    assert is_active, (
        f"Failed to open {modal_id} — .active class not found after openModal(). "
        f"Check that #{modal_id} exists in the DOM."
    )


async def is_modal_active(page: Page, modal_id: str) -> bool:
    """Return True if the modal currently has .active class."""
    return await page.evaluate(f"""
        () => {{
            const el = document.getElementById('{modal_id}');
            return el ? el.classList.contains('active') : false;
        }}
    """)


async def get_overlay_bbox(page: Page, modal_id: str) -> Optional[dict]:
    """
    Return the bounding box of the modal-overlay element (the full-screen backdrop).
    Returns None if the element does not exist.
    """
    bbox = await page.evaluate(f"""
        () => {{
            const el = document.getElementById('{modal_id}');
            if (!el) return null;
            const r = el.getBoundingClientRect();
            return {{ x: r.x, y: r.y, width: r.width, height: r.height }};
        }}
    """)
    return bbox


async def get_modal_content_bbox(page: Page, modal_id: str) -> Optional[dict]:
    """
    Return the bounding box of the inner .modal element inside the overlay.
    Returns None if not found.
    """
    bbox = await page.evaluate(f"""
        () => {{
            const overlay = document.getElementById('{modal_id}');
            if (!overlay) return null;
            const inner = overlay.querySelector('.modal');
            if (!inner) return null;
            const r = inner.getBoundingClientRect();
            return {{ x: r.x, y: r.y, width: r.width, height: r.height }};
        }}
    """)
    return bbox


# --------------------------------------------------------------------------- #
# TestSimpleBackdropClick — Regression Guards (should PASS today)             #
# --------------------------------------------------------------------------- #

class TestSimpleBackdropClick:
    """
    Regression guards: verifies the existing backdrop click handler
    (index_v2.html lines 6082-6095) works for the straightforward case.

    These tests are expected to PASS even in RED phase, because the handler
    already exists.  They act as guards to ensure the GREEN fix does not
    break this working path.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_simple_backdrop_click_closes_modal(self, page: Page):
        """
        Open modal-settings via openModal(), then simulate a click on the
        .modal-overlay area (top-left corner — outside the centered .modal
        content box), and assert the modal loses .active.

        Expected: PASS — the existing handler fires when e.target is the
        overlay element.
        """
        await load_page_clean(page)
        await open_modal_and_verify(page, "modal-settings")

        # Get overlay bounding box to find a safe click outside the modal content
        overlay_bbox = await get_overlay_bbox(page, "modal-settings")
        content_bbox = await get_modal_content_bbox(page, "modal-settings")

        assert overlay_bbox is not None, (
            "modal-settings overlay bounding box is None — element not found"
        )

        # Click the top-left corner of the overlay — guaranteed to be outside
        # the centered modal content
        click_x = overlay_bbox["x"] + 10
        click_y = overlay_bbox["y"] + 10

        # If the modal content happens to sit at y=0 (unlikely), fall back
        # to clicking the very bottom edge of the overlay
        if content_bbox and content_bbox["y"] < 20:
            click_x = overlay_bbox["x"] + overlay_bbox["width"] - 10
            click_y = overlay_bbox["y"] + overlay_bbox["height"] - 10

        await page.mouse.click(click_x, click_y)
        await page.wait_for_timeout(200)

        still_active = await is_modal_active(page, "modal-settings")

        assert not still_active, (
            "After clicking the backdrop area (outside modal content), "
            "modal-settings must lose .active class. "
            "Backdrop click handler (index_v2.html:6082) should fire when "
            "e.target is the .modal-overlay.active element."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_backdrop_click_via_js_dispatch_closes_modal(self, page: Page):
        """
        Dispatch a synthetic click event directly on the .modal-overlay element
        (not on a child element) and verify the modal closes.

        This bypasses coordinate-based targeting and directly tests that the
        backdrop click handler fires when e.target IS the overlay.

        Expected: PASS — the handler checks e.target.classList, and a synthetic
        click with target = the overlay element should satisfy that check.
        """
        await load_page_clean(page)
        await open_modal_and_verify(page, "modal-busca")

        closed = await page.evaluate("""
            () => {
                const overlay = document.getElementById('modal-busca');
                if (!overlay) return false;

                // Dispatch click event with target = the overlay element itself
                const event = new MouseEvent('click', {
                    bubbles: true,
                    cancelable: true,
                    target: overlay
                });
                // We need to dispatch on the overlay so e.target IS the overlay
                overlay.dispatchEvent(event);
                return true;
            }
        """)
        await page.wait_for_timeout(200)

        assert closed, "Could not dispatch click event on modal-busca overlay"

        still_active = await is_modal_active(page, "modal-busca")

        assert not still_active, (
            "After dispatching a click event with target = the .modal-overlay.active "
            "element, modal-busca must lose .active class. "
            "The backdrop handler (index_v2.html:6082) checks: "
            "e.target.classList.contains('modal-overlay') && e.target.classList.contains('active'). "
            "A click dispatched on the overlay directly should satisfy this."
        )


# --------------------------------------------------------------------------- #
# TestBackdropClickAllModals — Parametrized                                    #
# --------------------------------------------------------------------------- #

class TestBackdropClickAllModals:
    """
    Parametrized backdrop-close test for the full set of testable modals.

    Uses JS synthetic click dispatch (same approach as test_backdrop_click_via_js_dispatch)
    to directly target the overlay element and verify each modal closes.

    Expected: PASS for modals opened via openModal() — handler is wired.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    @pytest.mark.parametrize("modal_id", TESTABLE_MODALS)
    async def test_backdrop_click_closes_modal(self, page: Page, modal_id: str):
        """
        Dispatching a click on the .modal-overlay.active element for {modal_id}
        must remove .active class from the overlay.
        """
        await load_page_clean(page)
        await open_modal_and_verify(page, modal_id)

        await page.evaluate(f"""
            () => {{
                const overlay = document.getElementById('{modal_id}');
                if (overlay) {{
                    overlay.dispatchEvent(new MouseEvent('click', {{
                        bubbles: true,
                        cancelable: true
                    }}));
                }}
            }}
        """)
        await page.wait_for_timeout(200)

        still_active = await is_modal_active(page, modal_id)

        assert not still_active, (
            f"After dispatching backdrop click on #{modal_id} overlay, "
            f"the modal must lose .active class. "
            f"The handler at index_v2.html:6082 checks e.target.classList. "
            f"If this fails, the handler is not wired for this modal."
        )


# --------------------------------------------------------------------------- #
# TestTaskPanelInterference — Expected to FAIL in RED                         #
# --------------------------------------------------------------------------- #

class TestTaskPanelInterference:
    """
    Tests for the z-index conflict scenario (F3-T1 finding):

    .task-panel { z-index: 150 }  >  .modal-overlay { z-index: 100 }

    When the task panel is visible AND overlapping the modal overlay area,
    a real mouse click on the overlapping region hits the TASK PANEL
    (higher z-index), NOT the modal overlay.  The backdrop handler never fires
    because e.target is the task panel, not the overlay.

    These tests verify the BROKEN behavior and are expected to FAIL until
    the z-index conflict is resolved in F3-T3.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_task_panel_open_backdrop_click_still_closes_modal(self, page: Page):
        """
        Scenario:
          1. Force-open the task panel (.task-panel.show)
          2. Open modal-settings via openModal()
             NOTE: openModal() closes the task panel — but we re-open it
             AFTER the modal opens to simulate the z-index conflict.
          3. Re-open the task panel (simulating task panel that bypasses auto-close)
          4. Click on the modal overlay area where the task panel overlaps
          5. Assert modal-settings loses .active class

        Expected: FAIL in RED phase.

        The task panel (z-index 150) sits visually above the modal overlay
        (z-index 100).  A real mouse click on the task panel area hits the
        task panel element — the backdrop handler sees e.target = task-panel,
        not e.target = modal-overlay, so the handler does NOT close the modal.

        Fix required: either raise modal z-index above 150, or ensure task
        panel is hidden when any modal is open.
        """
        await load_page_clean(page)
        await open_modal_and_verify(page, "modal-settings")

        # Re-open task panel AFTER modal is open (bypassing openModal auto-close)
        # This simulates the task panel being shown via a code path that does
        # not call openModal(), reproducing the z-index overlap scenario.
        task_panel_exists = await page.evaluate("""
            () => {
                const tp = document.getElementById('task-panel');
                if (!tp) return false;
                tp.classList.add('show');
                return true;
            }
        """)

        if not task_panel_exists:
            pytest.skip("task-panel element not found in DOM — cannot test z-index conflict")

        await page.wait_for_timeout(100)

        # Verify task panel is now visible and modal is still open
        tp_visible = await page.evaluate("""
            () => {
                const tp = document.getElementById('task-panel');
                return tp && tp.classList.contains('show');
            }
        """)
        assert tp_visible, "Task panel should be visible for this test scenario"

        modal_still_open = await is_modal_active(page, "modal-settings")
        assert modal_still_open, "modal-settings should still be active for this test"

        # Get the task panel bounding box to find where it overlaps the overlay
        tp_bbox = await page.evaluate("""
            () => {
                const tp = document.getElementById('task-panel');
                if (!tp) return null;
                const r = tp.getBoundingClientRect();
                return { x: r.x, y: r.y, width: r.width, height: r.height };
            }
        """)

        if tp_bbox is None or tp_bbox["width"] == 0:
            pytest.skip("task-panel bounding box is zero — not rendered, cannot test")

        # Click inside the task panel bounding box — this area is where
        # the task panel (z-index 150) overlaps the modal overlay (z-index 100).
        # The click should hit the TASK PANEL, not the overlay.
        # After the fix, clicking here should STILL close the modal.
        click_x = tp_bbox["x"] + tp_bbox["width"] / 2
        click_y = tp_bbox["y"] + tp_bbox["height"] / 2

        await page.mouse.click(click_x, click_y)
        await page.wait_for_timeout(300)

        still_active = await is_modal_active(page, "modal-settings")

        assert not still_active, (
            "After clicking on the task-panel area (z-index 150) while modal-settings "
            "is open (z-index 100), the modal must still close. "
            "CURRENTLY FAILS because the task panel intercepts the click — "
            "e.target is the task panel, not the modal overlay, so the backdrop "
            "handler at index_v2.html:6082 does not fire. "
            "Fix: ensure task panel is always hidden when a modal is open, OR "
            "raise modal overlay z-index above task panel (>150)."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_openModal_always_hides_task_panel(self, page: Page):
        """
        Regression guard + new assertion:
        openModal() must ALWAYS hide the task panel before showing the modal,
        so the z-index conflict can never arise from a normal user flow.

        Currently PASSES (openModal already calls taskPanel.classList.remove('show')).
        Kept as a guard to ensure the fix for z-index does not remove this behavior.
        """
        await load_page_clean(page)

        # Open task panel first
        task_panel_exists = await page.evaluate("""
            () => {
                const tp = document.getElementById('task-panel');
                if (!tp) return false;
                tp.classList.add('show');
                return true;
            }
        """)

        if not task_panel_exists:
            pytest.skip("task-panel element not found in DOM")

        await page.wait_for_timeout(50)

        # Now call openModal — it should auto-close the task panel
        await page.evaluate("openModal('modal-comparacao')")
        await page.wait_for_timeout(100)

        tp_still_visible = await page.evaluate("""
            () => {
                const tp = document.getElementById('task-panel');
                return tp && tp.classList.contains('show');
            }
        """)

        assert not tp_still_visible, (
            "openModal() must remove .show from the task panel before opening the modal. "
            "This prevents z-index conflict (task panel z-index 150 > overlay 100). "
            "Currently implemented in index_v2.html:7461. "
            "Ensure this behavior is preserved by any fix."
        )

        # Cleanup
        await dismiss_all_modals(page)


# --------------------------------------------------------------------------- #
# TestMobileBackdropClose — Expected to FAIL in RED                           #
# --------------------------------------------------------------------------- #

class TestMobileBackdropClose:
    """
    Mobile backdrop close tests on iPhone 14 (393x852) with touch events.

    The backdrop handler is wired to the 'click' event.  On mobile, touch
    events (touchstart/touchend) fire before the synthetic 'click' event.
    Playwright's page.tap() fires touch events — if the handler only listens
    on 'click', it should still fire (browsers synthesize a click from touch).

    However, the issue may be that on mobile viewports the modal content fills
    most of the screen, leaving little or no tap-accessible backdrop area.
    Tests use coordinate-based tapping outside the modal content box.

    Expected: FAIL in RED phase for the coordinate tap test (modal content
    fills most of iPhone 14 viewport, leaving no tappable backdrop area).
    The JS-dispatch test may pass.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_mobile_tap_on_backdrop_closes_modal(self, mobile_page: Page):
        """
        On iPhone 14 (393x852): open modal-settings, tap on the backdrop area
        OUTSIDE the modal content, assert the modal closes.

        Expected: FAIL in RED phase.

        On mobile viewports, .modal has width: 90% and max-height: 85vh.
        On a 393px wide screen: modal width = 353px, centered.
        The backdrop area at edges is only ~20px wide on each side.
        If the modal content fills the vertical space, there may be
        no tappable area on the backdrop.

        Fix required: ensure the backdrop click area is accessible on mobile,
        or implement a dedicated "tap outside to close" touch target.
        """
        await load_page_clean(mobile_page)
        await open_modal_and_verify(mobile_page, "modal-settings")

        overlay_bbox = await get_overlay_bbox(mobile_page, "modal-settings")
        content_bbox = await get_modal_content_bbox(mobile_page, "modal-settings")

        assert overlay_bbox is not None, (
            "modal-settings overlay bounding box is None on mobile"
        )

        # On iPhone 14 (393px wide), the modal content is 90% = ~354px wide,
        # centered.  Left edge of content ≈ (393 - 354) / 2 ≈ 19px.
        # Tap at x=5, y=10 — should hit the backdrop, not the modal content.
        tap_x = 5
        tap_y = 10

        # Verify our tap coordinates are OUTSIDE the modal content
        if content_bbox:
            content_left = content_bbox["x"]
            content_top = content_bbox["y"]
            if tap_x >= content_left and tap_y >= content_top:
                # Modal content covers the intended tap point — adjust to above content
                tap_y = max(5, content_top - 10)

        await mobile_page.touchscreen.tap(tap_x, tap_y)
        await mobile_page.wait_for_timeout(300)

        still_active = await is_modal_active(mobile_page, "modal-settings")

        assert not still_active, (
            f"After tapping the backdrop at ({tap_x}, {tap_y}) on iPhone 14 (393x852), "
            f"modal-settings must lose .active class. "
            f"The modal content bounding box was: {content_bbox}. "
            f"The overlay bounding box was: {overlay_bbox}. "
            f"On mobile, the modal fills ~90% of the 393px viewport width, leaving "
            f"only ~20px of tappable backdrop on each side. "
            f"If no backdrop area is accessible, a dedicated tap-outside target is needed."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_mobile_js_dispatch_backdrop_click_closes_modal(self, mobile_page: Page):
        """
        On iPhone 14: dispatch a synthetic click on the modal overlay element
        and verify it closes.

        This tests the handler wiring without relying on coordinate-based tapping.
        Expected: PASS (the handler fires on click events regardless of viewport).
        Serves as a baseline to confirm the handler is wired before investigating
        why coordinate taps fail.
        """
        await load_page_clean(mobile_page)
        await open_modal_and_verify(mobile_page, "modal-turma")

        await mobile_page.evaluate("""
            () => {
                const overlay = document.getElementById('modal-turma');
                if (overlay) {
                    overlay.dispatchEvent(new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true
                    }));
                }
            }
        """)
        await mobile_page.wait_for_timeout(200)

        still_active = await is_modal_active(mobile_page, "modal-turma")

        assert not still_active, (
            "After dispatching a click event on the modal-turma overlay on iPhone 14, "
            "the modal must lose .active class. "
            "The backdrop handler (index_v2.html:6082) should fire for synthetic clicks "
            "on mobile viewports the same as desktop."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    @pytest.mark.parametrize("modal_id", TESTABLE_MODALS)
    async def test_mobile_all_modals_close_on_backdrop_click(
        self, mobile_page: Page, modal_id: str
    ):
        """
        On iPhone 14: every testable modal must close when the backdrop overlay
        receives a click event (dispatched via JS to ensure e.target = overlay).

        Expected: PASS for all modals opened via openModal() — handler wired.
        This serves as a comprehensive mobile regression guard.
        """
        await load_page_clean(mobile_page)
        await open_modal_and_verify(mobile_page, modal_id)

        await mobile_page.evaluate(f"""
            () => {{
                const overlay = document.getElementById('{modal_id}');
                if (overlay) {{
                    overlay.dispatchEvent(new MouseEvent('click', {{
                        bubbles: true,
                        cancelable: true
                    }}));
                }}
            }}
        """)
        await mobile_page.wait_for_timeout(200)

        still_active = await is_modal_active(mobile_page, modal_id)

        assert not still_active, (
            f"On iPhone 14, after dispatching backdrop click on #{modal_id}, "
            f"the modal must lose .active class. "
            f"Handler at index_v2.html:6082 must fire for this modal on mobile."
        )


# --------------------------------------------------------------------------- #
# TestModalContentClickDoesNotClose                                            #
# --------------------------------------------------------------------------- #

class TestModalContentClickDoesNotClose:
    """
    Regression guard: clicking INSIDE the modal content (on the .modal element)
    must NOT close the modal.

    The backdrop handler checks: e.target.classList.contains('modal-overlay').
    Clicking on the .modal content div sets e.target = .modal (inner div),
    NOT the .modal-overlay — so the handler should NOT fire.

    Expected: PASS (this is the correct existing behavior).
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_click_inside_modal_content_does_not_close(self, page: Page):
        """
        Clicking on the .modal inner content box must NOT close the modal.

        Tests that the backdrop handler correctly checks e.target and does not
        close the modal when clicking on the inner content (only the overlay).
        """
        await load_page_clean(page)
        await open_modal_and_verify(page, "modal-settings")

        content_bbox = await get_modal_content_bbox(page, "modal-settings")

        assert content_bbox is not None, (
            "Could not find .modal inner element inside modal-settings"
        )

        # Click dead center of the modal content
        click_x = content_bbox["x"] + content_bbox["width"] / 2
        click_y = content_bbox["y"] + content_bbox["height"] / 2

        await page.mouse.click(click_x, click_y)
        await page.wait_for_timeout(200)

        still_active = await is_modal_active(page, "modal-settings")

        assert still_active, (
            "Clicking INSIDE the modal content (on .modal element) must NOT close "
            "the modal. The backdrop handler checks e.target.classList.contains("
            "'modal-overlay') — a click on the inner .modal div has a different "
            "e.target, so the handler must not fire."
        )

        # Cleanup
        await dismiss_all_modals(page)


# --------------------------------------------------------------------------- #
# TestBackdropHandlerExistence — Unit checks                                   #
# --------------------------------------------------------------------------- #

class TestBackdropHandlerExistence:
    """
    Unit-level checks that the backdrop close handler is wired and functional
    without relying on coordinate-based clicking.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_backdrop_handler_closes_modal_welcome_uses_closeWelcome(
        self, page: Page
    ):
        """
        The backdrop handler (line 6087) routes modal-welcome to closeWelcome()
        instead of closeModal().  Verify this special case works.

        Expected: PASS if closeWelcome() exists and removes .active from modal-welcome.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Ensure modal-welcome is active (it may open automatically on first load)
        await page.evaluate("""
            () => {
                const welcome = document.getElementById('modal-welcome');
                if (welcome) welcome.classList.add('active');
            }
        """)
        await page.wait_for_timeout(100)

        is_open = await is_modal_active(page, "modal-welcome")
        if not is_open:
            pytest.skip("modal-welcome could not be opened — element may not exist")

        # Dispatch click on the overlay — should call closeWelcome()
        await page.evaluate("""
            () => {
                const overlay = document.getElementById('modal-welcome');
                if (overlay) {
                    overlay.dispatchEvent(new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true
                    }));
                }
            }
        """)
        await page.wait_for_timeout(300)

        still_active = await is_modal_active(page, "modal-welcome")

        assert not still_active, (
            "Dispatching a click on the modal-welcome overlay must close it "
            "via closeWelcome() (index_v2.html:6088). "
            "The welcome modal uses a special close function instead of closeModal()."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_backdrop_handler_wired_to_document_click(self, page: Page):
        """
        Verify the backdrop click handler is attached to 'document' by checking
        that it responds to a click event dispatched on the overlay.

        This confirms the document-level event delegation pattern is active
        (the handler at line 6082 listens on document, not on individual overlays).

        Expected: PASS — handler already exists.
        """
        await load_page_clean(page)
        await open_modal_and_verify(page, "modal-add-apikey")

        # Confirm the handler fires via event delegation from document
        result = await page.evaluate("""
            () => {
                const overlay = document.getElementById('modal-add-apikey');
                if (!overlay) return { found: false };

                // The handler is on document — dispatch click that bubbles up
                const evt = new MouseEvent('click', { bubbles: true, cancelable: true });
                overlay.dispatchEvent(evt);

                return {
                    found: true,
                    hasActive: overlay.classList.contains('active')
                };
            }
        """)
        await page.wait_for_timeout(200)

        assert result.get("found"), "modal-add-apikey not found in DOM"

        # After the event propagates to document, handler should have removed .active
        still_active = await is_modal_active(page, "modal-add-apikey")

        assert not still_active, (
            "After dispatching a bubbling click on modal-add-apikey overlay, "
            "the document-level backdrop handler (index_v2.html:6082) must "
            "remove .active from the overlay. "
            "The handler uses event delegation on document and checks: "
            "e.target.classList.contains('modal-overlay') && .contains('active')."
        )


# --------------------------------------------------------------------------- #
# pytest configuration                                                         #
# --------------------------------------------------------------------------- #

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "ui: UI tests using Playwright (requires local server)"
    )
