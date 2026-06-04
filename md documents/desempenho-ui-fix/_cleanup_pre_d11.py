#!/usr/bin/env python3
"""Cleanup pre-D11 generated docs for Lista0 (atividade 126e8b5ad7dd6d59).

D11 (2026-05-27) restored enunciado + gabarito after they were lost in the
2026-05-20 incident. Every pipeline-generated doc created BEFORE D11 ran
without the real input PDFs, so providers hallucinated questions and
gabarito. Those docs (and any correcao/analise/relatorio that consumed
them) are forensically invalid.

Target for deletion (DB rows only, Storage objects preserved):
- atividade_id = Lista0 (126e8b5ad7dd6d59)
- tipo in {EXTRACAO_QUESTOES, EXTRACAO_GABARITO, EXTRACAO_RESPOSTAS,
           CORRECAO, ANALISE_HABILIDADES, RELATORIO_FINAL}
- criado_em < 2026-05-27T00:00:00+00:00

Preserve:
- prova_respondida (student upload)
- enunciado + gabarito (D11 restored)
- All docs from 2026-05-27 onward

Idempotent. Audit before+after. Batches DELETEs to keep PostgREST IN(...) short.
"""
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

SUPA_URL = Path("/tmp/supa/url.txt").read_text().strip()
SUPA_KEY = Path("/tmp/supa/key.txt").read_text().strip()
ATIVIDADE_ID = "126e8b5ad7dd6d59"
CUTOFF = "2026-05-27T00:00:00"
TIPOS_PIPELINE = (
    "extracao_questoes,extracao_gabarito,extracao_respostas,"
    "correcao,analise_habilidades,relatorio_final"
)

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
}


def http(method, url, timeout=60, body=None):
    req = urllib.request.Request(url, method=method, headers=HEADERS,
                                  data=body.encode() if body else None)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def audit(label):
    q = urllib.parse.urlencode({
        "atividade_id": f"eq.{ATIVIDADE_ID}",
        "tipo": f"in.({TIPOS_PIPELINE})",
        "criado_em": f"lt.{CUTOFF}",
        "select": "id,tipo,ia_provider,criado_em",
    })
    url = f"{SUPA_URL}/rest/v1/documentos?{q}&limit=10000"
    rows = json.loads(http("GET", url))
    print(f"\n=== {label} ===")
    print(f"Total pre-D11 generated docs: {len(rows)}")
    by_tipo = {}
    by_prov = {}
    for r in rows:
        by_tipo[r["tipo"]] = by_tipo.get(r["tipo"], 0) + 1
        prov = r.get("ia_provider") or "NULL"
        by_prov[prov] = by_prov.get(prov, 0) + 1
    for t, n in sorted(by_tipo.items(), key=lambda kv: -kv[1]):
        print(f"  {t:<24s} {n}")
    print("  By provider:")
    for p, n in sorted(by_prov.items(), key=lambda kv: -kv[1]):
        print(f"    {p:<12s} {n}")
    return rows


def main():
    print(f"Cleanup pre-D11 docs for atividade {ATIVIDADE_ID}")
    print(f"Cutoff: criado_em < {CUTOFF}")
    print(f"Tipos: {TIPOS_PIPELINE}")

    rows = audit("BEFORE")
    if not rows:
        print("\nNothing to delete. Exiting.")
        return

    ids = [r["id"] for r in rows]
    print(f"\nDeleting {len(ids)} rows in batches of 100...")

    deleted_total = 0
    BATCH = 100
    for i in range(0, len(ids), BATCH):
        batch_ids = ids[i:i + BATCH]
        # PostgREST IN syntax: id=in.(id1,id2,...)
        in_clause = ",".join(batch_ids)
        q = urllib.parse.urlencode({
            "id": f"in.({in_clause})",
            "atividade_id": f"eq.{ATIVIDADE_ID}",  # safety
        })
        url = f"{SUPA_URL}/rest/v1/documentos?{q}"
        try:
            http("DELETE", url, timeout=60)
            deleted_total += len(batch_ids)
            print(f"  batch {i // BATCH + 1}: deleted {len(batch_ids)} (total {deleted_total}/{len(ids)})")
        except Exception as e:
            print(f"  batch {i // BATCH + 1} FAILED: {e}")
            print(f"    sample id: {batch_ids[0]}")
            sys.exit(1)

    print(f"\nDeletion complete: {deleted_total} rows")
    audit("AFTER")
    print("\nNote: Supabase Storage objects (PDF/JSON files) are NOT deleted by")
    print("this script. They remain accessible via storage paths but are now")
    print("orphaned from the documentos table. No further action needed unless")
    print("storage quota becomes an issue.")


if __name__ == "__main__":
    main()
