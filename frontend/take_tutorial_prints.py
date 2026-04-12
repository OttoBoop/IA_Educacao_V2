"""
Tira prints de todas as áreas do tutorial para usar como imagens nos slides.
Espera o deploy estar live (meta tag) antes de começar.
Salva em frontend/tutorial-images-v2/new/

Uso: python frontend/take_tutorial_prints.py
"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time
import sys

SITE = "https://ia-educacao-v2.onrender.com"
EXPECTED_META = None  # Skip meta check — verify content directly
OUTPUT_DIR = Path(__file__).parent / "tutorial-images-v2" / "new"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def wait_for_deploy(page, timeout=600):
    """Poll until the expected meta tag appears."""
    print(f"[*] Esperando deploy {EXPECTED_META}...")
    start = time.time()
    while time.time() - start < timeout:
        page.reload(wait_until="networkidle")
        meta = page.evaluate("document.querySelector('meta[name=novocr-deploy]')?.content || 'NOT_FOUND'")
        if meta == EXPECTED_META:
            print(f"[OK] Deploy {meta} live após {int(time.time()-start)}s")
            return True
        print(f"  {int(time.time()-start)}s — meta={meta}")
        time.sleep(15)
    print(f"[TIMEOUT] Deploy não chegou em {timeout}s")
    return False

def screenshot(page, name, description=""):
    """Take a cropped screenshot."""
    path = OUTPUT_DIR / f"{name}.png"
    page.screenshot(path=str(path))
    print(f"[📸] {name}: {description}")
    return path

def take_prints():
    print(f"[*] Script de prints — salvando em {OUTPUT_DIR}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            device_scale_factor=2
        )
        page = context.new_page()

        try:
            page.goto(SITE, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(2000)

            # Check if new content is live (skip meta check)
            has_modules = page.evaluate("typeof tutorialContent.modules !== 'undefined'")
            if has_modules:
                print("[OK] Conteúdo novo (modules) detectado no site!")
            else:
                print("[!] Conteúdo antigo — módulos não encontrados. Tirando prints assim mesmo.")

            # === PRINTS DA CAMADA 1 ===
            print("\n=== CAMADA 1 — Tutorial básico ===")

            # Fechar welcome se aberto
            page.evaluate("document.getElementById('modal-welcome')?.classList.remove('active')")
            page.wait_for_timeout(300)

            # Print 1: Banner gritão (reabrir)
            page.evaluate("localStorage.removeItem('novocr-welcomed-v2'); location.reload()")
            page.wait_for_timeout(3000)
            welcome = page.query_selector("#modal-welcome.active")
            if welcome:
                screenshot(page, "banner-scream", "Banner gritão de primeiro acesso")

            # Fechar banner
            page.evaluate("closeWelcome()")
            page.wait_for_timeout(300)

            # Print 2: Dashboard
            screenshot(page, "dashboard", "Dashboard principal com matérias")

            # Print 3: Modal Nova Matéria
            page.evaluate("openModal('modal-materia')")
            page.wait_for_timeout(500)
            screenshot(page, "modal-nova-materia", "Modal de criar matéria com tooltips")
            page.evaluate("closeModal('modal-materia')")
            page.wait_for_timeout(300)

            # Print 4: Modal Nova Turma
            page.evaluate("openModal('modal-turma')")
            page.wait_for_timeout(500)
            screenshot(page, "modal-nova-turma", "Modal de criar turma")
            page.evaluate("closeModal('modal-turma')")
            page.wait_for_timeout(300)

            # Print 5: Modal Adicionar Aluno
            page.evaluate("openModal('modal-aluno')")
            page.wait_for_timeout(500)
            screenshot(page, "modal-adicionar-aluno", "Modal de adicionar aluno")
            page.evaluate("closeModal('modal-aluno')")
            page.wait_for_timeout(300)

            # Print 6: Modal Nova Atividade
            page.evaluate("openModal('modal-atividade')")
            page.wait_for_timeout(500)
            screenshot(page, "modal-nova-atividade", "Modal de criar atividade")
            page.evaluate("closeModal('modal-atividade')")
            page.wait_for_timeout(300)

            # === PRINTS DO TUTORIAL ===
            print("\n=== TUTORIAL — Todos os passos básicos ===")
            page.evaluate("openTutorial()")
            page.wait_for_timeout(500)

            # Tirar print de cada passo
            steps_count = page.evaluate("tutorialContent.basic?.length || tutorialContent.quick?.length")
            print(f"Tutorial tem {steps_count} passos básicos")

            for i in range(steps_count):
                page.evaluate(f"goToTutorialStep({i})")
                page.wait_for_timeout(400)
                screenshot(page, f"tutorial-basic-{i+1:02d}", f"Passo {i+1}/{steps_count}")

            # === PRINTS DOS MÓDULOS ===
            print("\n=== MÓDULOS AVANÇADOS ===")
            modules = page.evaluate("Object.keys(tutorialContent.modules)")
            print(f"Módulos: {modules}")

            for mod in modules:
                mod_steps = page.evaluate(f"tutorialContent.modules['{mod}'].length")
                print(f"\n  Módulo '{mod}' ({mod_steps} passos):")
                page.evaluate(f"openTutorialModule('{mod}')")
                page.wait_for_timeout(400)

                for j in range(mod_steps):
                    page.evaluate(f"goToTutorialStep({j})")
                    page.wait_for_timeout(400)
                    screenshot(page, f"module-{mod}-{j+1:02d}", f"{mod} passo {j+1}/{mod_steps}")

            # Voltar ao hub
            page.evaluate("closeTutorialModule()")
            page.wait_for_timeout(300)

            # === PRINTS DA UI (para módulos que precisam) ===
            print("\n=== UI — Áreas do app ===")

            # Fechar tutorial
            page.evaluate("closeTutorial()")
            page.wait_for_timeout(300)

            # Chat
            page.evaluate("showChat()")
            page.wait_for_timeout(1000)
            screenshot(page, "chat-filtros", "Chat com painel de filtros")

            # Sidebar com matérias
            screenshot(page, "sidebar-materias", "Sidebar com árvore de matérias")

            # Navegar para uma matéria se existir
            materias = page.evaluate("document.querySelectorAll('[onclick*=\"showMateria\"]').length")
            if materias > 0:
                page.evaluate("document.querySelector('[onclick*=\"showMateria\"]').click()")
                page.wait_for_timeout(1000)
                screenshot(page, "view-materia", "View de matéria")

            print(f"\n{'='*50}")
            print(f"[OK] {len(list(OUTPUT_DIR.glob('*.png')))} prints salvos em {OUTPUT_DIR}")

        except Exception as e:
            print(f"\n[ERRO] {e}")
            screenshot(page, "error", f"Erro: {e}")
            import traceback
            traceback.print_exc()
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(take_prints() or 0)
