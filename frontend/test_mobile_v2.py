"""Test mobile responsive UI - Version 2 with comprehensive screenshots"""
import asyncio
from playwright.async_api import async_playwright
import os

OUTPUT_DIR = "mobile-screenshots-v2"

VIEWPORTS = [
    {"name": "iphone-se", "width": 375, "height": 667},
    {"name": "iphone-14-pro", "width": 393, "height": 852},
    {"name": "tablet-600", "width": 600, "height": 960},
    {"name": "ipad", "width": 768, "height": 1024},
]

async def test_viewport(browser, viewport):
    name = viewport["name"]
    print(f"\n=== Testing {name} ({viewport['width']}x{viewport['height']}) ===")

    page = await browser.new_page(viewport={"width": viewport["width"], "height": viewport["height"]})
    await page.goto("http://localhost:8000")
    await page.wait_for_timeout(2000)

    # Close welcome modal
    await page.evaluate("""
        const modal = document.getElementById('modal-welcome');
        if (modal) modal.classList.remove('active');
    """)
    await page.wait_for_timeout(500)

    # 1. Dashboard (sidebar hidden)
    await page.screenshot(path=f"{OUTPUT_DIR}/{name}_01_dashboard.png")
    print(f"  1. Dashboard")

    # 2. Open sidebar
    hamburger = await page.query_selector("#hamburger-btn")
    if hamburger:
        await hamburger.click()
        await page.wait_for_timeout(500)
        await page.screenshot(path=f"{OUTPUT_DIR}/{name}_02_sidebar_open.png")
        print(f"  2. Sidebar open")

        # Close sidebar
        await page.evaluate("closeMobileSidebar()")
        await page.wait_for_timeout(300)

    # 3. Open modal (Nova Materia)
    await page.evaluate("openModal('modal-materia')")
    await page.wait_for_timeout(500)
    await page.screenshot(path=f"{OUTPUT_DIR}/{name}_03_modal_materia.png")
    print(f"  3. Modal Nova Materia")
    await page.evaluate("closeModal('modal-materia')")
    await page.wait_for_timeout(300)

    # 4. Navigate to Chat
    await page.evaluate("showChat()")
    await page.wait_for_timeout(2000)
    await page.screenshot(path=f"{OUTPUT_DIR}/{name}_04_chat.png")
    print(f"  4. Chat interface")

    # 5. Open Settings modal
    await page.evaluate("openModal('modal-settings')")
    await page.wait_for_timeout(500)
    await page.screenshot(path=f"{OUTPUT_DIR}/{name}_05_settings.png")
    print(f"  5. Settings modal")
    await page.evaluate("closeModal('modal-settings')")
    await page.wait_for_timeout(300)

    # 6. Welcome modal
    await page.evaluate("openWelcome()")
    await page.wait_for_timeout(500)
    await page.screenshot(path=f"{OUTPUT_DIR}/{name}_06_welcome.png")
    print(f"  6. Welcome modal")

    await page.close()
    print(f"  Done with {name}!")

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for viewport in VIEWPORTS:
            await test_viewport(browser, viewport)

        await browser.close()
        print(f"\n Screenshots saved to: {OUTPUT_DIR}/")
        print(f" Total: {len(VIEWPORTS) * 6} screenshots")

if __name__ == "__main__":
    asyncio.run(main())
