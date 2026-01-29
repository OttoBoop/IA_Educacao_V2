"""
Script para capturar screenshots do Prova AI para o tutorial
Execute com: playwright install chromium && python capture_screenshots.py
"""

import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_DIR = Path(__file__).parent / "tutorial-images"

# Garantir que a pasta existe
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def capture_screenshots():
    print("🚀 Iniciando captura de screenshots...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2  # Retina quality
        )
        page = context.new_page()
        
        try:
            # 1. Dashboard Principal
            print("📸 1/8 - Dashboard...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUTPUT_DIR / "01-dashboard.png"))
            
            # 2. Sidebar expandido
            print("📸 2/8 - Sidebar navegação...")
            tree_item = page.query_selector(".tree-item")
            if tree_item:
                tree_item.click()
                page.wait_for_timeout(500)
            page.screenshot(
                path=str(OUTPUT_DIR / "02-sidebar.png"),
                clip={"x": 0, "y": 0, "width": 320, "height": 900}
            )
            
            # 3. Chat com IA
            print("📸 3/8 - Chat com IA...")
            chat_link = page.query_selector("text=Chat com IA")
            if chat_link:
                chat_link.click()
                page.wait_for_timeout(2500)
            page.screenshot(path=str(OUTPUT_DIR / "03-chat.png"))
            
            # 4. Chat - Modo filtrar
            print("📸 4/8 - Chat com filtros...")
            filter_btn = page.query_selector('[data-mode="filtrar"]') or page.query_selector("text=Filtrar")
            if filter_btn:
                filter_btn.click()
                page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "04-chat-filtros.png"))
            
            # 5. Modal de Configurações
            print("📸 5/8 - Configurações IA...")
            config_btn = page.query_selector("text=Configurações IA")
            if config_btn:
                config_btn.click()
                page.wait_for_timeout(1500)
            page.screenshot(path=str(OUTPUT_DIR / "05-config-apikeys.png"))
            
            # 6. Aba de Modelos (dentro do modal de settings)
            print("📸 6/8 - Configuração de modelos...")
            # Clicar na aba dentro do modal
            modelos_tab = page.query_selector('#modal-settings [data-tab="modelos"]')
            if modelos_tab:
                modelos_tab.click()
                page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "06-config-modelos.png"))
            
            # Fechar modal clicando no X dentro do modal
            close_btn = page.query_selector("#modal-settings .modal-close")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            
            # 7. Modal Nova Matéria
            print("📸 7/8 - Nova Matéria...")
            # Aguardar modal fechar
            page.wait_for_timeout(500)
            nova_materia_btn = page.query_selector('button:has-text("Nova Matéria")')
            if nova_materia_btn:
                nova_materia_btn.click()
                page.wait_for_timeout(1000)
            page.screenshot(path=str(OUTPUT_DIR / "07-nova-materia.png"))
            
            # Fechar modal
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
            # 8. Navegar para matéria/atividade
            print("📸 8/8 - Tela de matéria...")
            inicio_link = page.query_selector('a:has-text("Início")')
            if inicio_link:
                inicio_link.click()
                page.wait_for_timeout(1000)
            
            # Clicar em uma matéria se existir
            materia_card = page.query_selector(".materia-card")
            if materia_card:
                materia_card.click()
                page.wait_for_timeout(1500)
            page.screenshot(path=str(OUTPUT_DIR / "08-materia-view.png"))
            
            print("\n✅ Screenshots capturados com sucesso!")
            print(f"📁 Salvos em: {OUTPUT_DIR}")
            
            # Listar arquivos criados
            files = list(OUTPUT_DIR.glob("*.png"))
            print(f"\n📷 {len(files)} imagens capturadas:")
            for f in sorted(files):
                print(f"   - {f.name}")
                
        except Exception as e:
            print(f"❌ Erro durante captura: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    capture_screenshots()
