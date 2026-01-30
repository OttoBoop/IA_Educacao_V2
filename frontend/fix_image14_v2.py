"""
Corrigir imagem 14 - posicionar circulos e labels DENTRO da area de conteudo
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
    })();
    """

def fix_image14():
    print("[*] Corrigindo imagem 14-resultados...")

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

            # Criar mock da pagina de resultados
            page.evaluate("""
                const content = document.getElementById('content');
                if (content) {
                    content.innerHTML = `
                        <div class="page-header" style="padding: 20px 30px;">
                            <div class="page-title">
                                <span class="page-breadcrumb" style="color: #888; font-size: 12px;">Matematica > 9o Ano A > Prova Bimestral</span>
                                <h1 style="margin: 5px 0; font-size: 24px;">Resultado: Joao Silva</h1>
                            </div>
                        </div>

                        <div style="padding: 0 30px;">
                            <div id="nota-card" style="display: flex; gap: 20px; margin-bottom: 30px;">
                                <div style="flex: 1; background: #1e293b; border-radius: 12px; padding: 20px; text-align: center;">
                                    <div style="color: #888; font-size: 12px;">Nota Final</div>
                                    <div style="color: #22c55e; font-size: 48px; font-weight: bold;">8.5</div>
                                    <div style="color: #666; font-size: 11px;">de 10.0 pontos</div>
                                </div>
                                <div style="flex: 1; background: #1e293b; border-radius: 12px; padding: 20px; text-align: center;">
                                    <div style="color: #888; font-size: 12px;">Questoes Corretas</div>
                                    <div style="color: #3b82f6; font-size: 48px; font-weight: bold;">8/10</div>
                                    <div style="color: #666; font-size: 11px;">acertos</div>
                                </div>
                                <div style="flex: 1; background: #1e293b; border-radius: 12px; padding: 20px; text-align: center;">
                                    <div style="color: #888; font-size: 12px;">Nivel de Desempenho</div>
                                    <div style="color: #a855f7; font-size: 48px; font-weight: bold;">B</div>
                                    <div style="color: #666; font-size: 11px;">Bom</div>
                                </div>
                            </div>

                            <div id="tabs-header" style="display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px;">
                                <button style="background: #3b82f6; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;">Documentos</button>
                                <button style="background: transparent; color: #888; padding: 8px 16px; border: none; cursor: pointer;">Etapas da IA</button>
                                <button style="background: transparent; color: #888; padding: 8px 16px; border: none; cursor: pointer;">Resultado Final</button>
                            </div>

                            <div style="margin-bottom: 30px;">
                                <h3 style="color: white; margin-bottom: 15px;">Documentos do Aluno</h3>
                                <div id="doc-icons" style="display: flex; gap: 15px;">
                                    <div style="width: 80px; text-align: center;">
                                        <div style="width: 60px; height: 70px; background: #60a5fa; border-radius: 8px; margin: 0 auto 8px;"></div>
                                        <span style="color: #888; font-size: 11px;">Prova</span>
                                    </div>
                                    <div style="width: 80px; text-align: center;">
                                        <div style="width: 60px; height: 70px; background: #f97316; border-radius: 8px; margin: 0 auto 8px;"></div>
                                        <span style="color: #888; font-size: 11px;">Extraido</span>
                                    </div>
                                    <div style="width: 80px; text-align: center;">
                                        <div style="width: 60px; height: 70px; background: #22c55e; border-radius: 8px; margin: 0 auto 8px;"></div>
                                        <span style="color: #888; font-size: 11px;">Correcao</span>
                                    </div>
                                    <div style="width: 80px; text-align: center;">
                                        <div style="width: 60px; height: 70px; background: #ef4444; border-radius: 8px; margin: 0 auto 8px;"></div>
                                        <span style="color: #888; font-size: 11px;">Relatorio</span>
                                    </div>
                                </div>
                            </div>

                            <div>
                                <h3 style="color: white; margin-bottom: 15px;">Analise de Habilidades</h3>
                                <div id="skill-badges" style="display: flex; gap: 10px; flex-wrap: wrap;">
                                    <span style="background: #22c55e; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">Algebra: Excelente</span>
                                    <span style="background: #3b82f6; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">Geometria: Bom</span>
                                    <span style="background: #f59e0b; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">Trigonometria: Regular</span>
                                    <span style="background: #22c55e; color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px;">Aritmetica: Excelente</span>
                                </div>
                            </div>
                        </div>
                    `;
                }
            """)
            page.wait_for_timeout(500)

            # Adicionar anotacoes
            page.evaluate(add_annotation_script())

            # Posicionar circulos e labels DENTRO da area de conteudo
            # Labels posicionados ACIMA dos circulos para caberem na tela
            page.evaluate("""
                // 1. Nota - acima do card de nota (label ao lado do circulo)
                const notaCard = document.getElementById('nota-card');
                if (notaCard) {
                    const rect = notaCard.getBoundingClientRect();
                    addCircle(rect.left + 80, rect.top - 20, '1', '#3b82f6');
                    addLabel(rect.left + 100, rect.top - 30, 'Nota calculada pela IA', '#3b82f6');
                }

                // 2. Abas - circulo no final das abas, label acima
                const tabs = document.getElementById('tabs-header');
                if (tabs) {
                    const rect = tabs.getBoundingClientRect();
                    // Posicionar no meio das abas
                    addCircle(rect.left + 250, rect.top - 15, '2', '#22c55e');
                    addLabel(rect.left + 270, rect.top - 25, 'Navegue entre secoes', '#22c55e');
                }

                // 3. Documentos - circulo ao lado, label acima
                const docs = document.getElementById('doc-icons');
                if (docs) {
                    const rect = docs.getBoundingClientRect();
                    addCircle(rect.left + 350, rect.top - 15, '3', '#a855f7');
                    addLabel(rect.left + 370, rect.top - 25, 'Documentos gerados pela IA', '#a855f7');
                }

                // 4. Habilidades - circulo e label ACIMA dos badges, alinhado a esquerda
                const skills = document.getElementById('skill-badges');
                if (skills) {
                    const rect = skills.getBoundingClientRect();
                    addCircle(rect.left + 400, rect.top - 15, '4', '#ef4444');
                    addLabel(rect.left + 420, rect.top - 25, 'Analise de habilidades', '#ef4444');
                }
            """)

            page.screenshot(path=str(OUTPUT_DIR / "14-resultados.png"))
            print("[OK] 14-resultados.png corrigida!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    fix_image14()
