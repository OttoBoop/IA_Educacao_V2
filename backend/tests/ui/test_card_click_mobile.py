"""
test_card_click_mobile.py — RED Tests: Turma Card Click on Mobile (F4-T2)

Plan: docs/PLAN_Journey_UI_Fixes_Batch_2.md — Feature 4, Task T2

Verifies that turma cards respond correctly to a single click/tap on both
mobile (iPhone 14, 393x852) and desktop viewports:

  1. Cards have a `data-turma-id` attribute (core RED test — cards currently
     only use inline onclick, no data attribute exists)
  2. Single click on a turma card navigates to turma view (iPhone 14)
  3. Card enters loading state synchronously on click (iPhone 14)
  4. Card has pointer-events:none during loading (iPhone 14)
  5. Double-click only navigates once — debounce guard works (desktop)
  6. Single click on a turma card navigates to turma view (desktop, regression guard)

Root cause (from F4-T1 investigation):
  showTurma() uses `document.querySelector('.card-grid-item[onclick*="${turmaId}"]')`
  to find the clicked card. This fragile attribute selector can silently fail to
  match — especially when turmaId contains characters the CSS attribute value
  selector interprets differently. When querySelector returns null, no loading
  state is set and the debounce guard never activates, allowing duplicate taps.

Fix target (F4-T3): Replace the attribute selector with a `data-turma-id`
  attribute on each card and select with `[data-turma-id="${turmaId}"]`.

Tests CURRENTLY FAIL (RED phase):
  - test_cards_have_data_turma_id_attribute — FAILS: cards have no data-turma-id
  - test_card_enters_loading_state_on_click_mobile — MAY FAIL: querySelector fragile
  - test_card_has_pointer_events_none_during_loading_mobile — MAY FAIL: same reason
  - test_double_click_only_navigates_once — FAILS: debounce guard broken when
    querySelector fails to find the card

Run:
    cd IA_Educacao_V2/backend
    RUN_UI_TESTS=1 pytest tests/ui/test_card_click_mobile.py -v

Requires: local server at http://localhost:8000
    python -m uvicorn main_v2:app --port 8000 --reload
"""

import os
import asyncio
import pytest
from typing import Optional

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, expect, Page, Browser, Route
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

LOCAL_URL = "http://localhost:8000"

# iPhone 14 viewport (393x852) — matches plan Section 4 requirements
IPHONE_14 = {"width": 393, "height": 852}


# --------------------------------------------------------------------------- #
# Fixtures                                                                      #
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="session", autouse=True)
async def check_server():
    """Verify local server is running before any tests execute."""
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
                    f"Start with: cd IA_Educacao_V2/backend && "
                    f"python -m uvicorn main_v2:app --port 8000"
                )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.exit(
            f"Cannot connect to {LOCAL_URL}. Start server first.\n"
            f"  cd IA_Educacao_V2/backend && python -m uvicorn main_v2:app --port 8000\n"
            f"Error: {e}"
        )


@pytest.fixture(scope="function")
async def browser():
    """Creates and closes a Chromium browser instance per test."""
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
    """iPhone 14 viewport (393x852) with touch enabled."""
    p = await browser.new_page(viewport=IPHONE_14, has_touch=True)
    yield p
    await p.close()


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #

async def close_all_modals(page: Page):
    """Close welcome / tutorial modals so they do not block interaction."""
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
    """Navigate to the SPA root and dismiss any welcome / tutorial modals."""
    await page.goto(LOCAL_URL)
    await page.wait_for_load_state("networkidle")
    await close_all_modals(page)


async def navigate_to_materia_with_turmas(page: Page) -> Optional[str]:
    """
    Navigate to the first matéria that has turmas.

    Returns the matéria ID used, or None if no matéria with turmas exists.
    The SPA's showMateria() must be called so that turma cards are rendered
    into #content before tests attempt to interact with them.
    """
    try:
        materia_id = await page.evaluate("""
            async () => {
                const r = await fetch('/api/materias');
                const mData = await r.json();
                const materias = mData.materias || mData;
                if (!materias || !materias.length) return null;
                return materias[0].id;
            }
        """)
        if not materia_id:
            return None
        # Navigate to the materia so cards are rendered
        await page.evaluate(f"showMateria('{materia_id}')")
        await page.wait_for_timeout(800)
        return materia_id
    except Exception:
        return None


async def get_first_turma_id(page: Page) -> Optional[str]:
    """
    Return the first turma ID available via the API, or None.

    Used to confirm turma data exists before testing card behavior.
    """
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


async def get_rendered_card_count(page: Page) -> int:
    """Return the number of .card-grid-item elements currently in the DOM."""
    return await page.evaluate(
        "document.querySelectorAll('.card-grid-item').length"
    )


# --------------------------------------------------------------------------- #
# Test Class                                                                    #
# --------------------------------------------------------------------------- #

class TestTurmaCardClickMobile:
    """
    F4-T2: RED-phase tests for turma card click behavior on mobile and desktop.

    Core issue: showTurma() finds the clicked card with:
        document.querySelector('.card-grid-item[onclick*="${turmaId}"]')
    This attribute selector is fragile and silently returns null in some cases,
    meaning the card never gets pointer-events:none — so double-taps are possible.

    The fix (F4-T3) will add data-turma-id="<id>" to each card and replace the
    attribute selector with document.querySelector('[data-turma-id="${turmaId}"]').

    Tests 1 and 5 are guaranteed to FAIL in RED phase.
    Tests 2-4 may FAIL depending on querySelector fragility.
    Test 6 is a regression guard and may pass if navigation already works.
    """

    # ------------------------------------------------------------------ #
    # Test 1: Cards must have data-turma-id attribute (CORE RED TEST)     #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_cards_have_data_turma_id_attribute(self, page: Page):
        """
        RED: Every .card-grid-item rendered in the turma card grid must have
        a `data-turma-id` attribute so that showTurma() can reliably find it.

        FAILS because: cards are currently rendered with only an inline onclick
        attribute (onclick="showTurma('...')") and have NO data-turma-id attribute.

        Fix (F4-T3): Change card rendering from:
            <div class="card-grid-item" onclick="showTurma('${t.id}')">
        to:
            <div class="card-grid-item" data-turma-id="${t.id}" onclick="showTurma('${t.id}')">
        """
        await load_and_close_modals(page)

        materia_id = await navigate_to_materia_with_turmas(page)
        if materia_id is None:
            pytest.skip("No matéria with turmas found in the API. Cannot render cards.")

        card_count = await get_rendered_card_count(page)
        if card_count == 0:
            pytest.skip(
                f"No .card-grid-item elements found after navigating to matéria '{materia_id}'. "
                "Cannot test data-turma-id attribute."
            )

        # Check that every rendered card has a data-turma-id attribute
        cards_with_data_attr = await page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.card-grid-item');
                const results = [];
                cards.forEach(card => {
                    results.push({
                        hasDataTurmaId: card.hasAttribute('data-turma-id'),
                        dataTurmaIdValue: card.getAttribute('data-turma-id'),
                        onclickValue: card.getAttribute('onclick') || ''
                    });
                });
                return results;
            }
        """)

        cards_missing_attr = [
            c for c in cards_with_data_attr if not c.get("hasDataTurmaId")
        ]

        assert len(cards_missing_attr) == 0, (
            f"Found {len(cards_missing_attr)} of {len(cards_with_data_attr)} "
            f"turma cards WITHOUT a data-turma-id attribute.\n"
            f"Cards missing attribute: {cards_missing_attr}\n"
            f"Expected: every .card-grid-item has data-turma-id='<turma_id>' so that "
            f"showTurma() can reliably select the card via "
            f"document.querySelector('[data-turma-id=\"...\"]').\n"
            f"Currently cards only use onclick='showTurma(...)', which the fragile "
            f"attribute selector `[onclick*='...']` may fail to match."
        )

    # ------------------------------------------------------------------ #
    # Test 2: Single click navigates on iPhone 14                         #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_single_click_navigates_on_mobile(self, mobile_page: Page):
        """
        Integration: A single tap on a turma card on iPhone 14 (393x852) must
        navigate to the turma detail view (currentView === 'turma').

        This tests the basic navigation flow — not the debounce or loading state.
        If showTurma() throws or silently fails due to the fragile querySelector,
        currentView will remain 'materia' instead of 'turma'.
        """
        await load_and_close_modals(mobile_page)

        materia_id = await navigate_to_materia_with_turmas(mobile_page)
        if materia_id is None:
            pytest.skip("No matéria with turmas found. Cannot test card click navigation.")

        turma_id = await get_first_turma_id(mobile_page)
        if turma_id is None:
            pytest.skip("No turma data found via API. Cannot test card click navigation.")

        card_count = await get_rendered_card_count(mobile_page)
        if card_count == 0:
            pytest.skip(
                f"No .card-grid-item elements found after navigating to matéria. "
                "Cannot test card click."
            )

        # Click the first visible card
        first_card = mobile_page.locator(".card-grid-item").first
        await first_card.scroll_into_view_if_needed()
        await first_card.click()
        await mobile_page.wait_for_timeout(1000)

        current_view = await mobile_page.evaluate("typeof currentView !== 'undefined' ? currentView : 'UNDEFINED'")

        assert current_view == "turma", (
            f"After a single click on a turma card (iPhone 14 viewport), "
            f"currentView='{current_view}' but expected 'turma'.\n"
            f"A single tap must navigate to the turma detail view on first click."
        )

    # ------------------------------------------------------------------ #
    # Test 3: Card enters loading state synchronously on click (iPhone 14) #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_card_enters_loading_state_on_click_mobile(self, mobile_page: Page):
        """
        RED: Immediately after tapping a turma card on mobile, the card must have
        the 'card-loading' CSS class applied (pointer-events:none + opacity:0.6).

        This FAILS because showTurma() attempts to find the card with the fragile
        querySelector, which can return null. When it returns null, card.classList.add()
        is never called — the card never enters loading state.

        After F4-T3: querySelector is replaced with [data-turma-id="..."], which
        always finds the card, so card-loading is applied reliably.
        """
        await load_and_close_modals(mobile_page)

        materia_id = await navigate_to_materia_with_turmas(mobile_page)
        if materia_id is None:
            pytest.skip("No matéria with turmas found. Cannot test card loading state.")

        card_count = await get_rendered_card_count(mobile_page)
        if card_count == 0:
            pytest.skip("No .card-grid-item elements found. Cannot test loading state.")

        turma_id = await get_first_turma_id(mobile_page)
        if turma_id is None:
            pytest.skip("No turma data found via API. Cannot test card loading state.")

        # Slow down the turma API response so loading state is visible
        async def slow_turma_route(route: Route):
            await asyncio.sleep(2.0)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"turma": {"id": "' + turma_id + '", "nome": "Test", "materia_id": "m1", '
                     '"ano_letivo": "2024", "periodo": ""}, '
                     '"materia": {"id": "m1", "nome": "Test"}, '
                     '"total_atividades": 0, "total_alunos": 0, '
                     '"atividades": [], "alunos": []}'
            )

        await mobile_page.route(f"**/turmas/{turma_id}", slow_turma_route)

        # Click the first card — showTurma() runs, loading state should activate
        first_card = mobile_page.locator(".card-grid-item").first
        await first_card.scroll_into_view_if_needed()
        await first_card.click()

        # Wait briefly — only synchronous code before `await api(...)` has run
        await mobile_page.wait_for_timeout(150)

        # Check that the card has the card-loading class OR pointer-events:none
        has_loading_state = await mobile_page.evaluate("""
            () => {
                const cards = document.querySelectorAll('.card-grid-item');
                for (const card of cards) {
                    if (
                        card.classList.contains('card-loading') ||
                        card.style.pointerEvents === 'none' ||
                        getComputedStyle(card).pointerEvents === 'none'
                    ) {
                        return true;
                    }
                }
                return false;
            }
        """)

        assert has_loading_state, (
            "After clicking a turma card on mobile (iPhone 14), the card must immediately "
            "have class 'card-loading' (or pointer-events:none) applied synchronously "
            "BEFORE the API fetch completes.\n"
            "Currently showTurma() uses a fragile querySelector that may return null — "
            "when null, card.classList.add('card-loading') is never called.\n"
            "Fix (F4-T3): replace the attribute selector with [data-turma-id='...'] so "
            "the card is always found and loading state is always applied."
        )

    # ------------------------------------------------------------------ #
    # Test 4: Card has pointer-events:none during loading (iPhone 14)     #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_card_has_pointer_events_none_during_loading_mobile(self, mobile_page: Page):
        """
        RED: While showTurma() is fetching data on mobile, the clicked card must
        have computed pointer-events === 'none' (set via 'card-loading' class CSS).

        This is the debounce guard: it prevents duplicate taps from triggering
        multiple navigations. It currently MAY FAIL because the fragile querySelector
        can return null, leaving the card fully interactive during the fetch.
        """
        await load_and_close_modals(mobile_page)

        materia_id = await navigate_to_materia_with_turmas(mobile_page)
        if materia_id is None:
            pytest.skip("No matéria with turmas found. Cannot test pointer-events.")

        card_count = await get_rendered_card_count(mobile_page)
        if card_count == 0:
            pytest.skip("No .card-grid-item elements found. Cannot test pointer-events.")

        turma_id = await get_first_turma_id(mobile_page)
        if turma_id is None:
            pytest.skip("No turma data found via API. Cannot test pointer-events.")

        # Slow down API response to keep card in loading state during assertion
        async def slow_turma_route(route: Route):
            await asyncio.sleep(2.0)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"turma": {"id": "' + turma_id + '", "nome": "Test", "materia_id": "m1", '
                     '"ano_letivo": "2024", "periodo": ""}, '
                     '"materia": {"id": "m1", "nome": "Test"}, '
                     '"total_atividades": 0, "total_alunos": 0, '
                     '"atividades": [], "alunos": []}'
            )

        await mobile_page.route(f"**/turmas/{turma_id}", slow_turma_route)

        first_card = mobile_page.locator(".card-grid-item").first
        await first_card.scroll_into_view_if_needed()

        # Capture the card's current onclick value to identify it after click
        card_onclick = await first_card.get_attribute("onclick") or ""

        await first_card.click()
        await mobile_page.wait_for_timeout(150)

        # The card that was clicked should now have pointer-events:none
        pointer_events = await mobile_page.evaluate("""
            () => {
                // Check all cards for pointer-events:none (one of them was just clicked)
                const cards = document.querySelectorAll('.card-grid-item');
                for (const card of cards) {
                    const computed = getComputedStyle(card).pointerEvents;
                    const inline = card.style.pointerEvents;
                    if (computed === 'none' || inline === 'none') {
                        return 'none';
                    }
                }
                // If we find a card with card-loading class, check CSS
                const loadingCard = document.querySelector('.card-loading');
                if (loadingCard) {
                    return getComputedStyle(loadingCard).pointerEvents;
                }
                return 'auto';
            }
        """)

        assert pointer_events == "none", (
            f"While showTurma() is loading on mobile, the clicked turma card must have "
            f"computed pointer-events === 'none' to prevent duplicate taps.\n"
            f"Got pointer-events: '{pointer_events}'.\n"
            f"This fails because showTurma() uses a fragile querySelector that can return "
            f"null — when null, card.style.pointerEvents = 'none' is never executed.\n"
            f"Fix (F4-T3): use [data-turma-id='...'] selector to reliably find the card."
        )

    # ------------------------------------------------------------------ #
    # Test 5: Double-click only navigates once (desktop)                  #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_double_click_only_navigates_once(self, page: Page):
        """
        RED: Clicking a turma card twice in rapid succession should only trigger
        one navigation call. The debounce guard (pointer-events:none set after
        first click) must prevent the second click from firing showTurma() again.

        FAILS because: the fragile querySelector in showTurma() often returns null,
        which means pointer-events:none is never set after the first click. The
        card remains fully clickable, allowing a rapid second click to also call
        showTurma() and potentially cause duplicate API requests or navigation.

        Test strategy:
          1. Intercept showTurma calls by monkey-patching the function.
          2. Navigate to a matéria so cards are rendered.
          3. Click the same card twice with a 50ms gap (rapid double-click).
          4. Assert showTurma was called exactly once (debounce worked) or
             that the second call was blocked by pointer-events:none.
        """
        await load_and_close_modals(page)

        materia_id = await navigate_to_materia_with_turmas(page)
        if materia_id is None:
            pytest.skip("No matéria with turmas found. Cannot test double-click debounce.")

        card_count = await get_rendered_card_count(page)
        if card_count == 0:
            pytest.skip("No .card-grid-item elements found. Cannot test double-click debounce.")

        turma_id = await get_first_turma_id(page)
        if turma_id is None:
            pytest.skip("No turma data found via API. Cannot test double-click debounce.")

        # Slow down API so card stays in loading state between clicks
        async def slow_turma_route(route: Route):
            await asyncio.sleep(2.0)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body='{"turma": {"id": "' + turma_id + '", "nome": "Test", "materia_id": "m1", '
                     '"ano_letivo": "2024", "periodo": ""}, '
                     '"materia": {"id": "m1", "nome": "Test"}, '
                     '"total_atividades": 0, "total_alunos": 0, '
                     '"atividades": [], "alunos": []}'
            )

        await page.route(f"**/turmas/{turma_id}", slow_turma_route)

        # Patch showTurma to count calls without changing behavior
        await page.evaluate("""
            () => {
                window.__showTurmaCallCount = 0;
                const _origShowTurma = window.showTurma;
                window.showTurma = async function(turmaId) {
                    window.__showTurmaCallCount++;
                    return _origShowTurma(turmaId);
                };
            }
        """)

        first_card = page.locator(".card-grid-item").first
        await first_card.scroll_into_view_if_needed()

        # First click
        await first_card.click()
        # Wait 50ms — card should now have pointer-events:none if debounce works
        await page.wait_for_timeout(50)
        # Second click — should be blocked if pointer-events:none is set
        await first_card.click(force=True)  # force=True bypasses Playwright's pointer-events check
        await page.wait_for_timeout(200)

        call_count = await page.evaluate("window.__showTurmaCallCount")

        assert call_count == 1, (
            f"showTurma() was called {call_count} times after two rapid clicks "
            f"(50ms apart). Expected exactly 1 call.\n"
            f"The debounce guard should set pointer-events:none on the card after "
            f"the first click, preventing the second click from being processed.\n"
            f"This fails because showTurma() uses `document.querySelector("
            f"'.card-grid-item[onclick*=\"...\"]')` which can return null — "
            f"when null, pointer-events:none is never set and both clicks fire.\n"
            f"Fix (F4-T3): use [data-turma-id='...'] selector so the card is always "
            f"found and debounced correctly."
        )

    # ------------------------------------------------------------------ #
    # Test 6: Single click navigates on desktop (regression guard)        #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_single_click_navigates_on_desktop(self, page: Page):
        """
        Regression guard: A single click on a turma card on desktop (1400x900)
        must navigate to the turma detail view (currentView === 'turma').

        This test verifies that fixing the mobile card click issue (F4-T3) does
        NOT break desktop navigation. It may pass in RED phase if desktop click
        already works — that is acceptable. It must still pass in GREEN phase.
        """
        await load_and_close_modals(page)

        materia_id = await navigate_to_materia_with_turmas(page)
        if materia_id is None:
            pytest.skip("No matéria with turmas found. Cannot test card click navigation.")

        turma_id = await get_first_turma_id(page)
        if turma_id is None:
            pytest.skip("No turma data found via API. Cannot test card click navigation.")

        card_count = await get_rendered_card_count(page)
        if card_count == 0:
            pytest.skip(
                f"No .card-grid-item elements found after navigating to matéria. "
                "Cannot test card click."
            )

        # Click the first visible card
        first_card = page.locator(".card-grid-item").first
        await first_card.scroll_into_view_if_needed()
        await first_card.click()
        await page.wait_for_timeout(1000)

        current_view = await page.evaluate("typeof currentView !== 'undefined' ? currentView : 'UNDEFINED'")

        assert current_view == "turma", (
            f"After a single click on a turma card (desktop 1400x900), "
            f"currentView='{current_view}' but expected 'turma'.\n"
            f"Desktop card navigation must continue to work after F4-T3 fix."
        )
