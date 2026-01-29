"""
Captura screenshots anotados para o tutorial melhorado
Adiciona círculos, setas e números para guiar usuários não técnicos
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).parent / "tutorial-images-v2"
OUTPUT_DIR.mkdir(exist_ok=True)

def add_annotation_script():
    """JavaScript para adicionar anotações visuais"""
    return """
    (function() {
        // Criar overlay de anotações
        const overlay = document.createElement('div');
        overlay.id = 'annotation-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 99999;
        `;
        document.body.appendChild(overlay);
        
        window.addCircle = function(x, y, number, color = '#ef4444') {
            const circle = document.createElement('div');
            circle.style.cssText = `
                position: absolute;
                left: ${x - 20}px;
                top: ${y - 20}px;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: ${color};
                color: white;
                font-size: 18px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                font-family: Inter, sans-serif;
            `;
            circle.textContent = number;
            overlay.appendChild(circle);
        };
        
        window.addArrow = function(x1, y1, x2, y2, color = '#ef4444') {
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.style.cssText = `
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: visible;
            `;
            
            const angle = Math.atan2(y2 - y1, x2 - x1);
            const headLength = 15;
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `
                M ${x1} ${y1} L ${x2} ${y2}
                M ${x2} ${y2} L ${x2 - headLength * Math.cos(angle - Math.PI/6)} ${y2 - headLength * Math.sin(angle - Math.PI/6)}
                M ${x2} ${y2} L ${x2 - headLength * Math.cos(angle + Math.PI/6)} ${y2 - headLength * Math.sin(angle + Math.PI/6)}
            `);
            path.setAttribute('stroke', color);
            path.setAttribute('stroke-width', '3');
            path.setAttribute('fill', 'none');
            
            svg.appendChild(path);
            overlay.appendChild(svg);
        };
        
        window.addHighlight = function(selector, padding = 8) {
            const el = document.querySelector(selector);
            if (!el) return;
            const rect = el.getBoundingClientRect();
            
            const highlight = document.createElement('div');
            highlight.style.cssText = `
                position: absolute;
                left: ${rect.left - padding}px;
                top: ${rect.top - padding}px;
                width: ${rect.width + padding * 2}px;
                height: ${rect.height + padding * 2}px;
                border: 3px solid #ef4444;
                border-radius: 8px;
                box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.2);
                animation: pulse 1.5s infinite;
            `;
            overlay.appendChild(highlight);
        };
        
        window.addLabel = function(x, y, text, color = '#ef4444') {
            const label = document.createElement('div');
            label.style.cssText = `
                position: absolute;
                left: ${x}px;
                top: ${y}px;
                background: ${color};
                color: white;
                padding: 8px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                font-family: Inter, sans-serif;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                white-space: nowrap;
            `;
            label.textContent = text;
            overlay.appendChild(label);
        };
        
        window.clearAnnotations = function() {
            const overlay = document.getElementById('annotation-overlay');
            if (overlay) overlay.innerHTML = '';
        };
        
        // Adicionar animação de pulse
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.7; }
            }
        `;
        document.head.appendChild(style);
    })();
    """

def capture_annotated_screenshots():
    print("🎨 Capturando screenshots anotados para tutorial v2\n")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()
        
        try:
            # Carregar página
            page.goto(BASE_URL, wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            # Fechar modal de welcome clicando no botão
            close_btn = page.query_selector("#modal-welcome .btn-primary")
            if close_btn:
                close_btn.click()
                page.wait_for_timeout(500)
            else:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            
            # Garantir que o modal fechou
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(300)
            
            # Injetar script de anotações
            page.evaluate(add_annotation_script())
            
            # ========================================
            # 1. DASHBOARD COM ANOTAÇÕES
            # ========================================
            print("\n📸 1. Dashboard anotado...")
            
            page.evaluate("""
                // Destacar sidebar
                addCircle(140, 80, '1', '#3b82f6');
                addLabel(180, 70, 'Menu Principal');
                
                // Destacar estatísticas
                addCircle(600, 200, '2', '#22c55e');
                addLabel(640, 190, 'Resumo Geral');
                
                // Destacar botão Nova Matéria (posição fixa no footer do sidebar)
                addCircle(140, 870, '3', '#ef4444');
                addLabel(180, 860, 'Comece aqui!');
            """)
            
            page.screenshot(path=str(OUTPUT_DIR / "01-dashboard-anotado.png"))
            page.evaluate("clearAnnotations()")
            print("   ✅ 01-dashboard-anotado.png")
            
            # ========================================
            # 2. SIDEBAR ANOTADO
            # ========================================
            print("\n📸 2. Menu lateral anotado...")
            
            page.evaluate("""
                addCircle(140, 160, '1', '#3b82f6');
                addLabel(180, 150, 'Voltar ao Início');
                
                addCircle(140, 200, '2', '#22c55e');
                addLabel(180, 190, 'Chat com IA');
                
                addCircle(140, 280, '3', '#a855f7');
                addLabel(180, 270, 'Suas Matérias');
                
                addCircle(140, 850, '4', '#ef4444');
                addLabel(180, 840, 'Ajuda');
            """)
            
            page.screenshot(
                path=str(OUTPUT_DIR / "02-sidebar-anotado.png"),
                clip={"x": 0, "y": 0, "width": 400, "height": 900}
            )
            page.evaluate("clearAnnotations()")
            print("   ✅ 02-sidebar-anotado.png")
            
            # ========================================
            # 3. CHAT COM ANOTAÇÕES
            # ========================================
            print("\n📸 3. Chat anotado...")
            
            chat_link = page.query_selector("text=Chat com IA")
            if chat_link:
                chat_link.click()
                page.wait_for_timeout(1500)
            
            page.evaluate(add_annotation_script())
            page.evaluate("""
                // Painel de contexto
                addCircle(160, 150, '1', '#3b82f6');
                addLabel(200, 140, 'Escolha o que a IA vai ler');
                
                // Área de filtros
                addCircle(160, 300, '2', '#22c55e');
                addLabel(200, 290, 'Filtre por matéria, turma ou aluno');
                
                // Seletor de modelo
                addCircle(1200, 80, '3', '#a855f7');
                addLabel(1000, 70, 'Escolha o modelo de IA');
                
                // Área de mensagem
                addCircle(700, 800, '4', '#ef4444');
                addLabel(750, 790, 'Digite sua pergunta aqui');
            """)
            
            page.screenshot(path=str(OUTPUT_DIR / "03-chat-anotado.png"))
            page.evaluate("clearAnnotations()")
            print("   ✅ 03-chat-anotado.png")
            
            # ========================================
            # 4. EXEMPLO: PEDIR RELATÓRIO
            # ========================================
            print("\n📸 4. Exemplo: pedir relatório...")
            
            page.evaluate(add_annotation_script())
            page.evaluate("""
                addLabel(400, 300, '💡 Exemplo: "Faça um relatório completo da turma"', '#22c55e');
                addLabel(400, 350, '💡 Exemplo: "Como está o desempenho do João?"', '#3b82f6');
                addLabel(400, 400, '💡 Exemplo: "Quais questões os alunos mais erraram?"', '#a855f7');
            """)
            
            page.screenshot(path=str(OUTPUT_DIR / "04-chat-exemplos.png"))
            page.evaluate("clearAnnotations()")
            print("   ✅ 04-chat-exemplos.png")
            
            # ========================================
            # 5. VOLTAR E MOSTRAR NOVA MATÉRIA
            # ========================================
            print("\n📸 5. Criar nova matéria...")
            
            inicio = page.query_selector("text=Início")
            if inicio:
                inicio.click()
                page.wait_for_timeout(1000)
            
            nova_materia = page.query_selector('button:has-text("Nova Matéria")')
            if nova_materia:
                nova_materia.click()
                page.wait_for_timeout(500)
            
            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircle(500, 200, '1', '#ef4444');
                addLabel(540, 190, 'Nome da sua disciplina');
                
                addCircle(500, 280, '2', '#3b82f6');
                addLabel(540, 270, 'Descrição (opcional)');
                
                addCircle(500, 360, '3', '#22c55e');
                addLabel(540, 350, 'Nível de ensino');
            """)
            
            page.screenshot(path=str(OUTPUT_DIR / "05-nova-materia-anotado.png"))
            page.evaluate("clearAnnotations()")
            print("   ✅ 05-nova-materia-anotado.png")
            
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            
            # ========================================
            # 6. FLUXO COMPLETO: CORRIGIR PROVA
            # ========================================
            print("\n📸 6. Fluxo de correção...")
            
            # Navegar para uma matéria existente
            materia = page.query_selector(".materia-card")
            if materia:
                materia.click()
                page.wait_for_timeout(1000)
            
            page.evaluate(add_annotation_script())
            page.evaluate("""
                addLabel(600, 100, '📋 Passo a Passo para Corrigir Provas', '#ef4444');
                
                addCircle(400, 200, '1', '#ef4444');
                addLabel(450, 190, 'Faça upload do enunciado da prova');
                
                addCircle(400, 280, '2', '#3b82f6');
                addLabel(450, 270, 'Adicione o gabarito');
                
                addCircle(400, 360, '3', '#22c55e');
                addLabel(450, 350, 'Suba as provas respondidas dos alunos');
                
                addCircle(400, 440, '4', '#a855f7');
                addLabel(450, 430, 'Clique em "Pipeline" para corrigir tudo!');
            """)
            
            page.screenshot(path=str(OUTPUT_DIR / "06-fluxo-correcao.png"))
            page.evaluate("clearAnnotations()")
            print("   ✅ 06-fluxo-correcao.png")
            
            print("\n" + "="*60)
            print("✅ Screenshots anotados capturados!")
            print(f"📁 Pasta: {OUTPUT_DIR}")
            
            files = list(OUTPUT_DIR.glob("*.png"))
            print(f"\n📷 {len(files)} imagens criadas:")
            for f in sorted(files):
                print(f"   - {f.name}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    capture_annotated_screenshots()
