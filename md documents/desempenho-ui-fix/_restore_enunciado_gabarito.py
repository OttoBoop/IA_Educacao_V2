#!/usr/bin/env python3
"""Restore enunciado and gabarito records for Lista0 (Álgebra Linear Avançada).

The DB rows were lost during the 2026-05-20 incident. The physical PDFs
remain in Supabase Storage under
  arquivos/57861d16958965d2/3f3ab03dfe783f30/126e8b5ad7dd6d59/_base/

(with sanitized non-accented filenames). This script reinserts the two
`documentos` rows pointing at those physical files so the pipeline can
read them again.

Idempotent: uses on_conflict=ignore-duplicates.

Source of truth for ids and metadata:
  prova-ia-v2/md documents/algebra-linear-providers-mapping/_raw_lista0_docs_2026-05-20.json
"""
import json
import urllib.request
import urllib.error
from pathlib import Path

SUPA_URL = Path("/tmp/supa/url.txt").read_text().strip()
SUPA_KEY = Path("/tmp/supa/key.txt").read_text().strip()

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
}


def upsert(table, row, conflict_col="id"):
    body = json.dumps([row]).encode()
    hdrs = dict(HEADERS)
    hdrs["Prefer"] = "resolution=ignore-duplicates,return=representation"
    req = urllib.request.Request(
        f"{SUPA_URL}/rest/v1/{table}?on_conflict={conflict_col}",
        data=body, method="POST", headers=hdrs,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


ATIVIDADE_ID = "126e8b5ad7dd6d59"
TURMA_ID = "3f3ab03dfe783f30"
MATERIA_ID = "57861d16958965d2"
_BASE = f"arquivos/{MATERIA_ID}/{TURMA_ID}/{ATIVIDADE_ID}/_base"

# Storage filenames are sanitized (no accents) — must match exactly.
docs = [
    {
        "id": "5dc75513e958c25b",
        "tipo": "enunciado",
        "atividade_id": ATIVIDADE_ID,
        "aluno_id": None,
        "nome_arquivo": "Enunciado - Algebra Linear Avancada - 2026-1_b709.pdf",
        "caminho_arquivo": f"{_BASE}/Enunciado - Algebra Linear Avancada - 2026-1_b709.pdf",
        "extensao": ".pdf",
        "tamanho_bytes": 116026,
        "status": "concluido",
        "criado_por": "usuario",
        "criado_em": "2026-04-13T13:38:55.457000+00:00",
        "atualizado_em": "2026-04-13T13:38:55.457000+00:00",
        "versao": 1,
        "metadata": {"restored_from": "incidente_2026_05_20", "restored_at": "2026-05-27"},
    },
    {
        "id": "dbfe3a77a631489f",
        "tipo": "gabarito",
        "atividade_id": ATIVIDADE_ID,
        "aluno_id": None,
        "nome_arquivo": "Gabarito - Algebra Linear Avancada - 2026-1_013d.pdf",
        "caminho_arquivo": f"{_BASE}/Gabarito - Algebra Linear Avancada - 2026-1_013d.pdf",
        "extensao": ".pdf",
        "tamanho_bytes": 111666,
        "status": "concluido",
        "criado_por": "usuario",
        "criado_em": "2026-04-13T13:39:14.760000+00:00",
        "atualizado_em": "2026-04-13T13:39:14.760000+00:00",
        "versao": 1,
        "metadata": {"restored_from": "incidente_2026_05_20", "restored_at": "2026-05-27"},
    },
]

for d in docs:
    code, body = upsert("documentos", d)
    print(f"{d['tipo']:10s} id={d['id']}  HTTP {code}  {body[:200]}")

# Verify via storage listing
import urllib.parse
for d in docs:
    path = d["caminho_arquivo"]
    url = f"{SUPA_URL}/storage/v1/object/info/documentos/{urllib.parse.quote(path)}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            info = json.loads(r.read())
            print(f"  Storage check: {d['tipo']} size={info.get('size')} mimetype={info.get('mimetype') or info.get('contentType')}")
    except urllib.error.HTTPError as e:
        print(f"  Storage check FAIL: {d['tipo']} HTTP {e.code} {e.read().decode()[:200]}")
