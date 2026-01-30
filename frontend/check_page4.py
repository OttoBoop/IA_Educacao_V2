"""
Verificar pagina 4 do tutorial (Chat)
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"

def check_page4():
    print("[*] Verificando pagina 4 (Chat) no Render...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            page.goto("https://ia-educacao-v2.onrender.com", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)

            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(300)

            page.evaluate("openTutorial()")
            page.wait_for_timeout(1000)

            # Ir para pagina 4
            for _ in range(3):
                page.click("#tutorial-next")
                page.wait_for_timeout(500)

            page.screenshot(path=str(OUTPUT_DIR / "render_FINAL_page4.png"))
            print("[OK] Pagina 4 capturada: render_FINAL_page4.png")

        except Exception as e:
            print(f"[ERRO] {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_page4()
