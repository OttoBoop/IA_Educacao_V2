"""Screenshot da página de resultado do aluno - Fase 3"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "fase3-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 1000})

        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Fechar modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Navegar para Inglês > 9º Ano A > Test 1 - Verb Tenses
        await page.click(".tree-item:has-text('Inglês')")
        await page.wait_for_timeout(1000)

        # Expandir
        await page.evaluate("""
            document.querySelectorAll('.tree-item').forEach(item => {
                if (item.textContent.includes('Inglês')) {
                    const toggle = item.querySelector('.tree-toggle');
                    if (toggle) toggle.click();
                }
            });
        """)
        await page.wait_for_timeout(800)

        await page.click(".tree-item:has-text('9º Ano A')")
        await page.wait_for_timeout(800)

        # Expandir turma
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

        # Agora clicar em um aluno para ver o resultado
        # Procurar por um link/botão de aluno na página
        await page.screenshot(path=f"{OUTPUT_DIR}/08_atividade_full.png", full_page=True)
        print("8. Atividade (full page) capturada")

        # Scroll down para ver os alunos
        await page.evaluate("window.scrollTo(0, 500)")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/09_atividade_alunos.png")
        print("9. Seção de alunos capturada")

        # Tentar clicar em um aluno para ver resultado
        try:
            # Procurar por botão ou link de resultado
            aluno_btn = page.locator("button:has-text('Ver Resultado')").first
            if await aluno_btn.is_visible(timeout=2000):
                await aluno_btn.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path=f"{OUTPUT_DIR}/10_resultado_aluno.png", full_page=True)
                print("10. Resultado do aluno capturado!")
        except Exception as e:
            print(f"Nota: {e}")
            # Tentar clicar em um nome de aluno
            try:
                aluno_link = page.locator(".aluno-item, [onclick*='showResultado'], [onclick*='showAluno']").first
                if await aluno_link.is_visible(timeout=2000):
                    await aluno_link.click()
                    await page.wait_for_timeout(2000)
                    await page.screenshot(path=f"{OUTPUT_DIR}/10_resultado_aluno.png", full_page=True)
                    print("10. Resultado do aluno capturado (via aluno-item)!")
            except Exception as e2:
                print(f"Não foi possível navegar para resultado: {e2}")

        await browser.close()
        print(f"\nScreenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
