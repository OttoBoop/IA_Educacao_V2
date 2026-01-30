"""
Gerador de Imagens do Tutorial - Versão Melhorada
Gera screenshots limpos e profissionais para o tutorial
"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "tutorial-images-v3"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Desktop viewport para imagens de alta qualidade
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Fechar welcome modal
        await page.evaluate("""
            document.getElementById('modal-welcome').classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        print("=== GERANDO IMAGENS DO TUTORIAL V3 ===\n")

        # 1. Dashboard limpo
        print("1. Dashboard (visão geral)")
        await page.screenshot(path=f"{OUTPUT_DIR}/01-dashboard-limpo.png")

        # 2. Sidebar com navegação
        print("2. Sidebar (menu de navegação)")
        # Destacar a sidebar
        await page.evaluate("""
            document.querySelector('.sidebar').style.boxShadow = '4px 0 20px rgba(59, 130, 246, 0.3)';
        """)
        await page.wait_for_timeout(200)
        await page.screenshot(path=f"{OUTPUT_DIR}/02-sidebar-navegacao.png")
        await page.evaluate("""
            document.querySelector('.sidebar').style.boxShadow = '';
        """)

        # 3. Modal Nova Matéria (limpo, sem anotações)
        print("3. Modal Nova Matéria")
        await page.evaluate("openModal('modal-materia')")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/03-modal-nova-materia.png")
        await page.evaluate("closeModal('modal-materia')")
        await page.wait_for_timeout(300)

        # 4. Chat com IA (interface limpa)
        print("4. Chat com IA (interface)")
        await page.evaluate("showChat()")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=f"{OUTPUT_DIR}/04-chat-interface.png")

        # 5. Chat - área de input destacada
        print("5. Chat - área de mensagem")
        await page.evaluate("""
            const inputArea = document.querySelector('.chat-input-area') ||
                              document.querySelector('.chat-input-wrapper');
            if (inputArea) inputArea.style.boxShadow = '0 -4px 20px rgba(59, 130, 246, 0.3)';
        """)
        await page.wait_for_timeout(200)
        await page.screenshot(path=f"{OUTPUT_DIR}/05-chat-input-area.png")

        # 6. Todos os Alunos
        print("6. Todos os Alunos")
        await page.evaluate("showAlunos()")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/06-todos-alunos.png")

        # 7. Página de uma matéria
        print("7. Página de Matéria")
        await page.evaluate("""
            // Buscar primeira matéria disponível
            const materias = window.materias || [];
            if (materias.length > 0) {
                showMateria(materias[0].id);
            }
        """)
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/07-pagina-materia.png")

        # 8. Configurações de IA
        print("8. Configurações de IA")
        await page.evaluate("openModal('modal-settings')")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/08-configuracoes-ia.png")

        # 9. Tab de Modelos
        print("9. Configurações - Modelos")
        await page.evaluate("showSettingsTab('models')")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/09-config-modelos.png")
        await page.evaluate("closeModal('modal-settings')")

        # 10. Welcome modal (para referência)
        print("10. Welcome Modal")
        await page.evaluate("openWelcome()")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/10-welcome-modal.png")

        await browser.close()
        print(f"\n✅ Imagens salvas em: {OUTPUT_DIR}/")
        print("   Total: 10 imagens limpas sem anotações")

if __name__ == "__main__":
    asyncio.run(main())
