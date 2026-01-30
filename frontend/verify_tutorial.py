"""
Verifica o tutorial capturando screenshots de cada pagina
Compara producao (Render) vs local
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import sys

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture_tutorial_pages(base_url, prefix):
    """Captura todas as paginas do tutorial"""
    print(f"\n[*] Capturando tutorial de: {base_url}")
    print(f"    Prefixo: {prefix}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            # Carregar pagina
            print("[*] Carregando pagina...")
            page.goto(base_url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

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

            # Modo QUICK - 4 paginas
            print("\n[*] Modo QUICK (4 paginas):")
            for i in range(4):
                page.wait_for_timeout(500)
                output_path = OUTPUT_DIR / f"{prefix}_quick_page{i+1}.png"
                page.screenshot(path=str(output_path))
                print(f"    [OK] Pagina {i+1}: {output_path.name}")

                # Proximo (exceto na ultima)
                if i < 3:
                    next_btn = page.query_selector("#tutorial-next")
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(500)

            # Mudar para modo FULL
            print("\n[*] Modo FULL (8 paginas):")
            full_tab = page.query_selector('[data-mode="full"]')
            if full_tab:
                full_tab.click()
                page.wait_for_timeout(500)

            for i in range(8):
                page.wait_for_timeout(500)
                output_path = OUTPUT_DIR / f"{prefix}_full_page{i+1}.png"
                page.screenshot(path=str(output_path))
                print(f"    [OK] Pagina {i+1}: {output_path.name}")

                # Proximo (exceto na ultima)
                if i < 7:
                    next_btn = page.query_selector("#tutorial-next")
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(500)

            print(f"\n[OK] Tutorial capturado: {OUTPUT_DIR}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    # Capturar do Render (producao)
    capture_tutorial_pages(
        "https://ia-educacao-v2.onrender.com",
        "render"
    )

    # Se quiser capturar local tambem, descomente:
    # capture_tutorial_pages(
    #     "http://127.0.0.1:8000",
    #     "local"
    # )
