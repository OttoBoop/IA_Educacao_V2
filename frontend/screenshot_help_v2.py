"""Screenshot das melhorias de ajuda v2"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "help-v2-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Fechar modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # 1. Matéria com botão de ajuda
        await page.click(".tree-item:has-text('Inglês')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/01_materia_com_help.png")
        print("1. Matéria com botão ajuda capturada")

        # Clicar no botão de ajuda
        try:
            await page.click(".section-help")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/02_materia_help_panel.png")
            print("2. Painel de ajuda da Matéria capturado")
        except Exception as e:
            print(f"Erro matéria: {e}")

        # 2. Turma com botão de ajuda
        await page.evaluate("""
            document.querySelectorAll('.tree-item').forEach(item => {
                if (item.textContent.includes('Inglês')) {
                    const toggle = item.querySelector('.tree-toggle');
                    if (toggle) toggle.click();
                }
            });
        """)
        await page.wait_for_timeout(500)

        await page.click(".tree-item:has-text('9º Ano A')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/03_turma_com_help.png")
        print("3. Turma com botão ajuda capturada")

        # Clicar no botão de ajuda
        try:
            await page.click(".section-help")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/04_turma_help_panel.png")
            print("4. Painel de ajuda da Turma capturado")

            # Clicar na aba de atividade
            aba = page.locator(".help-tab:has-text('Criar Atividade')")
            if await aba.is_visible(timeout=2000):
                await aba.click()
                await page.wait_for_timeout(500)
                await page.screenshot(path=f"{OUTPUT_DIR}/05_turma_aba_atividade.png")
                print("5. Turma - Aba Atividade capturada")
        except Exception as e:
            print(f"Erro turma: {e}")

        # 3. Chat com ajuda
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2000)

        try:
            await page.click(".section-help")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/06_chat_help_professor.png")
            print("6. Chat - Aba Professor capturada")

            # Aba aluno
            aba = page.locator(".help-tab:has-text('Para Aluno')")
            if await aba.is_visible(timeout=2000):
                await aba.click()
                await page.wait_for_timeout(500)
                await page.screenshot(path=f"{OUTPUT_DIR}/07_chat_help_aluno.png")
                print("7. Chat - Aba Aluno capturada")

            # Aba filtros
            aba = page.locator(".help-tab:has-text('Usar Filtros')")
            if await aba.is_visible(timeout=2000):
                await aba.click()
                await page.wait_for_timeout(500)
                await page.screenshot(path=f"{OUTPUT_DIR}/08_chat_help_filtros.png")
                print("8. Chat - Aba Filtros capturada")
        except Exception as e:
            print(f"Erro chat: {e}")

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
