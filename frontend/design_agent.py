"""
Design Agent: Capturar e analisar o tutorial atual para iteração
"""

from playwright.sync_api import sync_playwright
from pathlib import Path
import os

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).parent / "design-review"
OUTPUT_DIR.mkdir(exist_ok=True)

def capture_current_state():
    print("🎨 DESIGN AGENT - Capturando estado atual do tutorial\n")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()
        
        try:
            # 1. Capturar modal de boas-vindas
            print("\n📸 1. Modal de Boas-vindas...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            # Screenshot do modal de welcome
            page.screenshot(path=str(OUTPUT_DIR / "01-welcome-modal.png"))
            print(f"   Salvo: 01-welcome-modal.png")
            
            # 2. Abrir tutorial - Guia Rápido
            print("\n📸 2. Tutorial - Guia Rápido...")
            tutorial_btn = page.query_selector("button:has-text('Ver Tutorial')")
            if tutorial_btn:
                tutorial_btn.click()
                page.wait_for_timeout(1000)
                
                # Step 1
                page.screenshot(path=str(OUTPUT_DIR / "02-tutorial-quick-step1.png"))
                print(f"   Salvo: 02-tutorial-quick-step1.png")
                
                # Step 2
                next_btn = page.query_selector("#tutorial-next")
                if next_btn:
                    next_btn.click()
                    page.wait_for_timeout(500)
                    page.screenshot(path=str(OUTPUT_DIR / "03-tutorial-quick-step2.png"))
                    print(f"   Salvo: 03-tutorial-quick-step2.png")
                
                # Step 3
                next_btn.click()
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUTPUT_DIR / "04-tutorial-quick-step3.png"))
                print(f"   Salvo: 04-tutorial-quick-step3.png")
            
            # 3. Tutorial Completo
            print("\n📸 3. Tutorial - Modo Completo...")
            full_tab = page.query_selector('[data-mode="full"]')
            if full_tab:
                full_tab.click()
                page.wait_for_timeout(500)
                page.screenshot(path=str(OUTPUT_DIR / "05-tutorial-full-step1.png"))
                print(f"   Salvo: 05-tutorial-full-step1.png")
            
            # 4. Fechar e verificar botão de ajuda
            print("\n📸 4. Botão de Ajuda no Sidebar...")
            close_btn = page.query_selector("#modal-tutorial .modal-close")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
            
            # Screenshot do sidebar com botão de ajuda
            page.screenshot(
                path=str(OUTPUT_DIR / "06-sidebar-help-btn.png"),
                clip={"x": 0, "y": 0, "width": 320, "height": 900}
            )
            print(f"   Salvo: 06-sidebar-help-btn.png")
            
            print("\n" + "="*60)
            print("✅ Capturas concluídas!")
            print(f"📁 Pasta: {OUTPUT_DIR}")
            
            # Listar arquivos
            files = list(OUTPUT_DIR.glob("*.png"))
            print(f"\n📷 {len(files)} imagens capturadas para análise")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    capture_current_state()
