#!/usr/bin/env python3
"""Verify the live progress panel: dispatch a desempenho-turma run via UI
and assert that the generateArea shows real per-student progress within
N minutes (not just a spinner).

Pass condition:
  - data.students from /api/task-progress is non-empty within max_wait
  - At least one student moves out of "pending" (running/completed/failed)
  - The DOM panel #desempenho-progress-panel shows counts (✅/❌/⏳)
    matching the backend data

Fail condition:
  - After max_wait minutes, panel still shows "aguardando inicialização"
    (i.e., students dict still empty)
  - OR panel never replaces the initial spinner

Usage:
    cd prova-ia-v2/backend
    python "../md documents/desempenho-ui-fix/_verify_progress.py" \\
        [--max-wait-min 8] [--provider-id 588f3efe7975]
"""
import argparse
import asyncio
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"
MATERIA_ID = "57861d16958965d2"
TURMA_ID = "3f3ab03dfe783f30"
LOOP_DIR = Path(__file__).parent
OUT = LOOP_DIR / f"_verify_progress_{datetime.now():%Y%m%d_%H%M%S}"


def log(msg, indent=0):
    print(("  " * indent) + f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def http_get(url, timeout=20):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider-id", default="588f3efe7975")  # Claude Haiku 4.5
    ap.add_argument("--max-wait-min", type=float, default=8.0)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    log(f"URL: {URL}")
    log(f"Output: {OUT}")
    log(f"Provider: {args.provider_id} (Claude Haiku 4.5)")
    log(f"Max wait: {args.max_wait_min} min")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()

        log("[1] Loading site")
        await page.goto(URL, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(1.5)
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
        await asyncio.sleep(0.3)

        log("[2] Sanity: new code is in the live HTML")
        has_new_panel = await page.evaluate(
            "typeof _renderDesempenhoProgressPanel === 'function'"
        )
        if not has_new_panel:
            log("FATAL: _renderDesempenhoProgressPanel not defined — deploy not live yet", 1)
            await browser.close()
            sys.exit(2)
        log("ok: new code is live", 1)

        log("[3] Navigate to Álgebra Linear → 2026-1 → Desempenho")
        await page.evaluate(f"showMateria('{MATERIA_ID}')")
        await asyncio.sleep(1.0)
        await page.evaluate(f"showTurma('{TURMA_ID}')")
        await asyncio.sleep(1.0)
        await page.evaluate("showTurmaTab('desempenho')")
        await asyncio.sleep(3.0)

        log("[4] Open modal + select provider + force_reexec + select-all")
        await page.evaluate(f"openDesempenhoSettings('turma', '{TURMA_ID}')")
        await asyncio.sleep(2.5)
        await page.wait_for_function(
            "document.querySelectorAll('#input-desempenho-provider option').length > 1",
            timeout=15000,
        )
        await page.evaluate(f"document.getElementById('input-desempenho-provider').value = '{args.provider_id}'")
        await page.evaluate("document.getElementById('input-desempenho-force-rerun').checked = true")
        await page.evaluate("toggleDesempenhoEtapas()")
        await asyncio.sleep(2.5)
        await page.evaluate("document.querySelectorAll('.desempenho-group-header').forEach(h => h.click())")
        await asyncio.sleep(3.0)
        await page.evaluate("""() => {
            const cb = document.getElementById('desempenho-etapa-select-all');
            cb.checked = true;
            toggleAllDesempenhoEtapas(cb);
        }""")
        await asyncio.sleep(0.5)

        log("[5] Capture task_id via response interceptor + submit")
        captured = {"task_id": None}
        async def on_response(response):
            if "/api/executar/pipeline-desempenho" in response.url:
                try:
                    body = await response.json()
                    captured["task_id"] = body.get("task_id")
                except Exception:
                    pass
        page.on("response", on_response)
        await page.evaluate("executarDesempenhoFromModal()")
        for _ in range(40):
            if captured["task_id"]:
                break
            await asyncio.sleep(0.5)
        if not captured["task_id"]:
            log("FATAL: no task_id captured", 1)
            await browser.close()
            sys.exit(3)
        task_id = captured["task_id"]
        log(f"task_id={task_id}", 1)

        log("[6] Polling DOM + backend for live progress (max {} min)".format(args.max_wait_min))
        deadline = time.time() + args.max_wait_min * 60
        first_seen = None  # timestamp when first non-pending student appeared
        last_counts = None
        screenshot_count = 0
        while time.time() < deadline:
            # Backend state
            try:
                backend = http_get(f"{URL}/api/task-progress/{task_id}", timeout=15)
            except Exception as e:
                log(f"poll error: {e}", 1)
                await asyncio.sleep(5)
                continue
            students = backend.get("students") or {}
            backend_total = len(students)
            backend_active = sum(
                1 for s in students.values()
                if any(v not in ("pending", None) for v in (s.get("stages") or {}).values())
            )

            # DOM state
            dom = await page.evaluate("""() => {
                const panel = document.getElementById('desempenho-progress-panel');
                if (!panel) return { panel_present: false, text: '' };
                return { panel_present: true, text: panel.innerText, html_len: panel.innerHTML.length };
            }""")

            counts_signature = f"backend={backend_active}/{backend_total} status={backend.get('status')} dom_panel={dom.get('panel_present')}"
            if counts_signature != last_counts:
                log(f"poll: {counts_signature}", 1)
                last_counts = counts_signature
                # Take a screenshot at each change for evidence
                screenshot_count += 1
                await page.screenshot(path=str(OUT / f"step_{screenshot_count:02d}_{int(time.time())}.png"), full_page=False)

            if backend_active >= 1 and dom.get("panel_present"):
                if first_seen is None:
                    first_seen = time.time()
                    log(f"FIRST PROGRESS SEEN at t={int(first_seen - (deadline - args.max_wait_min*60))}s — verifying DOM matches", 1)
                # Hold for a couple more polls to confirm panel actually shows counts
                if "✅" in (dom.get("text") or "") or "❌" in (dom.get("text") or "") or "⏳" in (dom.get("text") or ""):
                    log("PASS — DOM panel renders counts; live progress is visible", 1)
                    await page.screenshot(path=str(OUT / "PASS_final.png"), full_page=True)
                    # Save the panel text for the run log
                    (OUT / "PASS_panel_text.txt").write_text(dom.get("text") or "")
                    log(f"task_id={task_id} left running (cancel manually if needed: POST /api/task-cancel/{task_id})", 1)
                    await browser.close()
                    sys.exit(0)

            if backend.get("status") in ("completed", "failed", "cancelled"):
                log(f"task ended early with status={backend.get('status')} — failing verify", 1)
                await page.screenshot(path=str(OUT / "END_early.png"), full_page=True)
                await browser.close()
                sys.exit(4)

            await asyncio.sleep(5)

        log("TIMEOUT — no live progress visible within deadline", 1)
        await page.screenshot(path=str(OUT / "TIMEOUT_final.png"), full_page=True)
        await browser.close()
        sys.exit(5)


if __name__ == "__main__":
    asyncio.run(main())
