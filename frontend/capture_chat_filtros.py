"""
Captura screenshot do chat focando nos FILTROS com anotacoes explicativas
Alinhado com o texto do tutorial que diz: "Use os filtros: Selecione materia, turma ou aluno"
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
                left: ${x - 16}px;
                top: ${y - 16}px;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: ${color};
                color: white;
                font-size: 15px;
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
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12px;
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

def capture_chat_filtros():
    print("[*] Capturando screenshot do chat focado nos filtros...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
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

            # Adicionar anotacoes nos FILTROS (dropdowns do painel de contexto)
            # Coordenadas finais: Y +35 adicional
            print("[*] Adicionando anotacoes nos filtros...")
            page.evaluate("""
                // 1. Dropdown de Alunos - caixa "Selecionar alunos..."
                addCircle(350, 290, '1', '#3b82f6');
                addLabel(375, 283, 'Filtre por aluno');

                // 2. Dropdown de Materias - caixa "Selecionar materias..."
                addCircle(350, 355, '2', '#22c55e');
                addLabel(375, 348, 'Selecione a materia');

                // 3. Dropdown de Turmas - caixa "Selecione turma(s)..."
                addCircle(350, 420, '3', '#a855f7');
                addLabel(375, 413, 'Escolha a turma');

                // 4. Dropdown de Tipos - caixa "Selecionar tipos..."
                addCircle(350, 550, '4', '#ef4444');
                addLabel(375, 543, 'Tipo de documento');
            """)

            # Capturar screenshot
            output_path = OUTPUT_DIR / "03-chat-anotado.png"
            page.screenshot(path=str(output_path))
            print(f"[OK] Chat com filtros anotados: {output_path}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()

if __name__ == "__main__":
    capture_chat_filtros()
