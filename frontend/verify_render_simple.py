"""
Verificacao simples do Render
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"
OUTPUT_DIR.mkdir(exist_ok=True)

def verify_render():
    print("[*] Verificando Render...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            page.goto("https://ia-educacao-v2.onrender.com", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Screenshot inicial
            page.screenshot(path=str(OUTPUT_DIR / "render_initial.png"))
            print("[OK] Screenshot inicial capturado")

            # Fechar welcome
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(500)

            # Screenshot apos fechar welcome
            page.screenshot(path=str(OUTPUT_DIR / "render_dashboard.png"))
            print("[OK] Dashboard capturado")

            # Tentar abrir tutorial via botao de ajuda
            page.click("#btn-help")
            page.wait_for_timeout(1000)

            page.screenshot(path=str(OUTPUT_DIR / "render_tutorial_menu.png"))
            print("[OK] Menu de ajuda capturado")

            print("\n[OK] Verificacao concluida!")
            print(f"[*] Screenshots em: {OUTPUT_DIR}")

        except Exception as e:
            print(f"[ERRO] {e}")
            page.screenshot(path=str(OUTPUT_DIR / "render_error.png"))
            print("[*] Screenshot de erro salvo")
        finally:
            browser.close()


if __name__ == "__main__":
    verify_render()
