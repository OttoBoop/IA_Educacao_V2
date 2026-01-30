"""
Verificar tutorial no Render
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify"
OUTPUT_DIR.mkdir(exist_ok=True)

def verify_render():
    print("[*] Verificando tutorial no Render...")

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

            # O modal de welcome deve estar aberto, clicar em "Tutorial Guiado"
            tutorial_btn = page.query_selector('button.btn-tutorial')
            if tutorial_btn:
                tutorial_btn.click()
                page.wait_for_timeout(1000)
                print("[OK] Tutorial aberto via botao")
            else:
                # Tentar via JavaScript direto
                page.evaluate("openTutorial()")
                page.wait_for_timeout(1000)
                print("[OK] Tutorial aberto via JS")

            # Capturar pagina 1 (modo QUICK)
            page.screenshot(path=str(OUTPUT_DIR / "render_tutorial_p1.png"))
            print("[OK] Pagina 1 capturada")

            # Mudar para modo FULL
            full_btn = page.query_selector('[data-mode="full"]')
            if full_btn:
                full_btn.click()
                page.wait_for_timeout(500)
                print("[OK] Modo FULL ativado")

            # Navegar para pagina 8 (pipeline)
            print("[*] Navegando para pagina 8...")
            for i in range(7):
                next_btn = page.query_selector('#tutorial-next')
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(400)

            page.screenshot(path=str(OUTPUT_DIR / "render_tutorial_p8.png"))
            print("[OK] Pagina 8 capturada")

            # Navegar para pagina 10 (resultados)
            print("[*] Navegando para pagina 10...")
            for i in range(2):
                next_btn = page.query_selector('#tutorial-next')
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(400)

            page.screenshot(path=str(OUTPUT_DIR / "render_tutorial_p10.png"))
            print("[OK] Pagina 10 capturada")

            print("\n" + "="*50)
            print("[OK] Tutorial verificado no Render!")
            print(f"[*] Screenshots em: {OUTPUT_DIR}")

        except Exception as e:
            print(f"[ERRO] {e}")
            page.screenshot(path=str(OUTPUT_DIR / "render_error.png"))
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    verify_render()
