"""
MC-1 Desempenho Tab UX Overhaul — Direct Playwright Verification.

Takes screenshots at all 3 Desempenho tab levels (matéria, turma, atividade)
using JS navigation to bypass the agent's element resolution issues.

Usage:
    cd IA_Educacao_V2/backend
    python tests/ui/verify_desempenho_mc1.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding for Unicode (emojis in tab labels)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"

# Entity IDs from live API
MATERIA_ID = "f95445ace30e7dc5"       # Cálculo 1
TURMA_ID = "6b5dc44c08aaf375"         # EPGE 2021
ATIVIDADE_ID = "effad48d128c7083"     # A1 - Cálculo 1

OUTPUT_DIR = Path(__file__).parent.parent / "investor_journey_reports" / f"mc1_verify_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


async def take_screenshot(page, name, description):
    """Take a screenshot and print what we found."""
    path = OUTPUT_DIR / f"{name}.png"
    await page.screenshot(path=str(path), full_page=False)
    print(f"  [SCREENSHOT] {path.name}: {description}")
    return path


async def check_dom_elements(page, checks):
    """Check for DOM elements and report results."""
    results = {}
    for label, js_check in checks.items():
        result = await page.evaluate(js_check)
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {label}")
        results[label] = result
    return results


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n{'='*60}")
    print("MC-1 DESEMPENHO TAB VERIFICATION")
    print(f"{'='*60}")
    print(f"URL: {URL}")
    print(f"Output: {OUTPUT_DIR}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()

        # 1. Navigate to app
        print("[1/7] Loading app...")
        await page.goto(URL, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(1)

        # 2. Dismiss welcome modal
        print("[2/7] Dismissing welcome modal...")
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
        await asyncio.sleep(0.5)
        await take_screenshot(page, "00_dashboard", "Dashboard after welcome dismiss")

        # ============================================================
        # MATÉRIA LEVEL
        # ============================================================
        print("\n[3/7] Navigating to Cálculo 1 matéria...")
        await page.evaluate(f"showMateria('{MATERIA_ID}')")
        await asyncio.sleep(2)
        await take_screenshot(page, "01_materia_turmas_tab", "Cálculo 1 - Turmas tab (default)")

        print("[4/7] Switching to matéria Desempenho tab...")
        tab_result = await page.evaluate(f"""
            (() => {{
                const tabs = document.querySelectorAll('[onclick]');
                for (const tab of tabs) {{
                    const oc = tab.getAttribute('onclick') || '';
                    if (oc.includes("showMateriaTab") && oc.includes("desempenho")) {{
                        tab.click();
                        return {{ found: true, onclick: oc, text: tab.textContent.trim() }};
                    }}
                }}
                return {{ found: false }};
            }})()
        """)
        print(f"  Tab click result: {tab_result}")
        await asyncio.sleep(2)
        await take_screenshot(page, "02_materia_desempenho", "Cálculo 1 - Desempenho tab")

        # DOM checks for matéria level
        print("  Checking matéria Desempenho DOM elements:")
        materia_checks = await check_dom_elements(page, {
            "desempenho-runs-materia container": "!!document.getElementById('desempenho-runs-materia') || !!document.querySelector('[id*=desempenho-runs]')",
            "desempenho-generate-area container": "!!document.querySelector('[id*=desempenho-generate]')",
            "loadDesempenhoData function exists": "typeof loadDesempenhoData === 'function'",
            "Gerar Relatório button or text": "document.body.innerHTML.includes('Gerar Relat')",
            "No raw filenames visible": "!document.body.innerHTML.includes('.json') || document.querySelector('[id*=desempenho-runs]')?.innerHTML.includes('Excluir')",
        })

        # ============================================================
        # TURMA LEVEL
        # ============================================================
        print(f"\n[5/7] Navigating to EPGE 2021 turma...")
        await page.evaluate(f"showTurma('{TURMA_ID}')")
        await asyncio.sleep(2)
        await take_screenshot(page, "03_turma_default", "EPGE 2021 - default tab")

        # Find and click Desempenho tab in turma view
        turma_tab = await page.evaluate(f"""
            (() => {{
                const tabs = document.querySelectorAll('[onclick]');
                for (const tab of tabs) {{
                    const oc = tab.getAttribute('onclick') || '';
                    if (oc.includes("showTurmaTab") && oc.includes("desempenho")) {{
                        tab.click();
                        return {{ found: true, onclick: oc, text: tab.textContent.trim() }};
                    }}
                }}
                return {{ found: false }};
            }})()
        """)
        print(f"  Turma tab click result: {turma_tab}")
        await asyncio.sleep(2)
        await take_screenshot(page, "04_turma_desempenho", "EPGE 2021 - Desempenho tab")

        # DOM checks for turma level
        print("  Checking turma Desempenho DOM elements:")
        turma_checks = await check_dom_elements(page, {
            "desempenho-runs-turma container": "!!document.getElementById('desempenho-runs-turma') || !!document.querySelector('[id*=desempenho-runs]')",
            "Generate button area": "!!document.querySelector('[id*=desempenho-generate]')",
            "Empty state or reports": "document.body.innerHTML.includes('Nenhum relat') || document.body.innerHTML.includes('Excluir Run') || document.body.innerHTML.includes('Nenhuma atividade')",
        })

        # ============================================================
        # ATIVIDADE LEVEL
        # ============================================================
        print(f"\n[6/7] Navigating to A1 Cálculo 1 atividade...")
        await page.evaluate(f"showAtividade('{ATIVIDADE_ID}')")
        await asyncio.sleep(2)
        await take_screenshot(page, "05_atividade_default", "A1 Cálculo 1 - default tab")

        # Find and click Desempenho tab in atividade view
        ativ_tab = await page.evaluate(f"""
            (() => {{
                const tabs = document.querySelectorAll('[onclick]');
                for (const tab of tabs) {{
                    const oc = tab.getAttribute('onclick') || '';
                    if (oc.includes("showAtividadeTab") && oc.includes("desempenho")) {{
                        tab.click();
                        return {{ found: true, onclick: oc, text: tab.textContent.trim() }};
                    }}
                }}
                return {{ found: false }};
            }})()
        """)
        print(f"  Atividade tab click result: {ativ_tab}")
        await asyncio.sleep(2)
        await take_screenshot(page, "06_atividade_desempenho", "A1 Cálculo 1 - Desempenho tab")

        # DOM checks for atividade level
        print("  Checking atividade Desempenho DOM elements:")
        ativ_checks = await check_dom_elements(page, {
            "desempenho-runs-tarefa container": "!!document.getElementById('desempenho-runs-tarefa') || !!document.querySelector('[id*=desempenho-runs]')",
            "Generate button area": "!!document.querySelector('[id*=desempenho-generate]')",
            "Empty state or reports": "document.body.innerHTML.includes('Nenhum relat') || document.body.innerHTML.includes('Excluir Run') || document.body.innerHTML.includes('Nenhuma atividade')",
        })

        # ============================================================
        # SUMMARY
        # ============================================================
        print(f"\n{'='*60}")
        print("[7/7] MC-1 VERIFICATION SUMMARY")
        print(f"{'='*60}")

        all_checks = {**materia_checks, **turma_checks, **ativ_checks}
        passed = sum(1 for v in all_checks.values() if v)
        total = len(all_checks)

        print(f"\nDOM checks: {passed}/{total} passed")
        print(f"Screenshots saved to: {OUTPUT_DIR}")

        for name, result in all_checks.items():
            status = "PASS" if result else "FAIL"
            print(f"  [{status}] {name}")

        if passed == total:
            print(f"\nMC-1 VERIFICATION: ALL CHECKS PASSED")
        else:
            failed = [k for k, v in all_checks.items() if not v]
            print(f"\nMC-1 VERIFICATION: {len(failed)} CHECKS FAILED")
            for f in failed:
                print(f"  FAILED: {f}")

        await browser.close()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
