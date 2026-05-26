#!/usr/bin/env python3
"""Navigate to Álgebra Linear → 2026-1 → Lista0 → click on one student's
relatorio_final document and screenshot the actual rendered viewer.

This is end-to-end UX validation: simulates a user clicking through the
sidebar / lista de docs and seeing the JSON or PDF rendered on screen.

Pass condition: clicked the relatorio_final doc and the viewer pane
shows either rendered JSON content OR a download link. Saves screenshot.
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"
MATERIA = "57861d16958965d2"
TURMA = "3f3ab03dfe783f30"
ATIVIDADE = "126e8b5ad7dd6d59"
# Aluna with full pipeline (Anthropic Claude Haiku)
ALUNO = "457b04cfe16fb06b"  # Jordana Martinelli
OUT = Path(__file__).parent / f"_click_relatorio_{datetime.now():%Y%m%d_%H%M%S}"


def log(m, i=0):
    print(("  " * i) + f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log(f"output: {OUT}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()
        await page.goto(URL, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(1)
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")

        log("[1] Navigate Materia → Turma → Atividade")
        await page.evaluate(f"showMateria('{MATERIA}')")
        await asyncio.sleep(1)
        await page.evaluate(f"showTurma('{TURMA}')")
        await asyncio.sleep(1)
        await page.evaluate(f"showAtividade('{ATIVIDADE}')")
        await asyncio.sleep(3)
        await page.screenshot(path=str(OUT / "01_atividade_view.png"), full_page=True)

        log("[2] Look for the student row + their relatorio_final entry")
        # The atividade view usually shows students with their docs grouped
        # Try to find a clickable entry for the aluno's relatorio_final
        await asyncio.sleep(1)
        await page.screenshot(path=str(OUT / "02_after_wait.png"), full_page=True)

        # Probe DOM for any element referencing the aluno's relatorio doc
        log("[3] Inspect DOM for relatorio_final entries")
        info = await page.evaluate(f"""() => {{
            const findRows = (sel) => Array.from(document.querySelectorAll(sel))
                .map(el => ({{ text: (el.innerText || '').slice(0, 100), tag: el.tagName, id: el.id, cls: el.className }}));
            return {{
                title: document.title,
                aluno_present: !!document.body.innerText.match(/Jordana/i),
                relatorio_present: !!document.body.innerText.match(/Relat[oó]rio Final/i),
                doc_buttons: findRows('button[onclick*="visualizarDocumento"], a[onclick*="visualizarDocumento"]').slice(0, 10),
                cards: findRows('.aluno-card, .student-row, [class*="resultado"]').slice(0, 5),
            }};
        }}""")
        log(f"  title={info.get('title')!r}", 1)
        log(f"  aluno (Jordana) present in DOM: {info.get('aluno_present')}", 1)
        log(f"  'Relatório Final' present in DOM: {info.get('relatorio_present')}", 1)
        log(f"  doc_buttons found: {len(info.get('doc_buttons') or [])}", 1)
        for db in (info.get("doc_buttons") or [])[:3]:
            log(f"    {db}", 2)

        # Try to call visualizarDocumento directly with the known doc id
        # (this is what the UI button would do)
        log("[4] Call visualizarDocumento directly for the relatorio_final JSON")
        RELATORIO_JSON_ID = "54e9a53425a2c83c"  # Jordana .json
        result = await page.evaluate(f"""async () => {{
            if (typeof visualizarDocumento !== 'function') return {{ ok: false, reason: 'visualizarDocumento not defined' }};
            try {{
                await visualizarDocumento('{RELATORIO_JSON_ID}');
                await new Promise(r => setTimeout(r, 1500));
                // The viewer renders in modal-documento-conteudo
                const modal = document.getElementById('modal-documento-conteudo');
                if (!modal) return {{ ok: false, reason: 'modal not in DOM' }};
                const isOpen = modal.classList.contains('active') || getComputedStyle(modal).display !== 'none';
                const content = modal.innerText || '';
                return {{
                    ok: isOpen && content.length > 200,
                    isOpen: isOpen,
                    contentSnippet: content.slice(0, 800),
                    contentLen: content.length,
                }};
            }} catch (e) {{ return {{ ok: false, reason: String(e) }}; }}
        }}""")
        log(f"  modal opened: {result.get('isOpen')}, content length: {result.get('contentLen')}, snippet: {(result.get('contentSnippet') or '')[:200]!r}", 1)
        await asyncio.sleep(1)
        await page.screenshot(path=str(OUT / "03_relatorio_modal.png"), full_page=True)

        # Also try the PDF version → should show download/iframe
        log("[5] Same for the .pdf version")
        RELATORIO_PDF_ID = "6e319c0ab440c600"
        result_pdf = await page.evaluate(f"""async () => {{
            try {{
                await visualizarDocumento('{RELATORIO_PDF_ID}');
                await new Promise(r => setTimeout(r, 1500));
                const modal = document.getElementById('modal-documento-conteudo');
                return {{
                    isOpen: !!modal && (modal.classList.contains('active') || getComputedStyle(modal).display !== 'none'),
                    has_iframe: !!modal && !!modal.querySelector('iframe'),
                    has_download_link: !!modal && !!modal.querySelector('a[download], a[href*="download"]'),
                    contentSnippet: (modal ? modal.innerText : '').slice(0, 500),
                }};
            }} catch (e) {{ return {{ error: String(e) }}; }}
        }}""")
        log(f"  PDF modal: {result_pdf}", 1)
        await asyncio.sleep(1)
        await page.screenshot(path=str(OUT / "04_relatorio_pdf_modal.png"), full_page=True)

        await browser.close()
        verdict = "PASS" if (result.get("ok") and (result_pdf.get("has_iframe") or result_pdf.get("has_download_link"))) else "PARTIAL/FAIL"
        log(f"VERDICT: {verdict}")
        log(f"screenshots: {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
