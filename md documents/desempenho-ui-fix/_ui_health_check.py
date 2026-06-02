#!/usr/bin/env python3
"""UI health check after fb9c74d deploy.

Takes screenshots of:
  1. Home / matéria list
  2. Turma 2026-1 view (atividades + tem_correcao/tem_relatorio indicators)
  3. Atividade Lista0 — desempenho tab (live progress panel)
  4. Atividade Lista0 — students panel
  5. Modal "Executar pipeline para 1 aluno" populated for Alvaro+gem3flash001
  6. Click on one student that has full pipeline (Alvaro) → resultado modal

Reports DOM state for UI checks (button enabled, dropdowns populated, etc).
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"
MATERIA = "57861d16958965d2"
TURMA = "3f3ab03dfe783f30"
ATIVIDADE = "126e8b5ad7dd6d59"
ALVARO = "40ab839a5340e39a"
OUT = Path(__file__).parent / f"_health_{datetime.now():%Y%m%d_%H%M%S}"


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"output: {OUT}", flush=True)
    findings = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()
        page.on("pageerror", lambda e: findings.append(f"JS error: {e}"))
        page.on("console", lambda m: m.type == "error" and findings.append(f"console.error: {m.text[:200]}"))

        # 1. Home
        await page.goto(URL, wait_until="domcontentloaded")
        try: await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception: pass
        await asyncio.sleep(1.0)
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
        await asyncio.sleep(0.3)
        await page.screenshot(path=str(OUT / "01_home.png"), full_page=True)
        print(f"  [1] home — title='{await page.title()}'", flush=True)

        # 2. Materia → Turma
        await page.evaluate(f"showMateria('{MATERIA}')")
        await asyncio.sleep(0.8)
        await page.evaluate(f"showTurma('{TURMA}')")
        await asyncio.sleep(1.5)
        await page.screenshot(path=str(OUT / "02_turma.png"), full_page=True)
        t_count = await page.evaluate("document.querySelectorAll('.atividade-card, [data-atividade-id]').length")
        print(f"  [2] turma — atividade-cards={t_count}", flush=True)

        # 3. Desempenho tab
        await page.evaluate("showTurmaTab && showTurmaTab('desempenho')")
        await asyncio.sleep(4.0)
        await page.screenshot(path=str(OUT / "03_desempenho_tab.png"), full_page=True)
        des_info = await page.evaluate("""() => {
            const panel = document.getElementById('desempenho-progress-panel');
            const gen = document.querySelector('[id^="desempenho-generate-area"]');
            const btn = document.querySelector('[id^="btn-desempenho-generate"]');
            return {
                panel_present: !!panel,
                panel_text_len: panel ? panel.innerText.length : null,
                generate_btn_text: btn ? btn.textContent.trim() : null,
                generate_btn_disabled: btn ? btn.disabled : null,
                generate_area_text_snippet: gen ? gen.innerText.slice(0, 400) : null,
            };
        }""")
        print(f"  [3] desempenho: {des_info}", flush=True)

        # 4. Atividade Lista0 view via showAtividade (if available)
        await page.evaluate(f"if (typeof showAtividade === 'function') showAtividade('{ATIVIDADE}')")
        await asyncio.sleep(2.0)
        await page.screenshot(path=str(OUT / "04_atividade.png"), full_page=True)
        # Per-aluno indicators
        alunos_state = await page.evaluate("""() => {
            const rows = Array.from(document.querySelectorAll('[data-aluno-id]'));
            const items = rows.slice(0, 5).map(r => ({
                id: r.dataset.alunoId,
                text: (r.innerText || '').slice(0, 120),
            }));
            return { row_count: rows.length, items };
        }""")
        print(f"  [4] atividade — alunos rows: {alunos_state.get('row_count')}", flush=True)
        for it in alunos_state.get("items", [])[:3]:
            print(f"      {it['id']}  {it['text']}", flush=True)

        # 5. Modal pipeline-completo (aluno mode) for Alvaro + Gemini
        await page.evaluate(f"(async () => {{ await ensureAtividadeData('{ATIVIDADE}'); }})()")
        await asyncio.sleep(0.8)
        await page.evaluate(f"(async () => {{ await openModalPipelineCompleto('{ATIVIDADE}', 'aluno'); }})()")
        await asyncio.sleep(2.0)
        # Set alvaro + gem3flash001
        await page.evaluate(f"document.getElementById('input-pipeline-aluno').value = '{ALVARO}'")
        await page.evaluate("document.getElementById('input-pipeline-provider-default').value = 'gem3flash001'")
        await asyncio.sleep(0.3)
        await page.screenshot(path=str(OUT / "05_modal_pipeline.png"), full_page=True)
        modal_info = await page.evaluate("""() => {
            const m = document.getElementById('modal-pipeline-completo');
            return {
                active: m ? m.classList.contains('active') : false,
                aluno_options: document.querySelectorAll('#input-pipeline-aluno option').length,
                provider_options: document.querySelectorAll('#input-pipeline-provider-default option').length,
                steps_checked: document.querySelectorAll('.pipeline-step-checkbox:checked').length,
                btn_exec_disabled: document.getElementById('btn-executar-pipeline')?.disabled,
            };
        }""")
        print(f"  [5] modal: {modal_info}", flush=True)

        # 6. Close modal + visualizar Alvaro's relatorio (from previous successful run)
        await page.evaluate("if (typeof closeModal === 'function') closeModal('modal-pipeline-completo')")
        await asyncio.sleep(0.5)
        # Get Alvaro's relatorio doc id via API and try visualizarDocumento
        # The relatorio docs were saved at 20:30 UTC today
        alvaro_rel_id = "8e537097449ee7de"  # known from earlier audit
        await page.evaluate(f"if (typeof visualizarDocumento === 'function') visualizarDocumento('{alvaro_rel_id}')")
        await asyncio.sleep(3.0)
        await page.screenshot(path=str(OUT / "06_relatorio_alvaro_visualizar.png"), full_page=True)
        visu_info = await page.evaluate("""() => {
            const modal = document.querySelector('.modal-overlay.active');
            return {
                modal_active: !!modal,
                modal_text_len: modal ? modal.innerText.length : 0,
                modal_text_snippet: modal ? modal.innerText.slice(0, 500) : null,
            };
        }""")
        print(f"  [6] visualizar Alvaro relatorio: {visu_info}", flush=True)

        await browser.close()
    print("\n--- FINDINGS ---", flush=True)
    if findings:
        for f in findings[:20]:
            print(f"  ! {f}", flush=True)
    else:
        print("  (no JS errors or console.error captured)", flush=True)
    print(f"\nScreenshots: {OUT}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
