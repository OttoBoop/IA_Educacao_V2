"""Test UI fixes with screenshots"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "fix-test-screenshots"

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

        # 1. Sidebar com hover em item truncado
        print("1. Testando sidebar tooltips...")
        # Hover sobre Matematica-Auditoria (truncado)
        item = page.locator(".tree-item:has-text('Matemática')")
        if await item.first.is_visible(timeout=2000):
            await item.first.hover()
            await page.wait_for_timeout(1500)  # Espera tooltip aparecer
            await page.screenshot(path=f"{OUTPUT_DIR}/01_sidebar_tooltip.png")
            print("   Capturado: Sidebar com tooltip")

        # 2. Chat com documentos melhorados
        print("2. Testando chat com documentos...")
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUTPUT_DIR}/02_chat_docs.png")
        print("   Capturado: Chat com nomes de documentos")

        # 3. Hover sobre um documento para ver tooltip
        doc = page.locator(".doc-item-mini").first
        if await doc.is_visible(timeout=2000):
            await doc.hover()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"{OUTPUT_DIR}/03_doc_tooltip.png")
            print("   Capturado: Documento com tooltip")

        # 4. Hover sobre tag de aluno
        aluno_tag = page.locator(".doc-aluno").first
        if await aluno_tag.is_visible(timeout=2000):
            await aluno_tag.hover()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=f"{OUTPUT_DIR}/04_aluno_tooltip.png")
            print("   Capturado: Tag aluno com tooltip")

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
