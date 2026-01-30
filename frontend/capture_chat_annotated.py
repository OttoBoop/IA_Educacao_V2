"""
Captura screenshot do chat com anotacoes corrigidas
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

BASE_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_DIR = Path(__file__).parent / "tutorial-images-v2"
OUTPUT_DIR.mkdir(exist_ok=True)

def add_annotation_script():
    """JavaScript para adicionar anotacoes visuais"""
    return """
    (function() {
        // Criar overlay de anotacoes
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
    })();
    """

def capture_chat():
    print("[*] Capturando screenshot do chat anotado...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            # Carregar pagina
            print("[*] Carregando pagina...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Fechar modal de welcome
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

            # Navegar para o chat
            print("[*] Navegando para o Chat...")
            chat_link = page.query_selector("text=Chat com IA")
            if chat_link:
                chat_link.click()
                page.wait_for_timeout(2000)

            # Clicar em "Filtrados" para mostrar os filtros
            print("[*] Ativando modo Filtrados...")
            filtrar_btn = page.query_selector('[data-mode="filtered"]')
            if filtrar_btn:
                filtrar_btn.click()
                page.wait_for_timeout(500)

            # Injetar script de anotacoes
            page.evaluate(add_annotation_script())

            # Adicionar anotacoes
            print("[*] Adicionando anotacoes...")
            page.evaluate("""
                // 1. Item "Chat com IA" na sidebar
                addCircle(85, 115, '1', '#3b82f6');
                addLabel(110, 105, 'Acesse o Chat');

                // 2. Botoes de modo de selecao (Todos/Filtrados/Manual)
                addCircle(330, 130, '2', '#22c55e');
                addLabel(360, 120, 'Escolha o modo de selecao');

                // 3. Seletor de modelo no header
                addCircle(1200, 80, '3', '#a855f7');
                addLabel(1000, 70, 'Selecione o modelo de IA');

                // 4. Campo de input na parte inferior
                addCircle(700, 850, '4', '#ef4444');
                addLabel(750, 840, 'Digite sua pergunta aqui');
            """)

            # Capturar screenshot
            output_path = OUTPUT_DIR / "03-chat-anotado.png"
            page.screenshot(path=str(output_path))
            print(f"[OK] Chat anotado capturado: {output_path}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    capture_chat()
