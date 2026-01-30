"""
Corrigir imagem 05-nova-materia-anotado.png
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

        window.addCircleNearElement = function(selector, number, color, offsetX = -40, offsetY = 0) {
            const el = document.querySelector(selector);
            if (!el) { console.log('Element not found:', selector); return null; }
            const rect = el.getBoundingClientRect();
            addCircle(rect.left + offsetX, rect.top + rect.height/2 + offsetY, number, color);
            return rect;
        };

        window.addLabelNearElement = function(selector, text, color, offsetX = 30, offsetY = -10) {
            const el = document.querySelector(selector);
            if (!el) { console.log('Element not found:', selector); return null; }
            const rect = el.getBoundingClientRect();
            addLabel(rect.right + offsetX, rect.top + offsetY, text, color);
            return rect;
        };

        window.clearAnnotations = function() {
            const overlay = document.getElementById('annotation-overlay');
            if (overlay) overlay.innerHTML = '';
        };
    })();
    """

def fix_image05():
    print("[*] Corrigindo imagem 05-nova-materia-anotado.png...")

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

            # Fechar welcome
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(500)

            # Abrir modal Nova Materia com valores preenchidos
            page.evaluate("""
                document.getElementById('modal-materia').classList.add('active');
                document.getElementById('input-materia-nome').value = 'Matematica';
                document.getElementById('input-materia-desc').value = 'Algebra e Geometria para o 9o ano';
                document.getElementById('input-materia-nivel').value = 'fundamental_2';
            """)
            page.wait_for_timeout(500)

            # Adicionar anotacoes APENAS para o modal
            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircleNearElement('#input-materia-nome', '1', '#ef4444', -35, 0);
                addLabelNearElement('#input-materia-nome', 'Nome da disciplina', '#ef4444', 10, 0);

                addCircleNearElement('#input-materia-desc', '2', '#22c55e', -35, 0);
                addLabelNearElement('#input-materia-desc', 'Descricao (opcional)', '#22c55e', 10, 0);

                addCircleNearElement('#input-materia-nivel', '3', '#a855f7', -35, 0);
                addLabelNearElement('#input-materia-nivel', 'Nivel de ensino', '#a855f7', 10, 0);

                addCircleNearElement('#modal-materia .btn-primary', '4', '#3b82f6', -35, 0);
                addLabelNearElement('#modal-materia .btn-primary', 'Criar materia', '#3b82f6', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "05-nova-materia-anotado.png"))
            print("[OK] Imagem 05 corrigida!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    fix_image05()
