"""
Captura screenshots para o tutorial completo do Prova AI
Usa JavaScript direto para evitar problemas de navegacao
"""

from playwright.sync_api import sync_playwright
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
OUTPUT_DIR = Path(__file__).parent / "tutorial-images-v2"
OUTPUT_DIR.mkdir(exist_ok=True)

def add_annotation_script():
    """JavaScript para adicionar anotacoes visuais"""
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


def capture_tutorial_images():
    print("[*] Capturando screenshots para tutorial completo\n")
    print("="*60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            print("[*] Carregando aplicacao local...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Fechar modal de welcome
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(500)

            # ========================================
            # CAPTURAR MODAIS (sem criar dados reais)
            # ========================================
            print("\n[*] Capturando modais...")

            # 07: Modal Nova Turma
            print("\n[*] 07. Modal Nova Turma...")
            page.evaluate("""
                document.getElementById('modal-turma').classList.add('active');
                document.getElementById('input-turma-nome').value = '9o Ano A';
                document.getElementById('input-turma-ano').value = '2024';
                document.getElementById('input-turma-periodo').value = 'Manha';
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircleNearElement('#input-turma-nome', '1', '#3b82f6', -35, 0);
                addLabelNearElement('#input-turma-nome', 'Nome da turma', '#3b82f6', 10, 0);
                addCircleNearElement('#input-turma-ano', '2', '#22c55e', -35, 0);
                addLabelNearElement('#input-turma-ano', 'Ano letivo', '#22c55e', 10, 0);
                addCircleNearElement('#input-turma-periodo', '3', '#a855f7', -35, 0);
                addLabelNearElement('#input-turma-periodo', 'Periodo', '#a855f7', 10, 0);
                addCircleNearElement('#modal-turma .btn-primary', '4', '#ef4444', -35, 0);
                addLabelNearElement('#modal-turma .btn-primary', 'Criar turma', '#ef4444', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "07-nova-turma.png"))
            page.evaluate("clearAnnotations()")
            page.evaluate("document.getElementById('modal-turma').classList.remove('active')")
            page.wait_for_timeout(300)
            print("    [OK] 07-nova-turma.png")

            # 08: Modal Adicionar Aluno
            print("\n[*] 08. Modal Adicionar Aluno...")
            page.evaluate("""
                document.getElementById('modal-aluno').classList.add('active');
                // Trocar para aba de criar novo aluno
                const tabSel = document.getElementById('tab-selecionar-aluno');
                const tabCriar = document.getElementById('tab-criar-aluno');
                const btnSel = document.getElementById('tab-btn-selecionar');
                const btnCriar = document.getElementById('tab-btn-criar');
                if (tabSel) tabSel.style.display = 'none';
                if (tabCriar) tabCriar.style.display = 'block';
                if (btnSel) btnSel.classList.remove('active');
                if (btnCriar) btnCriar.classList.add('active');
                document.getElementById('input-aluno-nome').value = 'Maria Santos';
                document.getElementById('input-aluno-matricula').value = '2024002';
                document.getElementById('input-aluno-email').value = 'maria@escola.edu.br';
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircleNearElement('#tab-btn-selecionar', '1', '#3b82f6', -25, 0);
                addLabelNearElement('#tab-btn-selecionar', 'Buscar existente', '#3b82f6', 5, 0);
                addCircleNearElement('#tab-btn-criar', '2', '#22c55e', -25, 0);
                addLabelNearElement('#tab-btn-criar', 'Criar novo', '#22c55e', 5, 0);
                addCircleNearElement('#input-aluno-nome', '3', '#a855f7', -35, 0);
                addLabelNearElement('#input-aluno-nome', 'Nome completo', '#a855f7', 10, 0);
                addCircleNearElement('#input-aluno-matricula', '4', '#ef4444', -35, 0);
                addLabelNearElement('#input-aluno-matricula', 'Matricula', '#ef4444', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "08-adicionar-alunos.png"))
            page.evaluate("clearAnnotations()")
            page.evaluate("document.getElementById('modal-aluno').classList.remove('active')")
            page.wait_for_timeout(300)
            print("    [OK] 08-adicionar-alunos.png")

            # 09: Modal Nova Atividade
            print("\n[*] 09. Modal Nova Atividade...")
            page.evaluate("""
                document.getElementById('modal-atividade').classList.add('active');
                document.getElementById('input-ativ-nome').value = 'Prova Bimestral';
                document.getElementById('input-ativ-tipo').value = 'prova';
                document.getElementById('input-ativ-nota').value = '10';
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircleNearElement('#input-ativ-nome', '1', '#3b82f6', -35, 0);
                addLabelNearElement('#input-ativ-nome', 'Nome da atividade', '#3b82f6', 10, 0);
                addCircleNearElement('#input-ativ-tipo', '2', '#22c55e', -35, 0);
                addLabelNearElement('#input-ativ-tipo', 'Tipo', '#22c55e', 10, 0);
                addCircleNearElement('#input-ativ-nota', '3', '#a855f7', -35, 0);
                addLabelNearElement('#input-ativ-nota', 'Nota maxima', '#a855f7', 10, 0);
                addCircleNearElement('#modal-atividade .btn-primary', '4', '#ef4444', -35, 0);
                addLabelNearElement('#modal-atividade .btn-primary', 'Criar atividade', '#ef4444', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "09-nova-atividade.png"))
            page.evaluate("clearAnnotations()")
            page.evaluate("document.getElementById('modal-atividade').classList.remove('active')")
            page.wait_for_timeout(300)
            print("    [OK] 09-nova-atividade.png")

            # 10: Modal Upload
            print("\n[*] 10. Modal Upload...")
            page.evaluate("""
                document.getElementById('modal-upload').classList.add('active');
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircleNearElement('#input-upload-tipo', '1', '#3b82f6', -35, 0);
                addLabelNearElement('#input-upload-tipo', 'Tipo de documento', '#3b82f6', 10, 0);
                addCircleNearElement('#upload-zone-modal', '2', '#22c55e', -35, 0);
                addLabelNearElement('#upload-zone-modal', 'Arraste arquivos aqui', '#22c55e', 10, -20);
                addCircleNearElement('#modal-upload .btn-primary', '3', '#ef4444', -35, 0);
                addLabelNearElement('#modal-upload .btn-primary', 'Fazer upload', '#ef4444', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "10-upload-docs.png"))
            page.evaluate("clearAnnotations()")
            page.evaluate("document.getElementById('modal-upload').classList.remove('active')")
            page.wait_for_timeout(300)
            print("    [OK] 10-upload-docs.png")

            # 11: Modal Upload em Lote
            print("\n[*] 11. Modal Upload em Lote...")
            page.evaluate("""
                document.getElementById('modal-upload-provas').classList.add('active');
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                addCircleNearElement('#input-upload-provas-modo', '1', '#3b82f6', -35, 0);
                addLabelNearElement('#input-upload-provas-modo', 'Modo de identificacao', '#3b82f6', 10, 0);
                addCircleNearElement('#input-upload-provas-files', '2', '#22c55e', -35, 0);
                addLabelNearElement('#input-upload-provas-files', 'Selecione os arquivos', '#22c55e', 10, 0);
                addCircleNearElement('#modal-upload-provas .btn-primary', '3', '#ef4444', -35, 0);
                addLabelNearElement('#modal-upload-provas .btn-primary', 'Enviar provas', '#ef4444', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "11-upload-lote.png"))
            page.evaluate("clearAnnotations()")
            page.evaluate("document.getElementById('modal-upload-provas').classList.remove('active')")
            page.wait_for_timeout(300)
            print("    [OK] 11-upload-lote.png")

            # ========================================
            # 12: PAGINA DE ATIVIDADE COM BOTOES PIPELINE
            # ========================================
            print("\n[*] 12. Pagina de atividade com botoes do pipeline...")

            # Criar mock da pagina de atividade
            page.evaluate("""
                const content = document.getElementById('content');
                if (content) {
                    content.innerHTML = `
                        <div class="page-header">
                            <div class="page-title">
                                <span class="page-breadcrumb">Matematica > 9o Ano A</span>
                                <h1>Prova Bimestral</h1>
                            </div>
                            <div class="page-actions">
                                <button class="btn btn-outline" id="btn-executar-etapa">
                                    <span class="btn-icon">⚡</span>
                                    Executar Etapa
                                </button>
                                <button class="btn btn-outline" id="btn-pipeline-aluno">
                                    <span class="btn-icon">👤</span>
                                    Pipeline Aluno
                                </button>
                                <button class="btn btn-primary" id="btn-pipeline-turma">
                                    <span class="btn-icon">👥</span>
                                    Pipeline Turma Toda
                                </button>
                            </div>
                        </div>

                        <div class="content-grid" style="margin-top: 20px;">
                            <div class="card">
                                <div class="card-header">
                                    <h3>Documentos da Atividade</h3>
                                    <button class="btn btn-sm" id="btn-upload-docs">+ Upload</button>
                                </div>
                                <div class="card-body">
                                    <div class="doc-list">
                                        <div class="doc-item">
                                            <span class="doc-icon">📄</span>
                                            <span class="doc-name">Enunciado da Prova.pdf</span>
                                            <span class="doc-badge badge-success">Enunciado</span>
                                        </div>
                                        <div class="doc-item">
                                            <span class="doc-icon">✅</span>
                                            <span class="doc-name">Gabarito.pdf</span>
                                            <span class="doc-badge badge-info">Gabarito</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div class="card">
                                <div class="card-header">
                                    <h3>Provas dos Alunos</h3>
                                    <button class="btn btn-sm btn-primary" id="btn-upload-lote">📤 Upload em Lote</button>
                                </div>
                                <div class="card-body">
                                    <div class="student-list">
                                        <div class="student-item">
                                            <span class="student-name">Joao Silva</span>
                                            <span class="student-status badge-pending">Aguardando</span>
                                        </div>
                                        <div class="student-item">
                                            <span class="student-name">Maria Santos</span>
                                            <span class="student-status badge-pending">Aguardando</span>
                                        </div>
                                        <div class="student-item">
                                            <span class="student-name">Pedro Lima</span>
                                            <span class="student-status badge-pending">Aguardando</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;

                    // Adicionar estilos
                    const style = document.createElement('style');
                    style.textContent = `
                        .page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
                        .page-title { color: white; }
                        .page-breadcrumb { color: #64748b; font-size: 14px; }
                        .page-title h1 { margin: 5px 0 0 0; font-size: 24px; }
                        .page-actions { display: flex; gap: 10px; }
                        .page-actions .btn { display: flex; align-items: center; gap: 8px; padding: 10px 16px; }
                        .btn-icon { font-size: 16px; }
                        .content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
                        .card { background: #1e293b; border-radius: 8px; overflow: hidden; }
                        .card-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; border-bottom: 1px solid #334155; }
                        .card-header h3 { color: white; margin: 0; font-size: 16px; }
                        .card-body { padding: 20px; }
                        .doc-list, .student-list { display: flex; flex-direction: column; gap: 10px; }
                        .doc-item, .student-item { display: flex; align-items: center; gap: 10px; padding: 10px; background: #0f172a; border-radius: 6px; }
                        .doc-icon { font-size: 20px; }
                        .doc-name, .student-name { color: white; flex: 1; }
                        .doc-badge, .student-status { padding: 4px 10px; border-radius: 4px; font-size: 12px; font-weight: 500; }
                        .badge-success { background: #22c55e20; color: #22c55e; }
                        .badge-info { background: #3b82f620; color: #3b82f6; }
                        .badge-pending { background: #eab30820; color: #eab308; }
                    `;
                    document.head.appendChild(style);
                }
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                // Botao Executar Etapa
                const etapaBtn = document.getElementById('btn-executar-etapa');
                if (etapaBtn) {
                    const rect = etapaBtn.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '1', '#3b82f6');
                    addLabel(rect.left - 150, rect.bottom + 10, 'Executar etapa individual', '#3b82f6');
                }

                // Botao Pipeline Aluno
                const alunoBtn = document.getElementById('btn-pipeline-aluno');
                if (alunoBtn) {
                    const rect = alunoBtn.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '2', '#22c55e');
                    addLabel(rect.left - 100, rect.bottom + 10, 'Pipeline um aluno', '#22c55e');
                }

                // Botao Pipeline Turma
                const turmaBtn = document.getElementById('btn-pipeline-turma');
                if (turmaBtn) {
                    const rect = turmaBtn.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '3', '#a855f7');
                    addLabel(rect.left - 100, rect.bottom + 10, 'Pipeline turma toda', '#a855f7');
                }

                // Botao Upload em Lote
                const loteBtn = document.getElementById('btn-upload-lote');
                if (loteBtn) {
                    const rect = loteBtn.getBoundingClientRect();
                    addCircle(rect.right + 20, rect.top + rect.height/2, '4', '#ef4444');
                    addLabel(rect.right + 40, rect.top - 5, 'Upload provas em lote', '#ef4444');
                }
            """)

            page.screenshot(path=str(OUTPUT_DIR / "12-botoes-pipeline.png"))
            page.evaluate("clearAnnotations()")
            print("    [OK] 12-botoes-pipeline.png")

            # 13: Modal Pipeline Completo
            print("\n[*] 13. Modal Pipeline Completo...")
            page.evaluate("""
                document.getElementById('modal-pipeline-completo').classList.add('active');
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                // Radio buttons de modo
                const radios = document.querySelectorAll('input[name="pipeline-modo"]');
                if (radios.length > 0) {
                    const rect = radios[0].getBoundingClientRect();
                    addCircle(rect.left - 30, rect.top + 10, '1', '#3b82f6');
                    addLabel(rect.right + 10, rect.top - 5, 'Aluno ou turma', '#3b82f6');
                }

                addCircleNearElement('#input-pipeline-provider-default', '2', '#22c55e', -35, 0);
                addLabelNearElement('#input-pipeline-provider-default', 'Modelo de IA padrao', '#22c55e', 10, 0);

                // Checkboxes das etapas
                const checkboxes = document.querySelectorAll('.pipeline-step-checkbox');
                if (checkboxes.length > 0) {
                    const rect = checkboxes[0].getBoundingClientRect();
                    addCircle(rect.left - 30, rect.top + 10, '3', '#a855f7');
                    addLabel(rect.right + 10, rect.top - 5, 'Etapas a executar', '#a855f7');
                }

                addCircleNearElement('#modal-pipeline-completo .btn-primary', '4', '#ef4444', -35, 0);
                addLabelNearElement('#modal-pipeline-completo .btn-primary', 'Executar', '#ef4444', 10, 0);
            """)

            page.screenshot(path=str(OUTPUT_DIR / "13-config-pipeline.png"))
            page.evaluate("clearAnnotations()")
            page.evaluate("document.getElementById('modal-pipeline-completo').classList.remove('active')")
            page.wait_for_timeout(300)
            print("    [OK] 13-config-pipeline.png")

            # ========================================
            # 14: Pagina de Resultados
            # ========================================
            print("\n[*] 14. Pagina de Resultados...")

            # Criar mock da pagina de resultados
            page.evaluate("""
                const content = document.getElementById('content');
                if (content) {
                    content.innerHTML = `
                        <div class="page-header">
                            <div class="page-title">
                                <span class="page-breadcrumb">Matematica > 9o Ano A > Prova Bimestral</span>
                                <h1>Resultado: Joao Silva</h1>
                            </div>
                        </div>

                        <div class="results-summary" style="display: flex; gap: 20px; margin-bottom: 20px;">
                            <div class="summary-card" style="background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; text-align: center;">
                                <h3 style="color: #94a3b8; margin-bottom: 10px; font-size: 14px;">Nota Final</h3>
                                <div style="font-size: 48px; color: #22c55e; font-weight: bold;">8.5</div>
                                <div style="color: #64748b; font-size: 14px;">de 10.0 pontos</div>
                            </div>
                            <div class="summary-card" style="background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; text-align: center;">
                                <h3 style="color: #94a3b8; margin-bottom: 10px; font-size: 14px;">Questoes Corretas</h3>
                                <div style="font-size: 48px; color: #3b82f6; font-weight: bold;">8/10</div>
                                <div style="color: #64748b; font-size: 14px;">acertos</div>
                            </div>
                            <div class="summary-card" style="background: #1e293b; padding: 20px; border-radius: 8px; flex: 1; text-align: center;">
                                <h3 style="color: #94a3b8; margin-bottom: 10px; font-size: 14px;">Nivel de Desempenho</h3>
                                <div style="font-size: 48px; color: #a855f7; font-weight: bold;">B</div>
                                <div style="color: #64748b; font-size: 14px;">Bom</div>
                            </div>
                        </div>

                        <div class="results-tabs" style="background: #1e293b; border-radius: 8px; overflow: hidden;">
                            <div class="tabs-header" style="display: flex; gap: 0; border-bottom: 1px solid #334155;">
                                <button class="tab-btn active" style="background: #3b82f6; color: white; padding: 12px 20px; border: none; cursor: pointer;">📄 Documentos</button>
                                <button class="tab-btn" style="background: transparent; color: #94a3b8; padding: 12px 20px; border: none; cursor: pointer;">🤖 Etapas da IA</button>
                                <button class="tab-btn" style="background: transparent; color: #94a3b8; padding: 12px 20px; border: none; cursor: pointer;">📊 Resultado Final</button>
                            </div>
                            <div class="tabs-content" style="padding: 20px;">
                                <h4 style="color: white; margin-bottom: 15px;">Documentos do Aluno</h4>
                                <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                                    <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 120px;">
                                        <div style="font-size: 32px; margin-bottom: 8px;">📝</div>
                                        <div style="color: white; font-size: 12px;">Prova Respondida</div>
                                    </div>
                                    <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 120px;">
                                        <div style="font-size: 32px; margin-bottom: 8px;">🔍</div>
                                        <div style="color: white; font-size: 12px;">Texto Extraido</div>
                                    </div>
                                    <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 120px;">
                                        <div style="font-size: 32px; margin-bottom: 8px;">✅</div>
                                        <div style="color: white; font-size: 12px;">Correcao IA</div>
                                    </div>
                                    <div style="background: #0f172a; padding: 20px; border-radius: 8px; text-align: center; width: 120px;">
                                        <div style="font-size: 32px; margin-bottom: 8px;">📊</div>
                                        <div style="color: white; font-size: 12px;">Relatorio Final</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="skills-section" style="background: #1e293b; border-radius: 8px; padding: 20px; margin-top: 20px;">
                            <h4 style="color: white; margin-bottom: 15px;">Analise de Habilidades</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                                <span style="background: #22c55e20; color: #22c55e; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Algebra: Excelente</span>
                                <span style="background: #3b82f620; color: #3b82f6; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Geometria: Bom</span>
                                <span style="background: #eab30820; color: #eab308; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Trigonometria: Regular</span>
                                <span style="background: #22c55e20; color: #22c55e; padding: 6px 14px; border-radius: 20px; font-size: 13px;">Aritmetica: Excelente</span>
                            </div>
                        </div>
                    `;
                }
            """)
            page.wait_for_timeout(500)

            page.evaluate(add_annotation_script())
            page.evaluate("""
                // Nota final
                const summaryCards = document.querySelectorAll('.summary-card');
                if (summaryCards.length > 0) {
                    const rect = summaryCards[0].getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '1', '#22c55e');
                    addLabel(rect.left - 180, rect.top + 20, 'Nota calculada pela IA', '#22c55e');
                }

                // Abas
                const tabsHeader = document.querySelector('.tabs-header');
                if (tabsHeader) {
                    const rect = tabsHeader.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '2', '#3b82f6');
                    addLabel(rect.left - 200, rect.top, 'Navegue entre as secoes', '#3b82f6');
                }

                // Documentos
                const tabsContent = document.querySelector('.tabs-content');
                if (tabsContent) {
                    const rect = tabsContent.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + 60, '3', '#a855f7');
                    addLabel(rect.left - 160, rect.top + 50, 'Documentos gerados', '#a855f7');
                }

                // Habilidades
                const skillsSection = document.querySelector('.skills-section');
                if (skillsSection) {
                    const rect = skillsSection.getBoundingClientRect();
                    addCircle(rect.left - 20, rect.top + rect.height/2, '4', '#ef4444');
                    addLabel(rect.left - 180, rect.top + 20, 'Analise de habilidades', '#ef4444');
                }
            """)

            page.screenshot(path=str(OUTPUT_DIR / "14-resultados.png"))
            page.evaluate("clearAnnotations()")
            print("    [OK] 14-resultados.png")

            # ========================================
            # RESUMO
            # ========================================
            print("\n" + "="*60)
            print("[OK] Screenshots capturados!")
            print(f"[*] Pasta: {OUTPUT_DIR}")

            files = list(OUTPUT_DIR.glob("*.png"))
            print(f"\n[*] {len(files)} imagens:")
            for f in sorted(files):
                print(f"    - {f.name}")

        except Exception as e:
            print(f"[ERRO] {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    capture_tutorial_images()
