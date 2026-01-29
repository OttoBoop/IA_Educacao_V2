"""
Captura screenshots finais do tutorial melhorado - v3
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "design-review-v3"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        
        page.goto("http://127.0.0.1:8001", wait_until="networkidle")
        time.sleep(1)
        
        # 1. Welcome modal com novos estilos
        print("📸 1. Modal de boas-vindas (novo design)...")
        page.screenshot(path=str(OUTPUT_DIR / "01-welcome-v3.png"))
        
        # 2. Abrir tutorial e ver tabs
        print("📸 2. Tutorial com tabs melhoradas...")
        page.click(".welcome-footer .btn-tutorial")  # Botão verde
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "02-tutorial-tabs-v3.png"))
        
        # 3. Navegar passos
        print("📸 3. Tutorial passo 2...")
        page.click("#tutorial-next")
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "03-tutorial-passo2-v3.png"))
        
        # 4. Fechar e ver botão de ajuda pulsando
        print("📸 4. Sidebar com botão de ajuda...")
        page.evaluate("""
            document.querySelector('#modal-tutorial').classList.remove('active');
            document.querySelector('#modal-welcome').classList.remove('active');
        """)
        time.sleep(0.5)
        
        # Destacar área do sidebar footer
        page.evaluate("""
            const footer = document.querySelector('.sidebar-footer');
            if (footer) {
                footer.style.border = '3px solid #10b981';
                footer.style.borderRadius = '12px';
                footer.style.padding = '12px';
            }
        """)
        
        page.screenshot(path=str(OUTPUT_DIR / "04-sidebar-help-btn-v3.png"))
        
        browser.close()
        print(f"\n✅ Screenshots v3 salvas em: {OUTPUT_DIR}")

if __name__ == "__main__":
    capture()
