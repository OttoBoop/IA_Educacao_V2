"""
Script para testar as novas tooltips e capturar screenshots
"""
import os
import time
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "tooltip-screenshots"
BASE_URL = "http://127.0.0.1:8001"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()
        
        print("1. Abrindo página...")
        page.goto(BASE_URL, wait_until='networkidle')
        time.sleep(1)
        
        # Fechar welcome modal se aparecer
        try:
            close_btn = page.locator('.modal-welcome .welcome-footer .btn').first
            if close_btn.is_visible(timeout=2000):
                close_btn.click()
                time.sleep(0.5)
        except:
            pass
        
        # Fechar tutorial modal se aparecer
        try:
            tutorial_close = page.locator('#modal-tutorial .modal-close, #modal-tutorial .btn:has-text("Fechar")')
            if tutorial_close.first.is_visible(timeout=1000):
                tutorial_close.first.click()
                time.sleep(0.5)
        except:
            pass
        
        # Fechar qualquer modal que esteja aberto via JavaScript
        page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
        
        # Screenshot do Dashboard com botão de ajuda
        print("2. Capturando Dashboard...")
        page.screenshot(path=f"{OUTPUT_DIR}/01_dashboard_help_btn.png", full_page=False)
        
        # Testar tooltip no sidebar (hover sobre "Prompts")
        print("3. Testando tooltip no sidebar...")
        prompts_item = page.locator('.tree-item:has-text("Prompts")')
        prompts_item.hover()
        time.sleep(0.8)  # Aguardar tooltip aparecer
        page.screenshot(path=f"{OUTPUT_DIR}/02_sidebar_tooltip.png", full_page=False)
        
        # Testar tooltip no "Configurações IA"
        print("4. Testando tooltip em Configurações...")
        config_btn = page.locator('button:has-text("Configurações IA")')
        config_btn.hover()
        time.sleep(0.8)
        page.screenshot(path=f"{OUTPUT_DIR}/03_config_tooltip.png", full_page=False)
        
        # Clicar no botão de ajuda do Dashboard
        print("5. Testando painel de ajuda...")
        help_btn = page.locator('.section-help').first
        if help_btn.is_visible():
            help_btn.click()
            time.sleep(0.5)
            page.screenshot(path=f"{OUTPUT_DIR}/04_help_panel.png", full_page=False)
        
        # Ir para Prompts e testar tooltip e ajuda
        print("6. Abrindo Prompts...")
        prompts_item.click()
        time.sleep(1)
        page.screenshot(path=f"{OUTPUT_DIR}/05_prompts_page.png", full_page=False)
        
        # Clicar no botão de ajuda de Prompts
        help_btn_prompts = page.locator('.section-help').first
        if help_btn_prompts.is_visible():
            help_btn_prompts.click()
            time.sleep(0.5)
            page.screenshot(path=f"{OUTPUT_DIR}/06_prompts_help.png", full_page=False)
        
        # Ir para Chat
        print("7. Abrindo Chat...")
        page.locator('.tree-item:has-text("Chat com IA")').click()
        time.sleep(1)
        page.screenshot(path=f"{OUTPUT_DIR}/07_chat_page.png", full_page=False)
        
        # Abrir modal de upload para testar tooltip
        print("8. Criando matéria para teste...")
        page.locator('button:has-text("Nova Matéria")').click()
        time.sleep(0.5)
        page.fill('#input-materia-nome', 'Teste Tooltips')
        page.locator('button:has-text("Criar Matéria")').click()
        time.sleep(1)
        
        # Screenshot do modal de upload com tooltip
        print("9. Capturando página final...")
        page.screenshot(path=f"{OUTPUT_DIR}/08_final_state.png", full_page=False)
        
        browser.close()
        print(f"\n✅ Screenshots salvas em: {OUTPUT_DIR}/")
        print("Arquivos criados:")
        for f in os.listdir(OUTPUT_DIR):
            print(f"   - {f}")

if __name__ == "__main__":
    main()
