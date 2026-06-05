#!/usr/bin/env python3
"""Staggered dispatch: send pipeline-completo requests with a delay between
each to avoid rate-limit bursts on the LLM provider side.

The plain `_dispatch_batch.py` fires N requests in parallel — Render runs
up to PARALLEL_WORKERS (12) pipelines simultaneously, and each pipeline
fires 4–6 LLM calls. That bursts past Gemini Flash's per-minute quota
(429s observed 2026-06-02 23:48 onwards) and the whole batch fails.

This script dispatches with a configurable gap (default 30s) between
HTTP POSTs so the pipelines start spread out across the rate-limit
window. Polling and audit are deferred to `_audit_turma_run.py` after
the dispatch wave finishes — simpler than per-task polling.

Usage:
    python "_dispatch_staggered.py" --provider-id gem3flash001 \
        --alunos-file /tmp/need_final.txt --delay 30
"""
import argparse
import json
import sys
import time
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider-id", required=True)
    ap.add_argument("--alunos-file", required=True)
    ap.add_argument("--delay", type=int, default=30,
                    help="Seconds between dispatches (default 30)")
    ap.add_argument("--force-rerun", action="store_true")
    args = ap.parse_args()

    alunos = [l.strip() for l in open(args.alunos_file) if l.strip()]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"_stagger_{args.provider_id}_{ts}.log"
    log_f = open(log_path, "w", encoding="utf-8")

    def log(msg):
        line = f"[{datetime.now():%H:%M:%S}] {msg}"
        print(line, flush=True)
        log_f.write(line + "\n")
        log_f.flush()

    log(f"== Staggered dispatch: {len(alunos)} alunos, "
        f"provider={args.provider_id}, delay={args.delay}s, "
        f"force_rerun={args.force_rerun} ==")

    dispatched = []
    for i, aluno_id in enumerate(alunos):
        if i > 0:
            log(f"  sleeping {args.delay}s before next dispatch...")
            time.sleep(args.delay)
        payload = {
            "atividade_id": ATIVIDADE_ID,
            "aluno_id": aluno_id,
            "model_id": args.provider_id,
            "selected_steps": json.dumps([
                "extrair_questoes", "extrair_gabarito", "extrair_respostas",
                "corrigir", "analisar_habilidades", "gerar_relatorio",
            ]),
            "force_rerun": "true" if args.force_rerun else "false",
        }
        try:
            resp = http_post_form("/api/executar/pipeline-completo", payload)
            tid = resp.get("task_id")
            log(f"  [{i+1}/{len(alunos)}] {aluno_id[:12]}  task={tid}  "
                f"status={resp.get('status')}")
            dispatched.append((aluno_id, tid))
        except Exception as e:
            log(f"  [{i+1}/{len(alunos)}] {aluno_id[:12]}  ERROR {e}")
            dispatched.append((aluno_id, None))

    log(f"\nAll {len(alunos)} dispatched. {sum(1 for _,t in dispatched if t)} got task_id, "
        f"{sum(1 for _,t in dispatched if not t)} failed at dispatch.")
    log("Run _audit_turma_run.py with appropriate --since to check progress.")
    log_f.close()


if __name__ == "__main__":
    main()
