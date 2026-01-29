#!/usr/bin/env python3
"""
FGV eClass Scraper - Browse courses, download documents, upload to Prova AI
"""

from playwright.sync_api import sync_playwright, Page
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime

# Configuration
DOWNLOAD_DIR = Path("./fgv_downloads")
PROVA_AI_URL = "https://ia-educacao-v2.onrender.com/api"
SCREENSHOTS_DIR = Path("./fgv_screenshots")

class FGVScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.courses = []
        self.downloaded_files = []
        
        # Create directories
        DOWNLOAD_DIR.mkdir(exist_ok=True)
        SCREENSHOTS_DIR.mkdir(exist_ok=True)
    
    def start(self):
        """Start browser with visible window"""
        print("🌐 Starting browser...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,
            slow_mo=300,
        )
        self.context = self.browser.new_context(
            viewport={'width': 1400, 'height': 900},
            accept_downloads=True,
        )
        self.page = self.context.new_page()
        print("✅ Browser ready!")
    
    def navigate_to_eclass(self):
        """Navigate to FGV eClass"""
        print("📍 Navigating to FGV eClass...")
        self.page.goto("https://eclass.fgv.br/")
        self.page.wait_for_load_state("networkidle")
        
        # Check if already logged in
        if "d2l/home" in self.page.url or "cursos.fgv.br" in self.page.url:
            print("✅ Already logged in!")
            return True
        else:
            print("🔐 Login required. Please log in manually...")
            print("   Waiting for you to complete login...")
            # Wait for redirect to home after login
            self.page.wait_for_url("**/d2l/home**", timeout=300000)  # 5 min timeout
            print("✅ Login successful!")
            return True
    
    def screenshot(self, name: str):
        """Take a screenshot"""
        path = SCREENSHOTS_DIR / f"{name}_{datetime.now().strftime('%H%M%S')}.png"
        self.page.screenshot(path=str(path))
        print(f"📸 Screenshot: {path}")
        return path
    
    def get_courses(self):
        """Get list of enrolled courses"""
        print("\n📚 Finding your courses...")
        
        # Navigate to courses page
        # D2L usually has courses in a dropdown or dedicated page
        
        # Try to find course links
        self.page.goto("https://ss.cursos.fgv.br/d2l/home")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        self.screenshot("home_page")
        
        # Look for course cards/links - D2L typically shows them on homepage
        # Common selectors for D2L course listings
        selectors = [
            ".d2l-course-card",
            ".course-tile",
            "[class*='course']",
            ".homepage-card",
            "d2l-enrollment-card",
            ".d2l-card",
        ]
        
        courses = []
        for selector in selectors:
            try:
                elements = self.page.query_selector_all(selector)
                if elements:
                    print(f"   Found {len(elements)} elements with selector: {selector}")
                    for el in elements:
                        text = el.text_content()
                        href = el.get_attribute("href") if el.get_attribute("href") else ""
                        if text:
                            courses.append({"name": text.strip()[:100], "selector": selector})
            except:
                pass
        
        # Also look for any links containing course info
        links = self.page.query_selector_all("a")
        print(f"   Found {len(links)} total links on page")
        
        # Get page HTML for analysis
        html_content = self.page.content()
        with open(SCREENSHOTS_DIR / "home_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"   Saved page HTML for analysis")
        
        self.courses = courses
        return courses
    
    def explore_page(self):
        """Explore current page and show what's available"""
        print("\n🔍 Exploring current page...")
        
        url = self.page.url
        title = self.page.title()
        
        print(f"   URL: {url}")
        print(f"   Title: {title}")
        
        # Find all navigation elements
        nav_links = self.page.query_selector_all("nav a, .d2l-navigation a, [role='navigation'] a")
        print(f"\n   Navigation links ({len(nav_links)}):")
        for link in nav_links[:10]:
            text = link.text_content().strip()
            href = link.get_attribute("href") or ""
            if text:
                print(f"      - {text[:50]}: {href[:60]}")
        
        # Find main content areas
        main_content = self.page.query_selector_all("main, .content, #content, .main-content")
        print(f"\n   Main content areas: {len(main_content)}")
        
        self.screenshot("exploration")
        
        return {
            "url": url,
            "title": title,
            "nav_links": len(nav_links)
        }
    
    def interactive_mode(self):
        """Interactive mode - you control, I watch and help"""
        print("\n" + "=" * 60)
        print("🎮 INTERACTIVE MODE")
        print("=" * 60)
        print("""
Commands:
  explore  - Analyze current page
  screenshot <name> - Take screenshot
  courses  - Try to find courses
  download - Download visible files
  html     - Save page HTML
  url      - Show current URL
  quit     - Exit
        """)
        
        while True:
            try:
                cmd = input("\n> ").strip().lower()
                
                if cmd == "quit" or cmd == "exit":
                    break
                elif cmd == "explore":
                    self.explore_page()
                elif cmd.startswith("screenshot"):
                    name = cmd.split(" ", 1)[1] if " " in cmd else "manual"
                    self.screenshot(name)
                elif cmd == "courses":
                    self.get_courses()
                elif cmd == "url":
                    print(f"Current URL: {self.page.url}")
                elif cmd == "html":
                    html = self.page.content()
                    path = SCREENSHOTS_DIR / f"page_{datetime.now().strftime('%H%M%S')}.html"
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(html)
                    print(f"Saved to {path}")
                elif cmd == "download":
                    self.find_downloadable_files()
                else:
                    print("Unknown command. Type 'quit' to exit.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("\n👋 Exiting interactive mode...")
    
    def find_downloadable_files(self):
        """Find files that can be downloaded on current page"""
        print("\n📥 Looking for downloadable files...")
        
        # Common file extensions
        extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip']
        
        # Find links to files
        links = self.page.query_selector_all("a[href]")
        files = []
        
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.text_content().strip()
            
            # Check if it's a file link
            is_file = any(ext in href.lower() for ext in extensions)
            is_download = "download" in href.lower() or "attachment" in href.lower()
            
            if is_file or is_download:
                files.append({
                    "text": text[:50],
                    "href": href
                })
        
        print(f"   Found {len(files)} potential file links:")
        for f in files[:20]:
            print(f"      - {f['text']}: {f['href'][:60]}...")
        
        return files
    
    def close(self):
        """Close browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("👋 Browser closed.")


def main():
    scraper = FGVScraper()
    
    try:
        scraper.start()
        scraper.navigate_to_eclass()
        
        print("\n" + "=" * 60)
        print("✅ BROWSER IS READY!")
        print("=" * 60)
        print("\nYou can now:")
        print("1. Navigate manually in the browser")
        print("2. Use commands here to analyze pages")
        print("3. I'll help find and download your documents")
        
        # Start interactive mode
        scraper.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
