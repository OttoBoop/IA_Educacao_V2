#!/usr/bin/env python3
"""Audit every relatorio_final + correcao in atividade Lista0 and produce a
detailed JSON + markdown summary. Records:
- Per aluno: nota_final, provider/model, retries count per stage, missing-content avisos
- Per provider: total docs, tokens, estimated cost from catalog rates
- Hallucination flag: questao with `resposta_correta` non-empty in correcao while
  the same questao had MISSING_CONTENT in extracao_gabarito (= provider invented)
"""
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

URL = "https://ia-educacao-v2.onrender.com"
ATIVIDADE = "126e8b5ad7dd6d59"
TURMA = "3f3ab03dfe783f30"
OUT = Path(__file__).parent / f"_audit_{datetime.now():%Y%m%d_%H%M%S}"

RATES = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "gemini-3-flash-preview":    (0.50, 3.00),
    "gpt-5-nano":                (0.05, 0.40),
    "gpt-5.4-mini":              (0.75, 4.50),
}

STAGES_ALUNO = [
    "extracao_respostas",
    "correcao",
    "analise_habilidades",
    "relatorio_final",
]
STAGES_ATIVIDADE = ["extracao_questoes", "extracao_gabarito"]


def http(url, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def cost(modelo, tin, tout):
    rin, rout = RATES.get(modelo, (0, 0))
    return (tin * rin + tout * rout) / 1_000_000.0


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"output: {OUT}")

    # Fetch all docs
    docs = http(f"{URL}/api/documentos?atividade_id={ATIVIDADE}").get("documentos") or []
    print(f"total docs: {len(docs)}")

    # Fetch students
    alunos = http(f"{URL}/api/alunos?turma_id={TURMA}").get("alunos") or []
    nome_by_id = {a["id"]: a.get("nome", a["id"]) for a in alunos}
    print(f"alunos: {len(alunos)}")

    # Group docs by aluno_id (or activity-level for questoes/gabarito)
    activity_level = [d for d in docs if not d.get("aluno_id") and d.get("tipo") in STAGES_ATIVIDADE]
    per_aluno = defaultdict(list)
    for d in docs:
        a = d.get("aluno_id")
        if a:
            per_aluno[a].append(d)

    # Aggregate per (provider, model) totals
    prov_totals = defaultdict(lambda: {
        "docs": 0, "tok_in": 0, "tok_out": 0, "cost": 0.0,
        "stages": defaultdict(lambda: {"docs": 0, "tok_in": 0, "tok_out": 0, "cost": 0.0, "first": None, "last": None}),
        "first": None, "last": None,
    })

    for d in docs:
        ia = d.get("ia_provider")
        modelo = d.get("ia_modelo")
        if not ia or not modelo:
            continue
        t = d.get("tipo")
        if t in ("prova_respondida", "enunciado", "gabarito"):
            continue
        meta = d.get("metadata") or {}
        tin = int(meta.get("tokens_entrada") or 0)
        tout = int(meta.get("tokens_saida") or 0)
        c = cost(modelo, tin, tout)
        ts = d.get("criado_em", "")

        key = (ia, modelo)
        pt = prov_totals[key]
        pt["docs"] += 1
        pt["tok_in"] += tin
        pt["tok_out"] += tout
        pt["cost"] += c
        if not pt["first"] or ts < pt["first"]:
            pt["first"] = ts
        if not pt["last"] or ts > pt["last"]:
            pt["last"] = ts

        sb = pt["stages"][t]
        sb["docs"] += 1
        sb["tok_in"] += tin
        sb["tok_out"] += tout
        sb["cost"] += c
        if not sb["first"] or ts < sb["first"]:
            sb["first"] = ts
        if not sb["last"] or ts > sb["last"]:
            sb["last"] = ts

    # Find MISSING_CONTENT in extracao_gabarito (the truth from the prof PDF)
    # Pick the most recent gabarito to read which questions are reportedly missing
    gab_docs = [d for d in activity_level if d.get("tipo") == "extracao_gabarito" and d.get("extensao") == ".json"]
    gab_docs.sort(key=lambda x: x.get("criado_em", ""), reverse=True)

    missing_in_gabarito_truth = set()
    if gab_docs:
        try:
            gab_content = http(f"{URL}/api/documentos/{gab_docs[0]['id']}/conteudo").get("conteudo") or {}
            for av in (gab_content.get("_avisos_questao") or []):
                if isinstance(av, dict) and str(av.get("codigo", "")).upper() == "MISSING_CONTENT":
                    missing_in_gabarito_truth.add(int(av.get("questao")))
        except Exception as e:
            print(f"warn: could not read gabarito: {e}")
    print(f"truth: questões marcadas MISSING_CONTENT no gabarito: {sorted(missing_in_gabarito_truth)}")

    # Detailed per-aluno analysis on relatorio_final docs
    relatorios = [d for d in docs if d.get("tipo") == "relatorio_final" and d.get("extensao") == ".json"]
    print(f"relatorio_final .json: {len(relatorios)}")

    per_aluno_detail = []
    halluc_total_count = 0
    for d in sorted(relatorios, key=lambda x: x.get("criado_em", "")):
        aid = d.get("aluno_id")
        nome = nome_by_id.get(aid, aid)
        # Read content
        try:
            cont = http(f"{URL}/api/documentos/{d['id']}/conteudo").get("conteudo") or {}
        except Exception as e:
            per_aluno_detail.append({"aluno_id": aid, "nome": nome, "error": str(e)})
            continue
        # Find the corresponding correcao JSON (latest)
        cors = [x for x in per_aluno[aid] if x.get("tipo") == "correcao" and x.get("extensao") == ".json"]
        cors.sort(key=lambda x: x.get("criado_em", ""), reverse=True)
        cor_content = {}
        if cors:
            try:
                cor_content = http(f"{URL}/api/documentos/{cors[0]['id']}/conteudo").get("conteudo") or {}
            except Exception:
                pass

        # Hallucination detection: questoes in correcao where resposta_correta is filled but
        # the gabarito truth marked that questao as MISSING_CONTENT
        halluc_questoes = []
        if cor_content:
            for q in (cor_content.get("questoes") or []):
                if not isinstance(q, dict):
                    continue
                num = q.get("numero")
                rc = (q.get("resposta_correta") or "").strip()
                if num in missing_in_gabarito_truth and rc and rc.upper() != "MISSING_CONTENT":
                    halluc_questoes.append(num)

        if halluc_questoes:
            halluc_total_count += 1

        # Retries count for this aluno across stages
        retries_per_stage = defaultdict(int)
        for x in per_aluno[aid]:
            t = x.get("tipo")
            if t in STAGES_ALUNO and x.get("extensao") == ".json":
                retries_per_stage[t] += 1

        per_aluno_detail.append({
            "aluno_id": aid,
            "nome": nome,
            "provider": d.get("ia_provider"),
            "modelo": d.get("ia_modelo"),
            "nota_final": cont.get("nota_final") if isinstance(cont, dict) else None,
            "resumo_geral_snippet": (cont.get("resumo_geral") or "")[:140] if isinstance(cont, dict) else None,
            "tokens_total": (d.get("metadata") or {}).get("tokens_total"),
            "criado_em": d.get("criado_em"),
            "retries": dict(retries_per_stage),
            "halluc_questoes": halluc_questoes,
        })

    summary = {
        "atividade_id": ATIVIDADE,
        "total_docs": len(docs),
        "missing_in_gabarito_truth": sorted(missing_in_gabarito_truth),
        "providers": {
            f"{ia}|{modelo}": {
                "docs": pt["docs"],
                "tok_in": pt["tok_in"],
                "tok_out": pt["tok_out"],
                "cost": round(pt["cost"], 4),
                "first": pt["first"],
                "last": pt["last"],
                "stages": {
                    t: {
                        "docs": sb["docs"],
                        "tok_in": sb["tok_in"],
                        "tok_out": sb["tok_out"],
                        "cost": round(sb["cost"], 4),
                        "first": sb["first"],
                        "last": sb["last"],
                    }
                    for t, sb in pt["stages"].items()
                },
            }
            for (ia, modelo), pt in prov_totals.items()
        },
        "alunos_com_relatorio": len(relatorios),
        "alunos_com_hallucinations_em_correcao": halluc_total_count,
        "per_aluno": per_aluno_detail,
    }

    (OUT / "audit.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"audit saved: {OUT / 'audit.json'}")
    print()
    print(f"resumo: {len(relatorios)} relatórios; {halluc_total_count} com alucinação em correcao")
    print()
    for entry in per_aluno_detail:
        if "error" in entry:
            print(f"  {entry['nome'][:35]:35s} ERROR: {entry['error']}")
            continue
        nota = entry.get("nota_final")
        nota_s = f"{nota:.2f}" if isinstance(nota, (int, float)) else "?"
        halluc = entry.get("halluc_questoes") or []
        retries = entry.get("retries") or {}
        r_corr = retries.get("correcao", 0)
        r_resp = retries.get("extracao_respostas", 0)
        print(f"  {entry['nome'][:35]:35s} nota={nota_s:>5s} halluc_Q={halluc} retries(corr={r_corr},resp={r_resp})")


if __name__ == "__main__":
    main()
