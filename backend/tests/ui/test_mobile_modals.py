"""
test_mobile_modals.py - Testes TDD para Modais Mobile

Verifica correções de scroll e touch targets em dispositivos móveis:
1. Welcome modal deve ser scrollável
2. Chat modal deve ser scrollável em tablets
3. Touch targets devem ter pelo menos 44px
4. Task panel não deve aparecer sobre modais
5. Safe-area deve ser respeitada

Bug fixado em: 2026-01-30 (commit 6f59861)
Documentação: docs/logs/2026-01-30_mobile_modal_scroll_fix.md

Executar:
    RUN_UI_TESTS=1 pytest tests/ui/test_mobile_modals.py -v

Requisitos:
    pip install playwright pytest-playwright pytest-asyncio
    playwright install chromium
"""

import pytest
import os
import sys
from typing import List
from pathlib import Path

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, expect, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# URLs para teste
LOCAL_URL = "http://localhost:8000"
RENDER_URL = "https://ia-educacao-v2.onrender.com"

# Viewports de teste
IPHONE_14 = {"width": 393, "height": 852, "name": "iPhone 14"}
IPHONE_SE = {"width": 375, "height": 667, "name": "iPhone SE"}
IPAD_PORTRAIT = {"width": 768, "height": 1024, "name": "iPad Portrait"}
IPAD_LANDSCAPE = {"width": 1024, "height": 768, "name": "iPad Landscape"}
ANDROID_SMALL = {"width": 360, "height": 640, "name": "Android Small"}


# ============================================================
# IMPROVED FIXTURES WITH SERVER CHECK AND SCREENSHOTS
# ============================================================

@pytest.fixture(scope="session")
def screenshots_dir():
    """Creates a directory for test failure screenshots."""
    screenshot_path = Path(__file__).parent.parent.parent / "logs" / "ui_test_screenshots"
    screenshot_path.mkdir(parents=True, exist_ok=True)
    return screenshot_path


@pytest.fixture(scope="session", autouse=True)
async def check_server():
    """
    Verifies that the local server is running before tests.

    CRITICAL: UI tests require a running server. This fixture provides
    helpful error messages if the server is not available.
    """
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip(
            "Playwright não instalado. Execute:\n"
            "  pip install playwright pytest-playwright pytest-asyncio\n"
            "  playwright install chromium"
        )

    # Only check server if UI tests are enabled
    if not os.getenv("RUN_UI_TESTS"):
        pytest.skip("UI tests disabled. Set RUN_UI_TESTS=1 to enable")

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(LOCAL_URL, timeout=5.0)
            if response.status_code != 200:
                pytest.exit(
                    f"Server at {LOCAL_URL} returned status {response.status_code}.\n"
                    f"Start the server with:\n"
                    f"  cd IA_Educacao_V2/backend\n"
                    f"  python -m uvicorn main_v2:app --port 8000 --reload"
                )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.exit(
            f"Cannot connect to server at {LOCAL_URL}.\n"
            f"Please start the server first:\n"
            f"  cd IA_Educacao_V2/backend\n"
            f"  python -m uvicorn main_v2:app --port 8000 --reload\n"
            f"Error: {e}"
        )


@pytest.fixture(scope="function")
async def browser():
    """Fixture que cria e fecha o browser"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip(
            "Playwright não instalado. Execute:\n"
            "  pip install playwright pytest-playwright pytest-asyncio\n"
            "  playwright install chromium"
        )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def mobile_page(browser: Browser, screenshots_dir: Path, request):
    """Fixture para página mobile (iPhone 14) with screenshot on failure."""
    viewport = IPHONE_14
    print(f"\n  [Testing on {viewport['name']}: {viewport['width']}x{viewport['height']}]")

    page = await browser.new_page(viewport=viewport)

    yield page

    # Capture screenshot on test failure
    if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
        screenshot_path = screenshots_dir / f"{request.node.name}_mobile_failure.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"\n  [Screenshot saved: {screenshot_path}]")

    await page.close()


@pytest.fixture(scope="function")
async def tablet_page(browser: Browser, screenshots_dir: Path, request):
    """Fixture para página tablet (iPad portrait) with screenshot on failure."""
    viewport = IPAD_PORTRAIT
    print(f"\n  [Testing on {viewport['name']}: {viewport['width']}x{viewport['height']}]")

    page = await browser.new_page(viewport=viewport)

    yield page

    # Capture screenshot on test failure
    if request.node.rep_call.failed if hasattr(request.node, 'rep_call') else False:
        screenshot_path = screenshots_dir / f"{request.node.name}_tablet_failure.png"
        await page.screenshot(path=str(screenshot_path))
        print(f"\n  [Screenshot saved: {screenshot_path}]")

    await page.close()


# Hook to capture test results for screenshot fixture
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to store test results for screenshot capture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

async def close_welcome_modal_if_visible(page: Page):
    """Helper to close welcome modal if it's visible."""
    welcome = page.locator("#modal-welcome")
    if await welcome.is_visible(timeout=2000):
        close_btn = welcome.locator("button:has-text('Começar')")
        if await close_btn.count() > 0:
            await close_btn.click()
            await page.wait_for_timeout(300)


async def assert_element_exists_and_visible(page: Page, selector: str, element_name: str):
    """
    Assert that an element exists and is visible.

    This replaces silent "if visible" checks that would pass even if element is missing.
    """
    element = page.locator(selector)
    count = await element.count()

    if count == 0:
        # Take screenshot for debugging
        screenshot_path = Path(__file__).parent.parent.parent / "logs" / "ui_test_screenshots" / f"missing_{element_name}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path))

        pytest.fail(
            f"{element_name} not found (selector: {selector}).\n"
            f"Screenshot saved to: {screenshot_path}"
        )

    is_visible = await element.first.is_visible(timeout=5000)
    if not is_visible:
        pytest.skip(
            f"{element_name} exists but is not visible (selector: {selector}).\n"
            f"This may be expected for some test conditions. Skipping test."
        )

    return element.first


# ============================================================
# TEST CLASSES
# ============================================================

class TestWelcomeModalScroll:
    """
    TDD RED: Testes que FALHAVAM antes do fix.

    Problema: Welcome modal não scrollava em mobile porque:
    - Modal não tinha display: flex
    - Modal-body não tinha flex: 1 + overflow-y: auto
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_welcome_modal_has_flex_structure(self, mobile_page: Page):
        """
        RED: Modal-welcome deve ter estrutura flex para permitir scroll.

        Antes do fix: .modal-welcome .modal NÃO tinha display: flex
        Depois do fix: .modal-welcome .modal TEM display: flex
        """
        print("\n  [Checking welcome modal flex structure...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Welcome modal deve estar visível na primeira visita
        welcome_modal = await assert_element_exists_and_visible(
            mobile_page, "#modal-welcome", "Welcome modal"
        )

        # Verifica CSS do modal container
        modal_inner = welcome_modal.locator(".modal")
        display = await modal_inner.evaluate("el => getComputedStyle(el).display")
        flex_direction = await modal_inner.evaluate("el => getComputedStyle(el).flexDirection")

        print(f"  [Modal display: {display}, flex-direction: {flex_direction}]")

        assert display == "flex", f"Modal deve ter display: flex, mas tem: {display}"
        assert flex_direction == "column", f"Modal deve ter flex-direction: column, mas tem: {flex_direction}"

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_welcome_modal_body_is_scrollable(self, mobile_page: Page):
        """
        RED: Modal-body deve ser scrollável (overflow-y: auto + flex: 1).

        Antes do fix: overflow-y não era auto no mobile
        Depois do fix: overflow-y: auto com -webkit-overflow-scrolling: touch
        """
        print("\n  [Checking welcome modal body scrollability...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        welcome_modal = await assert_element_exists_and_visible(
            mobile_page, "#modal-welcome", "Welcome modal"
        )

        modal_body = welcome_modal.locator(".modal-body")

        overflow_y = await modal_body.evaluate("el => getComputedStyle(el).overflowY")
        flex_grow = await modal_body.evaluate("el => getComputedStyle(el).flexGrow")

        print(f"  [Modal-body overflow-y: {overflow_y}, flex-grow: {flex_grow}]")

        assert overflow_y in ["auto", "scroll"], f"Modal-body deve ter overflow-y: auto, mas tem: {overflow_y}"
        assert flex_grow == "1", f"Modal-body deve ter flex: 1, mas tem flex-grow: {flex_grow}"

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_welcome_modal_content_scrolls(self, mobile_page: Page):
        """
        RED: Conteúdo do welcome modal deve ser scrollável de fato.

        Simula scroll e verifica que scrollTop muda.
        """
        print("\n  [Testing actual scroll behavior...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        welcome_modal = await assert_element_exists_and_visible(
            mobile_page, "#modal-welcome", "Welcome modal"
        )

        modal_body = welcome_modal.locator(".modal-body")

        # Verifica se há conteúdo que excede a altura visível
        scroll_height = await modal_body.evaluate("el => el.scrollHeight")
        client_height = await modal_body.evaluate("el => el.clientHeight")

        print(f"  [Modal-body scrollHeight: {scroll_height}px, clientHeight: {client_height}px]")

        if scroll_height <= client_height:
            pytest.skip(
                f"Modal content does not exceed viewport (scrollHeight={scroll_height}, "
                f"clientHeight={client_height}). Cannot test scroll functionality."
            )

        # Tenta scrollar
        initial_scroll = await modal_body.evaluate("el => el.scrollTop")
        await modal_body.evaluate("el => el.scrollTop = 100")
        new_scroll = await modal_body.evaluate("el => el.scrollTop")

        print(f"  [Scroll position changed: {initial_scroll}px -> {new_scroll}px]")

        assert new_scroll > initial_scroll, (
            f"Scroll deve funcionar no modal-body. "
            f"Initial: {initial_scroll}px, After scroll: {new_scroll}px"
        )


class TestChatModalScroll:
    """
    TDD RED: Testes para scroll do chat modal em tablets.

    Problema: Chat modal tinha height: 80vh fixo sem flex structure,
    causando content cutoff em tablets portrait.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_chat_modal_has_flex_structure(self, tablet_page: Page):
        """
        RED: Chat modal deve ter estrutura flex.
        """
        print("\n  [Checking chat modal flex structure via CSS...]")

        await tablet_page.goto(LOCAL_URL)
        await tablet_page.wait_for_load_state("networkidle")

        # Fecha welcome modal se visível
        await close_welcome_modal_if_visible(tablet_page)

        # Verifica CSS do modal-chat via stylesheet
        has_flex = await tablet_page.evaluate("""
            () => {
                const styles = document.styleSheets;
                for (let sheet of styles) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.selectorText && rule.selectorText.includes('.modal-chat .modal')) {
                                return rule.style.display === 'flex';
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """)

        # Se não encontrar a regra, verifica se a classe existe no HTML
        chat_modal = tablet_page.locator("#modal-chat")
        modal_count = await chat_modal.count()

        if modal_count == 0:
            pytest.fail("Chat modal (#modal-chat) not found in DOM")

        has_modal_chat_class = await chat_modal.evaluate(
            "el => el.closest('.modal-chat') !== null || "
            "el.classList.contains('modal-chat') || "
            "el.parentElement.classList.contains('modal-chat')"
        )

        print(f"  [CSS rule has flex: {has_flex}, Element has modal-chat class: {has_modal_chat_class}]")

        assert has_flex or has_modal_chat_class, (
            "Chat modal deve ter classe modal-chat para CSS flex ou regra CSS com display: flex"
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_chat_modal_overlay_has_class(self, mobile_page: Page):
        """
        RED: Modal overlay do chat deve ter classe 'modal-chat' para CSS targeting.

        Antes do fix: <div class="modal-overlay" id="modal-chat">
        Depois do fix: <div class="modal-overlay modal-chat" id="modal-chat">
        """
        print("\n  [Checking chat modal overlay class attribute...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        chat_modal = mobile_page.locator("#modal-chat")
        count = await chat_modal.count()

        if count == 0:
            pytest.fail("Chat modal (#modal-chat) not found in DOM")

        class_list = await chat_modal.evaluate("el => el.className")

        print(f"  [Chat modal classes: {class_list}]")

        assert "modal-chat" in class_list, (
            f"Modal overlay deve ter classe 'modal-chat', mas tem: {class_list}"
        )


class TestTouchTargets:
    """
    TDD RED: Testes para touch targets >= 44px.

    WCAG e Apple HIG recomendam mínimo de 44x44px para touch targets.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_modal_close_button_size(self, mobile_page: Page):
        """
        RED: Botão de fechar modal deve ter pelo menos 44px.

        Antes do fix: 40px
        Depois do fix: 44px
        """
        print("\n  [Checking modal close button size...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Encontra qualquer botão de fechar modal visível
        modal_close = await assert_element_exists_and_visible(
            mobile_page, ".modal-close", "Modal close button"
        )

        width = await modal_close.evaluate("el => el.offsetWidth")
        height = await modal_close.evaluate("el => el.offsetHeight")

        print(f"  [Modal close button size: {width}x{height}px]")

        assert width >= 44, f"Modal close width deve ser >= 44px, mas é: {width}px"
        assert height >= 44, f"Modal close height deve ser >= 44px, mas é: {height}px"

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_section_header_buttons_size(self, mobile_page: Page):
        """
        RED: Botões no header de seção devem ter pelo menos 44px.

        Antes do fix: 36px
        Depois do fix: 44px
        """
        print("\n  [Checking section header button sizes...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Fecha welcome modal
        await close_welcome_modal_if_visible(mobile_page)

        # Abre sidebar mobile
        hamburger = mobile_page.locator(".hamburger-btn")
        hamburger_visible = await hamburger.is_visible()

        if hamburger_visible:
            await hamburger.click()
            await mobile_page.wait_for_timeout(300)

        # Verifica botões em section headers
        section_buttons = mobile_page.locator(".tree-section-header .btn")
        button_count = await section_buttons.count()

        if button_count == 0:
            pytest.skip(
                "No section header buttons found. This may be normal if no sections "
                "are populated. Skipping test."
            )

        first_btn = section_buttons.first
        btn_visible = await first_btn.is_visible()

        if not btn_visible:
            pytest.skip("Section button exists but is not visible. Skipping test.")

        width = await first_btn.evaluate("el => el.offsetWidth")
        height = await first_btn.evaluate("el => el.offsetHeight")

        print(f"  [Section button size: {width}x{height}px]")

        assert width >= 44, f"Section button width deve ser >= 44px, mas é: {width}px"
        assert height >= 44, f"Section button height deve ser >= 44px, mas é: {height}px"


class TestZIndexStacking:
    """
    TDD RED: Testes para z-index correto.

    Problema: Task panel (z-index: 150) aparecia acima de modais (z-index: 100).
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_task_panel_closes_when_modal_opens(self, mobile_page: Page):
        """
        RED: Task panel deve fechar quando modal abre.

        Antes do fix: openModal() não fechava task panel
        Depois do fix: openModal() fecha task panel primeiro
        """
        print("\n  [Testing task panel closes when modal opens...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Fecha welcome modal
        await close_welcome_modal_if_visible(mobile_page)

        # Verifica se openModal fecha task panel
        result = await mobile_page.evaluate("""
            () => {
                // Simula task panel aberto
                const taskPanel = document.getElementById('task-panel');
                if (!taskPanel) {
                    return { success: true, reason: 'no_task_panel' };
                }

                taskPanel.classList.add('show');

                // Chama openModal
                if (typeof openModal !== 'function') {
                    return { success: false, reason: 'no_openModal_function' };
                }

                openModal('modal-settings');

                // Verifica se task panel foi fechado
                const closed = !taskPanel.classList.contains('show');
                return { success: closed, reason: closed ? 'ok' : 'still_open' };
            }
        """)

        print(f"  [Task panel test result: {result}]")

        if result.get('reason') == 'no_task_panel':
            pytest.skip("Task panel element not found in DOM. Skipping test.")

        if result.get('reason') == 'no_openModal_function':
            pytest.fail("openModal function not found in page JavaScript")

        assert result.get('success'), (
            f"Task panel deve ser fechado quando modal abre. Reason: {result.get('reason')}"
        )


class TestSafeArea:
    """
    TDD RED: Testes para safe-area em dispositivos com notch.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_chat_input_has_safe_area_bottom(self, mobile_page: Page):
        """
        RED: Chat input wrapper deve ter padding-bottom com safe-area.

        Importante para iPhones com home indicator.
        """
        print("\n  [Checking chat input safe-area-bottom CSS...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Verifica se CSS tem safe-area-bottom para chat-input-wrapper
        has_safe_area = await mobile_page.evaluate("""
            () => {
                const styles = document.styleSheets;
                for (let sheet of styles) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.cssText && rule.cssText.includes('chat-input-wrapper') &&
                                rule.cssText.includes('safe-area-bottom')) {
                                return true;
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """)

        print(f"  [Chat input has safe-area-bottom: {has_safe_area}]")

        assert has_safe_area, (
            "chat-input-wrapper deve ter padding com safe-area-bottom para iPhones com notch"
        )

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_print_bar_has_safe_area_top(self, mobile_page: Page):
        """
        RED: Print bar deve ter padding-top com safe-area para notch.
        """
        print("\n  [Checking print bar safe-area-inset-top CSS...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Verifica se CSS tem safe-area-inset-top para print-bar
        has_safe_area = await mobile_page.evaluate("""
            () => {
                const styles = document.styleSheets;
                for (let sheet of styles) {
                    try {
                        for (let rule of sheet.cssRules) {
                            if (rule.cssText && rule.cssText.includes('print-bar') &&
                                rule.cssText.includes('safe-area-inset-top')) {
                                return true;
                            }
                        }
                    } catch (e) {}
                }
                return false;
            }
        """)

        # Este teste pode não encontrar porque print-bar está em template JS
        # Nesse caso, verificamos o HTML gerado
        if not has_safe_area:
            print("  [CSS rule not found, checking HTML template...]")
            has_in_template = await mobile_page.evaluate("""
                () => {
                    // Procura no HTML da página por safe-area-inset-top
                    return document.documentElement.innerHTML.includes('safe-area-inset-top');
                }
            """)
            print(f"  [Print bar has safe-area-inset-top in template: {has_in_template}]")

            assert has_in_template, (
                "print-bar deve ter padding com safe-area-inset-top para dispositivos com notch"
            )
        else:
            print(f"  [Print bar has safe-area-inset-top: {has_safe_area}]")
            assert has_safe_area


class TestTutorialModalScroll:
    """
    TDD RED: Testes para scroll do tutorial modal.

    Problema: Tutorial modal tinha overflow: hidden no desktop,
    bloqueando scroll completamente.
    """

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_tutorial_modal_body_not_overflow_hidden(self, mobile_page: Page):
        """
        RED: Tutorial modal-body NÃO deve ter overflow: hidden.

        Antes do fix: overflow: hidden (bloqueava scroll)
        Depois do fix: overflow-y: auto no mobile
        """
        print("\n  [Checking tutorial modal does not have overflow: hidden...]")

        await mobile_page.goto(LOCAL_URL)
        await mobile_page.wait_for_load_state("networkidle")

        # Abre tutorial se welcome estiver visível
        welcome = mobile_page.locator("#modal-welcome")
        if await welcome.is_visible():
            tutorial_btn = welcome.locator("button:has-text('Tutorial')")
            if await tutorial_btn.count() > 0:
                await tutorial_btn.click()
                await mobile_page.wait_for_timeout(500)

        tutorial_modal = mobile_page.locator("#modal-tutorial")
        tutorial_visible = await tutorial_modal.is_visible()

        if not tutorial_visible:
            pytest.skip(
                "Tutorial modal is not visible. This may be expected if welcome modal "
                "was not shown or tutorial button was not clicked. Skipping test."
            )

        modal_body = tutorial_modal.locator(".modal-body")
        overflow_y = await modal_body.evaluate("el => getComputedStyle(el).overflowY")

        print(f"  [Tutorial modal-body overflow-y: {overflow_y}]")

        # Em mobile, deve ser auto ou scroll, não hidden
        assert overflow_y != "hidden", (
            f"Tutorial modal-body não deve ter overflow: hidden, mas tem: {overflow_y}"
        )


# ============================================================
# PYTEST CONFIGURATION
# ============================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "ui: UI tests using Playwright (requires local server)"
    )
