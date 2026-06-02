#!/usr/bin/env python3
"""Dispatch pipeline-completo for ONE student (Alvaro) via the live UI.

Uses the modal-pipeline-completo with mode=aluno. Drives the website with
Playwright (Otavio rule: "use the website, not the API panel"). Captures
task_id from the POST response, then polls /api/task-progress/{task_id}.

Usage:
    cd backend
    python "../md documents/desempenho-ui-fix/_dispatch_alvaro.py" \\
        --provider-id gem3flash001 --force-rerun

Exit 0 on completed pipeline; non-zero on dispatch failure or task failed.
"""
import argparse
import asyncio
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"
MATERIA_ID = "57861d16958965d2"  # Álgebra Linear Avançada
TURMA_ID = "3f3ab03dfe783f30"    # 2026-1
ATIVIDADE_ID = "126e8b5ad7dd6d59"  # Lista0
ALUNO_ID = "40ab839a5340e39a"     # ALVARO JOEL TICONA MOTTA
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def poll_task(task_id, label, logf, max_minutes=20):
    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    deadline = time.time() + max_minutes * 60
    seen_404s = 0
    last_stage_state = None
    while time.time() < deadline:
        try:
            data = http_get(f"{URL}/api/task-progress/{task_id}", timeout=20)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                seen_404s += 1
                if seen_404s > 8:
                    log(f"[poll] 404 ×{seen_404s} — task registry may have lost it (server restart). Stopping.")
                    return {"final": "lost_404", "task_id": task_id}
                time.sleep(15)
                continue
            log(f"[poll] HTTP {e.code} — retrying in 30s")
            time.sleep(30)
            continue
        except Exception as e:
            log(f"[poll] error: {e}")
            time.sleep(15)
            continue
        seen_404s = 0
        status = data.get("status") or data.get("task_status") or "?"
        stages = data.get("stages") or {}
        # Per-student per-stage view
        students = data.get("students") or {}
        if students:
            student = students.get(ALUNO_ID) or next(iter(students.values()))
            stage_state = student.get("stages") if isinstance(student, dict) else None
        else:
            stage_state = stages
        if stage_state and stage_state != last_stage_state:
            log(f"[poll] status={status} stages={stage_state}")
            last_stage_state = stage_state
        if status in ("completed", "failed", "cancelled"):
            log(f"[poll] FINAL status={status}")
            return {"final": status, "task_id": task_id, "data": data}
        time.sleep(20)
    log(f"[poll] TIMEOUT after {max_minutes}min")
    return {"final": "timeout", "task_id": task_id}


async def dispatch_aluno(provider_id, force_rerun, logf):
    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()
        log(f"[dispatch] Loading {URL}")
        await page.goto(URL, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(1.5)
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
        await asyncio.sleep(0.3)

        log("[dispatch] Navigating to Materia → Turma → Atividade")
        await page.evaluate(f"showMateria('{MATERIA_ID}')")
        await asyncio.sleep(1.0)
        await page.evaluate(f"showTurma('{TURMA_ID}')")
        await asyncio.sleep(1.5)

        log("[dispatch] Pre-loading atividade data (hasStudentsInTurma needs it)")
        await page.evaluate(
            f"(async () => {{ await ensureAtividadeData('{ATIVIDADE_ID}'); }})()"
        )
        await asyncio.sleep(0.5)
        atividade_total = await page.evaluate(
            "window._atividadeData?.alunos?.total ?? null"
        )
        log(f"[dispatch] _atividadeData.alunos.total = {atividade_total}")

        log("[dispatch] Opening modal-pipeline-completo (mode=aluno) — awaiting promise")
        await page.evaluate(
            f"(async () => {{ await openModalPipelineCompleto('{ATIVIDADE_ID}', 'aluno'); }})()"
        )
        await asyncio.sleep(1.5)
        try:
            await page.wait_for_function(
                "document.querySelectorAll('#input-pipeline-aluno option').length > 1",
                timeout=45000,
            )
        except Exception:
            await page.screenshot(path=str(LOG_DIR / "_modal_no_alunos.png"), full_page=True)
            html = await page.evaluate("document.getElementById('input-pipeline-aluno')?.outerHTML || 'NO_ELEMENT'")
            log(f"[dispatch] FATAL: alunos dropdown not populated. element={html[:400]}")
            modal_visible = await page.evaluate(
                "document.getElementById('modal-pipeline-completo')?.classList.contains('active')"
            )
            log(f"[dispatch] modal active? {modal_visible}")
            await browser.close()
            return None
        try:
            await page.wait_for_function(
                "document.querySelectorAll('#input-pipeline-provider-default option').length > 1",
                timeout=20000,
            )
        except Exception:
            await page.screenshot(path=str(LOG_DIR / "_modal_no_providers.png"), full_page=True)
            html = await page.evaluate("document.getElementById('input-pipeline-provider-default')?.outerHTML || 'NO_ELEMENT'")
            log(f"[dispatch] FATAL: provider dropdown not populated. element={html[:400]}")
            await browser.close()
            return None
        await asyncio.sleep(0.5)

        # Confirm mode=aluno is selected
        await page.evaluate("document.querySelector('input[name=\"pipeline-modo\"][value=\"aluno\"]').checked = true; onPipelineModoChange()")
        await asyncio.sleep(0.3)

        # Select Alvaro
        alunos = await page.evaluate(
            "Array.from(document.querySelectorAll('#input-pipeline-aluno option')).map(o => ({id:o.value, text:o.textContent}))"
        )
        log(f"[dispatch] alunos options: {len(alunos)}")
        if not any(o["id"] == ALUNO_ID for o in alunos):
            log(f"[dispatch] FATAL: Alvaro {ALUNO_ID} not in dropdown. Sample: {alunos[:5]}")
            await browser.close()
            return None
        await page.evaluate(f"document.getElementById('input-pipeline-aluno').value = '{ALUNO_ID}'")
        await page.evaluate("document.getElementById('input-pipeline-aluno').dispatchEvent(new Event('change'))")

        # Select provider
        providers = await page.evaluate(
            "Array.from(document.querySelectorAll('#input-pipeline-provider-default option')).map(o => ({id:o.value, text:o.textContent}))"
        )
        log(f"[dispatch] provider options: {len(providers)}")
        if not any(o["id"] == provider_id for o in providers):
            log(f"[dispatch] FATAL: provider {provider_id} not in dropdown. Sample: {providers[:8]}")
            await browser.close()
            return None
        await page.evaluate(f"document.getElementById('input-pipeline-provider-default').value = '{provider_id}'")
        await page.evaluate("document.getElementById('input-pipeline-provider-default').dispatchEvent(new Event('change'))")

        # Force rerun
        if force_rerun:
            log("[dispatch] checking force_rerun")
            await page.evaluate("document.getElementById('input-pipeline-force-rerun').checked = true")

        # Select all etapas
        counts = await page.evaluate("""() => {
            const cbs = document.querySelectorAll('.pipeline-step-checkbox');
            cbs.forEach(cb => { cb.checked = true; });
            return { total: cbs.length, checked: document.querySelectorAll('.pipeline-step-checkbox:checked').length };
        }""")
        log(f"[dispatch] etapas: {counts}")

        # Submit + capture POST response
        captured = {"task_id": None, "status": None, "url": None}
        async def on_response(response):
            if "/api/executar/pipeline-completo" in response.url:
                try:
                    body = await response.json()
                    captured["task_id"] = body.get("task_id")
                    captured["status"] = body.get("status")
                    captured["url"] = response.url
                except Exception:
                    pass
        page.on("response", on_response)

        log("[dispatch] submitting executarPipelineCompleto()")
        await page.evaluate("executarPipelineCompleto()")
        for _ in range(40):
            if captured["task_id"]:
                break
            await asyncio.sleep(0.5)
        log(f"[dispatch] response captured: {captured}")
        if not captured["task_id"]:
            await page.screenshot(path=str(LOG_DIR / "_failed_dispatch_alvaro.png"), full_page=True)
            await browser.close()
            return None

        task_id = captured["task_id"]
        await page.screenshot(path=str(LOG_DIR / f"_dispatched_alvaro_{task_id[:12]}.png"), full_page=True)
        await browser.close()
        return task_id


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-id", required=True)
    parser.add_argument("--force-rerun", action="store_true")
    parser.add_argument("--no-poll", action="store_true")
    parser.add_argument("--max-minutes", type=int, default=20)
    args = parser.parse_args()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"_alvaro_{args.provider_id}_{ts}.log"
    with open(log_path, "w", encoding="utf-8") as logf:
        def log(msg):
            line = f"[{datetime.now():%H:%M:%S}] {msg}"
            print(line, flush=True)
            logf.write(line + "\n")
            logf.flush()

        log(f"== Dispatch Alvaro / provider={args.provider_id} / force_rerun={args.force_rerun} ==")
        task_id = await dispatch_aluno(args.provider_id, args.force_rerun, logf)
        if not task_id:
            log("FATAL: dispatch failed")
            sys.exit(2)
        log(f"task_id={task_id}")

        if args.no_poll:
            sys.exit(0)
        result = poll_task(task_id, args.provider_id, logf, max_minutes=args.max_minutes)
        log(f"RESULT: {result['final']}")
        sys.exit(0 if result["final"] == "completed" else 1)


if __name__ == "__main__":
    asyncio.run(main())
