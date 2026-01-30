"""
Captura o diagrama do pipeline como imagem PNG
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "tutorial-images-v2"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture_pipeline_diagram():
    print("[*] Capturando diagrama do pipeline...")

    # Caminho do arquivo HTML
    html_path = Path(__file__).parent / "diagram_pipeline.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 500},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            # Carregar o arquivo HTML local
            page.goto(f"file:///{html_path.resolve()}")
            page.wait_for_timeout(1000)

            # Capturar screenshot
            output_path = OUTPUT_DIR / "06-fluxo-correcao.png"
            page.screenshot(path=str(output_path))

            print(f"[OK] Diagrama capturado: {output_path}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    capture_pipeline_diagram()
