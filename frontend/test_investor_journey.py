"""Test mobile UI - Investor Journey Narrative"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "investor-journey"

URLS = [
    ("local", "http://localhost:8000"),
    ("online", "https://ia-educacao-v2.onrender.com"),
]

async def capture_journey(page, prefix, url):
    print(f"\n=== {prefix.upper()}: {url} ===\n")

    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"  ERRO ao acessar {url}: {e}")
        return

    # 1. Welcome Modal - Primeiro contato
    print("  1. Welcome Modal (primeiro contato)")
    await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_01_welcome.png")

    # 2. Fechar welcome e ver dashboard
    await page.evaluate("""
        const modal = document.getElementById('modal-welcome');
        if (modal) modal.classList.remove('active');
    """)
    await page.wait_for_timeout(500)
    print("  2. Dashboard")
    await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_02_dashboard.png")

    # 3. Abrir menu
    try:
        await page.click("#hamburger-btn", timeout=5000)
        await page.wait_for_timeout(500)
        print("  3. Menu aberto")
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_03_menu.png")
    except:
        print("  3. Menu (erro ao abrir)")

    # 4. Chat com IA
    try:
        await page.evaluate("showChat()")
        await page.wait_for_timeout(2000)
        print("  4. Chat com IA")
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_04_chat.png")
    except:
        print("  4. Chat (erro)")

    # 5. Abrir modal de materia
    try:
        await page.evaluate("showDashboard()")
        await page.wait_for_timeout(500)
        await page.evaluate("openModal('modal-materia')")
        await page.wait_for_timeout(500)
        print("  5. Modal Nova Materia")
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_05_modal_materia.png")
        await page.evaluate("closeModal('modal-materia')")
    except:
        print("  5. Modal (erro)")

    # 6. Configuracoes
    try:
        await page.evaluate("openModal('modal-settings')")
        await page.wait_for_timeout(500)
        print("  6. Configuracoes")
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_06_settings.png")
        await page.evaluate("closeModal('modal-settings')")
    except:
        print("  6. Settings (erro)")

    # 7. Todos os Alunos
    try:
        await page.evaluate("showAlunos()")
        await page.wait_for_timeout(1000)
        print("  7. Todos os Alunos")
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_07_alunos.png")
    except:
        print("  7. Alunos (erro)")

    # 8. Explorar materia
    try:
        await page.click("#hamburger-btn", timeout=3000)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_08_menu_materias.png")
        print("  8. Menu com materias")
    except:
        print("  8. Menu materias (erro)")

    # 9. Ajuda
    try:
        await page.evaluate("openWelcome()")
        await page.wait_for_timeout(500)
        print("  9. Ajuda/Tutorial")
        await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_09_ajuda.png")
    except:
        print("  9. Ajuda (erro)")

    print(f"  Concluido: {prefix}")

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # iPhone 14 Pro viewport
        page = await browser.new_page(viewport={"width": 393, "height": 852})

        for prefix, url in URLS:
            await capture_journey(page, prefix, url)

        await browser.close()
        print(f"\n Screenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
