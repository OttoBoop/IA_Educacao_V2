#!/usr/bin/env python3
"""
FGV eClass Browser - Opens a visible browser for you to see
"""

from playwright.sync_api import sync_playwright
import time

def main():
    print("🌐 Opening browser window...")
    print("=" * 50)
    
    with sync_playwright() as p:
        # Launch browser with VISIBLE window (headless=False)
        browser = p.chromium.launch(
            headless=False,  # SHOW THE WINDOW!
            slow_mo=500,     # Slow down actions so you can see them
        )
        
        # Create a new context (like incognito)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        
        # New page
        page = context.new_page()
        
        print("📍 Navigating to FGV eClass...")
        page.goto("https://eclass.fgv.br/")
        
        print("⏳ Waiting for login page to load...")
        page.wait_for_load_state("networkidle")
        
        print("\n" + "=" * 50)
        print("👆 BROWSER WINDOW IS NOW OPEN!")
        print("=" * 50)
        print("\nYou should see the FGV login page.")
        print("I'll wait here while you look at it...")
        print("\nPress ENTER in this terminal when you want to continue...")
        
        input()
        
        print("\n📸 Taking a screenshot...")
        page.screenshot(path="fgv_screenshot.png")
        print("Screenshot saved to fgv_screenshot.png")
        
        print("\n🔍 Current URL:", page.url)
        print("📄 Page title:", page.title())
        
        # Keep browser open for 30 more seconds
        print("\n⏰ Browser will stay open for 30 more seconds...")
        print("   You can interact with it manually!")
        time.sleep(30)
        
        print("\n👋 Closing browser...")
        browser.close()

if __name__ == "__main__":
    main()
