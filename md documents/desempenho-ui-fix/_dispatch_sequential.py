#!/usr/bin/env python3
"""Strictly sequential dispatcher — one aluno at a time.

Dispatches pipeline-completo for the next aluno, then polls
/api/task-progress until completed/failed, only then moves to the next.
Tradeoff: very slow (5min × N alunos) but zero rate-limit risk.

When Gemini Flash hits 429s with even 30s-gap staggering (observed
2026-06-05), this is the only safe mode. The rate limit ceiling
(~10 RPM on the Preview model) is consumed by a single in-flight
pipeline's 4–6 API calls during its 5-minute window.

Usage:
    python "_dispatch_sequential.py" --provider-id gem3flash001 \
        --alunos-file /tmp/need_stag.txt --max-minutes-per-aluno 10
"""
import argparse
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
        f"{URL}{path}", data=body, method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_get(path, timeout=30):
    req = urllib.request.Request(f"{URL}{path}", headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def poll_until_done(aluno_id, task_id, log, max_minutes):
    deadline = time.time() + max_minutes * 60
    last_state = None
    while time.time() < deadline:
        try:
            data = http_get(f"/api/task-progress/{task_id}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # P10 task_registry lost it — fall back to Supabase check via API
                # heuristic: if completed, the relatorio_final exists; otherwise it's gone.
                time.sleep(20)
                try:
                    atv = http_get(f"/api/atividades/{ATIVIDADE_ID}")
                    al = next((a for a in atv.get("alunos", {}).get("detalhes", [])
                               if a.get("aluno_id") == aluno_id), None)
                    rel_em = (al or {}).get("relatorio_criado_em") or ""
                    if rel_em >= "2026-06-05":
                        log(f"  task lost from registry but aluno has fresh relatorio — treating as completed")
                        return "completed"
                except Exception:
                    pass
                log(f"  task 404 + no fresh relatorio — treating as lost")
                return "lost"
            time.sleep(15); continue
        except Exception:
            time.sleep(15); continue
        status = data.get("status") or "?"
        if status != last_state:
            students = data.get("students") or {}
            st = (students.get(aluno_id, {}) or {}).get("stages")
            log(f"  status={status} stages={st}")
            last_state = status
        if status in ("completed", "failed", "cancelled"):
            return status
        time.sleep(15)
    return "timeout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider-id", required=True)
    ap.add_argument("--alunos-file", required=True)
    ap.add_argument("--max-minutes-per-aluno", type=int, default=10)
    ap.add_argument("--cooldown", type=int, default=10,
                    help="seconds between alunos to be extra safe (default 10)")
    args = ap.parse_args()

    alunos = [l.strip() for l in open(args.alunos_file) if l.strip()]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"_seq_{args.provider_id}_{ts}.log"
    log_f = open(log_path, "w", encoding="utf-8")

    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n")
        log_f.flush()

    log(f"== Sequential dispatch: {len(alunos)} alunos, provider={args.provider_id} ==")
    results = {"completed": [], "failed": [], "lost": [], "timeout": []}

    for i, aluno_id in enumerate(alunos):
        log(f"\n[{i+1}/{len(alunos)}] {aluno_id}")
        payload = {
            "atividade_id": ATIVIDADE_ID,
            "aluno_id": aluno_id,
            "model_id": args.provider_id,
            "selected_steps": json.dumps([
                "extrair_questoes", "extrair_gabarito", "extrair_respostas",
                "corrigir", "analisar_habilidades", "gerar_relatorio",
            ]),
            "force_rerun": "false",
        }
        try:
            resp = http_post_form("/api/executar/pipeline-completo", payload)
            tid = resp.get("task_id")
            log(f"  dispatched task={tid}")
        except Exception as e:
            log(f"  DISPATCH ERROR {e}")
            results["failed"].append(aluno_id)
            time.sleep(args.cooldown)
            continue

        if not tid:
            results["failed"].append(aluno_id)
            time.sleep(args.cooldown)
            continue

        outcome = poll_until_done(aluno_id, tid, log, args.max_minutes_per_aluno)
        log(f"  FINAL: {outcome}")
        results.setdefault(outcome, []).append(aluno_id)
        log(f"  totals so far: completed={len(results['completed'])} failed={len(results['failed'])} lost={len(results.get('lost',[]))} timeout={len(results.get('timeout',[]))}")
        time.sleep(args.cooldown)

    log(f"\n== DONE ==")
    for k, v in results.items():
        log(f"  {k}: {len(v)}")
    log_f.close()


if __name__ == "__main__":
    main()
