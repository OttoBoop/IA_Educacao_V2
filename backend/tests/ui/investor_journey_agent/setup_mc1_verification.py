"""
MC-1 setup script: navigate directly to atividade pipeline page and open TAREFAS panel.
This script bypasses the SPA navigation which causes timeouts on mobile viewports.

Receives 'page' and 'browser' in local namespace from journey runner.
"""
import asyncio

async def setup():
    # 1. Wait for page to load
    await page.wait_for_load_state('networkidle', timeout=15000)

    # 2. Close welcome modal via JS (if present)
    await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
    await asyncio.sleep(0.5)

    # 3. Navigate directly to atividade 'Prova 1 - Sistema Solar' (9º Ano A, Ciências)
    #    Activity ID from previous journey run: d67ec59d4a214213
    await page.evaluate("typeof showAtividade === 'function' && showAtividade('d67ec59d4a214213')")
    await asyncio.sleep(1.0)

    # 4. Scroll to Pipeline section within the atividade
    await page.evaluate("""
        // Scroll to find pipeline section
        const pipelineSection = document.querySelector('.pipeline-section, [data-section="pipeline"], #pipeline-section');
        if (pipelineSection) pipelineSection.scrollIntoView();
    """)
    await asyncio.sleep(0.5)

    # 5. Open TAREFAS panel so it's visible for the agent
    await page.evaluate("""
        const panel = document.getElementById('task-panel');
        if (panel) panel.classList.add('show');
    """)
    await asyncio.sleep(0.3)

    print("[Setup] Navigation complete: on atividade page, TAREFAS panel open")

asyncio.get_event_loop().run_until_complete(setup())
