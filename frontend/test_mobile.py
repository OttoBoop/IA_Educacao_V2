"""Test mobile responsive UI"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "mobile-test-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Test 1: Phone viewport (375x667 - iPhone SE)
        print("=== Testing Phone (375x667) ===")
        page = await browser.new_page(viewport={"width": 375, "height": 667})
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        # Close welcome modal
        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Screenshot 1: Phone dashboard (sidebar should be hidden)
        await page.screenshot(path=f"{OUTPUT_DIR}/01_phone_dashboard.png")
        print("1. Phone dashboard (sidebar hidden)")

        # Screenshot 2: Open hamburger menu
        await page.click("#hamburger-btn")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/02_phone_sidebar_open.png")
        print("2. Phone sidebar open")

        # Screenshot 3: Close sidebar and navigate to Chat
        await page.evaluate("closeMobileSidebar()")
        await page.wait_for_timeout(300)
        await page.click("#hamburger-btn")
        await page.wait_for_timeout(300)
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUTPUT_DIR}/03_phone_chat.png")
        print("3. Phone chat view")

        await page.close()

        # Test 2: Tablet viewport (768x1024 - iPad)
        print("\n=== Testing Tablet (768x1024) ===")
        page = await browser.new_page(viewport={"width": 768, "height": 1024})
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Screenshot 4: Tablet dashboard
        await page.screenshot(path=f"{OUTPUT_DIR}/04_tablet_dashboard.png")
        print("4. Tablet dashboard")

        # Screenshot 5: Open sidebar
        await page.click("#hamburger-btn")
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/05_tablet_sidebar.png")
        print("5. Tablet sidebar open")

        # Screenshot 6: Tablet chat
        await page.click(".tree-item:has-text('Chat com IA')")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUTPUT_DIR}/06_tablet_chat.png")
        print("6. Tablet chat view")

        await page.close()

        # Test 3: Desktop viewport (1400x900) - should be unchanged
        print("\n=== Testing Desktop (1400x900) ===")
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)

        await page.evaluate("""
            const modal = document.getElementById('modal-welcome');
            if (modal) modal.classList.remove('active');
        """)
        await page.wait_for_timeout(500)

        # Screenshot 7: Desktop (hamburger should be hidden, sidebar visible)
        await page.screenshot(path=f"{OUTPUT_DIR}/07_desktop_dashboard.png")
        print("7. Desktop dashboard (sidebar visible, no hamburger)")

        await browser.close()
        print(f"\nScreenshots saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
