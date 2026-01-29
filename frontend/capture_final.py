"""
Captura screenshots finais do tutorial melhorado - v4
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "design-review-v4"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        
        page.goto("http://127.0.0.1:8001", wait_until="networkidle")
        time.sleep(1)
        
        # 1. Welcome modal com novos estilos
        print("📸 1. Modal de boas-vindas v4...")
        page.screenshot(path=str(OUTPUT_DIR / "01-welcome-v4.png"))
        
        # 2. Abrir tutorial
        print("📸 2. Tutorial com imagem container...")
        page.click(".welcome-footer .btn-tutorial")
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "02-tutorial-v4.png"))
        
        # 3. Fechar e ver dashboard
        print("📸 3. Dashboard...")
        page.evaluate("""
            document.querySelector('#modal-tutorial').classList.remove('active');
            document.querySelector('#modal-welcome').classList.remove('active');
        """)
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "03-dashboard-v4.png"))
        
        browser.close()
        print(f"\n✅ Screenshots v4 salvas em: {OUTPUT_DIR}")

if __name__ == "__main__":
    capture()
