"""
Verificacao final sem cache
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify" / "final"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def verify():
    print("[*] Verificacao final (sem cache)\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Contexto sem cache
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2,
            bypass_csp=True
        )
        page = context.new_page()

        # Desabilitar cache
        page.route("**/*", lambda route: route.continue_(headers={
            **route.request.headers,
            "Cache-Control": "no-cache, no-store, must-revalidate"
        }))

        try:
            # Adicionar cache buster
            ts = int(time.time())
            page.goto(f"https://ia-educacao-v2.onrender.com?nocache={ts}", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Abrir tutorial
            tutorial_btn = page.query_selector('button.btn-tutorial')
            if tutorial_btn:
                tutorial_btn.click()
                page.wait_for_timeout(1000)

            # Mudar para modo FULL
            full_btn = page.query_selector('[data-mode="full"]')
            if full_btn:
                full_btn.click()
                page.wait_for_timeout(500)

            # Capturar pagina 2 (Nova Materia - imagem 05)
            page.click("#tutorial-next")
            page.wait_for_timeout(800)
            page.screenshot(path=str(OUTPUT_DIR / "p02_nova_materia.png"))
            print("[OK] Pagina 2 (Nova Materia)")

            # Ir para pagina 8 (Pipeline - imagem 12)
            for _ in range(6):
                page.click("#tutorial-next")
                page.wait_for_timeout(400)
            page.screenshot(path=str(OUTPUT_DIR / "p08_pipeline.png"))
            print("[OK] Pagina 8 (Pipeline)")

            # Ir para pagina 10 (Resultados - imagem 14)
            for _ in range(2):
                page.click("#tutorial-next")
                page.wait_for_timeout(400)
            page.screenshot(path=str(OUTPUT_DIR / "p10_resultados.png"))
            print("[OK] Pagina 10 (Resultados)")

            print("\n[OK] Verificacao concluida!")
            print(f"[*] Screenshots: {OUTPUT_DIR}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    verify()
