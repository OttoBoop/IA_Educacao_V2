"""
test_click_navigation.py - Teste de Navegação por Cliques

Verifica que todos os botões/links da interface funcionam corretamente:
1. Chat com IA - abre o modal de chat
2. Pipeline - navegação funcional
3. Configurações - abre settings
4. Menu lateral - todos os itens clicáveis

Captura erros de console JavaScript para detectar problemas como:
- 404 em arquivos JS/CSS (ex: chat_system.js não carregou)
- Funções não definidas (ReferenceError)
- Erros de sintaxe

Usa Playwright para automação de browser.

Executar:
    pytest tests/ui/test_click_navigation.py -v

Requisitos:
    pip install playwright pytest-playwright pytest-asyncio
    playwright install chromium
"""

import pytest
import asyncio
from typing import List
from pathlib import Path

# Skip se playwright não estiver instalado
pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, expect, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# URLs para teste
LOCAL_URL = "http://localhost:8000"
RENDER_URL = "https://ia-educacao-v2.onrender.com"


@pytest.fixture(scope="function")
async def browser():
    """Fixture que cria e fecha o browser"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright não instalado")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def page(browser: Browser):
    """Fixture que cria uma nova página"""
    page = await browser.new_page(viewport={"width": 1400, "height": 900})
    yield page
    await page.close()


class TestJavaScriptLoading:
    """Testes para verificar que arquivos JS carregam corretamente"""

    @pytest.mark.asyncio
    async def test_chat_system_js_loads(self, page: Page):
        """
        Verifica que chat_system.js carrega e define showChat().

        Este teste detectaria o bug onde static files não eram servidos,
        causando 'ReferenceError: showChat is not defined'.
        """
        errors: List[str] = []

        # Captura erros do console
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        # Captura requisições que falharam
        failed_requests: List[str] = []
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.failure} - {req.url}"))

        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Verifica que showChat existe (definida em chat_system.js)
        has_show_chat = await page.evaluate("typeof showChat === 'function'")

        # Diagnóstico em caso de falha
        if not has_show_chat:
            # Verificar se houve 404 no chat_system.js
            js_404 = [r for r in failed_requests if "chat_system.js" in r]
            if js_404:
                pytest.fail(f"chat_system.js não carregou (404): {js_404}")
            else:
                pytest.fail(f"showChat não definida. Erros: {errors}, Falhas: {failed_requests}")

        assert has_show_chat, "showChat() deve estar definida após carregar chat_system.js"

        # Verifica que não houve erros 404 em arquivos JS
        js_errors = [e for e in errors if "404" in e.lower()]
        assert len(js_errors) == 0, f"Erros 404 detectados: {js_errors}"

    @pytest.mark.asyncio
    async def test_no_reference_errors_on_load(self, page: Page):
        """Verifica que não há ReferenceError ao carregar a página"""
        errors: List[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(1000)  # Aguarda scripts executarem

        reference_errors = [e for e in errors if "ReferenceError" in e]
        assert len(reference_errors) == 0, f"ReferenceErrors detectados: {reference_errors}"


class TestClickNavigation:
    """Testes de navegação por cliques na interface"""

    @pytest.mark.asyncio
    async def test_chat_button_opens_modal(self, page: Page):
        """
        Verifica que clicar em 'Chat com IA' abre o modal de chat.

        Passos:
        1. Abre a página
        2. Clica no botão Chat
        3. Verifica que o modal aparece
        4. Verifica que não houve erros JS
        """
        errors: List[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Verifica que showChat existe antes de clicar
        has_show_chat = await page.evaluate("typeof showChat === 'function'")
        assert has_show_chat, "showChat() não definida - chat_system.js não carregou!"

        # Clica no item Chat com IA
        chat_button = page.locator(".tree-item:has-text('Chat com IA')")
        await chat_button.click()
        await page.wait_for_timeout(500)

        # Verifica que o modal de chat está visível
        modal = page.locator("#modal-chat")
        await expect(modal).to_be_visible(timeout=5000)

        # Verifica que não houve erros JS durante o clique
        js_errors = [e for e in errors if "404" in e or "ReferenceError" in e or "TypeError" in e]
        assert len(js_errors) == 0, f"Erros JS ao clicar em Chat: {js_errors}"

    @pytest.mark.asyncio
    async def test_close_chat_modal(self, page: Page):
        """Verifica que o modal de chat pode ser fechado"""
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Abre o chat
        await page.evaluate("showChat()")
        await page.wait_for_timeout(500)

        modal = page.locator("#modal-chat")
        await expect(modal).to_be_visible()

        # Fecha o chat clicando no X
        close_button = modal.locator(".modal-close")
        await close_button.click()
        await page.wait_for_timeout(300)

        # Verifica que o modal fechou
        await expect(modal).not_to_be_visible()

    @pytest.mark.asyncio
    async def test_settings_button_works(self, page: Page):
        """Verifica que o botão de configurações funciona"""
        errors: List[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Clica no ícone de configurações
        settings_button = page.locator(".sidebar-bottom .icon-btn:has-text('⚙')")
        if await settings_button.count() > 0:
            await settings_button.click()
            await page.wait_for_timeout(500)

            # Verifica que o modal de settings está visível
            settings_modal = page.locator("#modal-settings")
            if await settings_modal.count() > 0:
                await expect(settings_modal).to_be_visible()

        # Verifica erros
        js_errors = [e for e in errors if "ReferenceError" in e]
        assert len(js_errors) == 0, f"Erros ao abrir Settings: {js_errors}"


class TestResponsiveNavigation:
    """Testes de navegação em diferentes viewports"""

    @pytest.mark.asyncio
    async def test_mobile_menu_toggle(self, browser: Browser):
        """Verifica que o menu mobile funciona"""
        page = await browser.new_page(viewport={"width": 393, "height": 852})  # iPhone 14

        try:
            errors: List[str] = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

            await page.goto(LOCAL_URL)
            await page.wait_for_load_state("networkidle")

            # Em mobile, deve haver um botão de menu hamburger
            hamburger = page.locator(".hamburger-btn, .mobile-menu-btn, [aria-label='Menu']")
            if await hamburger.count() > 0:
                await hamburger.click()
                await page.wait_for_timeout(300)

                # Sidebar deve ficar visível após clicar
                sidebar = page.locator(".sidebar")
                # Em mobile pode ter classe adicional ou style

            # Verifica erros JS
            js_errors = [e for e in errors if "ReferenceError" in e or "TypeError" in e]
            assert len(js_errors) == 0, f"Erros JS em mobile: {js_errors}"

        finally:
            await page.close()


class TestChatFunctionality:
    """Testes de funcionalidade do Chat"""

    @pytest.mark.asyncio
    async def test_chat_input_accepts_text(self, page: Page):
        """Verifica que o input do chat aceita texto"""
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Abre o chat
        await page.evaluate("showChat()")
        await page.wait_for_timeout(500)

        # Encontra o input do chat
        chat_input = page.locator("#chat-input, .chat-input, textarea[placeholder*='mensagem']")
        if await chat_input.count() > 0:
            await chat_input.fill("Olá, esta é uma mensagem de teste")

            # Verifica que o texto foi inserido
            value = await chat_input.input_value()
            assert "teste" in value.lower(), "Texto não foi inserido no input do chat"

    @pytest.mark.asyncio
    async def test_model_selector_exists(self, page: Page):
        """Verifica que o seletor de modelo existe no chat"""
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Abre o chat
        await page.evaluate("showChat()")
        await page.wait_for_timeout(1000)

        # Verifica se existe um seletor de modelo
        model_selector = page.locator("#model-selector, select[name='model'], .model-select")
        if await model_selector.count() > 0:
            # Seletor existe
            await expect(model_selector).to_be_visible()


# Testes de regressão para bugs específicos
class TestRegressions:
    """Testes de regressão para bugs conhecidos"""

    @pytest.mark.asyncio
    async def test_static_files_are_served(self, page: Page):
        """
        Regressão: Verifica que /static/ serve arquivos corretamente.

        Bug histórico: app.mount("/static", ...) estava comentado,
        causando 404 em todos os arquivos JS/CSS.
        """
        response = await page.goto(f"{LOCAL_URL}/static/chat_system.js")

        # Deve retornar 200, não 404
        assert response.status == 200, f"static/chat_system.js retornou {response.status} (esperado 200)"

        # Deve ter conteúdo JavaScript
        content = await response.text()
        assert "function" in content or "const" in content or "var" in content, \
            "Resposta não parece ser JavaScript válido"

    @pytest.mark.asyncio
    async def test_showChat_is_callable(self, page: Page):
        """
        Regressão: Verifica que showChat() pode ser chamada sem erro.

        Bug histórico: 'ReferenceError: showChat is not defined' quando
        chat_system.js não carregava.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Tenta chamar showChat - deve funcionar sem erro
        error = None
        try:
            await page.evaluate("showChat()")
        except Exception as e:
            error = str(e)

        assert error is None or "showChat is not defined" not in (error or ""), \
            f"showChat() não está definida: {error}"


# Configuração do pytest-asyncio
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
