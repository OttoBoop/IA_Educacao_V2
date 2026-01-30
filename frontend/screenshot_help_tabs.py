"""Screenshot das abas de ajuda contextual"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "help-tabs-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Fechar modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # 1. Ir para uma matéria e ver ajuda
        await page.click(".tree-item:has-text('Inglês')")
        await page.wait_for_timeout(1000)

        # Clicar no botão de ajuda
        try:
            await page.click(".section-help")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/01_materia_help.png")
            print("1. Ajuda da Matéria capturada")
        except Exception as e:
            print(f"Erro: {e}")

        # 2. Ir para uma turma
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

        # Clicar no botão de ajuda
        try:
            await page.click(".section-help")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/02_turma_help_alunos.png")
            print("2. Ajuda da Turma - Aba Alunos capturada")

            # Clicar na aba de atividade
            await page.click(".help-tab:has-text('Criar Atividade')")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/03_turma_help_atividade.png")
            print("3. Ajuda da Turma - Aba Atividade capturada")
        except Exception as e:
            print(f"Erro: {e}")

        # 3. Ir para uma atividade
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
        await page.wait_for_timeout(1000)

        # Clicar no botão de ajuda
        try:
            await page.click(".section-help")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/04_atividade_help_docs.png")
            print("4. Ajuda da Atividade - Aba Docs capturada")

            # Clicar na aba de pipeline
            await page.click(".help-tab:has-text('Pipeline')")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/05_atividade_help_pipeline.png")
            print("5. Ajuda da Atividade - Aba Pipeline capturada")

            # Clicar na aba de resultados
            await page.click(".help-tab:has-text('Resultados')")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/06_atividade_help_resultados.png")
            print("6. Ajuda da Atividade - Aba Resultados capturada")
        except Exception as e:
            print(f"Erro: {e}")

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
