"""Compare local vs production versions for design inconsistencies"""
import asyncio
from playwright.async_api import async_playwright
import os

LOCAL_URL = "http://localhost:8000"
PROD_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_DIR = "version-comparison"

VIEWPORTS = [
    ("phone", 375, 667),
    ("tablet", 768, 1024),
    ("desktop", 1400, 900),
]

PAGES_TO_TEST = [
    ("dashboard", None),
    ("chat", ".tree-item:has-text('Chat com IA')"),
]

async def test_version(page, base_url, version_name):
    """Test a single version across viewports and pages"""
    results = []

    for vp_name, width, height in VIEWPORTS:
        await page.set_viewport_size({"width": width, "height": height})

        for page_name, nav_selector in PAGES_TO_TEST:
            await page.goto(base_url, timeout=30000)
            await page.wait_for_timeout(2000)

            # Close welcome modal
            await page.evaluate("""
                const modal = document.getElementById('modal-welcome');
                if (modal) modal.classList.remove('active');
            """)
            await page.wait_for_timeout(500)

            # Navigate if needed
            if nav_selector:
                try:
                    # On mobile, need to open sidebar first
                    if width < 769:
                        hamburger = await page.query_selector("#hamburger-btn")
                        if hamburger and await hamburger.is_visible():
                            await page.click("#hamburger-btn")
                            await page.wait_for_timeout(500)

                    await page.click(nav_selector)
                    await page.wait_for_timeout(2500)
                except Exception as e:
                    print(f"  [WARN] Navigation failed for {page_name}: {e}")
                    continue

            # Take screenshot
            filename = f"{OUTPUT_DIR}/{version_name}_{vp_name}_{page_name}.png"
            await page.screenshot(path=filename)
            print(f"  [OK] {version_name} {vp_name} {page_name}")

            # Check for specific elements
            checks = {}

            # Hamburger visibility
            hamburger = await page.query_selector("#hamburger-btn")
            if hamburger:
                checks["hamburger_visible"] = await hamburger.is_visible()
            else:
                checks["hamburger_visible"] = False

            # Sidebar visibility
            sidebar = await page.query_selector(".sidebar")
            if sidebar:
                box = await sidebar.bounding_box()
                checks["sidebar_visible"] = box is not None and box["x"] >= 0
            else:
                checks["sidebar_visible"] = False

            # Check for error messages
            error_alert = await page.query_selector(".alert-danger")
            checks["has_error"] = error_alert is not None and await error_alert.is_visible()

            results.append({
                "version": version_name,
                "viewport": vp_name,
                "page": page_name,
                "width": width,
                "checks": checks
            })

    return results

async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        all_results = []

        # Test LOCAL
        print("\n=== Testing LOCAL version ===")
        try:
            page = await browser.new_page()
            local_results = await test_version(page, LOCAL_URL, "local")
            all_results.extend(local_results)
            await page.close()
        except Exception as e:
            print(f"[ERROR] Local test failed: {e}")

        # Test PRODUCTION
        print("\n=== Testing PRODUCTION version ===")
        try:
            page = await browser.new_page()
            prod_results = await test_version(page, PROD_URL, "prod")
            all_results.extend(prod_results)
            await page.close()
        except Exception as e:
            print(f"[ERROR] Production test failed: {e}")

        await browser.close()

        # Compare results
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)

        issues = []

        for vp_name, width, _ in VIEWPORTS:
            for page_name, _ in PAGES_TO_TEST:
                local_r = next((r for r in all_results if r["version"] == "local" and r["viewport"] == vp_name and r["page"] == page_name), None)
                prod_r = next((r for r in all_results if r["version"] == "prod" and r["viewport"] == vp_name and r["page"] == page_name), None)

                if not local_r or not prod_r:
                    continue

                print(f"\n{vp_name.upper()} - {page_name}:")

                # Check hamburger
                local_ham = local_r["checks"].get("hamburger_visible", False)
                prod_ham = prod_r["checks"].get("hamburger_visible", False)
                expected_ham = width < 769

                if local_ham != prod_ham:
                    issues.append(f"[MISMATCH] {vp_name}/{page_name}: Hamburger - local={local_ham}, prod={prod_ham}")
                    print(f"  [MISMATCH] Hamburger: local={local_ham}, prod={prod_ham}")
                elif local_ham != expected_ham:
                    issues.append(f"[UNEXPECTED] {vp_name}/{page_name}: Hamburger visible={local_ham}, expected={expected_ham}")
                    print(f"  [UNEXPECTED] Hamburger visible={local_ham}, expected={expected_ham}")
                else:
                    print(f"  [OK] Hamburger: {local_ham} (expected: {expected_ham})")

                # Check errors
                if local_r["checks"].get("has_error"):
                    issues.append(f"[ERROR] Local {vp_name}/{page_name} has error alert")
                    print(f"  [ERROR] Local has error alert!")
                if prod_r["checks"].get("has_error"):
                    issues.append(f"[ERROR] Prod {vp_name}/{page_name} has error alert")
                    print(f"  [ERROR] Prod has error alert!")

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)

        if issues:
            print(f"\n[!] Found {len(issues)} issue(s):")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n[OK] No inconsistencies found between versions!")

        print(f"\nScreenshots saved to: {OUTPUT_DIR}/")

if __name__ == "__main__":
    asyncio.run(main())
