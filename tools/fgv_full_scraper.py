#!/usr/bin/env python3
"""
FGV eClass Complete Scraper
- Browse through years and subjects
- Download submitted documents
- Find answer keys
- Organize and rename files
- Create matérias, turmas, atividades on Prova AI
- Upload everything
"""

from playwright.sync_api import sync_playwright, Page, Download
import os
import json
import time
import requests
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import keyring

# Credential storage
CREDENTIAL_SERVICE = "fgv_eclass"

def get_stored_credentials():
    """Get credentials from Windows Credential Manager"""
    username = keyring.get_password(CREDENTIAL_SERVICE, "username")
    password = keyring.get_password(CREDENTIAL_SERVICE, "password")
    return username, password

# Configuration
BASE_DIR = Path("./fgv_data")
DOWNLOAD_DIR = BASE_DIR / "downloads"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
ORGANIZED_DIR = BASE_DIR / "organized"
PROVA_AI_URL = "https://ia-educacao-v2.onrender.com/api"

# Create directories
for d in [DOWNLOAD_DIR, SCREENSHOTS_DIR, ORGANIZED_DIR]:
    d.mkdir(parents=True, exist_ok=True)


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
        # Check if exists
        r = requests.get(f"{self.base_url}/alunos")
        if r.ok:
            for aluno in r.json().get("alunos", []):
                if nome.lower() in aluno.get("nome", "").lower():
                    self.aluno_id = aluno["id"]
                    print(f"   ✓ Found existing aluno: {nome} ({self.aluno_id})")
                    return self.aluno_id
        
        # Create new
        data = {"nome": nome, "email": email or f"{nome.lower().replace(' ', '.')}@email.com"}
        r = requests.post(f"{self.base_url}/alunos", json=data)
        if r.ok:
            self.aluno_id = r.json()["aluno"]["id"]
            print(f"   ✓ Created aluno: {nome} ({self.aluno_id})")
            return self.aluno_id
        else:
            print(f"   ✗ Failed to create aluno: {r.text}")
            return None
    
    def create_materia(self, nome: str, nivel: str = "superior") -> str:
        """Create or get subject"""
        key = nome.lower().strip()
        if key in self.materias:
            return self.materias[key]
        
        # Check existing
        r = requests.get(f"{self.base_url}/materias")
        if r.ok:
            for m in r.json().get("materias", []):
                if nome.lower() in m.get("nome", "").lower():
                    self.materias[key] = m["id"]
                    print(f"   ✓ Found existing matéria: {nome}")
                    return m["id"]
        
        # Create
        data = {"nome": nome, "nivel": nivel, "descricao": f"Importado do FGV eClass"}
        r = requests.post(f"{self.base_url}/materias", json=data)
        if r.ok:
            mid = r.json()["materia"]["id"]
            self.materias[key] = mid
            print(f"   ✓ Created matéria: {nome}")
            return mid
        return None
    
    def create_turma(self, nome: str, materia_id: str, ano: int) -> str:
        """Create or get class"""
        key = f"{nome}_{ano}".lower()
        if key in self.turmas:
            return self.turmas[key]
        
        # Check existing
        r = requests.get(f"{self.base_url}/turmas")
        if r.ok:
            for t in r.json().get("turmas", []):
                if nome.lower() in t.get("nome", "").lower() and t.get("ano_letivo") == ano:
                    self.turmas[key] = t["id"]
                    # Vincular aluno
                    if self.aluno_id:
                        requests.post(f"{self.base_url}/alunos/vincular", 
                                    json={"aluno_id": self.aluno_id, "turma_id": t["id"]})
                    print(f"   ✓ Found existing turma: {nome} {ano}")
                    return t["id"]
        
        # Create
        data = {"nome": nome, "materia_id": materia_id, "ano_letivo": ano}
        r = requests.post(f"{self.base_url}/turmas", json=data)
        if r.ok:
            tid = r.json()["turma"]["id"]
            self.turmas[key] = tid
            # Vincular aluno
            if self.aluno_id:
                requests.post(f"{self.base_url}/alunos/vincular",
                            json={"aluno_id": self.aluno_id, "turma_id": tid})
            print(f"   ✓ Created turma: {nome} {ano}")
            return tid
        return None
    
    def create_atividade(self, nome: str, turma_id: str, tipo: str = "prova") -> str:
        """Create or get activity"""
        key = f"{turma_id}_{nome}".lower()
        if key in self.atividades:
            return self.atividades[key]
        
        # Check existing
        r = requests.get(f"{self.base_url}/atividades", params={"turma_id": turma_id})
        if r.ok:
            for a in r.json().get("atividades", []):
                if nome.lower() in a.get("nome", "").lower():
                    self.atividades[key] = a["id"]
                    print(f"   ✓ Found existing atividade: {nome}")
                    return a["id"]
        
        # Create
        data = {"nome": nome, "turma_id": turma_id, "tipo": tipo}
        r = requests.post(f"{self.base_url}/atividades", json=data)
        if r.ok:
            aid = r.json()["atividade"]["id"]
            self.atividades[key] = aid
            print(f"   ✓ Created atividade: {nome}")
            return aid
        return None
    
    def upload_document(self, file_path: Path, atividade_id: str, aluno_id: str, 
                       tipo: str = "resolucao") -> bool:
        """Upload a document"""
        if not file_path.exists():
            print(f"   ✗ File not found: {file_path}")
            return False
        
        with open(file_path, "rb") as f:
            files = {"arquivo": (file_path.name, f)}
            data = {
                "atividade_id": atividade_id,
                "aluno_id": aluno_id,
                "tipo": tipo,
                "nome": file_path.stem
            }
            r = requests.post(f"{self.base_url}/documentos/upload", files=files, data=data)
            if r.ok:
                print(f"   ✓ Uploaded: {file_path.name} as {tipo}")
                return True
            else:
                print(f"   ✗ Upload failed: {r.text[:100]}")
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
        self.prova_ai = ProvaAIClient()
        
        # Data collected
        self.courses = []
        self.documents = []
        self.current_year = None
        self.current_course = None
    
    def start(self):
        """Start browser with PERSISTENT context - saves login session!"""
        print("\n🌐 Starting browser with persistent session...")
        print(f"   Session saved in: {BROWSER_DATA_DIR}")
        
        self.playwright = sync_playwright().start()
        
        # Use persistent context - this saves cookies, localStorage, etc.
        # Once you log in, you stay logged in!
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(BROWSER_DATA_DIR),
            headless=False,
            slow_mo=200,
            viewport={'width': 1400, 'height': 900},
            accept_downloads=True,
        )
        
        self.page = self.context.new_page()
        
        # Handle downloads
        self.page.on("download", self._handle_download)
        
        print("✅ Browser ready! (session will be remembered)")
    
    def _handle_download(self, download: Download):
        """Handle file downloads"""
        filename = download.suggested_filename
        path = DOWNLOAD_DIR / filename
        download.save_as(str(path))
        print(f"   📥 Downloaded: {filename}")
        self.documents.append({
            "path": str(path),
            "filename": filename,
            "course": self.current_course,
            "year": self.current_year,
            "url": download.url
        })
    
    def screenshot(self, name: str) -> Path:
        """Take screenshot"""
        path = SCREENSHOTS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.page.screenshot(path=str(path))
        return path
    
    def navigate_to_eclass(self):
        """Navigate and login automatically"""
        print("\n📍 Navigating to FGV eClass...")
        
        try:
            self.page.goto("https://eclass.fgv.br/", timeout=60000)
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"   ⚠️ Initial load issue: {e}")
        
        time.sleep(3)
        print(f"   Current URL: {self.page.url}")
        
        # Check login status
        if "d2l/home" in self.page.url or "cursos.fgv.br" in self.page.url:
            print("✅ Already logged in!")
            return
        
        print("\n🔐 Attempting automatic login...")
        
        # Get saved credentials
        try:
            from IA_Educacao_V2.tools.fgv_credentials import get_credentials
            username, password = get_credentials()
        except Exception as e:
            print(f"   Error loading credentials: {e}")
            username, password = None, None
        
        if username and password:
            print(f"   Using saved credentials for: {username}")
            try:
                # Wait for page to be ready
                time.sleep(3)
                
                # Take screenshot to see what's on page
                self.page.screenshot(path="fgv_data/screenshots/login_page.png")
                print("   📸 Screenshot saved to login_page.png")
                
                # Try multiple selectors for username
                username_selectors = [
                    "input[name='username']",
                    "input[name='userName']", 
                    "input[name='j_username']",
                    "input[id='username']",
                    "input[id='userName']",
                    "input[type='text']",
                    "input[type='email']",
                    "#username",
                    "#userNameInput"
                ]
                
                username_field = None
                for selector in username_selectors:
                    try:
                        field = self.page.query_selector(selector)
                        if field and field.is_visible():
                            username_field = field
                            print(f"   Found username field: {selector}")
                            break
                    except:
                        continue
                
                if username_field:
                    username_field.fill(username)
                    print("   ✓ Filled username")
                else:
                    print("   ⚠️ Could not find username field")
                
                # Find and fill password field
                password_selectors = [
                    "input[type='password']",
                    "input[name='password']",
                    "input[name='j_password']",
                    "#password",
                    "#passwordInput"
                ]
                
                password_field = None
                for selector in password_selectors:
                    try:
                        field = self.page.query_selector(selector)
                        if field and field.is_visible():
                            password_field = field
                            print(f"   Found password field: {selector}")
                            break
                    except:
                        continue
                
                if password_field:
                    password_field.fill(password)
                    print("   ✓ Filled password")
                else:
                    print("   ⚠️ Could not find password field")
                
                # Find and click login button
                button_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "button:has-text('Entrar')",
                    "button:has-text('Login')",
                    "button:has-text('ENTRAR')",
                    "#submitButton",
                    ".btn-primary",
                    "input[value='Entrar']",
                    "input[value='Login']"
                ]
                
                login_button = None
                for selector in button_selectors:
                    try:
                        btn = self.page.query_selector(selector)
                        if btn and btn.is_visible():
                            login_button = btn
                            print(f"   Found login button: {selector}")
                            break
                    except:
                        continue
                
                if login_button:
                    login_button.click()
                    print("   ✓ Clicked login button")
                else:
                    print("   ⚠️ Could not find login button - trying Enter key")
                    self.page.keyboard.press("Enter")
                
                # Wait for redirect
                print("   Waiting for login to complete...")
                time.sleep(5)
                
                # Check if we're logged in
                current_url = self.page.url
                print(f"   Current URL after login: {current_url}")
                
                if "d2l" in current_url or "home" in current_url:
                    print("✅ Login successful!")
                else:
                    print("   ⚠️ May need to complete login manually...")
                    print("   Waiting for you to finish logging in...")
                    # Wait longer for manual intervention
                    try:
                        self.page.wait_for_url("**/d2l/**", timeout=120000)
                        print("✅ Login completed!")
                    except:
                        print("   Continuing anyway...")
                
            except Exception as e:
                print(f"   ⚠️ Auto-login error: {e}")
                print("   Please log in manually in the browser window...")
                try:
                    self.page.wait_for_url("**/d2l/**", timeout=300000)
                except:
                    pass
        else:
            print("   No saved credentials. Please log in manually...")
            print("   (Run fgv_credentials.py to save your login)")
            try:
                self.page.wait_for_url("**/d2l/**", timeout=300000)
            except:
                pass
        
        self.screenshot("after_login")
        time.sleep(2)
    
    def find_courses(self) -> List[Dict]:
        """Find all available courses"""
        print("\n📚 Finding courses...")
        
        self.page.goto("https://ss.cursos.fgv.br/d2l/home")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        courses = []
        
        # D2L course cards - try multiple selectors
        selectors = [
            "d2l-card",
            ".d2l-card",
            "[class*='course-card']",
            "[class*='enrollment']",
            ".homepage-card",
            "a[href*='/d2l/home/']",
        ]
        
        for selector in selectors:
            try:
                elements = self.page.query_selector_all(selector)
                for el in elements:
                    try:
                        # Get course name and link
                        text = el.text_content().strip()
                        href = el.get_attribute("href") or ""
                        
                        # Try to find link inside
                        if not href:
                            link = el.query_selector("a")
                            if link:
                                href = link.get_attribute("href") or ""
                        
                        if text and len(text) > 3 and "d2l" in href.lower():
                            # Extract year from text if possible
                            year_match = re.search(r'20\d{2}', text)
                            year = int(year_match.group()) if year_match else None
                            
                            courses.append({
                                "name": text[:100],
                                "url": href,
                                "year": year,
                                "selector": selector
                            })
                    except:
                        pass
            except:
                pass
        
        # Remove duplicates
        seen = set()
        unique_courses = []
        for c in courses:
            key = c.get("url", c.get("name", ""))
            if key and key not in seen:
                seen.add(key)
                unique_courses.append(c)
        
        self.courses = unique_courses
        print(f"   Found {len(unique_courses)} courses")
        
        for i, c in enumerate(unique_courses[:20]):
            print(f"   {i+1}. {c['name'][:60]}...")
        
        self.screenshot("courses_list")
        return unique_courses
    
    def explore_course(self, course_url: str):
        """Explore a single course"""
        print(f"\n📖 Exploring course...")
        
        self.page.goto(course_url)
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        self.screenshot("course_page")
        
        # Look for content/assignments links
        nav_items = []
        
        # Common D2L navigation patterns
        nav_selectors = [
            "nav a",
            ".d2l-navigation a",
            "[class*='nav'] a",
            ".d2l-menu a",
            "a[href*='content']",
            "a[href*='dropbox']",
            "a[href*='grades']",
            "a[href*='quizzes']",
        ]
        
        for selector in nav_selectors:
            try:
                links = self.page.query_selector_all(selector)
                for link in links:
                    text = link.text_content().strip()
                    href = link.get_attribute("href") or ""
                    if text and href:
                        nav_items.append({"text": text, "href": href})
            except:
                pass
        
        # Find key sections
        sections = {
            "content": None,
            "assignments": None,
            "grades": None,
            "quizzes": None
        }
        
        for item in nav_items:
            href_lower = item["href"].lower()
            text_lower = item["text"].lower()
            
            if "content" in href_lower or "conteúdo" in text_lower:
                sections["content"] = item["href"]
            elif "dropbox" in href_lower or "atividade" in text_lower or "assignment" in text_lower:
                sections["assignments"] = item["href"]
            elif "grades" in href_lower or "notas" in text_lower:
                sections["grades"] = item["href"]
            elif "quiz" in href_lower or "prova" in text_lower:
                sections["quizzes"] = item["href"]
        
        print(f"   Found sections: {[k for k, v in sections.items() if v]}")
        
        return sections
    
    def find_submissions(self):
        """Find submitted assignments (dropbox)"""
        print("\n📤 Looking for submissions...")
        
        # Navigate to dropbox/assignments if found
        # Look for submission links
        submission_links = self.page.query_selector_all("a[href*='dropbox'], a[href*='submission']")
        
        submissions = []
        for link in submission_links:
            text = link.text_content().strip()
            href = link.get_attribute("href") or ""
            submissions.append({"name": text, "url": href})
        
        print(f"   Found {len(submissions)} submission areas")
        return submissions
    
    def download_files_from_page(self):
        """Download all downloadable files from current page"""
        print("\n📥 Looking for downloadable files...")
        
        # File extensions to look for
        extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.txt']
        
        # Find all download links
        links = self.page.query_selector_all("a[href]")
        files_found = []
        
        for link in links:
            href = link.get_attribute("href") or ""
            text = link.text_content().strip()
            
            is_file = any(ext in href.lower() for ext in extensions)
            is_download = "download" in href.lower() or "attachment" in href.lower()
            
            if is_file or is_download:
                files_found.append({"text": text, "href": href})
        
        print(f"   Found {len(files_found)} files to download")
        
        # Click to download each
        for f in files_found[:20]:  # Limit to 20 files
            try:
                print(f"   Downloading: {f['text'][:40]}...")
                link = self.page.query_selector(f"a[href='{f['href']}']")
                if link:
                    link.click()
                    time.sleep(1)  # Wait for download to start
            except Exception as e:
                print(f"   ⚠️ Could not download: {e}")
        
        return files_found
    
    def classify_document(self, filename: str, content_hint: str = "") -> str:
        """Classify document type based on filename"""
        filename_lower = filename.lower()
        
        if any(x in filename_lower for x in ["gabarito", "answer", "resposta", "solução", "solucao"]):
            return "gabarito"
        elif any(x in filename_lower for x in ["prova", "exam", "test", "avaliação", "avaliacao", "p1", "p2", "p3", "a1", "a2", "a3"]):
            return "prova"
        elif any(x in filename_lower for x in ["resolução", "resolucao", "submission", "entrega", "trabalho"]):
            return "resolucao"
        elif any(x in filename_lower for x in ["nota", "grade", "result"]):
            return "resultado"
        else:
            return "outro"
    
    def organize_and_upload(self):
        """Organize downloaded files and upload to Prova AI"""
        print("\n" + "=" * 60)
        print("📂 ORGANIZING AND UPLOADING")
        print("=" * 60)
        
        # Create student (you)
        self.prova_ai.create_aluno("Otávio Bopp", "otavio.bopp@fgv.edu.br")
        
        # Process each downloaded file
        for doc in self.documents:
            path = Path(doc["path"])
            if not path.exists():
                continue
            
            filename = doc["filename"]
            course_name = doc.get("course", "Unknown Course")
            year = doc.get("year") or 2024
            
            print(f"\n📄 Processing: {filename}")
            
            # Classify document
            doc_type = self.classify_document(filename)
            print(f"   Type: {doc_type}")
            
            # Extract activity name from filename
            activity_match = re.search(r'(P\d|A\d|Prova\s*\d|Trabalho\s*\d|Atividade\s*\d)', filename, re.I)
            activity_name = activity_match.group() if activity_match else "Atividade 1"
            
            # Create matéria from course name
            materia_name = re.sub(r'\d{4}|\(.*\)|\[.*\]', '', course_name).strip()[:50]
            if not materia_name:
                materia_name = "Matéria FGV"
            
            materia_id = self.prova_ai.create_materia(materia_name)
            if not materia_id:
                continue
            
            # Create turma
            turma_name = f"{materia_name} {year}"
            turma_id = self.prova_ai.create_turma(turma_name, materia_id, year)
            if not turma_id:
                continue
            
            # Create atividade
            atividade_id = self.prova_ai.create_atividade(activity_name, turma_id)
            if not atividade_id:
                continue
            
            # Organize file locally
            org_dir = ORGANIZED_DIR / str(year) / materia_name / activity_name
            org_dir.mkdir(parents=True, exist_ok=True)
            
            # Rename file with type prefix
            new_name = f"{doc_type}_{filename}"
            org_path = org_dir / new_name
            
            import shutil
            shutil.copy(path, org_path)
            print(f"   Organized to: {org_path}")
            
            # Upload to Prova AI
            self.prova_ai.upload_document(
                org_path, 
                atividade_id, 
                self.prova_ai.aluno_id,
                tipo=doc_type
            )
    
    def run_full_scrape(self):
        """Run the complete scraping process"""
        print("\n" + "=" * 60)
        print("🚀 STARTING FULL FGV SCRAPE")
        print("=" * 60)
        
        # 1. Navigate and login
        self.navigate_to_eclass()
        
        # 2. Find all courses
        courses = self.find_courses()
        
        if not courses:
            print("\n⚠️ No courses found automatically.")
            print("   Let me try to explore the page structure...")
            self.explore_page_structure()
            return
        
        # 3. For each course
        for i, course in enumerate(courses):
            print(f"\n{'='*60}")
            print(f"📖 Course {i+1}/{len(courses)}: {course['name'][:50]}")
            print("=" * 60)
            
            self.current_course = course['name']
            self.current_year = course.get('year')
            
            if not course.get('url'):
                print("   ⚠️ No URL for this course, skipping")
                continue
            
            try:
                # Navigate to course
                sections = self.explore_course(course['url'])
                
                # Check assignments/dropbox
                if sections.get("assignments"):
                    print("\n   📋 Checking assignments...")
                    self.page.goto(sections["assignments"])
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(1)
                    self.download_files_from_page()
                
                # Check content
                if sections.get("content"):
                    print("\n   📚 Checking content...")
                    self.page.goto(sections["content"])
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(1)
                    self.download_files_from_page()
                
                # Check grades
                if sections.get("grades"):
                    print("\n   📊 Checking grades...")
                    self.page.goto(sections["grades"])
                    self.page.wait_for_load_state("networkidle")
                    time.sleep(1)
                    self.screenshot(f"grades_{i}")
                
            except Exception as e:
                print(f"   ⚠️ Error processing course: {e}")
                continue
        
        # 4. Organize and upload
        self.organize_and_upload()
        
        print("\n" + "=" * 60)
        print("✅ SCRAPING COMPLETE!")
        print("=" * 60)
        print(f"   Downloaded: {len(self.documents)} files")
        print(f"   Saved to: {ORGANIZED_DIR}")
    
    def explore_page_structure(self):
        """Explore page to understand structure"""
        print("\n🔍 Analyzing page structure...")
        
        html = self.page.content()
        
        # Save HTML for manual inspection
        html_path = SCREENSHOTS_DIR / "page_structure.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   Saved HTML to: {html_path}")
        
        # Find all interactive elements
        buttons = self.page.query_selector_all("button, [role='button']")
        links = self.page.query_selector_all("a[href]")
        
        print(f"   Buttons: {len(buttons)}")
        print(f"   Links: {len(links)}")
        
        # Print first 20 links
        print("\n   Top links:")
        for link in links[:20]:
            text = link.text_content().strip()[:40]
            href = (link.get_attribute("href") or "")[:50]
            if text:
                print(f"      - {text}: {href}")
        
        self.screenshot("structure_analysis")
    
    def close(self):
        """Clean up"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("\n👋 Browser closed.")


def main():
    scraper = FGVScraper()
    
    try:
        scraper.start()
        scraper.run_full_scrape()
        
        # Keep browser open for review
        print("\n⏰ Browser will stay open for 60 seconds for review...")
        time.sleep(60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
