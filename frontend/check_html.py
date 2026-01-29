"""
Script para verificar o HTML do Prova AI
"""

from playwright.sync_api import sync_playwright

BASE_URL = "https://ia-educacao-v2.onrender.com"

def check_html():
    print("🔍 Verificando HTML do servidor...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            html = page.content()
            
            # Verificar elementos chave
            checks = [
                ("modal-welcome", "Modal de boas-vindas"),
                ("welcome-badge", "Badge PROTÓTIPO"),
                ("help-btn", "Botão de ajuda"),
                ("modal-tutorial", "Modal de tutorial"),
                ("tutorial-images", "Referência às imagens"),
                ("checkFirstVisit", "Função checkFirstVisit"),
                ("openWelcome", "Função openWelcome"),
            ]
            
            print("Verificando presença no HTML:")
            for keyword, desc in checks:
                found = keyword in html
                status = "✅" if found else "❌"
                print(f"   {status} {desc} ({keyword})")
            
            # Verificar último commit
            print("\n📄 Primeiros 500 chars do HTML:")
            print(html[:500])
            
        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_html()
