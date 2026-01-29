#!/usr/bin/env python3
"""
FGV eClass Complete Scraper
- Browse through years and subjects
- Download submitted documents
- Find answer keys (enunciados e gabaritos)
- Organize and rename files
- Create matérias, turmas, atividades on Prova AI
- Upload everything

FULLY AUTOMATED - No manual intervention required

BROWSER MODES:
- "camoufox": Uses Camoufox (anti-detection Firefox) - BEST for Cloudflare
- "undetected": Uses undetected-playwright with Tarnished

Change BROWSER_MODE below to switch between them.
"""

import os
import json
import time
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING
import hashlib
import shutil

# Type hints for Playwright
if TYPE_CHECKING:
    from playwright.sync_api import Download

# ============================================================================
# BROWSER MODE SELECTION - Change this to test different approaches
# ============================================================================
BROWSER_MODE = "playwright"  # Options: "camoufox", "undetected", or "playwright"
# ============================================================================

# Import credentials from our encrypted storage
from fgv_credentials import get_credentials

# Configuration
BASE_DIR = Path("./fgv_data")
DOWNLOAD_DIR = BASE_DIR / "downloads"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
ORGANIZED_DIR = BASE_DIR / "organized"
BROWSER_DATA_DIR = BASE_DIR / "browser_sessions"
LOG_FILE = BASE_DIR / "scrape_log.txt"
PROVA_AI_URL = "https://ia-educacao-v2.onrender.com/api"

# Create directories
for d in [DOWNLOAD_DIR, SCREENSHOTS_DIR, ORGANIZED_DIR, BROWSER_DATA_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def log_message(msg: str, also_print: bool = True):
    """Log message to file and optionally print"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {msg}"
    if also_print:
        print(full_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")


class ProvaAIClient:
    """Client for Prova AI API"""
    
    def __init__(self, base_url: str = PROVA_AI_URL):
        self.base_url = base_url
        self.aluno_id = None
        self.materias = {}  # name -> id
        self.turmas = {}    # name -> id
        self.atividades = {} # name -> id
    
    def create_aluno(self, nome: str, email: str = None) -> str:
        """Create or get student"""
        try:
            r = requests.get(f"{self.base_url}/alunos", timeout=10)
            if r.ok:
                for aluno in r.json().get("alunos", []):
                    if nome.lower() in aluno.get("nome", "").lower():
                        self.aluno_id = aluno["id"]
                        log_message(f"   ✓ Found existing aluno: {nome} ({self.aluno_id})")
                        return self.aluno_id
            
            data = {"nome": nome, "email": email or f"{nome.lower().replace(' ', '.')}@email.com"}
            r = requests.post(f"{self.base_url}/alunos", json=data, timeout=10)
            if r.ok:
                self.aluno_id = r.json()["aluno"]["id"]
                log_message(f"   ✓ Created aluno: {nome} ({self.aluno_id})")
                return self.aluno_id
        except Exception as e:
            log_message(f"   ✗ Aluno error: {e}")
        return None
    
    def create_materia(self, nome: str, nivel: str = "superior") -> str:
        """Create or get subject"""
        key = nome.lower().strip()
        if key in self.materias:
            return self.materias[key]
        
        try:
            r = requests.get(f"{self.base_url}/materias", timeout=10)
            if r.ok:
                for m in r.json().get("materias", []):
                    if nome.lower() in m.get("nome", "").lower():
                        self.materias[key] = m["id"]
                        log_message(f"   ✓ Found existing matéria: {nome}")
                        return m["id"]
            
            data = {"nome": nome, "nivel": nivel, "descricao": f"Importado do FGV eClass"}
            r = requests.post(f"{self.base_url}/materias", json=data, timeout=10)
            if r.ok:
                mid = r.json()["materia"]["id"]
                self.materias[key] = mid
                log_message(f"   ✓ Created matéria: {nome}")
                return mid
        except Exception as e:
            log_message(f"   ✗ Matéria error: {e}")
        return None
    
    def create_turma(self, nome: str, materia_id: str, ano: int) -> str:
        """Create or get class"""
        key = f"{nome}_{ano}".lower()
        if key in self.turmas:
            return self.turmas[key]
        
        try:
            r = requests.get(f"{self.base_url}/turmas", timeout=10)
            if r.ok:
                for t in r.json().get("turmas", []):
                    if nome.lower() in t.get("nome", "").lower() and t.get("ano_letivo") == ano:
                        self.turmas[key] = t["id"]
                        if self.aluno_id:
                            requests.post(f"{self.base_url}/alunos/vincular", 
                                        json={"aluno_id": self.aluno_id, "turma_id": t["id"]}, timeout=10)
                        log_message(f"   ✓ Found existing turma: {nome} {ano}")
                        return t["id"]
            
            data = {"nome": nome, "materia_id": materia_id, "ano_letivo": ano}
            r = requests.post(f"{self.base_url}/turmas", json=data, timeout=10)
            if r.ok:
                tid = r.json()["turma"]["id"]
                self.turmas[key] = tid
                if self.aluno_id:
                    requests.post(f"{self.base_url}/alunos/vincular",
                                json={"aluno_id": self.aluno_id, "turma_id": tid}, timeout=10)
                log_message(f"   ✓ Created turma: {nome} {ano}")
                return tid
        except Exception as e:
            log_message(f"   ✗ Turma error: {e}")
        return None
    
    def create_atividade(self, nome: str, turma_id: str, tipo: str = "prova") -> str:
        """Create or get activity"""
        key = f"{turma_id}_{nome}".lower()
        if key in self.atividades:
            return self.atividades[key]
        
        try:
            r = requests.get(f"{self.base_url}/atividades", params={"turma_id": turma_id}, timeout=10)
            if r.ok:
                for a in r.json().get("atividades", []):
                    if nome.lower() in a.get("nome", "").lower():
                        self.atividades[key] = a["id"]
                        log_message(f"   ✓ Found existing atividade: {nome}")
                        return a["id"]
            
            data = {"nome": nome, "turma_id": turma_id, "tipo": tipo}
            r = requests.post(f"{self.base_url}/atividades", json=data, timeout=10)
            if r.ok:
                aid = r.json()["atividade"]["id"]
                self.atividades[key] = aid
                log_message(f"   ✓ Created atividade: {nome}")
                return aid
        except Exception as e:
            log_message(f"   ✗ Atividade error: {e}")
        return None
    
    def upload_document(self, file_path: Path, atividade_id: str, aluno_id: str, 
                       tipo: str = "resolucao") -> bool:
        """Upload a document"""
        if not file_path.exists():
            log_message(f"   ✗ File not found: {file_path}")
            return False
        
        try:
            with open(file_path, "rb") as f:
                files = {"arquivo": (file_path.name, f)}
                data = {
                    "atividade_id": atividade_id,
                    "aluno_id": aluno_id,
                    "tipo": tipo,
                    "nome": file_path.stem
                }
                r = requests.post(f"{self.base_url}/documentos/upload", files=files, data=data, timeout=30)
                if r.ok:
                    log_message(f"   📤 UPLOADED: {file_path.name} → Prova AI ({tipo})")
                    return True
                else:
                    log_message(f"   ✗ Upload failed: {r.text[:100]}")
        except Exception as e:
            log_message(f"   ✗ Upload error: {e}")
        return False


# Persistent browser data directory - saves cookies/session
BROWSER_DATA_DIR = BASE_DIR / "browser_data"
BROWSER_DATA_DIR.mkdir(parents=True, exist_ok=True)


class FGVScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._camoufox = None  # Camoufox context manager (if using camoufox mode)
        self.prova_ai = ProvaAIClient()
        
        # Data collected
        self.courses = []
        self.documents = []
        self.current_year = None
        self.current_course = None
        self.current_activity = None
        
        # Stats
        self.files_downloaded = 0
        self.files_uploaded = 0
        self.screenshot_count = 0
        
        log_message("=" * 60)
        log_message(f"FGV SCRAPER INITIALIZED (mode: {BROWSER_MODE})")
        log_message("=" * 60)
    
    def start(self):
        """Start browser with anti-detection (Camoufox or Undetected-Playwright)"""
        log_message(f"\n🚀 Starting browser in '{BROWSER_MODE}' mode...")
        log_message(f"   📁 Session data: {BROWSER_DATA_DIR}")
        
        if BROWSER_MODE == "camoufox":
            self._start_camoufox()
        elif BROWSER_MODE == "undetected":
            self._start_undetected()
        elif BROWSER_MODE == "playwright":
            self._start_playwright_firefox()
        else:
            raise ValueError(f"Unknown BROWSER_MODE: {BROWSER_MODE}")
        
        # Set up download handling
        self.page.on("download", self._handle_download)
        
        log_message(f"   📁 Downloads will go to: {DOWNLOAD_DIR}")
        
        # Take initial screenshot
        self.screenshot("browser_started")
    
    def _start_camoufox(self):
        """Start Camoufox (anti-detection Firefox) with persistent session"""
        from camoufox.sync_api import Camoufox
        
        log_message("   🦊 Using Camoufox (anti-detection Firefox)...")
        log_message("   💭 This works at the C++ level - Cloudflare can't detect it!")
        
        # Camoufox with persistent context
        self._camoufox = Camoufox(
            headless=False,  # Visible browser
            persistent_context=True,  # Keep login sessions
            user_data_dir=str(BROWSER_DATA_DIR / "camoufox"),
            geoip=False,  # Disabled - requires extra install
        )
        
        # Enter context and get browser
        self.context = self._camoufox.__enter__()
        self.page = self.context.new_page()
        
        log_message("   ✓ Camoufox started with persistent session")
    
    def _start_playwright_firefox(self):
        """Fallback: Start regular Playwright Firefox with persistent context"""
        from playwright.sync_api import sync_playwright
        
        log_message("   🦊 Using regular Playwright Firefox...")
        
        self.playwright = sync_playwright().start()
        
        # Use persistent context for login session persistence
        session_dir = BROWSER_DATA_DIR / "playwright_firefox"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.context = self.playwright.firefox.launch_persistent_context(
                user_data_dir=str(session_dir),
                headless=False,
                viewport={"width": 1400, "height": 900},
                accept_downloads=True,
                slow_mo=100,
            )
            log_message("   ✓ Persistent Firefox context created")
        except Exception as e:
            log_message(f"   ⚠️ Persistent context failed: {e}")
            # Fallback to regular context
            self.browser = self.playwright.firefox.launch(headless=False, slow_mo=100)
            self.context = self.browser.new_context(
                viewport={"width": 1400, "height": 900},
                accept_downloads=True,
            )
            log_message("   ✓ Using regular context (no session persistence)")
        
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        log_message("   ✓ Playwright Firefox started")
    
    def _start_undetected(self):
        """Start Undetected-Playwright with Tarnished stealth"""
        from playwright.sync_api import sync_playwright
        from undetected_playwright import Tarnished
        
        log_message("   🕵️ Using Undetected-Playwright with Tarnished...")
        
        self.playwright = sync_playwright().start()
        
        # Use persistent context for login session persistence
        session_dir = BROWSER_DATA_DIR / "undetected"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                headless=False,
                viewport={"width": 1400, "height": 900},
                accept_downloads=True,
                slow_mo=100,
            )
            log_message("   ✓ Persistent context created")
        except Exception as e:
            log_message(f"   ⚠️ Persistent context failed: {e}")
            # Fallback to regular context
            self.browser = self.playwright.chromium.launch(headless=False, slow_mo=100)
            self.context = self.browser.new_context(
                viewport={"width": 1400, "height": 900},
                accept_downloads=True,
            )
            log_message("   ✓ Using regular context (no session persistence)")
        
        # Apply Tarnished stealth to context
        Tarnished.apply_stealth(self.context)
        log_message("   ✓ Tarnished stealth applied")
        
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
        log_message("   ✓ Undetected-Playwright started")
        
        # Set up download handling
        self.page.on("download", self._handle_download)
        
        log_message(f"   📁 Downloads will go to: {DOWNLOAD_DIR}")
        
        # Take initial screenshot
        self.screenshot("browser_started")
    
    def _handle_download(self, download):
        """Handle file downloads - save with context-aware naming"""
        original_filename = download.suggested_filename
        
        # Build context-aware filename
        year_str = str(self.current_year) if self.current_year else "unknown_year"
        course_clean = re.sub(r'[^\w\s-]', '', self.current_course or "unknown_course")[:30].strip()
        activity_clean = re.sub(r'[^\w\s-]', '', self.current_activity or "activity")[:30].strip()
        
        # Create organized directory structure: year/subject/activity/
        org_dir = DOWNLOAD_DIR / year_str / course_clean / activity_clean
        org_dir.mkdir(parents=True, exist_ok=True)
        
        save_path = org_dir / original_filename
        
        # Avoid duplicates
        counter = 1
        while save_path.exists():
            stem = Path(original_filename).stem
            suffix = Path(original_filename).suffix
            save_path = org_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        download.save_as(save_path)
        self.files_downloaded += 1
        
        # Detailed logging about the file
        log_message(f"\n   📥 DOWNLOADED: {original_filename}")
        log_message(f"      → Saved to: {save_path}")
        log_message(f"      → Year: {year_str}")
        log_message(f"      → Subject: {course_clean}")
        log_message(f"      → Activity: {activity_clean}")
        
        self.documents.append({
            "filename": original_filename,
            "path": str(save_path),
            "course": self.current_course,
            "activity": self.current_activity,
            "year": self.current_year,
            "timestamp": datetime.now().isoformat()
        })
    
    def screenshot(self, name: str, always: bool = False):
        """Take screenshot - always saves to disk for debugging"""
        self.screenshot_count += 1
        path = SCREENSHOTS_DIR / f"{self.screenshot_count:03d}_{name}_{datetime.now().strftime('%H%M%S')}.png"
        try:
            self.page.screenshot(path=path)
            log_message(f"   📸 Screenshot #{self.screenshot_count}: {path.name}")
        except Exception as e:
            log_message(f"   ⚠️ Screenshot failed: {e}")
        return path
    
    def check_for_errors(self):
        """Check page for error messages and capture them"""
        try:
            # Common error patterns
            error_selectors = [
                ".error", ".alert-danger", ".error-message",
                "[class*='error']", "[class*='Error']",
                ".warning", ".alert-warning"
            ]
            
            for selector in error_selectors:
                try:
                    error_el = self.page.query_selector(selector)
                    if error_el and error_el.is_visible():
                        error_text = error_el.text_content().strip()[:200]
                        if error_text:
                            log_message(f"   ⚠️ PAGE ERROR DETECTED: {error_text}")
                            self.screenshot("error_detected")
                            return error_text
                except:
                    pass
        except:
            pass
        return None
    
    def report_status(self):
        """Report current browser status"""
        try:
            url = self.page.url
            title = self.page.title()
            log_message(f"\n   📍 STATUS:")
            log_message(f"      URL: {url[:80]}")
            log_message(f"      Title: {title[:60]}")
            self.check_for_errors()
        except Exception as e:
            log_message(f"   ⚠️ Status check failed: {e}")
    
    def check_cloudflare(self) -> bool:
        """Check if Cloudflare challenge is actively blocking us"""
        try:
            # Check for actual Cloudflare CHALLENGE elements (not just references to cloudflare)
            cf_challenge_selectors = [
                "#challenge-running",
                "#challenge-stage",
                ".cf-browser-verification",
                "#cf-please-wait",
                "#cf-spinner-please-wait",
                "[id*='challenge']",
            ]
            
            for selector in cf_challenge_selectors:
                try:
                    el = self.page.query_selector(selector)
                    if el and el.is_visible():
                        log_message(f"   ⚠️ CLOUDFLARE CHALLENGE ACTIVE: '{selector}'")
                        self.screenshot("cloudflare_challenge")
                        return True
                except:
                    pass
            
            # Also check for challenge text in visible elements only
            page_title = self.page.title().lower()
            challenge_titles = ["just a moment", "checking your browser", "please wait"]
            for title in challenge_titles:
                if title in page_title:
                    log_message(f"   ⚠️ CLOUDFLARE CHALLENGE (title): '{title}'")
                    self.screenshot("cloudflare_challenge")
                    return True
            
            return False
        except:
            return False
    
    def navigate_to_eclass(self):
        """Navigate to FGV eClass and auto-login"""
        log_message("\n🌐 Navigating to FGV eClass...")
        
        # Longer timeout for slow page loads
        try:
            self.page.goto("https://eclass.fgv.br/", timeout=60000)
        except:
            log_message("   Page load slow, continuing anyway...")
        
        time.sleep(3)
        self.screenshot("initial_page")
        
        current_url = self.page.url
        log_message(f"   Current URL: {current_url}")
        
        # Check for Cloudflare
        if self.check_cloudflare():
            log_message("   💭 Cloudflare challenge detected - waiting for it to resolve...")
            # Give Cloudflare time to auto-resolve with stealth mode
            for i in range(15):
                time.sleep(2)
                if not self.check_cloudflare():
                    log_message("   ✓ Cloudflare challenge passed!")
                    self.screenshot("cloudflare_passed")
                    break
                else:
                    log_message(f"   💭 Still waiting... ({i+1}/15)")
        
        # Check if already logged in
        if "d2l" in current_url and "home" in current_url:
            log_message("   ✓ Already logged in! (session persisted)")
            return
        
        # Get saved credentials
        username, password = get_credentials()
        
        if not username or not password:
            log_message("   ❌ ERROR: No credentials found!")
            log_message("   Run: python fgv_credentials.py to save your login")
            self.screenshot("no_credentials_error")
            raise Exception("No credentials saved. Run fgv_credentials.py first!")
        
        log_message(f"   🔐 Logging in as: {username}")
        
        # Try to find and fill login form
        try:
            # Wait for page to be ready
            log_message("   💭 Waiting for login page to load...")
            time.sleep(3)
            
            # First, let's see what inputs are on the page
            all_inputs = self.page.query_selector_all("input")
            log_message(f"   💭 Found {len(all_inputs)} input fields on page")
            
            for inp in all_inputs[:10]:
                try:
                    inp_type = inp.get_attribute("type") or "unknown"
                    inp_name = inp.get_attribute("name") or ""
                    inp_placeholder = inp.get_attribute("placeholder") or ""
                    if inp.is_visible():
                        log_message(f"      • Input: type={inp_type}, name={inp_name}, placeholder={inp_placeholder[:30]}")
                except:
                    pass
            
            # Look for username field - FGV specific selectors first
            username_selectors = [
                "input[placeholder*='Conta de Acesso']",
                "input[placeholder*='Conta']",
                "input[placeholder*='FGV']",
                "input[name='username']",
                "input[name='userName']",
                "input[name='login']",
                "input[type='text']:not([type='password'])",
                "input[type='email']",
                "#username",
                "#loginId",
                "input.form-control[type='text']",
                "input[placeholder*='usuário']",
                "input[placeholder*='user']"
            ]
            
            username_field = None
            for selector in username_selectors:
                try:
                    field = self.page.query_selector(selector)
                    if field and field.is_visible():
                        username_field = field
                        log_message(f"   Found username field: {selector}")
                        break
                except:
                    continue
            
            if not username_field:
                log_message("   ❌ Could not find username field!")
                self.screenshot("login_error_no_username")
                raise Exception("Login form not found")
            
            username_field.fill(username)
            log_message("   ✓ Filled username")
            self.screenshot("filled_username")
            time.sleep(0.5)
            
            # Look for password field - FGV uses "Senha"
            password_selectors = [
                "input[placeholder*='Senha']",
                "input[name='password']",
                "input[name='senha']",
                "input[type='password']",
                "#password",
                "#senha",
                "input.form-control[type='password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    field = self.page.query_selector(selector)
                    if field and field.is_visible():
                        password_field = field
                        log_message(f"   Found password field: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                log_message("   ❌ Could not find password field!")
                self.screenshot("login_error_no_password")
                raise Exception("Password field not found")
            
            password_field.fill(password)
            log_message("   ✓ Filled password")
            self.screenshot("filled_credentials")
            time.sleep(0.5)
            
            # Click login button - FGV uses "ENTRAR"
            button_selectors = [
                "button:has-text('ENTRAR')",
                "button:has-text('Entrar')",
                "input[value='ENTRAR']",
                "input[value='Entrar']",
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Sign in')",
                ".btn-primary"
            ]
            
            login_button = None
            for selector in button_selectors:
                try:
                    btn = self.page.query_selector(selector)
                    if btn and btn.is_visible():
                        login_button = btn
                        log_message(f"   Found login button: {selector}")
                        break
                except:
                    continue
            
            if login_button:
                login_button.click()
                log_message("   ✓ Clicked login button")
            else:
                log_message("   ⚠️ No button found - trying Enter key")
                self.page.keyboard.press("Enter")
            
            # Wait for login to complete
            log_message("   Waiting for login redirect...")
            time.sleep(5)
            
            # Verify login success
            current_url = self.page.url
            log_message(f"   URL after login: {current_url}")
            self.screenshot("after_login_attempt")
            
            # Check if Cloudflare blocked us after login
            if self.check_cloudflare():
                log_message("   ⚠️ Cloudflare appeared after login - waiting...")
                time.sleep(10)
                self.screenshot("cloudflare_after_login")
            
            if "d2l" in current_url or "home" in current_url:
                log_message("   ✅ LOGIN SUCCESSFUL!")
                self.screenshot("login_success")
            else:
                log_message("   ⚠️ Login may have failed - continuing anyway...")
                self.report_status()
            
        except Exception as e:
            log_message(f"   ❌ Login error: {e}")
            self.screenshot("login_exception")
            raise
        
        time.sleep(2)
    
    def find_courses_by_year(self) -> Dict[int, List[Dict]]:
        """Find all courses organized by year"""
        log_message("\n📚 Finding courses by year...")
        log_message("\n🤔 THINKING: Looking for course links on the homepage...")
        log_message("   💭 D2L/Brightspace shows courses as links with 'ouHome' in URL")
        log_message("   💭 Each link leads to a course homepage")
        
        self.page.goto("https://ss.cursos.fgv.br/d2l/home")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        self.screenshot("d2l_homepage")
        
        courses_by_year = {}
        all_courses = []
        
        # D2L course links have 'ouHome' in URL
        log_message("   💭 Searching for course links (ouHome URLs)...")
        
        # Find ALL links with ouHome (course homepages)
        course_links = self.page.query_selector_all("a[href*='ouHome']")
        log_message(f"   💭 Found {len(course_links)} potential course links")
        
        seen_courses = set()
        
        for link in course_links:
            try:
                text = link.text_content().strip()
                href = link.get_attribute("href") or ""
                
                # Skip empty or very short names
                if not text or len(text) < 3:
                    continue
                
                # Extract course ID from URL (ou=XXXXX)
                ou_match = re.search(r'ou=(\d+)', href)
                course_id = ou_match.group(1) if ou_match else None
                
                # Skip duplicates (same course ID)
                if course_id and course_id in seen_courses:
                    continue
                seen_courses.add(course_id)
                
                # Extract year from course name or default to current year
                year_match = re.search(r'20\d{2}', text)
                year = int(year_match.group()) if year_match else datetime.now().year
                
                # Build full URL
                full_url = f"https://ss.cursos.fgv.br{href}" if href.startswith('/') else href
                
                log_message(f"\n      📖 Found course: '{text[:50]}'")
                log_message(f"         💭 Course ID: {course_id}, Year: {year}")
                
                all_courses.append({
                    "name": text[:100],
                    "url": full_url,
                    "year": year,
                    "id": course_id
                })
            except Exception as e:
                log_message(f"         ⚠️ Error parsing course: {e}")
        
        # If no ouHome links found, try the "My Courses" widget
        if not all_courses:
            log_message("   💭 No ouHome links found, looking for My Courses widget...")
            self.screenshot("no_courses_found")
            
            # Try clicking on "My Courses" or similar
            my_courses_patterns = [
                "a:has-text('Meus Cursos')",
                "a:has-text('My Courses')",
                "button:has-text('Cursos')",
                "d2l-my-courses",
            ]
            
            for pattern in my_courses_patterns:
                try:
                    el = self.page.query_selector(pattern)
                    if el and el.is_visible():
                        log_message(f"   💭 Found: {pattern}")
                        el.click()
                        time.sleep(2)
                        self.screenshot("clicked_my_courses")
                        break
                except:
                    pass
        
        # Organize by year
        for c in all_courses:
            year = c["year"]
            if year not in courses_by_year:
                courses_by_year[year] = []
            courses_by_year[year].append(c)
        
        sorted_years = sorted(courses_by_year.keys(), reverse=True)
        
        log_message(f"\n   Found courses by year:")
        for year in sorted_years:
            log_message(f"   📅 {year}: {len(courses_by_year[year])} courses")
            for c in courses_by_year[year][:5]:
                log_message(f"      • {c['name'][:50]}...")
        
        self.courses = all_courses
        return {y: courses_by_year[y] for y in sorted_years}
    
    def find_dropbox_submissions(self, course_url: str) -> List[Dict]:
        """
        Check the dropbox page for YOUR submissions.
        Returns ONLY assignments where you actually submitted something.
        
        Logic:
        1. Go to dropbox page
        2. Look at the STATUS column for each assignment
        3. If status shows "Enviado" or a date/file → you submitted → include it
        4. If status shows "Não Enviado" → skip immediately
        """
        log_message(f"\n   📤 Checking dropbox for YOUR submissions...")
        
        # Navigate to course if not there
        if course_url not in self.page.url:
            self.page.goto(course_url)
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)
        
        # Find and click the dropbox/submissions link
        dropbox_patterns = [
            "a[href*='dropbox']",
            "a:has-text('Dropbox')",
            "a:has-text('Atividades')",
            "a:has-text('Entregas')",
        ]
        
        dropbox_link = None
        for pattern in dropbox_patterns:
            try:
                link = self.page.query_selector(pattern)
                if link and link.is_visible():
                    dropbox_link = link
                    break
            except:
                continue
        
        if not dropbox_link:
            log_message("   ❌ No dropbox found in this course")
            return []
        
        dropbox_link.click()
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        self.screenshot("dropbox_list")
        
        # Now we're on the dropbox list page
        # D2L shows a table with: Assignment Name | Status | Due Date | etc.
        # We need to find rows where Status is NOT "Não Enviado"
        
        submitted_assignments = []
        
        # Get all table rows
        rows = self.page.query_selector_all("tr")
        log_message(f"   💭 Found {len(rows)} rows in dropbox table")
        
        for row in rows:
            try:
                row_text = row.text_content() or ""
                
                # Skip header rows
                if not row_text.strip() or "Nome" in row_text and "Status" in row_text:
                    continue
                
                # Look for links in this row (the assignment link)
                link = row.query_selector("a[href*='dropbox']")
                if not link:
                    continue
                
                assignment_name = link.text_content().strip()
                if not assignment_name or len(assignment_name) < 2:
                    continue
                
                href = link.get_attribute("href") or ""
                full_url = f"https://ss.cursos.fgv.br{href}" if href.startswith('/') else href
                
                # Check status - look for "Não Enviado" in the row
                if "Não Enviado" in row_text:
                    log_message(f"   ⏭️ SKIP: '{assignment_name[:40]}' → Não Enviado")
                    continue
                
                # Check if there's evidence of submission (date, file count, "Enviado")
                has_submission = False
                
                # Look for date patterns (dd/mm/yyyy or similar)
                date_pattern = r'\d{1,2}/\d{1,2}/\d{2,4}'
                if re.search(date_pattern, row_text):
                    has_submission = True
                
                # Look for "Enviado" or file indicators
                if "Enviado" in row_text or "arquivo" in row_text.lower():
                    has_submission = True
                
                # Look for cells that might contain submission info
                cells = row.query_selector_all("td")
                for cell in cells:
                    cell_text = cell.text_content().strip()
                    # If cell has a date or "Enviado", it's submitted
                    if re.search(date_pattern, cell_text) or "Enviado" in cell_text:
                        has_submission = True
                        break
                
                if has_submission:
                    log_message(f"   ✅ FOUND: '{assignment_name[:40]}' → Submitted!")
                    submitted_assignments.append({
                        "name": assignment_name,
                        "url": full_url,
                        "status": "submitted"
                    })
                else:
                    # Status unclear - we'll check inside
                    log_message(f"   🔍 CHECK: '{assignment_name[:40]}' → Status unclear")
                    submitted_assignments.append({
                        "name": assignment_name,
                        "url": full_url,
                        "status": "check"
                    })
                    
            except Exception as e:
                continue
        
        # Summary
        submitted_count = len([s for s in submitted_assignments if s['status'] == 'submitted'])
        check_count = len([s for s in submitted_assignments if s['status'] == 'check'])
        
        log_message(f"\n   📊 Result: {submitted_count} submitted, {check_count} to check")
        
        if not submitted_assignments:
            log_message("   💭 Nothing submitted in this course → Moving to next subject")
        
        return submitted_assignments
    
    def find_content_materials(self, course_url: str) -> List[Dict]:
        """Navigate to course content and find enunciados/gabaritos"""
        log_message("\n   📚 Looking for Content/Materials (enunciados, gabaritos)...")
        
        content_patterns = [
            "a[href*='content']",
            "a[href*='materials']",
            "a:has-text('Conteúdo')",
            "a:has-text('Content')",
            "a:has-text('Materiais')",
            "a:has-text('Materials')",
        ]
        
        for pattern in content_patterns:
            try:
                link = self.page.query_selector(pattern)
                if link and link.is_visible():
                    log_message(f"   Found content link: {pattern}")
                    link.click()
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    break
            except:
                continue
        
        materials = []
        file_links = self.page.query_selector_all("a[href]")
        
        log_message("\n   🤔 THINKING: Scanning page for relevant documents...")
        
        for link in file_links:
            try:
                text = link.text_content().strip()
                text_lower = text.lower()
                href = link.get_attribute("href") or ""
                
                # Keywords that indicate document types
                enunciado_keywords = ["enunciado", "prova", "questões", "questoes", "exercício", "exercicio", "atividade"]
                gabarito_keywords = ["gabarito", "resposta", "solução", "solucao", "answer", "key"]
                
                is_enunciado = any(x in text_lower for x in enunciado_keywords)
                is_gabarito = any(x in text_lower for x in gabarito_keywords)
                is_file = any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx'])
                
                if (is_enunciado or is_gabarito) or is_file:
                    doc_type = "gabarito" if is_gabarito else "enunciado" if is_enunciado else "material"
                    
                    # Build full URL (fix relative paths)
                    full_url = href
                    if href.startswith('/'):
                        full_url = f"https://ss.cursos.fgv.br{href}"
                    elif not href.startswith('http'):
                        full_url = f"https://ss.cursos.fgv.br/{href}"
                    
                    # Show reasoning
                    log_message(f"\n      📄 Found: '{text[:50]}'")
                    if is_gabarito:
                        matched = [k for k in gabarito_keywords if k in text_lower]
                        log_message(f"         💭 This looks like a GABARITO (answer key)")
                        log_message(f"         💭 Reason: contains keywords {matched}")
                    elif is_enunciado:
                        matched = [k for k in enunciado_keywords if k in text_lower]
                        log_message(f"         💭 This looks like an ENUNCIADO (problem statement)")
                        log_message(f"         💭 Reason: contains keywords {matched}")
                    elif is_file:
                        ext = [e for e in ['.pdf', '.doc', '.docx'] if e in href.lower()]
                        log_message(f"         💭 This is a downloadable file ({ext})")
                        log_message(f"         💭 Will classify based on filename later")
                    
                    materials.append({
                        "name": text[:80],
                        "url": full_url,
                        "type": doc_type
                    })
            except:
                pass
        
        log_message(f"\n   ✅ Found {len(materials)} relevant materials")
        return materials
    
    def download_files_from_page(self, description: str = ""):
        """Download all downloadable files from current page"""
        log_message(f"\n   📥 Downloading files{' - ' + description if description else ''}...")
        
        extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.txt']
        
        links = self.page.query_selector_all("a[href]")
        files_found = []
        
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                text = link.text_content().strip()
                
                is_file = any(ext in href.lower() for ext in extensions)
                is_download = "download" in href.lower() or "attachment" in href.lower()
                
                if is_file or is_download:
                    files_found.append({"text": text, "href": href})
            except:
                pass
        
        log_message(f"   Found {len(files_found)} files to download")
        for f in files_found[:30]:
            try:
                log_message(f"   Clicking: {f['text'][:50]}...")
                link = self.page.query_selector(f"a[href='{f['href']}']")
                if link:
                    link.click()
                    time.sleep(1.5)
            except Exception as e:
                log_message(f"   ⚠️ Could not download: {e}")
        
        return files_found
    
    def classify_document(self, filename: str) -> str:
        """Classify document type based on filename with reasoning"""
        filename_lower = filename.lower()
        
        log_message(f"\n   🤔 CLASSIFYING: '{filename}'")
        
        # Define classification rules with explanations
        rules = [
            (["gabarito", "answer", "resposta", "solução", "solucao", "key"], "gabarito", "answer key/solution"),
            (["enunciado", "questões", "questoes", "problema"], "enunciado", "problem statement/questions"),
            (["prova", "exam", "test", "avaliação", "avaliacao", "p1", "p2", "p3", "a1", "a2", "a3"], "prova", "exam/test"),
            (["resolução", "resolucao", "submission", "entrega", "trabalho"], "resolucao", "student submission/work"),
            (["nota", "grade", "result"], "resultado", "grades/results"),
        ]
        
        for keywords, doc_type, description in rules:
            matched = [k for k in keywords if k in filename_lower]
            if matched:
                log_message(f"      💭 Found keywords: {matched}")
                log_message(f"      💭 This is a {description.upper()}")
                log_message(f"      ✅ Classification: {doc_type}")
                return doc_type
        
        log_message(f"      💭 No specific keywords found")
        log_message(f"      💭 Could be: slides, notes, supplementary material...")
        log_message(f"      ✅ Classification: outro (other)")
        return "outro"
    
    def organize_and_upload(self):
        """Organize downloaded files and upload to Prova AI"""
        log_message("\n" + "=" * 60)
        log_message("📂 ORGANIZING AND UPLOADING FILES")
        log_message("=" * 60)
        
        if not self.documents:
            log_message("   No documents to organize")
            return
        
        self.prova_ai.create_aluno("Otávio Bopp", "otavio.bopp@fgv.edu.br")
        
        for doc in self.documents:
            path = Path(doc["path"])
            if not path.exists():
                continue
            
            filename = doc["filename"]
            course_name = doc.get("course", "Unknown Course") or "Unknown Course"
            year = doc.get("year") or 2024
            activity = doc.get("activity", "Atividade 1") or "Atividade 1"
            
            log_message(f"\n📄 Processing: {filename}")
            
            doc_type = self.classify_document(filename)
            log_message(f"   Type: {doc_type}")
            
            materia_name = re.sub(r'\d{4}|\(.*\)|\[.*\]|-\s*\d+T', '', course_name).strip()[:50]
            if not materia_name:
                materia_name = "Matéria FGV"
            
            materia_id = self.prova_ai.create_materia(materia_name)
            if not materia_id:
                continue
            
            turma_name = f"{materia_name} {year}"
            turma_id = self.prova_ai.create_turma(turma_name, materia_id, year)
            if not turma_id:
                continue
            
            atividade_id = self.prova_ai.create_atividade(activity, turma_id)
            if not atividade_id:
                continue
            
            org_dir = ORGANIZED_DIR / str(year) / materia_name / activity
            org_dir.mkdir(parents=True, exist_ok=True)
            
            new_name = f"{doc_type}_{filename}"
            org_path = org_dir / new_name
            
            shutil.copy(path, org_path)
            log_message(f"   📁 Organized to: {org_path}")
            
            if self.prova_ai.upload_document(org_path, atividade_id, self.prova_ai.aluno_id, tipo=doc_type):
                self.files_uploaded += 1
    
    def run_full_scrape(self):
        """Run the complete scraping process - SEQUENTIAL by year and subject"""
        log_message("\n" + "=" * 60)
        log_message("🚀 STARTING FULL FGV SCRAPE")
        log_message("=" * 60)
        log_message("This will go through:")
        log_message("  1. Each year (newest to oldest)")
        log_message("  2. Each subject in that year")
        log_message("  3. First: Sent Activities (your submissions)")
        log_message("  4. Then: Find matching enunciados and gabaritos")
        log_message("=" * 60)
        
        self.navigate_to_eclass()
        
        courses_by_year = self.find_courses_by_year()
        
        if not courses_by_year:
            log_message("\n⚠️ No courses found. Let me analyze the page...")
            self.explore_page_structure()
            return
        
        for year in courses_by_year:
            log_message(f"\n{'='*60}")
            log_message(f"📅 YEAR: {year}")
            log_message("=" * 60)
            
            self.current_year = year
            courses = courses_by_year[year]
            
            for i, course in enumerate(courses):
                log_message(f"\n{'─'*50}")
                log_message(f"📖 [{i+1}/{len(courses)}] {course['name'][:60]}")
                log_message("─" * 50)
                
                self.current_course = course['name']
                
                if not course.get('url'):
                    log_message("   ⚠️ No URL, skipping")
                    continue
                
                try:
                    self.page.goto(course['url'])
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(2)
                    
                    # STEP 1: Check Dropbox/Submissions FIRST
                    log_message("\n   📤 STEP 1: Checking your SUBMISSIONS...")
                    submissions = self.find_dropbox_submissions(course['url'])
                    
                    downloaded_count = 0
                    skipped_count = 0
                    
                    if not submissions:
                        log_message(f"\n   ⏭️ No submissions found - skipping to next course")
                        continue
                    
                    for sub in submissions[:10]:
                        self.current_activity = sub['name']
                        log_message(f"\n   📋 Submission: {sub['name'][:50]}")
                        
                        try:
                            if sub.get('url'):
                                self.page.goto(sub['url'])
                                self.page.wait_for_load_state("networkidle")
                                time.sleep(1)
                                
                                # Check the folder page for submission status
                                folder_text = self.page.text_content("body") or ""
                                
                                # Check for "Não Enviado" - means NO submission
                                if "Não Enviado" in folder_text or "Not Submitted" in folder_text:
                                    log_message(f"      ⏭️ SKIPPING: Status shows 'Não Enviado' (not submitted)")
                                    skipped_count += 1
                                    continue
                                
                                # Look specifically for YOUR submission section
                                # In D2L, submissions are in a specific section
                                submission_section = self.page.query_selector("[class*='submission'], [class*='Submission'], .d2l-submission")
                                
                                # Also check for file links that look like downloads (not instructions)
                                # Your submissions would be in a download link, not content links
                                submission_files = self.page.query_selector_all("a[href*='download'][href*='submission'], a[href*='viewSubmission'], a[href*='SubmittedFile']")
                                
                                if not submission_files:
                                    # Try more generic approach - look for any downloadable files in submission area
                                    submission_files = self.page.query_selector_all("a[href*='attachment'], a[href*='download']")
                                
                                if submission_files:
                                    log_message(f"      ✅ Found {len(submission_files)} submission file(s)")
                                    self.download_files_from_page("my submission")
                                    downloaded_count += 1
                                else:
                                    log_message(f"      ⏭️ SKIPPING: No submission files found in this folder")
                                    skipped_count += 1
                                    continue
                        except Exception as e:
                            log_message(f"   ⚠️ Error: {e}")
                    
                    log_message(f"\n   📊 Course Summary: Downloaded from {downloaded_count} submissions, Skipped {skipped_count}")
                    
                    # STEP 2: Find enunciados and gabaritos (only if we had submissions)
                    if downloaded_count > 0:
                        log_message("\n   📚 STEP 2: Finding ENUNCIADOS and GABARITOS for your submissions...")
                        self.page.goto(course['url'])
                        self.page.wait_for_load_state("networkidle")
                        time.sleep(1)
                        
                        materials = self.find_content_materials(course['url'])
                        
                        for mat in materials[:15]:
                            self.current_activity = mat.get('name', 'Material')
                            log_message(f"\n   📄 Material [{mat.get('type', 'unknown')}]: {mat['name'][:50]}")
                            
                            try:
                                if mat.get('url') and not mat['url'].startswith('#'):
                                    self.page.goto(mat['url'])
                                    self.page.wait_for_load_state("networkidle")
                                    time.sleep(1)
                                    self.download_files_from_page(mat.get('type', 'material'))
                            except Exception as e:
                                log_message(f"   ⚠️ Error: {e}")
                    else:
                        log_message("\n   ⏭️ Skipping Step 2 (gabaritos) - no submissions in this course")
                    
                except Exception as e:
                    log_message(f"   ❌ Error processing course: {e}")
                    continue
        
        self.organize_and_upload()
        
        log_message("\n" + "=" * 60)
        log_message("✅ SCRAPING COMPLETE!")
        log_message("=" * 60)
        log_message(f"   📥 Files downloaded: {self.files_downloaded}")
        log_message(f"   📤 Files uploaded:   {self.files_uploaded}")
        log_message(f"   📁 Local folder:     {ORGANIZED_DIR}")
        log_message(f"   📝 Log file:         {LOG_FILE}")
        log_message("\n   The browser will stay open. Close it when done.")
    
    def explore_page_structure(self):
        """Explore page to understand structure"""
        log_message("\n🔍 Analyzing page structure...")
        
        html = self.page.content()
        html_path = SCREENSHOTS_DIR / "page_structure.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        log_message(f"   Saved HTML to: {html_path}")
        
        buttons = self.page.query_selector_all("button, [role='button']")
        links = self.page.query_selector_all("a[href]")
        
        log_message(f"   Buttons: {len(buttons)}")
        log_message(f"   Links: {len(links)}")
        
        log_message("\n   Top links:")
        for link in links[:20]:
            text = link.text_content().strip()[:40]
            href = (link.get_attribute("href") or "")[:50]
            if text:
                log_message(f"      - {text}: {href}")
        
        self.screenshot("structure_analysis")
    
    def keep_open(self):
        """Keep browser open until user closes it"""
        log_message("\n" + "=" * 60)
        log_message("🔓 BROWSER STAYING OPEN")
        log_message("Close the browser window when you're done reviewing.")
        log_message("=" * 60)
        
        try:
            while True:
                try:
                    self.page.title()
                    time.sleep(2)
                except:
                    log_message("\n👋 Browser closed by user.")
                    break
        except KeyboardInterrupt:
            log_message("\n⚠️ Interrupted. Browser stays open.")


def main():
    scraper = FGVScraper()
    
    try:
        scraper.start()
        scraper.run_full_scrape()
        
        # Keep browser open - don't close it!
        scraper.keep_open()
        
    except KeyboardInterrupt:
        log_message("\n⚠️ Interrupted by user")
    except Exception as e:
        log_message(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        try:
            scraper.keep_open()
        except:
            pass


if __name__ == "__main__":
    main()
