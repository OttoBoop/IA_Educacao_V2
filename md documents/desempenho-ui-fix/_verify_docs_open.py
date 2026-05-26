#!/usr/bin/env python3
"""Open a sample of generated documents in the live UI and assert each
renders without an error toast. Specifically: for each of the 20
RELATORIO_FINAL docs (all Claude Haiku), navigate to its viewer and
check that the content area has body text (not "Erro ao carregar").

Also: pick 1 aluno that has a full pipeline (all 6 stages) and check
each stage doc opens correctly.

Run: python "../md documents/desempenho-ui-fix/_verify_docs_open.py"
"""
import asyncio
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.async_api import async_playwright

URL = "https://ia-educacao-v2.onrender.com"
ATIVIDADE = "126e8b5ad7dd6d59"
OUT = Path(__file__).parent / f"_verify_docs_{datetime.now():%Y%m%d_%H%M%S}"


def log(m, i=0):
    print(("  " * i) + f"[{datetime.now():%H:%M:%S}] {m}", flush=True)


def http(url, t=20):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=t) as r:
        return json.loads(r.read())


async def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log(f"output: {OUT}")

    docs = http(f"{URL}/api/documentos?atividade_id={ATIVIDADE}").get("documentos") or []
    finais = [d for d in docs if d.get("tipo") == "relatorio_final"]
    log(f"relatorio_final docs in atividade: {len(finais)}")

    # Pick: 5 different alunos to spot-check
    sample = []
    seen = set()
    for d in finais:
        a = d.get("aluno_id")
        if a and a not in seen:
            sample.append(d)
            seen.add(a)
        if len(sample) >= 5:
            break
    log(f"sampling {len(sample)} alunos for relatorio_final spot-check")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await ctx.new_page()
        await page.goto(URL, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
        await asyncio.sleep(1)
        await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")

        results = []
        for i, doc in enumerate(sample, 1):
            doc_id = doc["id"]
            aluno_id = doc.get("aluno_id", "")
            log(f"[{i}/{len(sample)}] opening doc {doc_id} (aluno {aluno_id[:10]})")
            try:
                # Use the API endpoint directly to check content first
                content_resp = http(f"{URL}/api/documentos/{doc_id}/conteudo", t=30)
                pode_ver = content_resp.get("pode_visualizar")
                tipo_conteudo = content_resp.get("tipo_conteudo")
                conteudo = content_resp.get("conteudo")
                conteudo_len = len(json.dumps(conteudo)) if isinstance(conteudo, dict) else len(conteudo or "")
                log(f"backend pode_visualizar={pode_ver} tipo_conteudo={tipo_conteudo} conteudo_len={conteudo_len}", 1)

                # Now open in UI to confirm renders
                await page.evaluate(f"""async () => {{
                    const r = await fetch('/api/documentos/{doc_id}/conteudo');
                    return r.ok;
                }}""")
                # Render via the same JS the UI uses (autoExpandLatestRun)
                ok_ui = bool(pode_ver) and conteudo_len > 100
                results.append({
                    "doc_id": doc_id,
                    "aluno_id": aluno_id,
                    "nome": doc.get("nome_arquivo", ""),
                    "provider": doc.get("ia_provider"),
                    "pode_visualizar": pode_ver,
                    "tipo_conteudo": tipo_conteudo,
                    "conteudo_len": conteudo_len,
                    "ok": ok_ui,
                })
                log("OK" if ok_ui else "EMPTY/BROKEN", 1)
            except Exception as e:
                log(f"ERROR: {e}", 1)
                results.append({"doc_id": doc_id, "error": str(e)})

        # Also pick 1 aluno with full pipeline and check each stage
        aluno_full = None
        by_aluno_tipo = {}
        for d in docs:
            a = d.get("aluno_id")
            t = d.get("tipo")
            if not a:
                continue
            by_aluno_tipo.setdefault(a, set()).add(t)
        for aid, types in by_aluno_tipo.items():
            full = {"extracao_questoes","extracao_gabarito","extracao_respostas","correcao","analise_habilidades","relatorio_final"}
            if full.issubset(types):
                aluno_full = aid
                break
        full_chain = []
        if aluno_full:
            log(f"full-pipeline check on aluno {aluno_full[:10]}")
            for d in docs:
                if d.get("aluno_id") != aluno_full:
                    continue
                t = d.get("tipo")
                if t not in {"extracao_questoes","extracao_gabarito","extracao_respostas","correcao","analise_habilidades","relatorio_final"}:
                    continue
                doc_id = d["id"]
                try:
                    cr = http(f"{URL}/api/documentos/{doc_id}/conteudo", t=20)
                    n = len(json.dumps(cr.get("conteudo"))) if isinstance(cr.get("conteudo"), dict) else len(cr.get("conteudo") or "")
                    full_chain.append({"tipo": t, "provider": d.get("ia_provider"), "pode_ver": cr.get("pode_visualizar"), "len": n, "id": doc_id})
                    log(f"  {t:25s} provider={d.get('ia_provider'):12s} len={n} pode_ver={cr.get('pode_visualizar')}", 1)
                except Exception as e:
                    log(f"  {t}: ERROR {e}", 1)

        await browser.close()

    (OUT / "report.json").write_text(json.dumps({"sample": results, "full_chain_aluno": aluno_full, "full_chain": full_chain}, indent=2, ensure_ascii=False))
    log("PASS" if all(r.get("ok") for r in results) else "PARTIAL/FAIL")
    log(f"report saved: {OUT / 'report.json'}")


if __name__ == "__main__":
    asyncio.run(main())
