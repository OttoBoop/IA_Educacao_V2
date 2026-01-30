"""
Corrigir imagem 04-chat-exemplos
Mostrar:
1. Filtros com selecoes amigaveis (materia e turma especificas)
2. Exemplos de perguntas na area do chat
3. Anotacoes claras e uteis
"""
from playwright.sync_api import sync_playwright
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).parent / "tutorial-images-v2"

def add_annotation_script():
    return """
    (function() {
        const oldOverlay = document.getElementById('annotation-overlay');
        if (oldOverlay) oldOverlay.remove();

        const overlay = document.createElement('div');
        overlay.id = 'annotation-overlay';
        overlay.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 99999;';
        document.body.appendChild(overlay);

        window.addCircle = function(x, y, number, color) {
            const circle = document.createElement('div');
            circle.style.cssText = 'position: absolute; left: ' + (x - 16) + 'px; top: ' + (y - 16) + 'px; width: 32px; height: 32px; border-radius: 50%; background: ' + color + '; color: white; font-size: 16px; font-weight: bold; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0,0,0,0.4); font-family: Inter, sans-serif;';
            circle.textContent = number;
            overlay.appendChild(circle);
        };

        window.addLabel = function(x, y, text, color) {
            const label = document.createElement('div');
            label.style.cssText = 'position: absolute; left: ' + x + 'px; top: ' + y + 'px; background: ' + color + '; color: white; padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; font-family: Inter, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.4); white-space: nowrap;';
            label.textContent = text;
            overlay.appendChild(label);
        };

        window.addExampleBubble = function(x, y, text, color) {
            const bubble = document.createElement('div');
            bubble.style.cssText = 'position: absolute; left: ' + x + 'px; top: ' + y + 'px; background: ' + color + '; color: white; padding: 10px 16px; border-radius: 12px; font-size: 13px; font-weight: 500; font-family: Inter, sans-serif; box-shadow: 0 2px 8px rgba(0,0,0,0.3); max-width: 250px;';
            bubble.textContent = text;
            overlay.appendChild(bubble);
        };
    })();
    """

def fix_image04():
    print("[*] Corrigindo imagem 04-chat-exemplos...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(500)

            # Navegar para o Chat
            page.click("text=Chat com IA")
            page.wait_for_timeout(2000)

            # Clicar no botao "Filtrar" para mudar o modo
            try:
                filtrar_btn = page.query_selector('button:has-text("Filtrar")')
                if filtrar_btn:
                    filtrar_btn.click()
                    page.wait_for_timeout(500)
            except:
                pass

            # Tambem tentar via data-mode
            page.evaluate("""
                const btn = document.querySelector('[data-mode="filter"]') ||
                            Array.from(document.querySelectorAll('button')).find(b =>
                                b.textContent.trim() === 'Filtrar' ||
                                b.textContent.includes('Filtrar'));
                if (btn) btn.click();
            """)
            page.wait_for_timeout(800)

            # Adicionar script de anotacoes
            page.evaluate(add_annotation_script())

            # Anotacoes mais simples e claras
            page.evaluate("""
                // 1. Contexto/Documentos - no titulo do painel
                addCircle(200, 65, '1', '#3b82f6');
                addLabel(220, 55, 'Contexto da conversa', '#3b82f6');

                // 2. Modelo de IA - no seletor
                addCircle(620, 65, '2', '#22c55e');
                addLabel(640, 55, 'Escolha o modelo', '#22c55e');

                // 3. Campo de pergunta - no input
                addCircle(620, 450, '3', '#ef4444');
                addLabel(640, 440, 'Faca sua pergunta', '#ef4444');

                // Exemplos - todos com X >= 550 para ficar na area do chat
                addLabel(550, 230, 'Experimente perguntar:', '#374151');
                addExampleBubble(550, 270, '"Relatorio completo da turma"', '#8b5cf6');
                addExampleBubble(550, 330, '"Desempenho do Joao Silva"', '#f59e0b');
                addExampleBubble(550, 390, '"Quais questoes mais erradas?"', '#10b981');
            """)

            page.screenshot(path=str(OUTPUT_DIR / "04-chat-exemplos.png"))
            print("[OK] 04-chat-exemplos.png gerada!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    fix_image04()
