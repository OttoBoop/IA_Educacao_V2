"""Test local mobile UI with backend"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "local-mobile-test"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Phone viewport (375x667)
        print("=== Testing LOCAL with backend (http://localhost:8000) ===")
        page = await browser.new_page(viewport={"width": 375, "height": 667})

        await page.goto("http://localhost:8000", timeout=15000)
        await page.wait_for_timeout(2000)

        # Close welcome modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # 1. Phone dashboard
        await page.screenshot(path=f"{OUTPUT_DIR}/01_phone_dashboard.png")
        print("1. Phone dashboard - hamburger should be visible")

        # 2. Open sidebar
        hamburger = await page.query_selector("#hamburger-btn")
        if hamburger and await hamburger.is_visible():
            print("   [OK] Hamburger button found and visible")
            await page.click("#hamburger-btn")
            await page.wait_for_timeout(500)
            await page.screenshot(path=f"{OUTPUT_DIR}/02_phone_sidebar.png")
            print("2. Sidebar open")
        else:
            print("   [FAIL] Hamburger button NOT visible - responsive CSS not working")

        # 3. Navigate to Chat
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUTPUT_DIR}/03_phone_chat.png")
        print("3. Phone chat - should be vertical layout")

        # 4. Test tablet size (768x1024)
        await page.set_viewport_size({"width": 768, "height": 1024})
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/04_tablet_dashboard.png")
        print("4. Tablet dashboard")

        # 5. Desktop (should have sidebar visible, no hamburger)
        await page.set_viewport_size({"width": 1200, "height": 800})
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/05_desktop_dashboard.png")
        print("5. Desktop - sidebar should always be visible")

        await browser.close()
        print(f"\n[OK] All screenshots saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
