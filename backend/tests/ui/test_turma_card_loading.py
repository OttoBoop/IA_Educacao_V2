"""
test_turma_card_loading.py — RED Tests: Turma Card Loading State + Debounce

F1-T2: Unit-level Playwright tests
  - Spinner appears synchronously inside the card BEFORE the API fetch completes
  - Card is unclickable (pointer-events: none) while loading (debounce)

F1-T3: Integration Playwright tests
  - Clicking a turma card shows spinner during fetch, then renders turma view with tabs
  - API error clears any spinner and restores the card to its original clickable state

These tests CURRENTLY FAIL (RED phase) because showTurma() (line 6192 of index_v2.html)
has no loading state, spinner, or debounce logic.

They will PASS after F1-T4 implements the fix.

Run:
    cd IA_Educacao_V2/backend
    RUN_UI_TESTS=1 pytest tests/ui/test_turma_card_loading.py -v

Requires: local server at http://localhost:8000
    python -m uvicorn main_v2:app --port 8000 --reload
"""

import os
import json
import asyncio
import pytest
from typing import List
from pathlib import Path

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, expect, Page, Browser, Route
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

LOCAL_URL = "http://localhost:8000"

# Fake API response matching showTurma()'s expected shape
FAKE_TURMA_RESPONSE = {
    "turma": {
        "id": "test-turma-1",
        "nome": "9\u00ba Ano A",
        "materia_id": "mat-test-1",
        "ano_letivo": "2024",
        "periodo": ""
    },
    "materia": {"id": "mat-test-1", "nome": "Matem\u00e1tica"},
    "total_atividades": 0,
    "total_alunos": 0,
    "atividades": [],
    "alunos": []
}

# Fake card HTML to inject into #content
FAKE_CARD_HTML = (
    '<div class="card-grid">'
    '<div class="card-grid-item" id="test-turma-card" onclick="showTurma(\'test-turma-1\')">'
    '<div class="card-icon">\U0001f465</div>'
    '<div class="card-name">9\u00ba Ano A</div>'
    '<div class="card-meta">2024</div>'
    '</div>'
    '</div>'
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

async def dismiss_welcome_modal(page: Page):
    """
    Force-close all active modal overlays (welcome, tutorial, and any other).

    Uses evaluate() to directly remove .active from all overlays — this is the same
    operation closeModal() performs and is safe for test setup.
    """
    await page.evaluate("""
        () => {
            // Remove .active from all open modal overlays
            document.querySelectorAll('.modal-overlay.active').forEach(el => {
                el.classList.remove('active');
            });
        }
    """)
    await page.wait_for_timeout(150)


async def inject_turma_card(page: Page):
    """
    Inject a self-contained fake turma card into #content.
    The card has onclick="showTurma('test-turma-1')" and id="test-turma-card".
    """
    await page.evaluate(
        """(html) => {
            const content = document.getElementById('content');
            if (content) { content.innerHTML = html; }
        }""",
        FAKE_CARD_HTML
    )
    # Verify injection succeeded
    card = page.locator("#test-turma-card")
    assert await card.count() == 1, "inject_turma_card: #test-turma-card not found after injection"


def _spinner_check_js() -> str:
    """
    JavaScript expression that returns true if #test-turma-card shows a loading indicator.
    Accepts any reasonable implementation pattern:
      - class 'card-loading' on the card element
      - any child element whose class contains 'spinner' or 'loading'
      - data-loading='true' attribute
    """
    return """
        () => {
            const card = document.getElementById('test-turma-card');
            if (!card) return false;
            return (
                card.classList.contains('card-loading') ||
                card.querySelector('[class*="spinner"]') !== null ||
                card.querySelector('[class*="loading"]') !== null ||
                card.dataset.loading === 'true'
            );
        }
    """


def _debounce_check_js() -> str:
    """
    JavaScript expression that returns true if #test-turma-card is debounced
    (not clickable while loading).
    Accepts pointer-events:none, data-loading='true', or card-loading class.
    """
    return """
        () => {
            const card = document.getElementById('test-turma-card');
            if (!card) return false;
            const computed = getComputedStyle(card);
            return (
                computed.pointerEvents === 'none' ||
                card.style.pointerEvents === 'none' ||
                card.dataset.loading === 'true' ||
                card.classList.contains('card-loading')
            );
        }
    """


# ── F1-T2: Unit-level Spinner + Debounce Tests ───────────────────────────────

class TestTurmaCardSpinner:
    """
    F1-T2: Unit-level tests for loading state in showTurma().

    RED: Both tests FAIL because showTurma() (index_v2.html:6192) has no spinner
    or debounce code.

    GREEN: Will PASS after F1-T4 adds synchronous spinner injection and
    pointer-events:none before the `await api(...)` call.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_spinner_appears_before_fetch_completes(self, page: Page):
        """
        RED: showTurma() must inject a loading indicator into the clicked card
        SYNCHRONOUSLY (before the API fetch resolves) so users see immediate feedback.

        Test strategy:
          1. Route /api/turmas/test-turma-1 to respond after a 2s delay.
          2. Click the turma card — fires onclick="showTurma('test-turma-1')".
          3. Wait 150ms (synchronous code before `await api()` has already run).
          4. Assert: card contains a loading indicator (spinner/loading class or data attr).

        Currently FAILS: showTurma() has no spinner code — card stays unchanged.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_welcome_modal(page)

        # Slow route — ensures fetch is still in flight when we check
        async def slow_route(route: Route):
            await asyncio.sleep(2.0)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(FAKE_TURMA_RESPONSE)
            )

        await page.route("**/turmas/test-turma-1", slow_route)
        await inject_turma_card(page)

        # Click fires onclick, showTurma() starts; page.click() returns before fetch resolves
        await page.click("#test-turma-card")

        # Brief wait — the synchronous code before `await api(...)` has executed
        await page.wait_for_timeout(150)

        has_spinner = await page.evaluate(_spinner_check_js())

        assert has_spinner, (
            "showTurma() must inject a loading indicator into the card "
            "synchronously BEFORE the API fetch completes (<100ms after click). "
            "Currently showTurma() (index_v2.html:6192) has no loading state. "
            "Fix: inject a .spinner element or add class 'card-loading' to the card "
            "before the `await api(...)` call."
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_card_is_unclickable_while_loading(self, page: Page):
        """
        RED: While showTurma() fetch is in flight, the card must be debounced
        (pointer-events: none) to prevent duplicate API calls from double-clicks.

        Test strategy:
          1. Route /api/turmas/test-turma-1 to delay 2s.
          2. Click the turma card.
          3. Wait 150ms (synchronous code has run).
          4. Assert: card's computed pointer-events is 'none' or equivalent debounce flag.

        Currently FAILS: showTurma() sets no pointer-events — card stays clickable.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_welcome_modal(page)

        async def slow_route(route: Route):
            await asyncio.sleep(2.0)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(FAKE_TURMA_RESPONSE)
            )

        await page.route("**/turmas/test-turma-1", slow_route)
        await inject_turma_card(page)

        await page.click("#test-turma-card")
        await page.wait_for_timeout(150)

        is_debounced = await page.evaluate(_debounce_check_js())

        assert is_debounced, (
            "While showTurma() is loading, the turma card must have "
            "pointer-events: none (or equivalent) to prevent double-click submissions. "
            "Currently showTurma() (index_v2.html:6192) does not disable the card. "
            "Fix: set card.style.pointerEvents = 'none' before the `await api(...)` call."
        )


# ── F1-T3: Integration Tests ──────────────────────────────────────────────────

class TestTurmaCardNavigation:
    """
    F1-T3: Integration tests for the full turma card click flow.

    Tests: click card → spinner visible → API resolves → turma view with .tabs renders.
    The spinner assertion in the first test ensures it FAILS in RED phase even though
    the underlying navigation already works.

    GREEN: Both tests pass after F1-T4 implements spinner + navigation.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_click_card_shows_spinner_then_renders_turma_view(self, page: Page):
        """
        RED (step 1: spinner) + Integration (step 2: view renders).

        Full flow:
          1. Inject fake turma card with a short API delay route.
          2. Click card — spinner must appear immediately (RED assertion: FAILS now).
          3. After API responds — #content must contain .tabs with Atividades + Alunos.

        The spinner assertion in step 2 causes this test to FAIL in RED phase.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_welcome_modal(page)

        # Short delay route — long enough to observe spinner, short enough for test speed
        async def short_delay_route(route: Route):
            await asyncio.sleep(0.5)
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(FAKE_TURMA_RESPONSE)
            )

        await page.route("**/turmas/test-turma-1", short_delay_route)
        await inject_turma_card(page)

        # Click the card
        await page.click("#test-turma-card")

        # ── Step 1: Spinner must appear before fetch resolves ────────────────
        await page.wait_for_timeout(150)

        has_spinner = await page.evaluate(_spinner_check_js())

        assert has_spinner, (
            "After clicking a turma card, a loading spinner must appear in the card "
            "BEFORE the API fetch completes. "
            "Currently showTurma() (index_v2.html:6192) has no loading state."
        )

        # ── Step 2: Turma view with tabs renders after API responds ──────────
        tabs = page.locator("#content .tabs")
        await expect(tabs).to_be_visible(timeout=5000)

        tab_texts = await tabs.locator(".tab").all_inner_texts()
        assert any("tividade" in t for t in tab_texts), (
            f"Turma view must have an 'Atividades' tab after navigation. Got: {tab_texts}"
        )
        assert any("luno" in t for t in tab_texts), (
            f"Turma view must have an 'Alunos' tab after navigation. Got: {tab_texts}"
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_api_error_clears_spinner_and_restores_card(self, page: Page):
        """
        Integration: When the API returns an error, the loading state must be cleared.

        After F1-T4 implementation:
          - Spinner is injected before fetch
          - On 500 error: spinner is removed, card pointer-events restored
          - Existing toast error is preserved (showToast already fires)

        Note: In RED phase, since no spinner is added, `has_spinner_after_error`
        will be false — making `not has_spinner_after_error` pass. The card
        pointer-events check will also pass (never disabled). This test primarily
        serves as a regression guard to prevent GREEN from leaving a dangling spinner.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_welcome_modal(page)

        # Route to return a server error after a brief delay
        async def error_route(route: Route):
            await asyncio.sleep(0.3)
            await route.fulfill(
                status=500,
                content_type="application/json",
                body=json.dumps({"detail": "Internal Server Error"})
            )

        await page.route("**/turmas/test-turma-1", error_route)
        await inject_turma_card(page)

        await page.click("#test-turma-card")

        # Wait long enough for the error response to be processed
        await page.wait_for_timeout(800)

        # Assert: no spinner persists after error
        has_spinner_after_error = await page.evaluate(_spinner_check_js())
        assert not has_spinner_after_error, (
            "After an API error, any loading spinner must be cleared from the card. "
            "The card must not remain in a loading state after showTurma() catches the error."
        )

        # Assert: card is clickable again after error (pointer-events restored)
        is_clickable_after_error = await page.evaluate(
            """
            () => {
                const card = document.getElementById('test-turma-card');
                if (!card) return false;
                return getComputedStyle(card).pointerEvents !== 'none';
            }
            """
        )
        assert is_clickable_after_error, (
            "After an API error in showTurma(), the turma card must be clickable again. "
            "pointer-events must be restored (not remain 'none') so the user can retry."
        )


# ── pytest configuration ──────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line("markers", "ui: UI tests using Playwright (requires local server)")
