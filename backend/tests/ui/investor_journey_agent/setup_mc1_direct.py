"""
MC-1 direct verification setup:
1. Close welcome modal
2. Navigate to atividade via JS
3. Directly call taskQueue.addBackendTask() with a test task to verify sidebar renders
"""
import asyncio

async def setup():
    # Wait for page
    await page.wait_for_load_state('networkidle', timeout=15000)

    # 1. Close welcome modal
    await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
    await asyncio.sleep(0.5)

    # 2. Navigate to atividade via JS
    await page.evaluate("typeof showAtividade === 'function' && showAtividade('d67ec59d4a214213')")
    await asyncio.sleep(1.5)

    # 3. Open the TAREFAS panel
    await page.evaluate("""
        const panel = document.getElementById('task-panel');
        if (panel) panel.classList.add('show');
    """)
    await asyncio.sleep(0.3)

    # 4. Simulate pipeline trigger: directly call addBackendTask (same as F4-T1 code)
    result = await page.evaluate("""
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

        if (typeof taskQueue !== 'undefined' && typeof taskQueue.addBackendTask === 'function') {
            taskQueue.addBackendTask(testTaskId, initialState);
            return { success: true, task_id: testTaskId };
        } else {
            return { success: false, error: 'taskQueue or addBackendTask not found' };
        }
    """)
    print(f"[Setup] addBackendTask result: {result}")
    await asyncio.sleep(0.5)

    print("[Setup] MC-1 direct simulation complete — TAREFAS panel should show task")

asyncio.get_event_loop().run_until_complete(setup())
