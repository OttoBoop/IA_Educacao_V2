"""
Verifica o tutorial LOCAL modo FULL
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture_full_tutorial():
    print("[*] Capturando tutorial LOCAL modo FULL...")

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

            # Fechar modal
            close_btn = page.query_selector("#modal-welcome .btn-primary")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(300)

            # Abrir tutorial
            print("[*] Abrindo tutorial...")
            page.evaluate("openTutorial()")
            page.wait_for_timeout(1000)

            # Mudar para modo FULL
            full_tab = page.query_selector('[data-mode="full"]')
            if full_tab:
                full_tab.click()
                page.wait_for_timeout(500)

            print("\n[*] Modo FULL (8 paginas):")
            for i in range(8):
                page.wait_for_timeout(500)
                output_path = OUTPUT_DIR / f"local_full_page{i+1}.png"
                page.screenshot(path=str(output_path))
                print(f"    [OK] Pagina {i+1}: {output_path.name}")

                if i < 7:
                    next_btn = page.query_selector("#tutorial-next")
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(500)

            print(f"\n[OK] Tutorial FULL local capturado!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    capture_full_tutorial()
