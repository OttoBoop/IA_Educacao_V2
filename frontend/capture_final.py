"""
Captura screenshots finais do tutorial melhorado
"""
from playwright.sync_api import sync_playwright
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "design-review-v2"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1400, 'height': 900})
        
        page.goto("http://127.0.0.1:8001", wait_until="networkidle")
        time.sleep(1)
        
        # 1. Welcome modal
        print("📸 1. Modal de boas-vindas...")
        page.screenshot(path=str(OUTPUT_DIR / "01-welcome-novo.png"))
        
        # Abrir tutorial clicando no botao
        print("📸 2. Abrindo tutorial...")
        page.click(".welcome-footer button.btn:first-child")  # Ver Tutorial
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "02-tutorial-passo1.png"))
        
        # 3. Próximo passo
        print("📸 3. Tutorial passo 2...")
        page.click("#tutorial-next")  # Próximo
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "03-tutorial-passo2.png"))
        
        # 4. Próximo passo
        print("📸 4. Tutorial passo 3...")
        page.click("#tutorial-next")  # Próximo
        time.sleep(0.5)
        page.screenshot(path=str(OUTPUT_DIR / "04-tutorial-passo3.png"))
        
        # 5. Fechar tutorial e ver sidebar
        print("📸 5. Novo botão de ajuda...")
        # Fechar usando JavaScript ao inves de clicar
        page.evaluate("""
            document.querySelector('#modal-tutorial').classList.remove('active');
            document.querySelector('#modal-welcome').classList.remove('active');
        """)
        time.sleep(0.5)
        
        # Highlight the help button area
        page.evaluate("""
            const sidebar = document.querySelector('.sidebar-footer');
            if (sidebar) {
                sidebar.style.border = '3px solid #3b82f6';
                sidebar.style.borderRadius = '8px';
            }
        """)
        
        page.screenshot(path=str(OUTPUT_DIR / "05-sidebar-botao-ajuda.png"))
        
        browser.close()
        print(f"\n✅ Screenshots salvas em: {OUTPUT_DIR}")

if __name__ == "__main__":
    capture()
