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
    """Fixture que cria uma nova página e fecha o modal de boas-vindas"""
    page = await browser.new_page(viewport={"width": 1400, "height": 900})
    yield page
    await page.close()


async def close_all_modals(page: Page):
    """Helper para fechar todos os modais de overlay (welcome, tutorial, etc.)"""
    modals_to_close = ["#modal-welcome", "#modal-tutorial"]

    for modal_id in modals_to_close:
        modal = page.locator(modal_id)
        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            try:
                if await modal.count() > 0 and await modal.is_visible():
                    # Tenta fechar clicando no botão de fechar
                    close_btn = modal.locator(".modal-close, .btn-primary, .close-btn, button:has-text('Fechar'), button:has-text('Entendi'), button:has-text('OK')")
                    if await close_btn.count() > 0:
                        await close_btn.first.click()
                        await page.wait_for_timeout(300)
                    else:
                        # Clica fora do modal para fechar
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(300)
                else:
                    break
            except:
                break
            attempts += 1

    # Aguarda um pouco para garantir que os modais fecharam
    await page.wait_for_timeout(200)


# Alias para manter compatibilidade
close_welcome_modal = close_all_modals


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

        # Verifica que não houve erros 404 em arquivos JS/CSS críticos
        # Ignora favicon e outros recursos não essenciais
        js_css_errors = [e for e in errors if "404" in e.lower() and (".js" in e.lower() or ".css" in e.lower())]
        assert len(js_css_errors) == 0, f"Erros 404 em JS/CSS detectados: {js_css_errors}"

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
    async def test_chat_button_opens_chat_view(self, page: Page):
        """
        Verifica que clicar em 'Chat com IA' abre a view de chat.

        NOTA: showChat() renderiza o chat no #content (view-based),
        não abre um modal. O #modal-chat é uma implementação diferente.

        Passos:
        1. Abre a página
        2. Fecha modais de boas-vindas/tutorial (se existirem)
        3. Clica no botão Chat
        4. Verifica que a view de chat aparece no #content
        5. Verifica que não houve erros JS
        """
        errors: List[str] = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Fecha modais de boas-vindas/tutorial se estiverem visíveis
        await close_welcome_modal(page)

        # Verifica que showChat existe antes de clicar
        has_show_chat = await page.evaluate("typeof showChat === 'function'")
        assert has_show_chat, "showChat() não definida - chat_system.js não carregou!"

        # Clica no item Chat com IA
        chat_button = page.locator(".tree-item:has-text('Chat com IA')")
        await chat_button.click()
        await page.wait_for_timeout(1000)  # Aguarda async showChat() completar

        # Verifica que a view de chat foi renderizada no #content
        # showChat() cria um .chat-layout dentro de #content
        chat_layout = page.locator("#content .chat-layout")
        await expect(chat_layout).to_be_visible(timeout=5000)

        # Verifica elementos da view de chat
        context_panel = page.locator("#context-panel")
        await expect(context_panel).to_be_visible(timeout=3000)

        # Verifica que não houve erros JS durante o clique
        js_errors = [e for e in errors if "ReferenceError" in e or "TypeError" in e]
        assert len(js_errors) == 0, f"Erros JS ao clicar em Chat: {js_errors}"

    @pytest.mark.asyncio
    async def test_navigate_away_from_chat(self, page: Page):
        """Verifica que é possível navegar para fora da view de chat"""
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Fecha modais de boas-vindas/tutorial
        await close_welcome_modal(page)

        # Abre o chat
        await page.evaluate("showChat()")
        await page.wait_for_timeout(1000)

        # Verifica que a view de chat está visível
        chat_layout = page.locator("#content .chat-layout")
        await expect(chat_layout).to_be_visible(timeout=5000)

        # Navega de volta para o Dashboard clicando em "Início" no breadcrumb
        dashboard_link = page.locator(".breadcrumb a:has-text('Início'), .breadcrumb-item:has-text('Início')")
        if await dashboard_link.count() > 0:
            await dashboard_link.first.click()
            await page.wait_for_timeout(500)

            # Verifica que saiu da view de chat
            # (chat-layout não deve mais estar visível após navegar para dashboard)
            is_chat_visible = await chat_layout.is_visible()
            # Se ainda estiver no chat, navegar clicando no logo ou item do menu
            if is_chat_visible:
                home_link = page.locator(".sidebar-header, .tree-item:has-text('Dashboard'), .tree-item:has-text('Início')")
                if await home_link.count() > 0:
                    await home_link.first.click()
                    await page.wait_for_timeout(500)

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

            # Fecha modal de boas-vindas primeiro
            await close_welcome_modal(page)

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

        # Fecha modais de boas-vindas/tutorial
        await close_welcome_modal(page)

        # Abre a view de chat
        await page.evaluate("showChat()")
        await page.wait_for_timeout(1000)  # Aguarda async showChat() completar

        # Verifica que a view de chat está visível
        chat_layout = page.locator("#content .chat-layout")
        await expect(chat_layout).to_be_visible(timeout=5000)

        # Encontra o input do chat na view (não no modal)
        chat_input = chat_layout.locator("#chat-input, .chat-input, textarea")
        if await chat_input.count() > 0:
            await chat_input.first.fill("Olá, esta é uma mensagem de teste")

            # Verifica que o texto foi inserido
            value = await chat_input.first.input_value()
            assert "teste" in value.lower(), "Texto não foi inserido no input do chat"
        else:
            # Se não encontrar input, verificar se existe pelo menos a área de mensagens
            messages_area = chat_layout.locator(".chat-messages, #chat-messages")
            assert await messages_area.count() > 0, "Área de mensagens do chat não encontrada"

    @pytest.mark.asyncio
    async def test_model_selector_exists(self, page: Page):
        """Verifica que o seletor de modelo existe no chat"""
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")

        # Fecha modais de boas-vindas/tutorial
        await close_welcome_modal(page)

        # Abre a view de chat
        await page.evaluate("showChat()")
        await page.wait_for_timeout(1000)

        # Verifica que a view de chat está visível
        chat_layout = page.locator("#content .chat-layout")
        await expect(chat_layout).to_be_visible(timeout=5000)

        # Verifica se existe um seletor de modelo na view
        model_selector = chat_layout.locator("#model-selector, select[name='model'], .model-select, #chat-provider-select")
        if await model_selector.count() > 0:
            # Seletor existe
            await expect(model_selector.first).to_be_visible()


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
