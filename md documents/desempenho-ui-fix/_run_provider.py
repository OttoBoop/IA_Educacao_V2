#!/usr/bin/env python3
"""Dispatch a desempenho-turma pipeline run for one provider through the live UI,
then poll until completion and capture cost delta.

Drives the website with Playwright (Otavio's instruction: "use the website,
not the API panel"). Captures task_id from window._desempenhoActiveTasks,
then polls /api/task-progress/{task_id} for status. Captures cost via
/api/custos/resumo snapshot before/after.

Outputs go to:
  - logs/_run_<label>_<timestamp>.log   — wall-time progress log
  - 03_evidencias_runs.md               — markdown ledger (appended)

Usage:
    cd prova-ia-v2/backend
    python "../md documents/desempenho-ui-fix/_run_provider.py" \\
        --provider-id 588f3efe7975 \\
        --label claude-haiku-4-5 \\
        --force-reexec
"""
import argparse
import asyncio
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"
MATERIA_ID = "57861d16958965d2"  # Álgebra Linear Avançada
TURMA_ID = "3f3ab03dfe783f30"    # 2026-1
ATIVIDADE_ID = "126e8b5ad7dd6d59"  # Lista0
LOOP_DIR = Path(__file__).parent
LOG_DIR = LOOP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def get_cost_snapshot():
    try:
        return http_get(f"{URL}/api/custos/resumo?limit=2000", timeout=20)
    except Exception as e:
        return {"_error": str(e)}


async def dispatch_run(provider_id, label, force_reexec, logf):
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

        log("[dispatch] Navigating to Álgebra Linear → 2026-1 → Desempenho")
        await page.evaluate(f"showMateria('{MATERIA_ID}')")
        await asyncio.sleep(1.0)
        await page.evaluate(f"showTurma('{TURMA_ID}')")
        await asyncio.sleep(1.0)
        await page.evaluate("showTurmaTab('desempenho')")
        await asyncio.sleep(3.0)

        log("[dispatch] Opening modal")
        await page.evaluate(f"openDesempenhoSettings('turma', '{TURMA_ID}')")
        await asyncio.sleep(2.5)

        # Wait for provider dropdown to populate, then select target provider.
        await page.wait_for_function(
            "document.querySelectorAll('#input-desempenho-provider option').length > 1",
            timeout=15000,
        )
        opts = await page.evaluate(
            "Array.from(document.querySelectorAll('#input-desempenho-provider option')).map(o => ({id:o.value, text:o.textContent}))"
        )
        log(f"[dispatch] provider options: {len(opts)} available")
        match = [o for o in opts if o["id"] == provider_id]
        if not match:
            log(f"[dispatch] FATAL: provider_id {provider_id} not in dropdown. Available: {opts}")
            await browser.close()
            return None
        log(f"[dispatch] selecting provider {match[0]}")
        await page.evaluate(f"document.getElementById('input-desempenho-provider').value = '{provider_id}'")

        if force_reexec:
            log("[dispatch] checking force_reexec")
            await page.evaluate("document.getElementById('input-desempenho-force-rerun').checked = true")

        log("[dispatch] expanding etapas + master select-all (228 stages)")
        await page.evaluate("toggleDesempenhoEtapas()")
        await asyncio.sleep(2.5)
        # Expand lazy children (turma view = atividades collapsed)
        await page.evaluate("document.querySelectorAll('.desempenho-group-header').forEach(h => h.click())")
        await asyncio.sleep(3.0)
        # Master select-all
        await page.evaluate("""() => {
            const cb = document.getElementById('desempenho-etapa-select-all');
            cb.checked = true;
            toggleAllDesempenhoEtapas(cb);
        }""")
        await asyncio.sleep(0.5)
        counts = await page.evaluate("""() => ({
            total: document.querySelectorAll('.desempenho-etapa-check').length,
            checked: document.querySelectorAll('.desempenho-etapa-check:checked').length,
        })""")
        log(f"[dispatch] checkboxes: {counts}")

        # Snapshot start
        start_iso = datetime.now(timezone.utc).isoformat()
        cost_before = get_cost_snapshot()
        log(f"[dispatch] cost snapshot BEFORE: $ {cost_before.get('custo_usd', '?')}, "
            f"runs={cost_before.get('runs_analisados', '?')}, "
            f"tokens_in={cost_before.get('tokens_entrada', '?')}")

        log("[dispatch] submitting executarDesempenhoFromModal() — listening for response")
        # Intercept the POST response so we don't depend on _desempenhoActiveTasks timing.
        captured = {"task_id": None, "status": None, "url": None}
        async def on_response(response):
            if "/api/executar/pipeline-desempenho" in response.url:
                try:
                    body = await response.json()
                    captured["task_id"] = body.get("task_id")
                    captured["status"] = body.get("status")
                    captured["url"] = response.url
                except Exception:
                    pass
        page.on("response", on_response)
        await page.evaluate("executarDesempenhoFromModal()")
        # apiForm + cold start can take 10-15s — poll the captured dict.
        for _ in range(40):  # 40 * 0.5s = 20s
            if captured["task_id"]:
                break
            await asyncio.sleep(0.5)
        log(f"[dispatch] response captured: {captured}")
        if not captured["task_id"]:
            # Fallback: peek at window._desempenhoActiveTasks
            task_info = await page.evaluate("""() => {
                try {
                    const k = Object.keys(window._desempenhoActiveTasks || {})[0];
                    return k ? window._desempenhoActiveTasks[k] : null;
                } catch (e) { return { error: String(e) }; }
            }""")
            log(f"[dispatch] fallback window._desempenhoActiveTasks: {task_info}")
            if task_info and task_info.get("taskId"):
                captured["task_id"] = task_info["taskId"]

        if not captured["task_id"]:
            log("[dispatch] FATAL: no task_id captured. Submission likely failed.")
            await page.screenshot(path=str(LOG_DIR / f"_failed_dispatch_{label}.png"), full_page=True)
            await browser.close()
            return None

        task_id = captured["task_id"]
        log(f"[dispatch] task_id={task_id} status={captured['status']} via={captured['url']}")
        await page.screenshot(path=str(LOG_DIR / f"_dispatched_{label}.png"), full_page=True)
        await browser.close()
        return {"task_id": task_id, "start_iso": start_iso, "cost_before": cost_before}


async def poll_until_done(task_id, label, logf, max_wait_hours=4):
    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    deadline = time.time() + max_wait_hours * 3600
    last_status = None
    last_count = -1
    while time.time() < deadline:
        try:
            data = http_get(f"{URL}/api/task-progress/{task_id}", timeout=20)
            status = data.get("status")
            students = data.get("students") or {}
            done = sum(1 for v in students.values() if v.get("status") in ("completed", "failed"))
            total = len(students)
            if status != last_status or done != last_count:
                log(f"[poll] status={status} students_done={done}/{total} "
                    f"summary={data.get('summary')}")
                last_status, last_count = status, done
            if status in ("completed", "failed", "error"):
                log(f"[poll] FINAL status={status} done={done}/{total}")
                return data
        except Exception as e:
            log(f"[poll] ERROR fetching progress: {e}")
        await asyncio.sleep(30)
    log("[poll] TIMEOUT reached")
    return None


def diff_costs(before, after):
    bp = {p["provider"]: p for p in before.get("por_provider", [])}
    diffs = []
    for p in after.get("por_provider", []):
        prev = bp.get(p["provider"], {"runs": 0, "tokens_entrada": 0, "tokens_saida": 0, "custo_usd": 0})
        diffs.append({
            "provider": p["provider"],
            "delta_runs": p["runs"] - prev["runs"],
            "delta_tokens_in": p["tokens_entrada"] - prev["tokens_entrada"],
            "delta_tokens_out": p["tokens_saida"] - prev["tokens_saida"],
            "delta_cost_usd": p["custo_usd"] - prev["custo_usd"],
        })
    total_delta = after.get("custo_usd", 0) - before.get("custo_usd", 0)
    return {"by_provider": diffs, "total_delta_usd": total_delta}


def append_evidence(label, provider_id, dispatch_result, final_progress, cost_delta, logf_path):
    md = LOOP_DIR / "03_evidencias_runs.md"
    block = f"""
---

## Auto-appended {datetime.now(timezone.utc).isoformat()}

- **Label:** `{label}`
- **provider_id:** `{provider_id}`
- **task_id:** `{dispatch_result.get('task_id') if dispatch_result else 'NO_DISPATCH'}`
- **start:** `{dispatch_result.get('start_iso') if dispatch_result else '-'}`
- **end:** `{datetime.now(timezone.utc).isoformat()}`
- **final status:** `{(final_progress or {}).get('status', 'no_progress_data')}`
- **students done:** `{sum(1 for v in (final_progress or {}).get('students', {}).values() if v.get('status') == 'completed')}/{len((final_progress or {}).get('students', {}))}`
- **failures:** `{sum(1 for v in (final_progress or {}).get('students', {}).values() if v.get('status') == 'failed')}`
- **cost delta USD (total):** `${cost_delta.get('total_delta_usd', 0):.4f}`
- **cost delta by provider:**
{chr(10).join('  - ' + p['provider'] + ': $' + format(p['delta_cost_usd'], '.4f') + ' (' + str(p['delta_tokens_in']) + ' in / ' + str(p['delta_tokens_out']) + ' out tokens, ' + str(p['delta_runs']) + ' new runs)' for p in cost_delta.get('by_provider', []))}
- **log:** `{logf_path.relative_to(LOOP_DIR)}`

"""
    if md.exists():
        md.write_text(md.read_text() + block)
    else:
        md.write_text(block)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider-id", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--force-reexec", action="store_true")
    ap.add_argument("--max-wait-hours", type=float, default=4.0)
    args = ap.parse_args()

    log_path = LOG_DIR / f"_run_{args.label}_{datetime.now():%Y%m%d_%H%M%S}.log"
    with open(log_path, "w") as logf:
        print(f"=== Run {args.label} ({args.provider_id}) ===", file=logf, flush=True)
        print(f"Log: {log_path}", flush=True)

        dispatch = await dispatch_run(args.provider_id, args.label, args.force_reexec, logf)
        if not dispatch:
            print("ABORT: dispatch failed", flush=True)
            sys.exit(1)
        print(f"DISPATCHED task_id={dispatch['task_id']}", flush=True)

        final = await poll_until_done(dispatch["task_id"], args.label, logf, args.max_wait_hours)

        cost_after = get_cost_snapshot()
        delta = diff_costs(dispatch["cost_before"], cost_after)
        print(f"COST DELTA: ${delta['total_delta_usd']:.4f} total", flush=True)
        for p in delta["by_provider"]:
            if abs(p["delta_cost_usd"]) > 1e-6:
                print(f"  - {p['provider']}: ${p['delta_cost_usd']:.4f} ({p['delta_tokens_in']} in / {p['delta_tokens_out']} out)", flush=True)

        append_evidence(args.label, args.provider_id, dispatch, final, delta, log_path)
        print(f"DONE — evidence appended to 03_evidencias_runs.md", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
