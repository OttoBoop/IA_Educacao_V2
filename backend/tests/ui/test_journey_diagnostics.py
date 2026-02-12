"""
test_journey_diagnostics.py - Diagnostic reproducer scripts for journey agent failures

Investigates 3 failures from the 2026-02-09 investor journey (iPhone 14 viewport):
  F1: CTA button "Começar a Usar" click timeout
  F2: Welcome modal re-appears after every reload
  F3: Sidebar tree items unclickable on mobile

Each test measures timing, captures screenshots, and outputs a diagnostic verdict.

Run:
    RUN_DIAGNOSTIC=1 pytest tests/ui/test_journey_diagnostics.py -v -s

Requires:
    pip install playwright pytest-playwright pytest-asyncio
    playwright install chromium

Plan: docs/PLAN_JOURNEY_MOBILE_DIAGNOSTIC.md
"""

import pytest
import time
import json
from pathlib import Path

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Target: production (where the journey failed)
PRODUCTION_URL = "https://ia-educacao-v2.onrender.com"

# iPhone 14 viewport (same as the failing journey)
IPHONE_14 = {"width": 390, "height": 844}

# Evidence output directory
EVIDENCE_DIR = Path(__file__).parent.parent.parent / "investor_journey_reports" / "diagnostics"


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(scope="session")
def evidence_dir():
    """Create evidence output directory."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    return EVIDENCE_DIR


@pytest.fixture(scope="function")
async def mobile_browser():
    """Launch browser for mobile testing."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def mobile_page(mobile_browser: Browser):
    """Create a mobile page with iPhone 14 viewport."""
    context = await mobile_browser.new_context(
        viewport=IPHONE_14,
        device_scale_factor=3,
        is_mobile=True,
        has_touch=True,
    )
    page = await context.new_page()
    yield page
    await page.close()
    await context.close()


async def goto_production(page: Page, timeout: int = 60000) -> float:
    """Navigate to production, return load time in ms. Tolerates cold start."""
    start = time.monotonic()
    await page.goto(PRODUCTION_URL, timeout=timeout, wait_until="domcontentloaded")
    # Best-effort networkidle (don't fail if it times out)
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    elapsed_ms = (time.monotonic() - start) * 1000
    return elapsed_ms


# ============================================================
# F1: CTA BUTTON CLICK TIMING
# ============================================================

class TestF1CtaButtonTiming:
    """
    F1-T1: Diagnose why "Começar a Usar" click times out on mobile.

    Hypotheses:
    A) Button is below the fold in the scrollable modal — Playwright can't scroll it into view within 5s
    B) Render cold-start makes the page too slow for a 5s click timeout
    C) The selector the agent used doesn't match the actual DOM
    """

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_cta_button_exists_with_expected_selectors(self, mobile_page: Page, evidence_dir: Path):
        """Verify which selectors actually match the CTA button."""
        load_time = await goto_production(mobile_page)
        print(f"\n  [Page load time: {load_time:.0f}ms]")

        # Wait for welcome modal to appear (it has a 500ms setTimeout)
        await mobile_page.wait_for_timeout(1000)

        # Test each selector the agent tried
        selectors = {
            "text='Começar a Usar ->'": "Exact text match",
            "button:has-text('Começar a Usar')": "Playwright has-text",
            ".btn-primary": "Class selector",
            "#modal-welcome .btn-primary": "Scoped to modal",
            "button.btn.btn-primary": "Full class chain",
        }

        results = {}
        for selector, description in selectors.items():
            count = await mobile_page.locator(selector).count()
            results[selector] = {"description": description, "matches": count}
            print(f"  [{description}] {selector} -> {count} match(es)")

        # Save evidence
        await mobile_page.screenshot(path=str(evidence_dir / "f1_modal_state.png"))
        (evidence_dir / "f1_selector_results.json").write_text(
            json.dumps(results, indent=2)
        )

        # At least one selector must work
        any_match = any(r["matches"] > 0 for r in results.values())
        assert any_match, "No selector matched the CTA button — DOM structure may have changed"

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_cta_button_position_relative_to_viewport(self, mobile_page: Page, evidence_dir: Path):
        """Check if the CTA button is above or below the fold on iPhone 14."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Get button bounding box
        btn = mobile_page.locator("#modal-welcome .btn-primary")
        if await btn.count() == 0:
            btn = mobile_page.locator("button:has-text('Começar a Usar')")

        assert await btn.count() > 0, "CTA button not found"

        box = await btn.bounding_box()
        viewport_height = IPHONE_14["height"]

        # Get modal-body scroll info
        scroll_info = await mobile_page.evaluate("""
            () => {
                const body = document.querySelector('#modal-welcome .modal-body');
                if (!body) return null;
                return {
                    scrollHeight: body.scrollHeight,
                    clientHeight: body.clientHeight,
                    scrollTop: body.scrollTop,
                    needsScroll: body.scrollHeight > body.clientHeight
                };
            }
        """)

        result = {
            "button_y": box["y"] if box else None,
            "button_bottom": (box["y"] + box["height"]) if box else None,
            "viewport_height": viewport_height,
            "button_visible_without_scroll": box["y"] + box["height"] <= viewport_height if box else False,
            "modal_scroll_info": scroll_info,
        }

        print(f"\n  Button Y position: {result['button_y']:.0f}px")
        print(f"  Button bottom: {result['button_bottom']:.0f}px")
        print(f"  Viewport height: {viewport_height}px")
        print(f"  Visible without scroll: {result['button_visible_without_scroll']}")
        if scroll_info:
            print(f"  Modal needs scroll: {scroll_info['needsScroll']}")
            print(f"  Modal scrollHeight: {scroll_info['scrollHeight']}px vs clientHeight: {scroll_info['clientHeight']}px")

        # Save evidence
        (evidence_dir / "f1_button_position.json").write_text(
            json.dumps(result, indent=2, default=str)
        )

        # This is diagnostic — we want to know the position, not assert pass/fail
        # But we DO assert the button exists and has a bounding box
        assert box is not None, "Button has no bounding box (may be hidden or off-screen)"

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_cta_click_timing_at_various_timeouts(self, mobile_page: Page, evidence_dir: Path):
        """Measure actual click time for the CTA button at different timeouts."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        btn_selector = "#modal-welcome button.btn-primary"

        # Try clicking with increasing timeouts
        timeouts_ms = [3000, 5000, 10000, 15000]
        timing_results = []

        for timeout in timeouts_ms:
            # Reload to reset state (welcome modal reappears)
            # Use generous timeout — Render can go to sleep between requests
            try:
                await mobile_page.reload(wait_until="domcontentloaded", timeout=60000)
            except Exception:
                # If reload times out, try a fresh goto
                await goto_production(mobile_page)
            try:
                await mobile_page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            await mobile_page.wait_for_timeout(1000)

            start = time.monotonic()
            try:
                await mobile_page.click(btn_selector, timeout=timeout)
                elapsed = (time.monotonic() - start) * 1000
                timing_results.append({
                    "timeout_ms": timeout,
                    "actual_ms": round(elapsed),
                    "success": True,
                })
                print(f"  [Timeout {timeout}ms] Click succeeded in {elapsed:.0f}ms")
            except Exception as e:
                elapsed = (time.monotonic() - start) * 1000
                timing_results.append({
                    "timeout_ms": timeout,
                    "actual_ms": round(elapsed),
                    "success": False,
                    "error": str(e)[:200],
                })
                print(f"  [Timeout {timeout}ms] Click FAILED after {elapsed:.0f}ms: {str(e)[:100]}")

        # Save evidence
        (evidence_dir / "f1_click_timing.json").write_text(
            json.dumps(timing_results, indent=2)
        )

        # Diagnostic assertion: at least one timeout should succeed
        any_success = any(r["success"] for r in timing_results)
        assert any_success, (
            f"CTA button click failed at ALL timeouts ({timeouts_ms}ms). "
            f"This indicates a real app or selector bug, not just slow hosting."
        )


# ============================================================
# F2: MODAL PERSISTENCE AFTER RELOAD
# ============================================================

class TestF2ModalPersistence:
    """
    F1-T2: Diagnose why the welcome modal reappears after every reload.

    Hypotheses:
    A) Clicking "Começar a Usar" doesn't set localStorage (only the checkbox does)
    B) reload() in the agent has a networkidle bug that makes it think reload failed
    C) Both
    """

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_modal_localstorage_without_checkbox(self, mobile_page: Page, evidence_dir: Path):
        """Check if clicking 'Começar a Usar' WITHOUT checkbox sets localStorage."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Verify modal is visible
        modal_visible = await mobile_page.locator("#modal-welcome").is_visible()
        assert modal_visible, "Welcome modal not visible on first visit"

        # Check localStorage BEFORE clicking
        ls_before = await mobile_page.evaluate(
            "() => localStorage.getItem('prova-ai-welcomed')"
        )

        # Click "Começar a Usar" WITHOUT checking the checkbox
        btn = mobile_page.locator("#modal-welcome button.btn-primary")
        await btn.scroll_into_view_if_needed()
        await btn.click(timeout=15000)
        await mobile_page.wait_for_timeout(500)

        # Check localStorage AFTER clicking
        ls_after = await mobile_page.evaluate(
            "() => localStorage.getItem('prova-ai-welcomed')"
        )

        # Check if modal closed
        modal_still_visible = await mobile_page.locator("#modal-welcome").is_visible()

        result = {
            "localStorage_before": ls_before,
            "localStorage_after": ls_after,
            "modal_closed": not modal_still_visible,
            "verdict": "localStorage NOT set" if ls_after is None else "localStorage set",
        }

        print(f"\n  localStorage before click: {ls_before}")
        print(f"  localStorage after click: {ls_after}")
        print(f"  Modal closed: {not modal_still_visible}")
        print(f"  VERDICT: {result['verdict']}")

        (evidence_dir / "f2_localstorage_no_checkbox.json").write_text(
            json.dumps(result, indent=2)
        )

        # This test documents the behavior — it should pass regardless
        assert not modal_still_visible, "Modal didn't close after clicking 'Começar a Usar'"

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_modal_reappears_after_reload(self, mobile_page: Page, evidence_dir: Path):
        """Verify modal reappears after reload when checkbox was NOT checked."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Close modal without checkbox
        btn = mobile_page.locator("#modal-welcome button.btn-primary")
        await btn.scroll_into_view_if_needed()
        await btn.click(timeout=15000)
        await mobile_page.wait_for_timeout(500)

        modal_before_reload = await mobile_page.locator("#modal-welcome").is_visible()

        # Reload the page
        await mobile_page.reload(wait_until="domcontentloaded")
        try:
            await mobile_page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await mobile_page.wait_for_timeout(1500)  # Wait for 500ms setTimeout in checkFirstVisit

        modal_after_reload = await mobile_page.locator("#modal-welcome").is_visible()

        result = {
            "modal_visible_before_reload": modal_before_reload,
            "modal_visible_after_reload": modal_after_reload,
            "modal_reappeared": modal_after_reload,
            "verdict": (
                "EXPECTED: modal reappears because checkbox was not checked"
                if modal_after_reload
                else "UNEXPECTED: modal did NOT reappear"
            ),
        }

        print(f"\n  Modal visible before reload: {modal_before_reload}")
        print(f"  Modal visible after reload: {modal_after_reload}")
        print(f"  VERDICT: {result['verdict']}")

        await mobile_page.screenshot(path=str(evidence_dir / "f2_after_reload.png"))
        (evidence_dir / "f2_reload_persistence.json").write_text(
            json.dumps(result, indent=2)
        )

        # We EXPECT the modal to reappear (correct app behavior)
        assert modal_after_reload, (
            "Modal should reappear after reload when checkbox was not checked. "
            "If it doesn't, the app changed behavior."
        )

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_modal_stays_dismissed_with_checkbox(self, mobile_page: Page, evidence_dir: Path):
        """Verify modal stays dismissed after reload when checkbox IS checked."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Check the "Não mostrar novamente" checkbox
        checkbox = mobile_page.locator("#welcome-dont-show")
        await checkbox.scroll_into_view_if_needed()
        await checkbox.check()

        # Click "Começar a Usar"
        btn = mobile_page.locator("#modal-welcome button.btn-primary")
        await btn.scroll_into_view_if_needed()
        await btn.click(timeout=15000)
        await mobile_page.wait_for_timeout(500)

        # Check localStorage
        ls_value = await mobile_page.evaluate(
            "() => localStorage.getItem('prova-ai-welcomed')"
        )

        # Reload
        await mobile_page.reload(wait_until="domcontentloaded")
        try:
            await mobile_page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await mobile_page.wait_for_timeout(1500)

        modal_after_reload = await mobile_page.locator("#modal-welcome").is_visible()

        result = {
            "localStorage_value": ls_value,
            "modal_visible_after_reload": modal_after_reload,
            "verdict": (
                "CORRECT: modal stays dismissed with checkbox"
                if not modal_after_reload
                else "BUG: modal reappeared despite checkbox being checked"
            ),
        }

        print(f"\n  localStorage after checkbox: {ls_value}")
        print(f"  Modal visible after reload: {modal_after_reload}")
        print(f"  VERDICT: {result['verdict']}")

        (evidence_dir / "f2_checkbox_persistence.json").write_text(
            json.dumps(result, indent=2)
        )

        # Modal should NOT reappear when checkbox was checked
        assert not modal_after_reload, (
            "Modal reappeared after reload even though checkbox was checked. "
            "This is an app bug — localStorage not being set properly."
        )


# ============================================================
# F3: SIDEBAR VISIBILITY ON MOBILE
# ============================================================

class TestF3SidebarMobile:
    """
    F1-T3: Diagnose why sidebar tree items are unclickable on mobile.

    Hypotheses:
    A) Sidebar is hidden (translateX(-100%)) on mobile — needs hamburger click first
    B) Tree items exist but have zero size / are not visible
    C) The selector doesn't match
    """

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_sidebar_is_hidden_on_mobile(self, mobile_page: Page, evidence_dir: Path):
        """Verify sidebar is off-screen by default on iPhone 14."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Close welcome modal first
        btn = mobile_page.locator("#modal-welcome button.btn-primary")
        if await btn.count() > 0:
            await btn.scroll_into_view_if_needed()
            await btn.click(timeout=15000)
            await mobile_page.wait_for_timeout(500)

        # Check sidebar CSS state
        sidebar_state = await mobile_page.evaluate("""
            () => {
                const sidebar = document.querySelector('.sidebar');
                if (!sidebar) return { found: false };
                const style = getComputedStyle(sidebar);
                return {
                    found: true,
                    transform: style.transform,
                    position: style.position,
                    hasMobileOpen: sidebar.classList.contains('mobile-open'),
                    isVisible: sidebar.offsetParent !== null,
                    boundingBox: sidebar.getBoundingClientRect().toJSON(),
                };
            }
        """)

        print(f"\n  Sidebar found: {sidebar_state.get('found')}")
        print(f"  Transform: {sidebar_state.get('transform')}")
        print(f"  Position: {sidebar_state.get('position')}")
        print(f"  Has mobile-open class: {sidebar_state.get('hasMobileOpen')}")

        await mobile_page.screenshot(path=str(evidence_dir / "f3_sidebar_hidden.png"))
        (evidence_dir / "f3_sidebar_state.json").write_text(
            json.dumps(sidebar_state, indent=2)
        )

        assert sidebar_state.get("found"), "Sidebar element not found"
        # On mobile, sidebar should be translated off-screen
        assert not sidebar_state.get("hasMobileOpen"), (
            "Sidebar has mobile-open class by default — it should be hidden"
        )

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_sidebar_opens_via_hamburger(self, mobile_page: Page, evidence_dir: Path):
        """Verify hamburger menu opens sidebar and makes tree items clickable."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Close welcome modal
        btn = mobile_page.locator("#modal-welcome button.btn-primary")
        if await btn.count() > 0:
            await btn.scroll_into_view_if_needed()
            await btn.click(timeout=15000)
            await mobile_page.wait_for_timeout(500)

        # Find and click hamburger
        hamburger = mobile_page.locator("#hamburger-btn")
        hamburger_count = await hamburger.count()
        hamburger_visible = await hamburger.is_visible() if hamburger_count > 0 else False

        print(f"\n  Hamburger button found: {hamburger_count > 0}")
        print(f"  Hamburger visible: {hamburger_visible}")

        assert hamburger_visible, "Hamburger button not visible on mobile"

        await hamburger.click()
        await mobile_page.wait_for_timeout(500)  # Wait for slide animation

        # Check sidebar state after hamburger click
        sidebar_open = await mobile_page.evaluate(
            "() => document.querySelector('.sidebar')?.classList.contains('mobile-open') ?? false"
        )
        print(f"  Sidebar open after hamburger click: {sidebar_open}")

        await mobile_page.screenshot(path=str(evidence_dir / "f3_sidebar_open.png"))

        # Now check if tree items are visible
        tree_items = mobile_page.locator(".tree-item")
        tree_count = await tree_items.count()
        first_visible = await tree_items.first.is_visible() if tree_count > 0 else False

        print(f"  Tree items found: {tree_count}")
        print(f"  First tree item visible: {first_visible}")

        result = {
            "hamburger_visible": hamburger_visible,
            "sidebar_opened": sidebar_open,
            "tree_item_count": tree_count,
            "tree_items_visible_after_hamburger": first_visible,
            "verdict": (
                "CONFIRMED: sidebar needs hamburger click first on mobile"
                if sidebar_open and first_visible
                else "UNEXPECTED: sidebar didn't open properly"
            ),
        }

        (evidence_dir / "f3_hamburger_test.json").write_text(
            json.dumps(result, indent=2)
        )

        assert sidebar_open, "Sidebar did not open after clicking hamburger"
        assert first_visible, "Tree items still not visible after opening sidebar"

    @pytest.mark.asyncio
    @pytest.mark.diagnostic
    async def test_tree_item_selector_matches(self, mobile_page: Page, evidence_dir: Path):
        """Test which selectors match tree items on mobile."""
        await goto_production(mobile_page)
        await mobile_page.wait_for_timeout(1000)

        # Close welcome, open sidebar
        btn = mobile_page.locator("#modal-welcome button.btn-primary")
        if await btn.count() > 0:
            await btn.scroll_into_view_if_needed()
            await btn.click(timeout=15000)
            await mobile_page.wait_for_timeout(500)

        hamburger = mobile_page.locator("#hamburger-btn")
        if await hamburger.is_visible():
            await hamburger.click()
            await mobile_page.wait_for_timeout(500)

        # Test selectors the agent would try
        selectors = {
            ".tree-item": "Generic tree item class",
            ".tree-item:has-text('Todos os Alunos')": "Agent's exact selector",
            ".nav-tree .tree-item": "Scoped to nav-tree",
            "[data-type='alunos']": "Data attribute selector",
        }

        results = {}
        for selector, description in selectors.items():
            try:
                count = await mobile_page.locator(selector).count()
                results[selector] = {"description": description, "matches": count}
                print(f"  [{description}] {selector} -> {count} match(es)")
            except Exception as e:
                results[selector] = {"description": description, "matches": 0, "error": str(e)[:100]}
                print(f"  [{description}] {selector} -> ERROR: {str(e)[:100]}")

        (evidence_dir / "f3_selector_results.json").write_text(
            json.dumps(results, indent=2)
        )

        # At least the generic .tree-item should match
        generic_matches = results.get(".tree-item", {}).get("matches", 0)
        assert generic_matches > 0, "No .tree-item elements found even with sidebar open"


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "diagnostic: Diagnostic reproducer tests (require RUN_DIAGNOSTIC=1)"
    )
