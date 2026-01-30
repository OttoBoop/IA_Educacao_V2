"""
Verificacao completa do tutorial no Render
Captura todas as 12 paginas do modo FULL
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-verify" / "render-final"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def verify_render():
    print("[*] Verificacao completa do tutorial no Render\n")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            print("[*] Carregando site...")
            page.goto("https://ia-educacao-v2.onrender.com", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Abrir tutorial via botao
            tutorial_btn = page.query_selector('button.btn-tutorial')
            if tutorial_btn:
                tutorial_btn.click()
                page.wait_for_timeout(1000)
                print("[OK] Tutorial aberto")
            else:
                print("[!] Botao tutorial nao encontrado, tentando JS...")
                page.evaluate("openTutorial()")
                page.wait_for_timeout(1000)

            # Capturar pagina 1 do modo Quick
            page.screenshot(path=str(OUTPUT_DIR / "quick_p1.png"))
            print("[OK] Quick pagina 1")

            # Mudar para modo FULL
            full_btn = page.query_selector('[data-mode="full"]')
            if full_btn:
                full_btn.click()
                page.wait_for_timeout(500)
                print("[OK] Modo FULL ativado")

            # Capturar todas as 12 paginas
            for i in range(12):
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUTPUT_DIR / f"full_p{i+1:02d}.png"))
                print(f"[OK] Full pagina {i+1}/12")

                if i < 11:
                    next_btn = page.query_selector('#tutorial-next')
                    if next_btn:
                        next_btn.click()
                        page.wait_for_timeout(400)

            print("\n" + "="*60)
            print("[OK] Verificacao completa!")
            print(f"[*] Screenshots em: {OUTPUT_DIR}")

        except Exception as e:
            print(f"[ERRO] {e}")
            page.screenshot(path=str(OUTPUT_DIR / "error.png"))
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    verify_render()
