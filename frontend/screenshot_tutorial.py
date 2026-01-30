"""Screenshot de todas as paginas do tutorial"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "tutorial-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Fechar modal welcome
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Abrir tutorial diretamente via JavaScript
        print("Abrindo tutorial...")
        await page.evaluate("openTutorial()")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/tutorial_page1.png")
        print("Pagina 1 capturada")

        # Navegar pelas paginas usando botao Proximo (id=tutorial-next)
        for i in range(2, 7):
            try:
                btn = page.locator("#tutorial-next")
                if await btn.is_visible(timeout=2000):
                    await btn.click()
                    await page.wait_for_timeout(800)
                    await page.screenshot(path=f"{OUTPUT_DIR}/tutorial_page{i}.png")
                    print(f"Pagina {i} capturada")
                else:
                    print(f"Botao Proximo nao encontrado na pagina {i-1}")
                    break
            except Exception as e:
                print(f"Erro na pagina {i}: {e}")
                break

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
