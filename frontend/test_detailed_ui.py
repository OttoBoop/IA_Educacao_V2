"""Detailed UI test for modals and edge cases"""
import asyncio
from playwright.async_api import async_playwright
import os

PROD_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_DIR = "detailed-ui-test"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    issues = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})

        await page.goto(PROD_URL, timeout=30000)
        await page.wait_for_timeout(2000)

        # Close welcome modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        print("=== Testing Production UI Details ===\n")

        # 1. Test modal - Nova Materia
        print("1. Testing Nova Materia modal...")
        try:
            await page.click("text=+ Nova Matéria")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/01_modal_nova_materia.png")

            # Check if form inputs are properly sized
            nome_input = await page.query_selector("#input-materia-nome")
            if nome_input:
                box = await nome_input.bounding_box()
                if box and box["width"] < 200:
                    issues.append("Nova Materia: Nome input too narrow")
                print(f"   Nome input width: {box['width'] if box else 'N/A'}px")

            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(300)
        except Exception as e:
            issues.append(f"Nova Materia modal: {e}")

        # 2. Test search modal
        print("2. Testing Search modal...")
        try:
            await page.click("text=Buscar")
            await page.wait_for_timeout(800)
            await page.screenshot(path=f"{OUTPUT_DIR}/02_modal_busca.png")
            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(300)
        except Exception as e:
            issues.append(f"Search modal: {e}")

        # 3. Test settings modal
        print("3. Testing Configuracoes modal...")
        try:
            await page.click("text=Configurações IA")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/03_modal_config.png")

            # Test each tab
            tabs = await page.query_selector_all(".config-tab")
            for i, tab in enumerate(tabs[:4]):  # First 4 tabs
                await tab.click()
                await page.wait_for_timeout(500)
                await page.screenshot(path=f"{OUTPUT_DIR}/03_config_tab_{i+1}.png")
                print(f"   Tab {i+1} captured")

            await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
            await page.wait_for_timeout(300)
        except Exception as e:
            issues.append(f"Config modal: {e}")

        # 4. Navigate to a materia page
        print("4. Testing Materia page...")
        try:
            await page.click(".tree-item:has-text('Inglês')")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=f"{OUTPUT_DIR}/04_materia_page.png")
        except Exception as e:
            issues.append(f"Materia page: {e}")

        # 5. Navigate to turma
        print("5. Testing Turma page...")
        try:
            turma_card = await page.query_selector(".card-grid-item")
            if turma_card:
                await turma_card.click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path=f"{OUTPUT_DIR}/05_turma_page.png")
        except Exception as e:
            issues.append(f"Turma page: {e}")

        # 6. Navigate to atividade
        print("6. Testing Atividade page...")
        try:
            atividade_card = await page.query_selector(".card-grid-item")
            if atividade_card:
                await atividade_card.click()
                await page.wait_for_timeout(1000)
                await page.screenshot(path=f"{OUTPUT_DIR}/06_atividade_page.png")

                # Test upload modal
                upload_btn = await page.query_selector("text=+ Upload")
                if upload_btn:
                    await upload_btn.click()
                    await page.wait_for_timeout(800)
                    await page.screenshot(path=f"{OUTPUT_DIR}/06b_upload_modal.png")
                    await page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")
                    await page.wait_for_timeout(300)
        except Exception as e:
            issues.append(f"Atividade page: {e}")

        # 7. Test phone viewport specific issues
        print("7. Testing phone viewport edge cases...")
        await page.set_viewport_size({"width": 375, "height": 667})
        await page.goto(PROD_URL)
        await page.wait_for_timeout(2000)
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Check header doesn't overflow
        header = await page.query_selector("header")
        if header:
            box = await header.bounding_box()
            if box and box["width"] > 375:
                issues.append(f"Header overflows on phone: {box['width']}px > 375px")
            print(f"   Header width: {box['width'] if box else 'N/A'}px")

        await page.screenshot(path=f"{OUTPUT_DIR}/07_phone_header.png")

        # Open sidebar and check width
        await page.click("#hamburger-btn")
        await page.wait_for_timeout(500)
        sidebar = await page.query_selector(".sidebar")
        if sidebar:
            box = await sidebar.bounding_box()
            print(f"   Sidebar width on phone: {box['width'] if box else 'N/A'}px")
            if box and box["width"] > 375:
                issues.append(f"Sidebar too wide on phone: {box['width']}px")

        await page.screenshot(path=f"{OUTPUT_DIR}/07b_phone_sidebar.png")

        # 8. Test very long text handling
        print("8. Checking text truncation...")
        await page.set_viewport_size({"width": 1400, "height": 900})
        await page.goto(PROD_URL)
        await page.wait_for_timeout(2000)
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)

        # Check sidebar items for truncation
        sidebar_items = await page.query_selector_all(".tree-item .tree-name")
        truncated_items = []
        for item in sidebar_items:
            text = await item.inner_text()
            box = await item.bounding_box()
            if text and "..." in text:
                truncated_items.append(text)

        if truncated_items:
            print(f"   Truncated sidebar items: {truncated_items}")
            # This is expected behavior, not an issue

        await browser.close()

        # Summary
        print("\n" + "="*50)
        print("DETAILED UI TEST RESULTS")
        print("="*50)

        if issues:
            print(f"\n[!] Found {len(issues)} issue(s):")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n[OK] No functional UI issues found!")

        print(f"\nScreenshots saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
