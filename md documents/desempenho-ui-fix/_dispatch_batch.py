#!/usr/bin/env python3
"""Dispatch pipeline-completo for a batch of aluno_ids in parallel via the live API.

Uses /api/executar/pipeline-completo (same endpoint as modal-pipeline-completo
in aluno mode). One HTTP POST per aluno, all dispatched concurrently. Render
handles queueing internally. No force_rerun — existing docs are skipped per
_should_run.

Usage:
    python "_dispatch_batch.py" --provider-id gem3flash001 \\
        --alunos-file /tmp/need_dispatch.txt --max-minutes 25
"""
import argparse
import asyncio
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

URL = "https://ia-educacao-v2.onrender.com"
ATIVIDADE_ID = "126e8b5ad7dd6d59"
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def http_post_form(path, data, timeout=60):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f"{URL}{path}",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_get(path, timeout=30):
    req = urllib.request.Request(f"{URL}{path}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


async def dispatch_one(aluno_id, provider_id, logf):
    loop = asyncio.get_event_loop()
    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()
    try:
        payload = {
            "atividade_id": ATIVIDADE_ID,
            "aluno_id": aluno_id,
            "model_id": provider_id,
            "selected_steps": json.dumps([
                "extrair_questoes", "extrair_gabarito", "extrair_respostas",
                "corrigir", "analisar_habilidades", "gerar_relatorio",
            ]),
            "force_rerun": "false",
        }
        resp = await loop.run_in_executor(None, http_post_form, "/api/executar/pipeline-completo", payload)
        tid = resp.get("task_id")
        log(f"[dispatch] {aluno_id[:12]}  task_id={tid}  status={resp.get('status')}")
        return aluno_id, tid
    except Exception as e:
        log(f"[dispatch] {aluno_id[:12]}  ERROR {e}")
        return aluno_id, None


async def poll_aluno(aluno_id, task_id, logf, deadline):
    loop = asyncio.get_event_loop()
    last_state = None
    while time.time() < deadline:
        try:
            data = await loop.run_in_executor(None, http_get, f"/api/task-progress/{task_id}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # task_registry may have lost it — check Supabase directly
                await asyncio.sleep(30); continue
            await asyncio.sleep(30); continue
        except Exception:
            await asyncio.sleep(30); continue
        status = data.get("status") or "?"
        if status != last_state:
            students = data.get("students") or {}
            st = students.get(aluno_id, {}).get("stages") if students else (data.get("stages") or {})
            print(f"[{datetime.now():%H:%M:%S}] {aluno_id[:12]} status={status} stages={st}", flush=True)
            last_state = status
        if status in ("completed", "failed", "cancelled"):
            return aluno_id, status
        await asyncio.sleep(30)
    return aluno_id, "timeout"


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider-id", required=True)
    ap.add_argument("--alunos-file", required=True)
    ap.add_argument("--max-minutes", type=int, default=30)
    args = ap.parse_args()

    alunos = [l.strip() for l in open(args.alunos_file).readlines() if l.strip()]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"_batch_{args.provider_id}_{ts}.log"
    with open(log_path, "w", encoding="utf-8") as logf:
        def log(msg):
            line = f"[{datetime.now():%H:%M:%S}] {msg}"
            print(line, flush=True)
            logf.write(line + "\n")
            logf.flush()

        log(f"== Dispatch BATCH {len(alunos)} alunos / provider={args.provider_id} ==")
        # Dispatch all in parallel
        dispatch_results = await asyncio.gather(
            *[dispatch_one(aid, args.provider_id, logf) for aid in alunos]
        )
        ok_dispatches = [(aid, tid) for aid, tid in dispatch_results if tid]
        log(f"Dispatched OK: {len(ok_dispatches)}/{len(alunos)}")

        # Poll all in parallel
        deadline = time.time() + args.max_minutes * 60
        poll_results = await asyncio.gather(
            *[poll_aluno(aid, tid, logf, deadline) for aid, tid in ok_dispatches]
        )
        # Tally
        completed = [aid for aid, s in poll_results if s == "completed"]
        failed = [aid for aid, s in poll_results if s == "failed"]
        timeout = [aid for aid, s in poll_results if s == "timeout"]
        log(f"\nFINAL: completed={len(completed)}  failed={len(failed)}  timeout={len(timeout)}")
        for aid in failed[:10]: log(f"  FAIL: {aid}")
        for aid in timeout[:10]: log(f"  TIMEOUT: {aid}")


if __name__ == "__main__":
    asyncio.run(main())
