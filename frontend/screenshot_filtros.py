"""Screenshot dos filtros melhorados"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "filtros-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Fechar modal de boas-vindas
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Ir para o Chat
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)

        # 1. Screenshot com modo "Todos"
        await page.screenshot(path=f"{OUTPUT_DIR}/01_chat_todos.png")
        print("1. Chat modo 'Todos' capturado")

        # 2. Clicar em "Filtrar"
        await page.click("button[data-mode='filtered']")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/02_filtros_fechados.png")
        print("2. Filtros fechados capturados")

        # 3. Abrir dropdown de alunos
        try:
            await page.click("#filter-alunos-container .filter-dropdown-trigger")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/03_dropdown_alunos.png")
            print("3. Dropdown de alunos aberto capturado")

            # 4. Selecionar alguns alunos
            items = await page.locator("#filter-alunos-container .filter-dropdown-item").all()
            if len(items) >= 2:
                await items[0].click()
                await page.wait_for_timeout(200)
                await items[1].click()
                await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/04_alunos_selecionados.png")
            print("4. Alunos selecionados capturados")

            # Fechar dropdown
            await page.click("#filter-alunos-container .filter-dropdown-trigger")
            await page.wait_for_timeout(300)
        except Exception as e:
            print(f"Erro no dropdown de alunos: {e}")

        # 5. Abrir dropdown de matérias
        try:
            await page.click("#filter-materias-container .filter-dropdown-trigger")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/05_dropdown_materias.png")
            print("5. Dropdown de matérias aberto capturado")

            # Selecionar uma matéria
            item = page.locator("#filter-materias-container .filter-dropdown-item").first
            if await item.is_visible(timeout=1000):
                await item.click()
                await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/06_materia_selecionada.png")
            print("6. Matéria selecionada capturada")

            # Fechar dropdown
            await page.click("#filter-materias-container .filter-dropdown-trigger")
            await page.wait_for_timeout(300)
        except Exception as e:
            print(f"Erro no dropdown de matérias: {e}")

        # 7. Ver dropdown de turmas (deve ter opções agora)
        try:
            await page.click("#filter-turmas-container .filter-dropdown-trigger")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/07_dropdown_turmas.png")
            print("7. Dropdown de turmas capturado")
        except Exception as e:
            print(f"Erro no dropdown de turmas: {e}")

        # 8. Screenshot final com chips visíveis
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUTPUT_DIR}/08_filtros_com_chips.png")
        print("8. Filtros com chips capturados")

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
