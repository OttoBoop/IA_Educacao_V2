"""Auditoria completa da interface do Prova AI"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "ui-audit"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    issues = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # ========== 1. WELCOME MODAL ==========
        print("\n=== 1. Welcome Modal ===")
        await page.screenshot(path=f"{OUTPUT_DIR}/01_welcome_modal.png")
        print("Capturado: Welcome modal")

        # Fechar modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # ========== 2. DASHBOARD ==========
        print("\n=== 2. Dashboard ===")
        await page.screenshot(path=f"{OUTPUT_DIR}/02_dashboard.png")
        print("Capturado: Dashboard")

        # Testar botão de ajuda
        try:
            await page.click(".section-help")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/02b_dashboard_help.png")
            print("Capturado: Dashboard help panel")
        except:
            issues.append("Dashboard: botão de ajuda não encontrado")

        # ========== 3. SIDEBAR - NAVEGAÇÃO ==========
        print("\n=== 3. Sidebar ===")
        # Hover sobre items
        await page.hover(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(300)
        await page.screenshot(path=f"{OUTPUT_DIR}/03_sidebar_hover.png")
        print("Capturado: Sidebar hover")

        # ========== 4. MODAL NOVA MATÉRIA ==========
        print("\n=== 4. Modal Nova Matéria ===")
        await page.click("text=+ Nova Matéria")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{OUTPUT_DIR}/04_modal_materia.png")
        print("Capturado: Modal nova matéria")
        # Fechar modal via JavaScript (mais confiável que Escape)
        await page.evaluate("""
            const modal = document.getElementById('modal-materia');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # ========== 5. PÁGINA DE MATÉRIA ==========
        print("\n=== 5. Página de Matéria ===")
        await page.click(".tree-item:has-text('Inglês')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/05_materia.png")
        print("Capturado: Página matéria")

        # ========== 6. PÁGINA DE TURMA ==========
        print("\n=== 6. Página de Turma ===")
        # Expandir matéria
        await page.evaluate("""
            document.querySelectorAll('.tree-item').forEach(item => {
                if (item.textContent.includes('Inglês')) {
                    const toggle = item.querySelector('.tree-toggle');
                    if (toggle) toggle.click();
                }
            });
        """)
        await page.wait_for_timeout(500)
        await page.click(".tree-item:has-text('9º Ano A')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=f"{OUTPUT_DIR}/06_turma.png")
        print("Capturado: Página turma")

        # Testar abas
        await page.click("text=Alunos")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/06b_turma_alunos.png")
        print("Capturado: Turma - aba alunos")

        # ========== 7. PÁGINA DE ATIVIDADE ==========
        print("\n=== 7. Página de Atividade ===")
        await page.evaluate("""
            document.querySelectorAll('.tree-item').forEach(item => {
                if (item.textContent.includes('9º Ano A')) {
                    const toggle = item.querySelector('.tree-toggle');
                    if (toggle) toggle.click();
                }
            });
        """)
        await page.wait_for_timeout(500)
        await page.click(".tree-item:has-text('Test 1')")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{OUTPUT_DIR}/07_atividade.png", full_page=True)
        print("Capturado: Página atividade")

        # ========== 8. MODAIS DA ATIVIDADE ==========
        print("\n=== 8. Modais da Atividade ===")

        # Modal Upload
        try:
            await page.click("text=+ Upload")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/08a_modal_upload.png")
            print("Capturado: Modal upload")
            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(500)
        except Exception as e:
            issues.append(f"Modal upload: {e}")

        # Modal Pipeline Aluno
        try:
            await page.click("text=Pipeline Aluno")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/08b_modal_pipeline.png")
            print("Capturado: Modal pipeline aluno")
            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(500)
        except Exception as e:
            issues.append(f"Modal pipeline: {e}")

        # Modal Executar Etapa
        try:
            await page.click("text=Executar Etapa")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/08c_modal_etapa.png")
            print("Capturado: Modal executar etapa")
            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(500)
        except Exception as e:
            issues.append(f"Modal etapa: {e}")

        # ========== 9. RESULTADO DO ALUNO ==========
        print("\n=== 9. Resultado do Aluno ===")
        # Scroll para ver alunos
        await page.evaluate("window.scrollTo(0, 800)")
        await page.wait_for_timeout(500)

        try:
            aluno = page.locator("[onclick*='showResultadoAluno']").first
            if await aluno.is_visible(timeout=2000):
                await aluno.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path=f"{OUTPUT_DIR}/09_resultado_aluno.png", full_page=True)
                print("Capturado: Resultado do aluno")
        except Exception as e:
            issues.append(f"Resultado aluno: {e}")

        # ========== 10. CHAT ==========
        print("\n=== 10. Chat ===")
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUTPUT_DIR}/10_chat.png")
        print("Capturado: Chat")

        # Testar filtros
        try:
            await page.click("button[data-mode='filtered']")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/10b_chat_filtros.png")
            print("Capturado: Chat com filtros")
        except Exception as e:
            issues.append(f"Chat filtros: {e}")

        # ========== 11. PROMPTS ==========
        print("\n=== 11. Prompts ===")
        await page.click(".tree-item:has-text('Prompts')")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{OUTPUT_DIR}/11_prompts.png")
        print("Capturado: Prompts")

        # ========== 12. MODELOS ==========
        print("\n=== 12. Modelos de LLM ===")
        await page.click(".tree-item:has-text('Modelos')")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{OUTPUT_DIR}/12_modelos.png")
        print("Capturado: Modelos")

        # ========== 13. CONFIGURAÇÕES ==========
        print("\n=== 13. Configurações ===")
        try:
            await page.click("text=Configurações IA")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/13_config.png")
            print("Capturado: Configurações")
            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(500)
        except Exception as e:
            issues.append(f"Configurações: {e}")

        # ========== 14. BUSCA ==========
        print("\n=== 14. Busca ===")
        try:
            await page.click("text=Buscar")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/14_busca.png")
            print("Capturado: Modal busca")
            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(500)
        except Exception as e:
            issues.append(f"Busca: {e}")

        # ========== 15. TUTORIAL ==========
        print("\n=== 15. Tutorial ===")
        try:
            await page.click("text=Ajuda")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/15a_tutorial_1.png")
            print("Capturado: Tutorial página 1")

            # Próxima página
            await page.click("text=Próximo")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/15b_tutorial_2.png")
            print("Capturado: Tutorial página 2")

            await page.click("text=Próximo")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/15c_tutorial_3.png")
            print("Capturado: Tutorial página 3")

            await page.click("text=Próximo")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/15d_tutorial_4.png")
            print("Capturado: Tutorial página 4")

            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(500)
        except Exception as e:
            issues.append(f"Tutorial: {e}")

        await browser.close()

        # ========== RESUMO ==========
        print("\n" + "="*50)
        print("AUDITORIA COMPLETA")
        print("="*50)
        print(f"Screenshots salvos em: {OUTPUT_DIR}/")
        if issues:
            print(f"\nProblemas encontrados ({len(issues)}):")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\nNenhum problema técnico encontrado durante a captura.")

if __name__ == "__main__":
    asyncio.run(main())
