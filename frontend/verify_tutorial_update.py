"""
Verifica se o tutorial atualizado esta funcionando corretamente
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"
OUTPUT_DIR.mkdir(exist_ok=True)

def verify_tutorial():
    print("[*] Verificando tutorial atualizado...\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            page.goto("http://127.0.0.1:8000", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Fechar modal de welcome
            close_btn = page.query_selector("#modal-welcome .btn-primary")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)

            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(300)

            # Abrir tutorial
            page.evaluate("openTutorial()")
            page.wait_for_timeout(1000)

            # Verificar modo QUICK (4 paginas)
            print("[*] Modo QUICK (4 paginas):")
            for i in range(4):
                page.wait_for_timeout(500)
                output_path = OUTPUT_DIR / f"quick_page{i+1}.png"
                page.screenshot(path=str(output_path))
                print(f"    [OK] Pagina {i+1}")

                if i < 3:
                    page.click("#tutorial-next")
                    page.wait_for_timeout(500)

            # Mudar para modo FULL
            page.click('[data-mode="full"]')
            page.wait_for_timeout(500)

            # Verificar modo FULL (12 paginas)
            print("\n[*] Modo FULL (12 paginas):")
            for i in range(12):
                page.wait_for_timeout(500)
                output_path = OUTPUT_DIR / f"full_page{i+1}.png"
                page.screenshot(path=str(output_path))
                print(f"    [OK] Pagina {i+1}")

                if i < 11:
                    page.click("#tutorial-next")
                    page.wait_for_timeout(500)

            print("\n" + "="*60)
            print("[OK] Tutorial verificado!")
            print(f"[*] Screenshots salvos em: {OUTPUT_DIR}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    verify_tutorial()
