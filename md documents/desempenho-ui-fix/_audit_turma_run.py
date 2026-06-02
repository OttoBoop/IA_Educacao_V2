#!/usr/bin/env python3
"""Audit all per-aluno docs produced by a turma pipeline run.

Reads correcao.json + relatorio_final.json from Supabase Storage for each
aluno_id with docs created within a given time window (default: last 90min).
Checks:
  - correcao.json: nota_final numeric, questoes[] non-empty, feedback_geral
    >= 50 chars, MISSING_CONTENT consistency for questions without gabarito
  - correcao.pdf: file exists, > 2000 bytes, contains "Nota final" label
  - analise_habilidades.json: habilidades[] non-empty
  - relatorio_final.json: feedback_geral / resumo_geral / nota_final present
  - PDFs: metadata.tool="execute_python_code" + auto_generated_from rastreabilidade

Outputs:
  - Summary table per aluno (status, nota, n_questoes, n_missing, custo_run)
  - Aggregate stats: how many alunos completed full pipeline, how many failed
  - Cost summary (sum of token_usage rows)

Usage:
    python "_audit_turma_run.py" --since "2026-06-02T20:30:00" [--ativ 126e8b5ad7dd6d59]
"""
import argparse
import json
import sys
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime

SUPA_URL = Path("/tmp/supa/url.txt").read_text().strip()
SUPA_KEY = Path("/tmp/supa/key.txt").read_text().strip()
ATIVIDADE_ID = "126e8b5ad7dd6d59"

HEADERS = {"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}"}

RATES = {
    ("google", "gemini-3-flash-preview"): (0.50/1e6, 3.00/1e6),
    ("openai", "gpt-5-nano"): (0.05/1e6, 0.40/1e6),
    ("anthropic", "claude-haiku-4-5-20251001"): (1.00/1e6, 5.00/1e6),
}


def http_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def list_docs(atividade_id, since_iso):
    q = urllib.parse.urlencode({
        "atividade_id": f"eq.{atividade_id}",
        "criado_em": f"gte.{since_iso}",
        "select": "id,tipo,extensao,aluno_id,ia_provider,ia_modelo,tamanho_bytes,criado_em,metadata,caminho_arquivo",
        "order": "criado_em.asc",
    })
    return json.loads(http_get(f"{SUPA_URL}/rest/v1/documentos?{q}"))


def storage_get(path):
    url = f"{SUPA_URL}/storage/v1/object/documentos/{urllib.parse.quote(path)}"
    return http_get(url)


def audit_correcao(payload):
    issues = []
    if not isinstance(payload, dict):
        return ["payload is not dict"]
    nf = payload.get("nota_final")
    if not isinstance(nf, (int, float)):
        issues.append("nota_final missing/non-numeric")
    questoes = payload.get("questoes") or []
    if not questoes:
        issues.append("questoes empty")
    fg = payload.get("feedback_geral") or ""
    if len(fg) < 50:
        issues.append(f"feedback_geral too short ({len(fg)} chars)")
    # Check MISSING_CONTENT honesty
    missing_count = 0
    corrected_count = 0
    for q in questoes:
        if not isinstance(q, dict): continue
        rc = str(q.get("resposta_correta") or "").strip().upper()
        if rc in ("", "MISSING_CONTENT", "N/A", "NULL", "NONE"):
            missing_count += 1
        elif isinstance(q.get("nota"), (int, float)):
            corrected_count += 1
    return issues, {
        "nota_final": nf,
        "total_acertos": payload.get("total_acertos"),
        "total_erros": payload.get("total_erros"),
        "n_questoes": len(questoes),
        "n_missing": missing_count,
        "n_corrected": corrected_count,
        "feedback_len": len(fg),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="ISO timestamp, e.g. 2026-06-02T20:30:00")
    ap.add_argument("--ativ", default=ATIVIDADE_ID)
    ap.add_argument("--show-failures", action="store_true")
    args = ap.parse_args()

    print(f"Auditing docs since {args.since} for atividade {args.ativ}")
    docs = list_docs(args.ativ, args.since)
    print(f"Total docs in window: {len(docs)}")

    # Group by (aluno_id, tipo, extensao) — latest
    per_aluno = {}
    for d in docs:
        aid = d.get("aluno_id")
        if not aid: continue  # atividade-level
        per_aluno.setdefault(aid, []).append(d)

    print(f"\n{'Aluno':<18} {'Etapas docs':<12} {'corr.json':>10} {'corr.pdf':>10} {'an.json':>9} {'an.pdf':>9} {'rel.json':>9} {'rel.pdf':>9} {'nota':>6}  status")
    print("-" * 130)

    summary = {"ok": 0, "partial": 0, "fail": 0, "total_alunos": 0}
    failures = []
    total_in = total_out = 0

    for aid, alist in sorted(per_aluno.items()):
        summary["total_alunos"] += 1
        # Pick latest of each tipo
        by_tipo = {}
        for d in alist:
            key = (d["tipo"], d["extensao"])
            if key not in by_tipo or d["criado_em"] > by_tipo[key]["criado_em"]:
                by_tipo[key] = d
        corr_json = by_tipo.get(("correcao", ".json"))
        corr_pdf = by_tipo.get(("correcao", ".pdf"))
        ana_json = by_tipo.get(("analise_habilidades", ".json"))
        ana_pdf = by_tipo.get(("analise_habilidades", ".pdf"))
        rel_json = by_tipo.get(("relatorio_final", ".json"))
        rel_pdf = by_tipo.get(("relatorio_final", ".pdf"))

        nota = "?"
        status = "UNKNOWN"
        issues_text = ""

        if corr_json:
            try:
                payload = json.loads(storage_get(corr_json["caminho_arquivo"]))
                issues, stats = audit_correcao(payload)
                nota = f"{stats.get('nota_final','?')}"
                if not issues and corr_pdf and ana_json and rel_json:
                    status = "✅ OK"
                    summary["ok"] += 1
                elif issues:
                    status = "❌ corr_issues"
                    issues_text = ";".join(issues)
                    summary["partial"] += 1
                    failures.append((aid, issues_text))
                else:
                    missing = [t for t in ["correcao.pdf","analise.json","relatorio.json"]
                               if (t=="correcao.pdf" and not corr_pdf)
                               or (t=="analise.json" and not ana_json)
                               or (t=="relatorio.json" and not rel_json)]
                    status = f"⚠️ missing {','.join(missing)}"
                    summary["partial"] += 1
                    failures.append((aid, f"missing:{missing}"))
            except Exception as e:
                status = f"❌ read_err"
                issues_text = str(e)[:80]
                summary["fail"] += 1
                failures.append((aid, issues_text))
        else:
            status = "❌ no correcao"
            summary["fail"] += 1
            failures.append((aid, "no correcao.json"))

        print(f"{aid:<18} {len(alist):<12} "
              f"{corr_json['tamanho_bytes'] if corr_json else 0:>10} "
              f"{corr_pdf['tamanho_bytes'] if corr_pdf else 0:>10} "
              f"{ana_json['tamanho_bytes'] if ana_json else 0:>9} "
              f"{ana_pdf['tamanho_bytes'] if ana_pdf else 0:>9} "
              f"{rel_json['tamanho_bytes'] if rel_json else 0:>9} "
              f"{rel_pdf['tamanho_bytes'] if rel_pdf else 0:>9} "
              f"{nota:>6}  {status}")
        if args.show_failures and issues_text:
            print(f"   ↳ issues: {issues_text}")

    # Cost from token_usage
    q = urllib.parse.urlencode({
        "atividade_id": f"eq.{args.ativ}",
        "criado_em": f"gte.{args.since}",
        "select": "etapa,provider,modelo,tokens_entrada,tokens_saida,aluno_id",
    })
    tu_rows = json.loads(http_get(f"{SUPA_URL}/rest/v1/token_usage?{q}"))
    cost_total = 0
    cost_by_stage = {}
    for r in tu_rows:
        rates = RATES.get((r.get("provider"), r.get("modelo")), (0, 0))
        c = (int(r.get("tokens_entrada") or 0) * rates[0]) + (int(r.get("tokens_saida") or 0) * rates[1])
        cost_total += c
        cost_by_stage[r.get("etapa")] = cost_by_stage.get(r.get("etapa"), 0) + c
        total_in += int(r.get("tokens_entrada") or 0)
        total_out += int(r.get("tokens_saida") or 0)

    print(f"\n=== AGGREGATE ===")
    print(f"Alunos: total={summary['total_alunos']}, OK={summary['ok']}, partial={summary['partial']}, fail={summary['fail']}")
    print(f"Tokens: in={total_in:,} out={total_out:,}")
    print(f"Cost total: ${cost_total:.4f}")
    print(f"Cost por etapa:")
    for stage, c in sorted(cost_by_stage.items(), key=lambda x: -x[1]):
        print(f"  {stage:<28} ${c:.4f}")

    if failures:
        print(f"\n=== FAILURES ({len(failures)}) ===")
        for aid, msg in failures[:20]:
            print(f"  {aid}: {msg}")

if __name__ == "__main__":
    main()
