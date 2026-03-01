"""
MC-1 Desempenho Tab UX Overhaul verification setup.

Navigates directly to the matéria-level Desempenho tab via JS,
bypassing SPA click timeouts that caused the previous journey to fail.

Receives 'page' and 'browser' in local namespace from journey runner.
"""
import asyncio
import nest_asyncio

nest_asyncio.apply()

# Entity IDs from live API (/api/navegacao/arvore)
MATERIA_ID = "f95445ace30e7dc5"       # Cálculo 1
TURMA_ID = "6b5dc44c08aaf375"         # EPGE 2021
ATIVIDADE_ID = "effad48d128c7083"     # A1 - Cálculo 1


async def _setup():
    # 1. Wait for initial page load
    await page.wait_for_load_state("networkidle", timeout=15000)
    print("[Setup] Page loaded")

    # 2. Dismiss welcome modal
    await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
    await asyncio.sleep(0.5)
    print("[Setup] Welcome dismissed")

    # 3. Navigate to matéria Cálculo 1
    await page.evaluate(f"typeof showMateria === 'function' && showMateria('{MATERIA_ID}')")
    await asyncio.sleep(2.0)
    print("[Setup] Navigated to Cálculo 1 matéria")

    # 4. Click the Desempenho tab via JS (find the tab element and click it)
    clicked = await page.evaluate("""
        (() => {
            // Find all elements with onclick containing 'desempenho'
            const tabs = document.querySelectorAll('[onclick]');
            for (const tab of tabs) {
                const onclick = tab.getAttribute('onclick') || '';
                if (onclick.toLowerCase().includes("materiatab") && onclick.toLowerCase().includes("desempenho")) {
                    tab.click();
                    return 'clicked_materia_desempenho_tab';
                }
            }
            // Fallback: try to find tab by text content
            const allTabs = document.querySelectorAll('.tab, .nav-tab, [role="tab"]');
            for (const tab of allTabs) {
                if (tab.textContent.includes('Desempenho')) {
                    tab.click();
                    return 'clicked_desempenho_by_text';
                }
            }
            return 'tab_not_found';
        })()
    """)
    print(f"[Setup] Tab click result: {clicked}")
    await asyncio.sleep(2.0)

    print("[Setup] Ready on matéria Desempenho tab — agent can now verify")


asyncio.get_event_loop().run_until_complete(_setup())
