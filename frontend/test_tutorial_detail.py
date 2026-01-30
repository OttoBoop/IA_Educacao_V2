"""Análise detalhada do Tutorial Principal"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "tutorial-analysis"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # iPhone 14 Pro
        page = await browser.new_page(viewport={"width": 393, "height": 852})

        for prefix, url in [("local", "http://localhost:8000"), ("online", "https://ia-educacao-v2.onrender.com")]:
            print(f"\n=== {prefix.upper()}: Análise do Tutorial ===\n")

            try:
                await page.goto(url, timeout=60000)
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"  ERRO: {e}")
                continue

            # 1. Welcome Modal - Parte superior
            print("  1. Welcome - Topo")
            await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_01_welcome_topo.png")

            # 2. Scroll para ver mais do welcome
            await page.evaluate("""
                const modal = document.querySelector('.modal-welcome .modal-body') ||
                              document.querySelector('.modal-welcome .modal') ||
                              document.querySelector('#modal-welcome .modal-body');
                if (modal) modal.scrollTop = 300;
            """)
            await page.wait_for_timeout(300)
            print("  2. Welcome - Meio (scroll)")
            await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_02_welcome_meio.png")

            # 3. Scroll mais para ver footer
            await page.evaluate("""
                const modal = document.querySelector('.modal-welcome .modal-body') ||
                              document.querySelector('.modal-welcome .modal') ||
                              document.querySelector('#modal-welcome .modal-body');
                if (modal) modal.scrollTop = 600;
            """)
            await page.wait_for_timeout(300)
            print("  3. Welcome - Rodapé (scroll)")
            await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_03_welcome_rodape.png")

            # 4. Scroll até o final
            await page.evaluate("""
                const modal = document.querySelector('.modal-welcome .modal-body') ||
                              document.querySelector('.modal-welcome .modal') ||
                              document.querySelector('#modal-welcome .modal-body');
                if (modal) modal.scrollTop = modal.scrollHeight;
            """)
            await page.wait_for_timeout(300)
            print("  4. Welcome - Final")
            await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_04_welcome_final.png")

            # 5. Clicar em Tutorial Completo (se existir)
            try:
                await page.evaluate("""
                    const tutorialBtn = document.querySelector('button:has-text("Tutorial")') ||
                                       document.querySelector('[onclick*="tutorial"]');
                    if (tutorialBtn) tutorialBtn.click();
                """)
                await page.wait_for_timeout(500)
                print("  5. Tutorial - Passo 1")
                await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_05_tutorial_passo1.png")

                # Navegar pelos passos do tutorial
                for i in range(2, 6):
                    await page.evaluate("""
                        const nextBtn = document.querySelector('.tutorial-nav .btn-primary') ||
                                       document.querySelector('button:has-text("Próximo")') ||
                                       document.querySelector('button:has-text("Continuar")');
                        if (nextBtn) nextBtn.click();
                    """)
                    await page.wait_for_timeout(500)
                    print(f"  {4+i}. Tutorial - Passo {i}")
                    await page.screenshot(path=f"{OUTPUT_DIR}/{prefix}_{4+i:02d}_tutorial_passo{i}.png")
            except Exception as e:
                print(f"  Tutorial navegação erro: {e}")

            print(f"  Concluído: {prefix}")

        await browser.close()
        print(f"\n Screenshots salvos em: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
