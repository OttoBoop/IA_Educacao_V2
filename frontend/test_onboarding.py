"""
Script para testar o sistema de onboarding do Prova AI
"""

from playwright.sync_api import sync_playwright
import time

BASE_URL = "https://ia-educacao-v2.onrender.com"

def test_onboarding():
    print("🧪 Testando sistema de onboarding...\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Contexto limpo (sem localStorage)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900}
        )
        page = context.new_page()
        
        try:
            # 1. Carregar página
            print("📡 Carregando página...")
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)
            
            # 2. Verificar modal de boas-vindas
            print("\n🔍 Verificando modal de boas-vindas...")
            welcome_modal = page.query_selector("#modal-welcome")
            if welcome_modal:
                is_active = "active" in (welcome_modal.get_attribute("class") or "")
                print(f"   Modal existe: ✅")
                print(f"   Modal visível: {'✅' if is_active else '❌ (não apareceu automaticamente)'}")
                
                if is_active:
                    # Verificar conteúdo
                    badge = page.query_selector(".welcome-badge")
                    print(f"   Badge 'PROTÓTIPO': {'✅' if badge else '❌'}")
                    
                    title = page.query_selector(".welcome-title")
                    print(f"   Título 'Bem-vindo': {'✅' if title else '❌'}")
                    
                    model_chips = page.query_selector_all(".model-chip")
                    print(f"   Chips de modelos: {len(model_chips)} encontrados {'✅' if len(model_chips) == 3 else '⚠️'}")
                    
                    flow_cards = page.query_selector_all(".flow-card")
                    print(f"   Cards de fluxo: {len(flow_cards)} encontrados {'✅' if len(flow_cards) == 2 else '⚠️'}")
                    
                    warning = page.query_selector(".welcome-warning")
                    print(f"   Aviso de custo: {'✅' if warning else '❌'}")
                    
                    # Testar botão "Ver Tutorial"
                    print("\n🔍 Testando botão 'Ver Tutorial'...")
                    tutorial_btn = page.query_selector("button:has-text('Ver Tutorial')")
                    if tutorial_btn:
                        tutorial_btn.click()
                        page.wait_for_timeout(1000)
                        
                        tutorial_modal = page.query_selector("#modal-tutorial.active")
                        print(f"   Modal tutorial abriu: {'✅' if tutorial_modal else '❌'}")
                        
                        if tutorial_modal:
                            # Verificar tabs
                            tabs = page.query_selector_all(".tutorial-tab")
                            print(f"   Tabs encontradas: {len(tabs)} {'✅' if len(tabs) == 2 else '⚠️'}")
                            
                            # Verificar imagem
                            img = page.query_selector(".tutorial-image")
                            if img:
                                src = img.get_attribute("src")
                                print(f"   Imagem do step: {src}")
                            
                            # Testar navegação
                            next_btn = page.query_selector("#tutorial-next")
                            if next_btn:
                                next_btn.click()
                                page.wait_for_timeout(500)
                                progress = page.query_selector("#tutorial-progress-text")
                                if progress:
                                    print(f"   Navegação funciona: {progress.inner_text()}")
                            
                            # Testar modo completo
                            full_tab = page.query_selector('[data-mode="full"]')
                            if full_tab:
                                full_tab.click()
                                page.wait_for_timeout(500)
                                dots = page.query_selector_all(".tutorial-dot")
                                print(f"   Modo completo: {len(dots)} steps {'✅' if len(dots) == 8 else '⚠️'}")
                            
                            # Fechar tutorial
                            close_btn = page.query_selector("#modal-tutorial .modal-close")
                            if close_btn:
                                close_btn.click()
                                page.wait_for_timeout(500)
            else:
                print("   ❌ Modal de boas-vindas não encontrado no DOM")
            
            # 3. Verificar botão de ajuda
            print("\n🔍 Verificando botão de ajuda no sidebar...")
            help_btn = page.query_selector(".help-btn")
            if help_btn:
                print("   Botão de ajuda: ✅")
                help_btn.click()
                page.wait_for_timeout(1000)
                
                welcome_active = page.query_selector("#modal-welcome.active")
                print(f"   Reabre boas-vindas: {'✅' if welcome_active else '❌'}")
            else:
                print("   ❌ Botão de ajuda não encontrado")
            
            # 4. Verificar imagens do tutorial
            print("\n🔍 Verificando carregamento de imagens...")
            page.goto(f"{BASE_URL}/static/tutorial-images/01-dashboard.png")
            page.wait_for_timeout(1000)
            
            # Check if it's an image or error
            content_type = page.evaluate("() => document.contentType")
            if content_type and "image" in content_type:
                print("   Imagens acessíveis via /static: ✅")
            else:
                # Try checking if there's content
                body = page.query_selector("body")
                if body:
                    text = body.inner_text()
                    if "Not Found" in text or "404" in text:
                        print("   ⚠️ Imagens não encontradas em /static")
                    else:
                        print("   Imagens possivelmente acessíveis: ⚠️")
            
            print("\n" + "="*50)
            print("🏁 Teste concluído!")
            print("="*50)
                
        except Exception as e:
            print(f"❌ Erro durante teste: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_onboarding()
