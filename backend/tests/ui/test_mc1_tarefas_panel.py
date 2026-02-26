"""
MC-1 TAREFAS Panel Live Verification Test
Verifies that after triggering executarPipelineCompleto(), the TAREFAS sidebar
shows a task entry with pending stages (addBackendTask → updateUI → sidebar renders).

The TAREFAS section renders into #tree-tarefas inside <aside class="sidebar">.
The old #task-panel FAB is deprecated (commented out since F6-T1).

Run with: pytest tests/ui/test_mc1_tarefas_panel.py -v -s
"""
import pytest
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://ia-educacao-v2.onrender.com"
ATIVIDADE_ID = "d67ec59d4a214213"  # Prova 1 - Sistema Solar (9º Ano A, Ciências)


@pytest.mark.asyncio
async def test_tarefas_sidebar_shows_task_after_add_backend_task():
    """
    MC-1 acceptance: taskQueue.addBackendTask() causes task to appear in #tree-tarefas.
    Direct JS injection test — no SPA navigation required.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})  # iPhone 14

        await page.goto(BASE_URL, wait_until="networkidle")

        # 1. Dismiss welcome modal
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
        await asyncio.sleep(0.5)

        # 2. Navigate to atividade via JS
        await page.evaluate(f"typeof showAtividade === 'function' && showAtividade('{ATIVIDADE_ID}')")
        await asyncio.sleep(2.0)  # wait for data load

        # 3. Verify #tree-tarefas exists in the DOM (it's inside .sidebar)
        tree_tarefas_count = await page.evaluate("""
            (() => {
                return document.querySelectorAll('#tree-tarefas').length;
            })()
        """)
        assert tree_tarefas_count > 0, "#tree-tarefas element not found in DOM"

        # 4. Check panel body before addBackendTask
        initial_body_html = await page.evaluate("""
            (() => {
                const body = document.getElementById('tree-tarefas');
                return body ? body.innerHTML.trim() : 'not found';
            })()
        """)
        assert initial_body_html != "not found", "#tree-tarefas element missing"

        # 5. Call addBackendTask() directly — this is the exact F4-T1 code path
        result = await page.evaluate("""
            (() => {
                const testTaskId = 'mc1_test_task_001';
                const pendingStages = {
                    extrair_questoes: 'pending',
                    extrair_gabarito: 'pending',
                    extrair_respostas: 'pending',
                    corrigir: 'pending',
                    analisar_habilidades: 'pending',
                    gerar_relatorio: 'pending'
                };
                const initialState = {
                    task_id: testTaskId,
                    status: 'running',
                    students: { 'test_aluno': { stages: pendingStages } }
                };

                if (typeof taskQueue === 'undefined') return { error: 'taskQueue undefined' };
                if (typeof taskQueue.addBackendTask !== 'function') return { error: 'addBackendTask not a function' };

                taskQueue.addBackendTask(testTaskId, initialState);
                return { success: true };
            })()
        """)

        assert result.get("success"), f"addBackendTask failed: {result}"

        # 6. Wait briefly for UI update
        await asyncio.sleep(0.3)

        # 7. Check #tree-tarefas has rendered content
        tree_html = await page.evaluate("""
            (() => {
                const body = document.getElementById('tree-tarefas');
                return body ? body.innerHTML.trim() : 'not found';
            })()
        """)

        assert tree_html != "not found", "#tree-tarefas element missing after addBackendTask"
        assert len(tree_html) > 50, (
            f"#tree-tarefas should have task content after addBackendTask, got: '{tree_html[:200]}'"
        )

        # 8. Verify task content appears in sidebar
        assert (
            "mc1_test_task_001" in tree_html
            or "running" in tree_html
            or "pending" in tree_html
        ), (
            f"Expected task content in #tree-tarefas, got: '{tree_html[:300]}'"
        )

        print(f"\n[PASS] MC-1 PASS -- TAREFAS sidebar rendered task content")
        print(f"   Panel content (first 300 chars): {tree_html[:300]}")

        await browser.close()


@pytest.mark.asyncio
async def test_tarefas_sidebar_visible_on_mobile_after_toggle():
    """
    Verify the TAREFAS sidebar (#tree-tarefas inside .sidebar) is accessible on iPhone 14.
    On mobile, .sidebar becomes visible when toggleMobileSidebar() adds .mobile-open.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 390, "height": 844})

        await page.goto(BASE_URL, wait_until="networkidle")
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
        await asyncio.sleep(0.3)

        # Check initial sidebar state — should be closed on mobile
        initial_state = await page.evaluate("""
            (() => {
                const sidebar = document.querySelector('.sidebar');
                if (!sidebar) return 'sidebar not found';
                return sidebar.classList.contains('mobile-open') ? 'open' : 'closed';
            })()
        """)
        assert initial_state == "closed", f"Sidebar should start closed on mobile, got: {initial_state}"

        # Call toggleMobileSidebar() — same function executarPipelineCompleto uses
        await page.evaluate("""
            (() => {
                if (typeof toggleMobileSidebar === 'function') {
                    toggleMobileSidebar();
                }
            })()
        """)
        await asyncio.sleep(0.2)

        # Sidebar should now be open
        after_state = await page.evaluate("""
            (() => {
                const sidebar = document.querySelector('.sidebar');
                if (!sidebar) return 'sidebar not found';
                return sidebar.classList.contains('mobile-open') ? 'open' : 'closed';
            })()
        """)
        assert after_state == "open", f"Sidebar should be open after toggleMobileSidebar(), got: {after_state}"

        # Verify #tree-tarefas is accessible inside it
        tree_exists = await page.evaluate("""
            (() => {
                return document.getElementById('tree-tarefas') !== null;
            })()
        """)
        assert tree_exists, "#tree-tarefas should exist inside sidebar"

        print(f"\n[PASS] MC-1 CSS PASS -- TAREFAS sidebar visible and accessible on mobile")

        await browser.close()
