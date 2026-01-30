"""Compare local vs production mobile UI"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "compare-screenshots"

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Phone viewport
        phone_viewport = {"width": 375, "height": 667}

        # Test LOCAL (port 8001)
        print("=== LOCAL (http://localhost:8001/frontend/index_v2.html) ===")
        page = await browser.new_page(viewport=phone_viewport)
        try:
            await page.goto("http://localhost:8001/frontend/index_v2.html", timeout=10000)
            await page.wait_for_timeout(2000)

            # Close welcome modal
            await page.evaluate("""
                const modal = document.getElementById('modal-welcome');
                if (modal) modal.classList.remove('active');
            """)
            await page.wait_for_timeout(500)

            await page.screenshot(path=f"{OUTPUT_DIR}/local_phone_dashboard.png")
            print("1. Local phone dashboard captured")

            # Check for hamburger button
            hamburger = await page.query_selector("#hamburger-btn")
            if hamburger:
                is_visible = await hamburger.is_visible()
                print(f"   Hamburger button: {'VISIBLE' if is_visible else 'hidden'}")
                if is_visible:
                    await page.click("#hamburger-btn")
                    await page.wait_for_timeout(500)
                    await page.screenshot(path=f"{OUTPUT_DIR}/local_phone_sidebar.png")
                    print("2. Local sidebar open captured")
            else:
                print("   Hamburger button: NOT FOUND")

        except Exception as e:
            print(f"   Error: {e}")
        await page.close()

        # Test PRODUCTION
        print("\n=== PRODUCTION (https://ia-educacao-2.onrender.com) ===")
        page = await browser.new_page(viewport=phone_viewport)
        try:
            await page.goto("https://ia-educacao-2.onrender.com", timeout=30000)
            await page.wait_for_timeout(3000)

            # Close welcome modal
            await page.evaluate("""
                const modal = document.getElementById('modal-welcome');
                if (modal) modal.classList.remove('active');
            """)
            await page.wait_for_timeout(500)

            await page.screenshot(path=f"{OUTPUT_DIR}/prod_phone_dashboard.png")
            print("1. Production phone dashboard captured")

            # Check for hamburger button
            hamburger = await page.query_selector("#hamburger-btn")
            if hamburger:
                is_visible = await hamburger.is_visible()
                print(f"   Hamburger button: {'VISIBLE' if is_visible else 'hidden'}")
                if is_visible:
                    await page.click("#hamburger-btn")
                    await page.wait_for_timeout(500)
                    await page.screenshot(path=f"{OUTPUT_DIR}/prod_phone_sidebar.png")
                    print("2. Production sidebar open captured")
            else:
                print("   Hamburger button: NOT FOUND (deploy pending)")

        except Exception as e:
            print(f"   Error: {e}")
        await page.close()

        await browser.close()
        print(f"\nScreenshots saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
