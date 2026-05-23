#!/usr/bin/env python3
"""Recover Álgebra Linear Avançada data into Supabase from local snapshot.

Insere via REST:
1. Matéria 57861d16958965d2 "Álgebra Linear Avançada"
2. Turma 3f3ab03dfe783f30 "2026-1"
3. Atividade 126e8b5ad7dd6d59 "Lista0"
4. 38 alunos (extraídos do snapshot)
5. 38 vínculos alunos_turmas
6. 66 documentos uploads (prova_respondida + enunciado + gabarito) com paths físicos preservados

PDFs físicos no Supabase Storage estão intactos — só metadata foi apagada.
"""
import json
import os
import hashlib
import sys
import urllib.request
import urllib.error
from pathlib import Path

SUPA_URL = Path("/tmp/supa/url.txt").read_text().strip()
SUPA_KEY = Path("/tmp/supa/key.txt").read_text().strip()

SNAPSHOT = Path(__file__).parent / "_raw_lista0_docs_2026-05-20.json"
CONFIRM_TOKEN = "ALGEBRA_LISTA0_2026_05_20"

HEADERS = {
    "apikey": SUPA_KEY,
    "Authorization": f"Bearer {SUPA_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

def log(msg):
    print(msg, flush=True)

def insert(table, row):
    body = json.dumps([row]).encode()
    req = urllib.request.Request(
        f"{SUPA_URL}/rest/v1/{table}",
        data=body,
        method="POST",
        headers=HEADERS,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def upsert(table, row, conflict_col="id"):
    """Insert with on-conflict do nothing."""
    body = json.dumps([row]).encode()
    hdrs = dict(HEADERS)
    hdrs["Prefer"] = f"resolution=ignore-duplicates,return=minimal"
    req = urllib.request.Request(
        f"{SUPA_URL}/rest/v1/{table}?on_conflict={conflict_col}",
        data=body,
        method="POST",
        headers=hdrs,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, ""
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

def extract_aluno_nome(filename):
    """De 'EDILTON BRANDÃO DE SOUSA - lista0_alglin.pdf_0ec2.pdf' tira 'EDILTON BRANDÃO DE SOUSA'."""
    # remove _hash.ext (the salt + final ext)
    name = filename.split(" - ", 1)[0] if " - " in filename else filename
    return name.strip()

def stable_id(*parts):
    """Generate an id compatible with StorageManager._generate_id."""
    raw = ":".join(str(part) for part in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:16]

if os.getenv("CONFIRM_SUPABASE_RECOVERY") != CONFIRM_TOKEN:
    log(
        "Recovery is disabled by default. Set "
        f"CONFIRM_SUPABASE_RECOVERY={CONFIRM_TOKEN} after PITR/backups are ruled out."
    )
    sys.exit(2)

with open(SNAPSHOT) as f:
    docs = json.load(f)["documentos"]

# Step 1: Materia
log("=== Step 1: Materia ===")
code, err = upsert("materias", {
    "id": "57861d16958965d2",
    "nome": "Álgebra Linear Avançada",
    "descricao": "Álgebra Linear mestrado EMAp",
    "nivel": "superior",
    "criado_em": "2026-04-13T12:50:46.534447+00:00",
    "atualizado_em": "2026-04-13T12:50:46.534448+00:00",
    "metadata": {},
})
log(f"  materia: HTTP {code} {err[:200]}")

# Step 2: Turma
log("=== Step 2: Turma ===")
code, err = upsert("turmas", {
    "id": "3f3ab03dfe783f30",
    "materia_id": "57861d16958965d2",
    "nome": "2026-1",
    "ano_letivo": 2026,
    "periodo": None,
    "descricao": None,
    "criado_em": "2026-04-13T13:07:59.968462+00:00",
    "atualizado_em": "2026-04-13T13:07:59.968463+00:00",
    "metadata": {},
})
log(f"  turma: HTTP {code} {err[:200]}")

# Step 3: Atividade
log("=== Step 3: Atividade ===")
code, err = upsert("atividades", {
    "id": "126e8b5ad7dd6d59",
    "turma_id": "3f3ab03dfe783f30",
    "nome": "Lista0",
    "tipo": "exercicio",
    "data_aplicacao": None,
    "data_entrega": None,
    "peso": 1,
    "nota_maxima": 10,
    "descricao": None,
    "criado_em": "2026-04-13T13:12:32.863267+00:00",
    "atualizado_em": "2026-04-13T13:12:32.863268+00:00",
    "metadata": {},
})
log(f"  atividade: HTTP {code} {err[:200]}")

# Step 4: Alunos — extrair únicos dos uploads
log("=== Step 4: Alunos ===")
provas = [d for d in docs if d["tipo"] == "prova_respondida"]
alunos_dict = {}
for d in provas:
    aid = d.get("aluno_id")
    if not aid or aid in alunos_dict:
        continue
    nome = extract_aluno_nome(d.get("nome_arquivo", "")) or f"Aluno {aid[:8]}"
    alunos_dict[aid] = nome
log(f"  alunos únicos: {len(alunos_dict)}")
ok_a = 0
for aid, nome in alunos_dict.items():
    code, err = upsert("alunos", {
        "id": aid,
        "nome": nome,
        "email": None,
        "matricula": None,
        "criado_em": "2026-04-13T14:00:00+00:00",
        "atualizado_em": "2026-04-13T14:00:00+00:00",
        "metadata": {"criado_por": "recover_2026_05_20"},
    })
    if code in (201, 204, 200, 409):
        ok_a += 1
    else:
        log(f"    aluno {aid} FAIL HTTP {code} {err[:200]}")
log(f"  alunos OK: {ok_a}/{len(alunos_dict)}")

# Step 5: Alunos_turmas vínculos
log("=== Step 5: Alunos_turmas ===")
ok_at = 0
for aid in alunos_dict:
    code, err = upsert("alunos_turmas", {
        "id": stable_id("vinculo", aid, "3f3ab03dfe783f30"),
        "aluno_id": aid,
        "turma_id": "3f3ab03dfe783f30",
        "ativo": True,
        "data_entrada": "2026-04-13T14:00:00+00:00",
        "data_saida": None,
        "observacoes": "recover_2026_05_20",
    }, conflict_col="aluno_id,turma_id")
    if code in (201, 204, 200, 409):
        ok_at += 1
    else:
        log(f"    aluno_turma {aid} FAIL HTTP {code} {err[:200]}")
log(f"  alunos_turmas OK: {ok_at}/{len(alunos_dict)}")

# Step 6: Documentos uploads (preservar tipos)
log("=== Step 6: Documentos uploads ===")
preservar_set = {"prova_respondida", "enunciado", "gabarito"}
uploads = [d for d in docs if d["tipo"] in preservar_set]
log(f"  uploads a re-inserir: {len(uploads)}")
ok_d = 0
fail_d = 0
for d in uploads:
    row = {
        "id": d["id"],
        "tipo": d["tipo"],
        "atividade_id": d.get("atividade_id"),
        "aluno_id": d.get("aluno_id"),
        "nome_arquivo": d.get("nome_arquivo", ""),
        "caminho_arquivo": d.get("caminho_arquivo", ""),
        "extensao": d.get("extensao", ""),
        "tamanho_bytes": d.get("tamanho_bytes", 0),
        "ia_provider": None,
        "ia_modelo": None,
        "prompt_usado": None,
        "prompt_versao": None,
        "tokens_usados": 0,
        "tempo_processamento_ms": 0,
        "status": d.get("status", "concluido"),
        "criado_em": d.get("criado_em"),
        "atualizado_em": d.get("atualizado_em"),
        "criado_por": "usuario",
        "versao": d.get("versao", 1),
        "documento_origem_id": d.get("documento_origem_id"),
        "metadata": d.get("metadata", {}) or {},
    }
    code, err = upsert("documentos", row)
    if code in (201, 204, 200, 409):
        ok_d += 1
    else:
        fail_d += 1
        if fail_d <= 3:
            log(f"    doc {d['id']} FAIL HTTP {code} {err[:300]}")
log(f"  docs uploads OK: {ok_d}/{len(uploads)} (fail={fail_d})")

log("=== Recovery DONE ===")
