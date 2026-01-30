"""
Corrigir imagens 02-sidebar e 14-resultados
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

def fix_images():
    print("[*] Corrigindo imagens 02 e 14...\n")

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

            # ========================================
            # IMAGEM 02 - SIDEBAR
            # ========================================
            print("[*] Corrigindo imagem 02-sidebar...")

            page.evaluate(add_annotation_script())

            # Posicionar circulos nos itens CORRETOS da sidebar
            page.evaluate("""
                // 1. Inicio (primeiro item da navegacao)
                const navItems = document.querySelectorAll('.nav-item');
                const inicio = navItems[0]; // Primeiro item = Inicio
                if (inicio) {
                    const rect = inicio.getBoundingClientRect();
                    addCircle(rect.right + 15, rect.top + rect.height/2, '1', '#3b82f6');
                    addLabel(rect.right + 35, rect.top + rect.height/2 - 12, 'Voltar ao Inicio', '#3b82f6');
                }

                // 2. Chat com IA (segundo item)
                const chatItem = navItems[1];
                if (chatItem) {
                    const rect = chatItem.getBoundingClientRect();
                    addCircle(rect.right + 15, rect.top + rect.height/2, '2', '#22c55e');
                    addLabel(rect.right + 35, rect.top + rect.height/2 - 12, 'Chat com IA', '#22c55e');
                }

                // 3. Secao Materias - usar o header da secao
                const sectionHeaders = document.querySelectorAll('.sidebar-section-header, .nav-section-title, h4');
                let materiasHeader = null;
                sectionHeaders.forEach(el => {
                    if (el.textContent.toUpperCase().includes('MATERI')) {
                        materiasHeader = el;
                    }
                });
                if (materiasHeader) {
                    const rect = materiasHeader.getBoundingClientRect();
                    addCircle(rect.right + 15, rect.top + rect.height/2, '3', '#a855f7');
                    addLabel(rect.right + 35, rect.top + rect.height/2 - 12, 'Suas Materias', '#a855f7');
                } else {
                    // Fallback: usar a area de materias (tree-items)
                    const treeItems = document.querySelectorAll('.tree-item');
                    if (treeItems.length > 0) {
                        const rect = treeItems[0].getBoundingClientRect();
                        addCircle(rect.left - 20, rect.top - 30, '3', '#a855f7');
                        addLabel(rect.left, rect.top - 45, 'Suas Materias', '#a855f7');
                    }
                }

                // 4. Botao Ajuda
                const ajudaBtn = document.querySelector('.help-btn') || document.querySelector('#help-btn');
                if (ajudaBtn) {
                    const rect = ajudaBtn.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '4', '#ef4444');
                    addLabel(rect.left - 80, rect.top + rect.height/2 - 12, 'Ajuda', '#ef4444');
                }
            """)

            # Capturar apenas a sidebar (clip)
            page.screenshot(
                path=str(OUTPUT_DIR / "02-sidebar-anotado.png"),
                clip={"x": 0, "y": 0, "width": 400, "height": 900}
            )
            page.evaluate("clearAnnotations()")
            print("    [OK] 02-sidebar-anotado.png")

            # ========================================
            # IMAGEM 14 - RESULTADOS
            # ========================================
            print("\n[*] Corrigindo imagem 14-resultados...")

            # Criar mock da pagina de resultados
            page.evaluate("""
                const content = document.getElementById('content');
                if (content) {
                    content.innerHTML = `
                        <div style="padding: 20px;">
                            <div style="margin-bottom: 10px;">
                                <span style="color: #64748b; font-size: 14px;">Matematica > 9o Ano A > Prova Bimestral</span>
                            </div>
                            <h1 style="color: white; margin: 0 0 20px 0; font-size: 24px;">Resultado: Joao Silva</h1>

                            <div id="summary-cards" style="display: flex; gap: 20px; margin-bottom: 20px;">
                                <div id="nota-card" style="background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; text-align: center;">
                                    <h3 style="color: #94a3b8; margin-bottom: 10px; font-size: 14px;">Nota Final</h3>
                                    <div style="font-size: 48px; color: #22c55e; font-weight: bold;">8.5</div>
                                    <div style="color: #64748b; font-size: 14px;">de 10.0 pontos</div>
                                </div>
                                <div style="background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; text-align: center;">
                                    <h3 style="color: #94a3b8; margin-bottom: 10px; font-size: 14px;">Questoes Corretas</h3>
                                    <div style="font-size: 48px; color: #3b82f6; font-weight: bold;">8/10</div>
                                    <div style="color: #64748b; font-size: 14px;">acertos</div>
                                </div>
                                <div style="background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; text-align: center;">
                                    <h3 style="color: #94a3b8; margin-bottom: 10px; font-size: 14px;">Nivel</h3>
                                    <div style="font-size: 48px; color: #a855f7; font-weight: bold;">B</div>
                                    <div style="color: #64748b; font-size: 14px;">Bom</div>
                                </div>
                            </div>

                            <div id="tabs-section" style="background: #1e293b; border-radius: 8px; overflow: hidden;">
                                <div id="tabs-header" style="display: flex; gap: 0; border-bottom: 1px solid #334155;">
                                    <button style="background: #3b82f6; color: white; padding: 12px 20px; border: none;">📄 Documentos</button>
                                    <button style="background: transparent; color: #94a3b8; padding: 12px 20px; border: none;">🤖 Etapas da IA</button>
                                    <button style="background: transparent; color: #94a3b8; padding: 12px 20px; border: none;">📊 Resultado Final</button>
                                </div>
                                <div id="docs-content" style="padding: 20px;">
                                    <h4 style="color: white; margin-bottom: 15px;">Documentos do Aluno</h4>
                                    <div id="doc-icons" style="display: flex; gap: 15px; flex-wrap: wrap;">
                                        <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 100px;">
                                            <div style="font-size: 28px; margin-bottom: 8px;">📝</div>
                                            <div style="color: white; font-size: 11px;">Prova</div>
                                        </div>
                                        <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 100px;">
                                            <div style="font-size: 28px; margin-bottom: 8px;">🔍</div>
                                            <div style="color: white; font-size: 11px;">Extraido</div>
                                        </div>
                                        <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 100px;">
                                            <div style="font-size: 28px; margin-bottom: 8px;">✅</div>
                                            <div style="color: white; font-size: 11px;">Correcao</div>
                                        </div>
                                        <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 100px;">
                                            <div style="font-size: 28px; margin-bottom: 8px;">📊</div>
                                            <div style="color: white; font-size: 11px;">Relatorio</div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="skills-section" style="background: #1e293b; border-radius: 8px; padding: 20px; margin-top: 20px;">
                                <h4 style="color: white; margin-bottom: 15px;">Analise de Habilidades</h4>
                                <div id="skill-badges" style="display: flex; flex-wrap: wrap; gap: 10px;">
                                    <span style="background: #22c55e20; color: #22c55e; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Algebra: Excelente</span>
                                    <span style="background: #3b82f620; color: #3b82f6; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Geometria: Bom</span>
                                    <span style="background: #eab30820; color: #eab308; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Trigonometria: Regular</span>
                                    <span style="background: #22c55e20; color: #22c55e; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Aritmetica: Excelente</span>
                                </div>
                            </div>
                        </div>
                    `;
                }
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())

            # Adicionar circulos nos elementos CORRETOS (no conteudo, nao na sidebar)
            page.evaluate("""
                // 1. Card da Nota (primeiro card)
                const notaCard = document.getElementById('nota-card');
                if (notaCard) {
                    const rect = notaCard.getBoundingClientRect();
                    addCircle(rect.left + rect.width/2, rect.top - 15, '1', '#22c55e');
                    addLabel(rect.left + rect.width/2 + 20, rect.top - 25, 'Nota calculada pela IA', '#22c55e');
                }

                // 2. Abas de navegacao
                const tabsHeader = document.getElementById('tabs-header');
                if (tabsHeader) {
                    const rect = tabsHeader.getBoundingClientRect();
                    addCircle(rect.left - 15, rect.top + rect.height/2, '2', '#3b82f6');
                    addLabel(rect.left - 180, rect.top + rect.height/2 - 10, 'Navegue entre secoes', '#3b82f6');
                }

                // 3. Icones de documentos
                const docIcons = document.getElementById('doc-icons');
                if (docIcons) {
                    const rect = docIcons.getBoundingClientRect();
                    addCircle(rect.left - 15, rect.top + rect.height/2, '3', '#a855f7');
                    addLabel(rect.left - 160, rect.top + rect.height/2 - 10, 'Documentos gerados', '#a855f7');
                }

                // 4. Badges de habilidades
                const skillBadges = document.getElementById('skill-badges');
                if (skillBadges) {
                    const rect = skillBadges.getBoundingClientRect();
                    addCircle(rect.left - 15, rect.top + rect.height/2, '4', '#ef4444');
                    addLabel(rect.left - 180, rect.top + rect.height/2 - 10, 'Analise de habilidades', '#ef4444');
                }
            """)

            page.screenshot(path=str(OUTPUT_DIR / "14-resultados.png"))
            page.evaluate("clearAnnotations()")
            print("    [OK] 14-resultados.png")

            print("\n[OK] Imagens corrigidas!")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    fix_images()
