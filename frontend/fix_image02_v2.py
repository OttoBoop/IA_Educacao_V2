"""
Corrigir imagem 02-sidebar com posicoes fixas
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
                font-size: 16px;
                font-weight: bold;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
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
                box-shadow: 0 2px 8px rgba(0,0,0,0.4);
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

def fix_image02():
    print("[*] Corrigindo imagem 02-sidebar...\n")

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

            page.evaluate(add_annotation_script())

            # Encontrar elementos e posicionar circulos usando getBoundingClientRect
            page.evaluate("""
                // Encontrar itens da navegacao
                const navItems = document.querySelectorAll('.sidebar .nav-item, .sidebar a, .sidebar-nav a');
                console.log('Found nav items:', navItems.length);

                // Procurar por texto especifico
                let inicioEl = null;
                let chatEl = null;

                document.querySelectorAll('*').forEach(el => {
                    const text = el.textContent.trim();
                    if (text === 'Início' && el.closest('.sidebar')) {
                        inicioEl = el;
                    }
                    if (text === 'Chat com IA' && el.closest('.sidebar')) {
                        chatEl = el;
                    }
                });

                // 1. Inicio
                if (inicioEl) {
                    const rect = inicioEl.getBoundingClientRect();
                    console.log('Inicio rect:', rect);
                    addCircle(rect.right + 20, rect.top + rect.height/2, '1', '#3b82f6');
                    addLabel(rect.right + 40, rect.top + rect.height/2 - 12, 'Voltar ao Inicio', '#3b82f6');
                } else {
                    // Fallback com posicao fixa
                    addCircle(180, 95, '1', '#3b82f6');
                    addLabel(200, 83, 'Voltar ao Inicio', '#3b82f6');
                }

                // 2. Chat com IA
                if (chatEl) {
                    const rect = chatEl.getBoundingClientRect();
                    console.log('Chat rect:', rect);
                    addCircle(rect.right + 20, rect.top + rect.height/2, '2', '#22c55e');
                    addLabel(rect.right + 40, rect.top + rect.height/2 - 12, 'Chat com IA', '#22c55e');
                } else {
                    // Fallback com posicao fixa
                    addCircle(180, 130, '2', '#22c55e');
                    addLabel(200, 118, 'Chat com IA', '#22c55e');
                }

                // 3. Secao MATERIAS - procurar o header especificamente
                let materiasEl = null;
                // Procurar spans ou divs que contenham exatamente MATERIAS
                document.querySelectorAll('span, div, h4, h5, p').forEach(el => {
                    const text = el.textContent.trim();
                    if (text === 'MATÉRIAS' || text === 'MATERIAS') {
                        materiasEl = el;
                    }
                });

                if (materiasEl) {
                    const rect = materiasEl.getBoundingClientRect();
                    console.log('Materias encontrado:', rect);
                    addCircle(rect.right + 30, rect.top + rect.height/2, '3', '#a855f7');
                    addLabel(rect.right + 50, rect.top + rect.height/2 - 12, 'Suas Materias', '#a855f7');
                } else {
                    // Fallback com posicao fixa baseada na UI observada
                    // MATERIAS fica abaixo de Todos os Alunos
                    console.log('Materias nao encontrado, usando fallback');
                    addCircle(270, 360, '3', '#a855f7');
                    addLabel(290, 348, 'Suas Materias', '#a855f7');
                }

                // 4. Botao Ajuda
                const ajudaBtn = document.querySelector('.help-btn') ||
                                 document.querySelector('#help-btn') ||
                                 document.querySelector('button.btn-help');

                // Tambem procurar por texto "Ajuda"
                let ajudaEl = ajudaBtn;
                if (!ajudaEl) {
                    document.querySelectorAll('button').forEach(el => {
                        if (el.textContent.includes('Ajuda')) {
                            ajudaEl = el;
                        }
                    });
                }

                if (ajudaEl) {
                    const rect = ajudaEl.getBoundingClientRect();
                    console.log('Ajuda rect:', rect);
                    addCircle(rect.left + rect.width/2, rect.top - 20, '4', '#ef4444');
                    addLabel(rect.right + 10, rect.top - 15, 'Ajuda e Tutorial', '#ef4444');
                } else {
                    // Fallback com posicao fixa
                    addCircle(200, 830, '4', '#ef4444');
                    addLabel(220, 818, 'Ajuda e Tutorial', '#ef4444');
                }
            """)

            # Capturar apenas a sidebar (largura maior para labels)
            page.screenshot(
                path=str(OUTPUT_DIR / "02-sidebar-anotado.png"),
                clip={"x": 0, "y": 0, "width": 450, "height": 900}
            )

            print("[OK] 02-sidebar-anotado.png corrigida!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    fix_image02()
