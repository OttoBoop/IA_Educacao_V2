"""Screenshot das mudanças da Fase 3 - Documentos Gerados"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "fase3-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        # 1. Ir para o dashboard
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Screenshot com modal de boas-vindas
        await page.screenshot(path=f"{OUTPUT_DIR}/01_welcome_modal.png")
        print("1. Welcome modal capturado")

        # Fechar modal de boas-vindas - usar JavaScript diretamente
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        await page.screenshot(path=f"{OUTPUT_DIR}/02_dashboard.png")
        print("2. Dashboard capturado")

        # 3. Ir para o Chat para ver filtros
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUTPUT_DIR}/03_chat_todos.png")
        print("3. Chat modo 'Todos' capturado")

        # 4. Clicar em "Filtrar" para ver o painel de filtros
        try:
            await page.click("button[data-mode='filtered']")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/04_chat_filtrar.png")
            print("4. Chat modo 'Filtrar' capturado")
        except Exception as e:
            print(f"Erro ao clicar em Filtrar: {e}")

        # 5. Navegar para uma matéria
        await page.click(".tree-item:has-text('Inglês')")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{OUTPUT_DIR}/05_materia.png")
        print("5. Matéria capturada")

        # 6. Expandir a matéria e clicar em uma turma (via sidebar)
        try:
            expand_btn = page.locator(".tree-item:has-text('Inglês') .tree-toggle").first
            await expand_btn.click()
            await page.wait_for_timeout(800)

            turma_item = page.locator(".tree-item:has-text('9')").first
            if await turma_item.is_visible(timeout=2000):
                await turma_item.click()
                await page.wait_for_timeout(1500)
                await page.screenshot(path=f"{OUTPUT_DIR}/06_turma.png")
                print("6. Turma capturada")
        except Exception as e:
            print(f"Erro na turma: {e}")

        # 7. Navegar para atividade
        try:
            expand_turma = page.locator(".tree-item:has-text('9') .tree-toggle").first
            await expand_turma.click()
            await page.wait_for_timeout(500)

            ativ_item = page.locator(".tree-item:has-text('Test')").first
            if await ativ_item.is_visible(timeout=2000):
                await ativ_item.click()
                await page.wait_for_timeout(1500)
                await page.screenshot(path=f"{OUTPUT_DIR}/07_atividade.png")
                print("7. Atividade capturada")
        except Exception as e:
            print(f"Erro na atividade: {e}")

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
