"""
Teste local do sistema de onboarding
"""

from playwright.sync_api import sync_playwright

def test_local():
    print("🧪 Testando servidor LOCAL (http://127.0.0.1:8000)...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        
        try:
            page.goto("http://127.0.0.1:8000", wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            html = page.content()
            
            print("Verificações do HTML:")
            checks = [
                ("modal-welcome", "Modal de boas-vindas"),
                ("welcome-badge", "Badge PROTÓTIPO"),
                ("help-btn", "Botão de ajuda"),
                ("modal-tutorial", "Modal de tutorial"),
                ("checkFirstVisit", "Função checkFirstVisit"),
            ]
            
            for keyword, desc in checks:
                found = keyword in html
                status = "✅" if found else "❌"
                print(f"   {status} {desc}")
            
            # Verificar se modal apareceu automaticamente
            print("\n🔍 Verificando modal de boas-vindas...")
            welcome_modal = page.query_selector("#modal-welcome")
            if welcome_modal:
                is_active = "active" in (welcome_modal.get_attribute("class") or "")
                print(f"   Modal existe: ✅")
                print(f"   Modal visível (active): {'✅' if is_active else '❌'}")
                
                if is_active:
                    # Capturar screenshot
                    page.screenshot(path="test_welcome_modal.png")
                    print("   📸 Screenshot salvo: test_welcome_modal.png")
            
            # Verificar botão de ajuda
            print("\n🔍 Verificando botão de ajuda...")
            help_btn = page.query_selector(".help-btn")
            print(f"   Botão existe: {'✅' if help_btn else '❌'}")
            
            # Verificar imagens
            print("\n🔍 Verificando imagens do tutorial...")
            page.goto("http://127.0.0.1:8000/static/tutorial-images/01-dashboard.png")
            page.wait_for_timeout(500)
            
            # Check if we got an image
            img = page.query_selector("img")
            if img:
                print("   Imagem acessível: ✅")
            else:
                body_text = page.query_selector("body").inner_text() if page.query_selector("body") else ""
                if "Not Found" in body_text:
                    print("   ❌ Imagem não encontrada (404)")
                else:
                    print("   ⚠️ Status desconhecido")
                    
        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            browser.close()
            
    print("\n✅ Teste local concluído!")

if __name__ == "__main__":
    test_local()
