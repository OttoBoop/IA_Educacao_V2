"""
test_spa_history.py - SPA History Navigation Tests (RED Phase)

Verifies that the app supports browser history:
  1. pushState is called when navigating between views
  2. Browser back restores the previous view
  3. Back at dashboard root stays on dashboard (does not leave SPA)
  4. Forward works after back
  5. Rapid back presses are debounced (only 1 view change within 200ms)
  6. All tests run on iPhone 14 viewport (393x852)

These tests are written BEFORE implementation — they MUST FAIL in RED phase
because the app has zero history.pushState / popstate support.

Executar:
    cd IA_Educacao_V2/backend
    RUN_UI_TESTS=1 pytest tests/ui/test_spa_history.py -v

Requisitos:
    pip install playwright pytest-playwright pytest-asyncio
    playwright install chromium
"""

import pytest
import asyncio
from typing import List, Optional

try:
    from playwright.async_api import async_playwright, Page, Browser, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

LOCAL_URL = "http://localhost:8000"

# --------------------------------------------------------------------------- #
# Fixtures                                                                      #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="function")
async def browser():
    """Creates and closes a Chromium browser instance."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright não instalado")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def iphone_page(browser: Browser):
    """iPhone 14 viewport (393x852) — matches the test requirements."""
    page = await browser.new_page(viewport={"width": 393, "height": 852})
    yield page
    await page.close()


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

async def close_all_modals(page: Page):
    """Close welcome / tutorial modals so they do not block navigation."""
    modals_to_close = ["#modal-welcome", "#modal-tutorial"]
    for modal_id in modals_to_close:
        modal = page.locator(modal_id)
        for _ in range(3):
            try:
                if await modal.count() > 0 and await modal.is_visible():
                    close_btn = modal.locator(
                        ".modal-close, .btn-primary, .close-btn, "
                        "button:has-text('Fechar'), button:has-text('Entendi'), button:has-text('OK')"
                    )
                    if await close_btn.count() > 0:
                        await close_btn.first.click()
                        await page.wait_for_timeout(300)
                    else:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(300)
                else:
                    break
            except Exception:
                break
    await page.wait_for_timeout(200)


async def load_and_close_modals(page: Page):
    """Load the SPA and dismiss any welcome / tutorial modals."""
    await page.goto(LOCAL_URL)
    await page.wait_for_load_state("networkidle")
    await close_all_modals(page)


async def get_first_materia_id(page: Page) -> Optional[str]:
    """Return the first materia ID available in the sidebar tree, or None."""
    materia_id = await page.evaluate(
        "document.querySelector('[data-id]')?.dataset?.id || null"
    )
    if materia_id:
        return materia_id
    # Fallback: hit the API directly
    try:
        response = await page.evaluate("""
            async () => {
                const r = await fetch('/api/materias');
                const data = await r.json();
                return (data.materias || data)[0]?.id || null;
            }
        """)
        return response
    except Exception:
        return None


async def get_first_turma_id(page: Page) -> Optional[str]:
    """Return the first turma ID available, or None."""
    try:
        response = await page.evaluate("""
            async () => {
                const r = await fetch('/api/materias');
                const mData = await r.json();
                const materias = mData.materias || mData;
                if (!materias || !materias.length) return null;
                const matId = materias[0].id;
                const r2 = await fetch('/api/turmas?materia_id=' + matId);
                const tData = await r2.json();
                const turmas = tData.turmas || tData;
                return (turmas && turmas.length) ? turmas[0].id : null;
            }
        """)
        return response
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Test Class                                                                    #
# --------------------------------------------------------------------------- #

class TestSPAHistoryNavigation:
    """
    RED-phase tests for browser history support in the SPA.

    ALL of these tests are expected to FAIL until history.pushState and
    popstate are implemented in index_v2.html.
    """

    # ------------------------------------------------------------------ #
    # Test 1: pushState called on showTurma()                             #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_pushstate_called_on_show_turma(self, iphone_page: Page):
        """
        When showTurma(id) is called, history.length should increase and
        history.state should contain {view: 'turma', turmaId: <id>}.

        FAILS because: showTurma() does not call history.pushState().
        """
        await load_and_close_modals(iphone_page)

        # Record baseline history length
        initial_length = await iphone_page.evaluate("window.history.length")

        turma_id = await get_first_turma_id(iphone_page)
        if turma_id is None:
            # Even without a real ID we can check pushState with a fake call
            turma_id = "test-turma-001"

        # Navigate to turma view
        await iphone_page.evaluate(f"showTurma('{turma_id}')")
        await iphone_page.wait_for_timeout(500)

        new_length = await iphone_page.evaluate("window.history.length")
        history_state = await iphone_page.evaluate("window.history.state")

        # Assertions — both fail in RED phase
        assert new_length > initial_length, (
            f"history.length did not increase after showTurma(). "
            f"Before: {initial_length}, After: {new_length}. "
            "Expected: history.pushState() called inside showTurma()."
        )
        assert history_state is not None, (
            "history.state is null after showTurma(). "
            "Expected: {view: 'turma', turmaId: ...} pushed to history."
        )
        assert history_state.get("view") == "turma", (
            f"history.state.view is '{history_state.get('view')}', expected 'turma'."
        )

    # ------------------------------------------------------------------ #
    # Test 2: Browser back restores previous view                         #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_browser_back_restores_previous_view(self, iphone_page: Page):
        """
        Navigate dashboard → materia → turma, then page.go_back()
        should restore the materia view (currentView === 'materia').

        FAILS because: there is no popstate handler; go_back() reloads the
        page instead of restoring a view.
        """
        await load_and_close_modals(iphone_page)

        materia_id = await get_first_materia_id(iphone_page)
        turma_id = await get_first_turma_id(iphone_page)

        if not materia_id:
            materia_id = "test-materia-001"
        if not turma_id:
            turma_id = "test-turma-001"

        # Navigate: dashboard → materia → turma
        await iphone_page.evaluate("showDashboard()")
        await iphone_page.wait_for_timeout(300)

        await iphone_page.evaluate(f"showMateria('{materia_id}')")
        await iphone_page.wait_for_timeout(300)

        await iphone_page.evaluate(f"showTurma('{turma_id}')")
        await iphone_page.wait_for_timeout(300)

        current_view_before_back = await iphone_page.evaluate("currentView")
        assert current_view_before_back == "turma", (
            f"Expected currentView='turma' before going back, got '{current_view_before_back}'"
        )

        # Go back using browser back button
        await iphone_page.go_back(timeout=5000)
        await iphone_page.wait_for_timeout(500)

        # If the page navigated away entirely, currentView will not be defined.
        # That itself is the failure: without pushState/popstate wiring, go_back()
        # leaves the SPA instead of restoring the previous view.
        try:
            current_view_after_back = await iphone_page.evaluate("currentView")
        except Exception:
            current_view_after_back = "UNKNOWN (page navigated away from SPA)"

        assert current_view_after_back == "materia", (
            f"After pressing back, currentView='{current_view_after_back}', expected 'materia'. "
            "Expected: popstate handler restores the materia view. "
            "If page navigated away entirely, pushState was never called so there is "
            "no in-SPA history entry to go back to."
        )

    # ------------------------------------------------------------------ #
    # Test 3: Back at dashboard root stays on dashboard                   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_back_at_dashboard_root_stays_on_dashboard(self, iphone_page: Page):
        """
        When at dashboard and pressing back, the user should remain on
        dashboard — NOT navigate away from the SPA.

        FAILS because: without popstate support, go_back() from dashboard
        either reloads or leaves the SPA.
        """
        await load_and_close_modals(iphone_page)

        # Ensure we are at dashboard
        await iphone_page.evaluate("showDashboard()")
        await iphone_page.wait_for_timeout(300)

        current_view = await iphone_page.evaluate("currentView")
        assert current_view == "dashboard", (
            f"Expected currentView='dashboard', got '{current_view}'"
        )

        current_url_before = iphone_page.url

        # Attempt to go back — should stay on the SPA
        await iphone_page.go_back(timeout=3000)
        await iphone_page.wait_for_timeout(500)

        current_url_after = iphone_page.url

        # Must stay on the same origin
        assert LOCAL_URL in current_url_after, (
            f"Pressing back at dashboard navigated away from the SPA. "
            f"URL after back: '{current_url_after}'. Expected to stay at '{LOCAL_URL}'."
        )

        # currentView must still be 'dashboard'
        try:
            current_view_after = await iphone_page.evaluate("currentView")
        except Exception:
            current_view_after = "UNKNOWN (page navigated away)"

        assert current_view_after == "dashboard", (
            f"After pressing back at dashboard root, currentView='{current_view_after}', "
            "expected 'dashboard'. SPA should intercept navigation and stay on dashboard."
        )

    # ------------------------------------------------------------------ #
    # Test 4: Forward works after back                                     #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_forward_after_back_restores_view(self, iphone_page: Page):
        """
        Navigate to turma, go back to materia, then go_forward() should
        return to turma view (currentView === 'turma').

        FAILS because: there is no pushState / popstate support.
        """
        await load_and_close_modals(iphone_page)

        materia_id = await get_first_materia_id(iphone_page)
        turma_id = await get_first_turma_id(iphone_page)

        if not materia_id:
            materia_id = "test-materia-001"
        if not turma_id:
            turma_id = "test-turma-001"

        # Navigate: dashboard → materia → turma
        await iphone_page.evaluate("showDashboard()")
        await iphone_page.wait_for_timeout(300)

        await iphone_page.evaluate(f"showMateria('{materia_id}')")
        await iphone_page.wait_for_timeout(300)

        await iphone_page.evaluate(f"showTurma('{turma_id}')")
        await iphone_page.wait_for_timeout(300)

        # Go back to materia
        await iphone_page.go_back(timeout=5000)
        await iphone_page.wait_for_timeout(500)

        try:
            view_at_materia = await iphone_page.evaluate("currentView")
        except Exception:
            view_at_materia = "UNKNOWN (page navigated away from SPA)"

        assert view_at_materia == "materia", (
            f"After go_back(), expected currentView='materia', got '{view_at_materia}'. "
            "Without pushState wiring, go_back() leaves the SPA entirely — "
            "there is no in-SPA materia history entry to restore."
        )

        # Go forward — should return to turma
        await iphone_page.go_forward()
        await iphone_page.wait_for_timeout(500)

        view_after_forward = await iphone_page.evaluate("currentView")

        assert view_after_forward == "turma", (
            f"After go_forward(), currentView='{view_after_forward}', expected 'turma'. "
            "Expected: forward restores the turma view from history stack."
        )

    # ------------------------------------------------------------------ #
    # Test 5: pushState called on showMateria()                           #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_pushstate_called_on_show_materia(self, iphone_page: Page):
        """
        When showMateria(id) is called, history.state should contain
        {view: 'materia', materiaId: <id>}.

        FAILS because: showMateria() does not call history.pushState().
        """
        await load_and_close_modals(iphone_page)

        materia_id = await get_first_materia_id(iphone_page)
        if not materia_id:
            materia_id = "test-materia-001"

        initial_length = await iphone_page.evaluate("window.history.length")

        await iphone_page.evaluate(f"showMateria('{materia_id}')")
        await iphone_page.wait_for_timeout(500)

        new_length = await iphone_page.evaluate("window.history.length")
        history_state = await iphone_page.evaluate("window.history.state")

        assert new_length > initial_length, (
            f"history.length did not increase after showMateria(). "
            f"Before: {initial_length}, After: {new_length}. "
            "Expected: history.pushState() called inside showMateria()."
        )
        assert history_state is not None, (
            "history.state is null after showMateria(). "
            "Expected: {view: 'materia', materiaId: ...} pushed to history."
        )
        assert history_state.get("view") == "materia", (
            f"history.state.view is '{history_state.get('view')}', expected 'materia'."
        )

    # ------------------------------------------------------------------ #
    # Test 6: Rapid back presses debounced                                #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_rapid_back_presses_debounced(self, iphone_page: Page):
        """
        Multiple popstate events fired within 200ms should result in only
        ONE view change, not multiple jumps.

        Strategy: navigate dashboard → materia → turma, then fire two
        popstate events in quick succession (<100ms apart) by directly
        dispatching them.  The final currentView should match a single
        step back (materia), not two steps back (dashboard).

        FAILS because: there is no popstate handler at all, so the view
        stays at 'turma' regardless of popstate events.
        """
        await load_and_close_modals(iphone_page)

        materia_id = await get_first_materia_id(iphone_page)
        turma_id = await get_first_turma_id(iphone_page)

        if not materia_id:
            materia_id = "test-materia-001"
        if not turma_id:
            turma_id = "test-turma-001"

        # Navigate: dashboard → materia → turma
        await iphone_page.evaluate("showDashboard()")
        await iphone_page.wait_for_timeout(300)

        await iphone_page.evaluate(f"showMateria('{materia_id}')")
        await iphone_page.wait_for_timeout(300)

        await iphone_page.evaluate(f"showTurma('{turma_id}')")
        await iphone_page.wait_for_timeout(300)

        # Fire two popstate events rapidly (within 50ms) to simulate
        # rapid back-button presses.  With debouncing (200ms window),
        # only the FIRST event should be processed → view = 'materia'.
        # Without debouncing both would fire → view = 'dashboard'.
        # Without a handler at all → view stays 'turma'.
        await iphone_page.evaluate("""
            () => {
                // Simulate two rapid popstate events
                const stateMateria = { view: 'materia', materiaId: window._lastMateriaId || null };
                const stateDash    = { view: 'dashboard' };

                window.dispatchEvent(new PopStateEvent('popstate', { state: stateMateria }));
                // Fire second event 30ms later (well within 200ms debounce window)
                setTimeout(() => {
                    window.dispatchEvent(new PopStateEvent('popstate', { state: stateDash }));
                }, 30);
            }
        """)

        # Wait long enough for both events to have fired but short enough
        # that no debounce-exempt timer has expired
        await iphone_page.wait_for_timeout(300)

        current_view_after = await iphone_page.evaluate("currentView")

        # With correct debouncing: only first popstate processed → 'materia'
        # Without any handler: stays 'turma'
        # Without debouncing: both fire → 'dashboard'
        assert current_view_after == "materia", (
            f"After two rapid popstate events, currentView='{current_view_after}', "
            "expected 'materia' (first event only processed due to 200ms debounce). "
            "No popstate handler exists yet — test fails in RED phase."
        )
