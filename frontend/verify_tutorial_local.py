"""
Verifica o tutorial LOCAL capturando screenshots das paginas 3 e 4
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture_local_tutorial():
    """Captura paginas 3 e 4 do tutorial local"""
    print("[*] Capturando tutorial LOCAL...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            print("[*] Carregando pagina local...")
            page.goto("http://127.0.0.1:8000", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Fechar modal de welcome
            close_btn = page.query_selector("#modal-welcome .btn-primary")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)

            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(300)

            # Abrir tutorial
            print("[*] Abrindo tutorial...")
            page.evaluate("openTutorial()")
            page.wait_for_timeout(1000)

            # Modo QUICK - capturar paginas 3 e 4
            print("\n[*] Modo QUICK:")

            # Navegar ate pagina 3
            for i in range(2):
                next_btn = page.query_selector("#tutorial-next")
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(500)

            # Capturar pagina 3
            page.wait_for_timeout(500)
            output_path = OUTPUT_DIR / "local_quick_page3.png"
            page.screenshot(path=str(output_path))
            print(f"    [OK] Pagina 3 (Pipeline): {output_path.name}")

            # Navegar para pagina 4
            next_btn = page.query_selector("#tutorial-next")
            if next_btn:
                next_btn.click()
                page.wait_for_timeout(500)

            # Capturar pagina 4
            output_path = OUTPUT_DIR / "local_quick_page4.png"
            page.screenshot(path=str(output_path))
            print(f"    [OK] Pagina 4 (Chat): {output_path.name}")

            print(f"\n[OK] Tutorial local capturado!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    capture_local_tutorial()
