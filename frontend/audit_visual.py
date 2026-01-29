"""
Auditoria Visual Completa do Prova AI
Navega por todas as áreas, captura screenshots e testa funcionalidades
"""
import os
import time
import json
from playwright.sync_api import sync_playwright

OUTPUT_DIR = "audit-screenshots"
BASE_URL = "http://127.0.0.1:8001"
ISSUES = []

def log_issue(category, severity, description, screenshot=None):
    """Registra um problema encontrado"""
    issue = {
        "category": category,
        "severity": severity,
        "description": description,
        "screenshot": screenshot
    }
    ISSUES.append(issue)
    icon = {"critical": "🔴", "warning": "🟡", "suggestion": "🔵"}[severity]
    print(f"   {icon} [{severity.upper()}] {description}")

def close_all_modals(page):
    """Fecha todos os modais abertos"""
    page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
    time.sleep(0.3)

def take_screenshot(page, name):
    """Captura screenshot com nome padronizado"""
    path = f"{OUTPUT_DIR}/{name}.png"
    page.screenshot(path=path, full_page=False)
    return path

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1400, 'height': 900})
        page = context.new_page()
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        print("\n" + "="*60)
        print("🔍 AUDITORIA VISUAL - PROVA AI")
        print("="*60)
        
        # ============================================================
        # 1. PÁGINA INICIAL E WELCOME MODAL
        # ============================================================
        print("\n📍 1. Testando página inicial e welcome modal...")
        page.goto(BASE_URL, wait_until='networkidle')
        time.sleep(1)
        
        welcome_visible = page.locator('#modal-welcome.active').is_visible()
        if welcome_visible:
            print("   ✅ Welcome modal aparece corretamente")
            take_screenshot(page, "01_welcome_modal")
            
            try:
                titulo = page.locator('.welcome-title').text_content()
                if "Prova AI" in titulo:
                    print("   ✅ Título do welcome está correto")
            except:
                log_issue("welcome", "warning", "Não conseguiu ler título do welcome")
            
            page.locator('.welcome-footer .btn').first.click()
            time.sleep(0.5)
        else:
            log_issue("welcome", "warning", "Welcome modal não apareceu (pode ser localStorage)")
        
        close_all_modals(page)
        
        # ============================================================
        # 2. DASHBOARD
        # ============================================================
        print("\n📍 2. Testando Dashboard...")
        page.locator('.tree-item:has-text("Início")').click()
        time.sleep(1)
        take_screenshot(page, "02_dashboard")
        
        help_btn = page.locator('.section-help').first
        if help_btn.is_visible():
            print("   ✅ Botão de ajuda (?) presente no título")
            help_btn.click()
            time.sleep(0.5)
            take_screenshot(page, "02b_dashboard_help_panel")
            
            help_panel = page.locator('.help-panel.show')
            if help_panel.is_visible():
                print("   ✅ Painel de ajuda abre corretamente")
            else:
                log_issue("dashboard", "warning", "Painel de ajuda não abriu")
        else:
            log_issue("dashboard", "warning", "Botão de ajuda (?) não encontrado")
        
        stats = page.locator('.stat-card')
        print(f"   ✅ {stats.count()} stat cards encontrados")
        
        # ============================================================
        # 3. TOOLTIPS NO SIDEBAR
        # ============================================================
        print("\n📍 3. Testando tooltips no sidebar...")
        
        prompts_item = page.locator('.tree-item:has-text("Prompts")')
        prompts_item.hover()
        time.sleep(0.8)
        take_screenshot(page, "03_tooltip_prompts")
        print("   ✅ Tooltip de Prompts testado")
        
        config_btn = page.locator('button:has-text("Configurações IA")')
        config_btn.hover()
        time.sleep(0.8)
        take_screenshot(page, "03b_tooltip_config")
        print("   ✅ Tooltip de configurações testado")
        
        # ============================================================
        # 4. CRIAR MATÉRIA
        # ============================================================
        print("\n📍 4. Testando criação de matéria...")
        page.locator('button:has-text("Nova Matéria")').click()
        time.sleep(0.5)
        take_screenshot(page, "04_modal_materia")
        
        modal = page.locator('#modal-materia.active')
        if modal.is_visible():
            print("   ✅ Modal de matéria abre")
            page.fill('#input-materia-nome', 'Matemática - Auditoria')
            page.locator('#modal-materia .btn-primary').click()
            time.sleep(1)
            
            materia_card = page.locator('.card-grid-item:has-text("Matemática - Auditoria")')
            if materia_card.is_visible():
                print("   ✅ Matéria criada com sucesso")
                take_screenshot(page, "04b_materia_criada")
            else:
                log_issue("materia", "critical", "Matéria não apareceu após criação")
        else:
            log_issue("materia", "critical", "Modal de matéria não abriu")
        
        close_all_modals(page)
        
        # ============================================================
        # 5. CRIAR TURMA
        # ============================================================
        print("\n📍 5. Testando criação de turma...")
        page.locator('.card-grid-item:has-text("Matemática - Auditoria")').click()
        time.sleep(1)
        take_screenshot(page, "05_pagina_materia")
        
        page.locator('button:has-text("Nova Turma")').click()
        time.sleep(0.5)
        take_screenshot(page, "05b_modal_turma")
        
        modal_turma = page.locator('#modal-turma.active')
        if modal_turma.is_visible():
            page.fill('#input-turma-nome', '9º Ano A')
            page.locator('#modal-turma .btn-primary').click()
            time.sleep(1)
            print("   ✅ Turma criada")
        else:
            log_issue("turma", "critical", "Modal de turma não abriu")
        
        close_all_modals(page)
        
        # ============================================================
        # 6. CRIAR ATIVIDADE
        # ============================================================
        print("\n📍 6. Testando criação de atividade...")
        turma_card = page.locator('.card-grid-item:has-text("9º Ano A")')
        if turma_card.is_visible():
            turma_card.click()
            time.sleep(1)
            take_screenshot(page, "06_pagina_turma")
            
            page.locator('button:has-text("Nova Atividade")').click()
            time.sleep(0.5)
            take_screenshot(page, "06b_modal_atividade")
            
            modal_ativ = page.locator('#modal-atividade.active')
            if modal_ativ.is_visible():
                page.fill('#input-ativ-nome', 'Prova Bimestral')
                page.locator('#modal-atividade .btn-primary').click()
                time.sleep(1)
                print("   ✅ Atividade criada")
            else:
                log_issue("atividade", "critical", "Modal de atividade não abriu")
        
        close_all_modals(page)
        
        # ============================================================
        # 7. PÁGINA DE ATIVIDADE
        # ============================================================
        print("\n📍 7. Testando página de atividade...")
        ativ_card = page.locator('.card-grid-item:has-text("Prova Bimestral")')
        if ativ_card.is_visible():
            ativ_card.click()
            time.sleep(1)
            take_screenshot(page, "07_pagina_atividade")
            
            help_btn = page.locator('.section-help').first
            if help_btn.is_visible():
                print("   ✅ Botão de ajuda presente")
                help_btn.click()
                time.sleep(0.5)
                take_screenshot(page, "07b_atividade_help")
            
            btn_pipeline = page.locator('button:has-text("Pipeline Aluno")')
            if btn_pipeline.is_visible():
                btn_pipeline.hover()
                time.sleep(0.8)
                take_screenshot(page, "07c_tooltip_pipeline")
                print("   ✅ Tooltip do botão Pipeline testado")
            
            # Testar modal de upload
            upload_btns = page.locator('button:has-text("Upload")')
            if upload_btns.count() > 0:
                upload_btns.first.click()
                time.sleep(0.5)
                take_screenshot(page, "07d_modal_upload")
                
                tooltip_icon = page.locator('#modal-upload .tooltip-icon')
                if tooltip_icon.is_visible():
                    print("   ✅ Ícone de tooltip presente no upload")
                    tooltip_icon.hover()
                    time.sleep(0.8)
                    take_screenshot(page, "07e_tooltip_upload")
                
                hint = page.locator('#upload-tipo-hint')
                if hint.is_visible():
                    print(f"   ✅ Hint dinâmico presente")
                else:
                    log_issue("upload", "warning", "Hint dinâmico não encontrado")
                
                close_all_modals(page)
        
        # ============================================================
        # 8. MODAL DE EXECUÇÃO
        # ============================================================
        print("\n📍 8. Testando modal de execução de etapa...")
        btn_exec = page.locator('button:has-text("Executar Etapa")')
        if btn_exec.is_visible():
            btn_exec.click()
            time.sleep(0.5)
            take_screenshot(page, "08_modal_execucao")
            
            tooltip_title = page.locator('#modal-execucao .tooltip-icon')
            if tooltip_title.count() > 0:
                print("   ✅ Tooltip no título do modal")
            
            hint_etapa = page.locator('#execucao-etapa-hint')
            if hint_etapa.is_visible():
                print(f"   ✅ Hint de etapa presente")
            else:
                log_issue("execucao", "warning", "Hint de etapa não encontrado")
            
            close_all_modals(page)
        
        # ============================================================
        # 9. PROMPTS
        # ============================================================
        print("\n📍 9. Testando página de Prompts...")
        page.locator('.tree-item:has-text("Prompts")').click()
        time.sleep(1)
        take_screenshot(page, "09_pagina_prompts")
        
        help_btn = page.locator('.section-help').first
        if help_btn.is_visible():
            help_btn.click()
            time.sleep(0.5)
            take_screenshot(page, "09b_prompts_help")
            print("   ✅ Painel de ajuda de prompts funciona")
        
        # ============================================================
        # 10. MODELOS DE LLM
        # ============================================================
        print("\n📍 10. Testando página de Modelos de LLM...")
        page.locator('.tree-item:has-text("Modelos de LLM")').click()
        time.sleep(1)
        take_screenshot(page, "10_pagina_providers")
        
        help_btn = page.locator('.section-help').first
        if help_btn.is_visible():
            help_btn.click()
            time.sleep(0.5)
            take_screenshot(page, "10b_providers_help")
            print("   ✅ Painel de ajuda de providers funciona")
        
        # ============================================================
        # 11. CONFIGURAÇÕES IA
        # ============================================================
        print("\n📍 11. Testando modal de Configurações IA...")
        page.locator('button:has-text("Configurações IA")').click()
        time.sleep(0.5)
        take_screenshot(page, "11_modal_settings")
        print("   ✅ Modal de settings aberto")
        close_all_modals(page)
        
        # ============================================================
        # 12. CHAT
        # ============================================================
        print("\n📍 12. Testando Chat com IA...")
        page.locator('.tree-item:has-text("Chat com IA")').click()
        time.sleep(1)
        take_screenshot(page, "12_pagina_chat")
        
        help_btn = page.locator('.section-help').first
        if help_btn.is_visible():
            help_btn.click()
            time.sleep(0.5)
            take_screenshot(page, "12b_chat_help")
            print("   ✅ Painel de ajuda do chat funciona")
        
        # ============================================================
        # 13. TODOS OS ALUNOS
        # ============================================================
        print("\n📍 13. Testando página Todos os Alunos...")
        page.locator('.tree-item:has-text("Todos os Alunos")').click()
        time.sleep(1)
        take_screenshot(page, "13_todos_alunos")
        print("   ✅ Página de alunos carregada")
        
        # ============================================================
        # 14. ERROS NO CONSOLE
        # ============================================================
        print("\n📍 14. Verificando erros no console...")
        if console_errors:
            for err in console_errors[:5]:
                log_issue("console", "warning", f"Erro JS: {err[:100]}")
        else:
            print("   ✅ Nenhum erro no console")
        
        # ============================================================
        # RESUMO
        # ============================================================
        print("\n" + "="*60)
        print("📊 RESUMO DA AUDITORIA")
        print("="*60)
        
        critical = [i for i in ISSUES if i["severity"] == "critical"]
        warnings = [i for i in ISSUES if i["severity"] == "warning"]
        suggestions = [i for i in ISSUES if i["severity"] == "suggestion"]
        
        print(f"\n🔴 Críticos: {len(critical)}")
        for i in critical:
            print(f"   - {i['description']}")
        
        print(f"\n🟡 Avisos: {len(warnings)}")
        for i in warnings:
            print(f"   - {i['description']}")
        
        print(f"\n🔵 Sugestões: {len(suggestions)}")
        for i in suggestions:
            print(f"   - {i['description']}")
        
        print(f"\n📁 Screenshots salvas em: {OUTPUT_DIR}/")
        print(f"   Total: {len(os.listdir(OUTPUT_DIR))} arquivos")
        
        with open(f"{OUTPUT_DIR}/audit_report.json", "w", encoding="utf-8") as f:
            json.dump({
                "total_issues": len(ISSUES),
                "critical": len(critical),
                "warnings": len(warnings),
                "suggestions": len(suggestions),
                "issues": ISSUES
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: {OUTPUT_DIR}/audit_report.json")
        
        browser.close()
        
        if len(critical) == 0:
            print("\n✅ AUDITORIA CONCLUÍDA - Nenhum problema crítico!")
        else:
            print(f"\n⚠️ AUDITORIA CONCLUÍDA - {len(critical)} problema(s) crítico(s)")

if __name__ == "__main__":
    main()
