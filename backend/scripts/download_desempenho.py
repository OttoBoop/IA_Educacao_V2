#!/usr/bin/env python3
"""
Download all desempenho documents from the live IA-Educacao-V2 server.

Downloads both JSON and PDF files to test_downloads/desempenho/
Usage: python scripts/download_desempenho.py
"""

import requests
import json
import os
from pathlib import Path
from datetime import datetime

LIVE_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_DIR = Path(__file__).parent.parent / "test_downloads" / "desempenho"

DESEMPENHO_TIPOS = [
    "relatorio_desempenho_tarefa",
    "relatorio_desempenho_turma",
    "relatorio_desempenho_materia",
]


def fetch_json(url: str, params=None) -> dict:
    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return {}


def download_file(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, timeout=60, stream=True)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        size_kb = dest.stat().st_size // 1024
        print(f"  ✅ Saved {dest.name} ({size_kb} KB)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to download {dest.name}: {e}")
        return False


def get_all_desempenho_docs() -> list:
    """Fetch all documents and filter to desempenho types."""
    print("\n📋 Fetching all matérias, turmas, atividades...")

    # Get materias
    materias_data = fetch_json(f"{LIVE_URL}/api/materias")
    materias = materias_data.get("materias", [])
    print(f"  Found {len(materias)} matérias")

    # Get turmas
    turmas_data = fetch_json(f"{LIVE_URL}/api/turmas")
    turmas = turmas_data.get("turmas", [])
    print(f"  Found {len(turmas)} turmas")

    # Get atividades from each turma
    atividades = []
    for turma in turmas:
        t_ativs = fetch_json(f"{LIVE_URL}/api/atividades", params={"turma_id": turma["id"]})
        atividades.extend(t_ativs.get("atividades", []))
    print(f"  Found {len(atividades)} atividades total")

    # Now fetch desempenho documents for each entity
    desempenho_docs = []

    print("\n🔍 Checking desempenho endpoints for each entity...")

    # Check tarefa level for each atividade
    for ativ in atividades:
        data = fetch_json(f"{LIVE_URL}/api/desempenho/tarefa/{ativ['id']}")
        runs = data.get("runs", [])
        if runs:
            print(f"  📁 Atividade '{ativ.get('nome', ativ['id'])}': {len(runs)} run(s)")
            for run in runs:
                for doc in run.get("docs", []):
                    doc["_entity_type"] = "tarefa"
                    doc["_entity_nome"] = ativ.get("nome", ativ["id"])
                    desempenho_docs.append(doc)

    # Check turma level
    for turma in turmas:
        data = fetch_json(f"{LIVE_URL}/api/desempenho/turma/{turma['id']}")
        runs = data.get("runs", [])
        if runs:
            print(f"  📁 Turma '{turma.get('nome', turma['id'])}': {len(runs)} run(s)")
            for run in runs:
                for doc in run.get("docs", []):
                    doc["_entity_type"] = "turma"
                    doc["_entity_nome"] = turma.get("nome", turma["id"])
                    desempenho_docs.append(doc)

    # Check materia level
    for materia in materias:
        data = fetch_json(f"{LIVE_URL}/api/desempenho/materia/{materia['id']}")
        runs = data.get("runs", [])
        if runs:
            print(f"  📁 Matéria '{materia.get('nome', materia['id'])}': {len(runs)} run(s)")
            for run in runs:
                for doc in run.get("docs", []):
                    doc["_entity_type"] = "materia"
                    doc["_entity_nome"] = materia.get("nome", materia["id"])
                    desempenho_docs.append(doc)

    # Fallback: if no docs found via desempenho endpoints, fetch all docs and filter
    if not desempenho_docs:
        print("\n⚠️  No docs found via desempenho endpoints. Falling back to /api/documentos/todos ...")
        # Try fetching all documents with type filter
        all_docs_data = fetch_json(f"{LIVE_URL}/api/documentos/todos")
        all_docs = all_docs_data.get("documentos", [])
        desempenho_docs = [
            d for d in all_docs
            if d.get("tipo", "").startswith("relatorio_desempenho")
        ]
        print(f"  Found {len(desempenho_docs)} desempenho docs in /api/documentos/todos")

    return desempenho_docs, materias, turmas, atividades


def download_doc(doc: dict, subfolder: str) -> dict:
    """Download a single document (JSON content + file download)."""
    doc_id = doc.get("id")
    tipo = doc.get("tipo", "unknown")
    nome = doc.get("nome_arquivo", doc.get("filename", f"{tipo}_{doc_id}"))
    ext = Path(nome).suffix if nome else ".bin"

    result = {"id": doc_id, "tipo": tipo, "nome": nome, "downloads": []}

    # Download the actual file
    dest_path = OUTPUT_DIR / subfolder / nome
    ok = download_file(f"{LIVE_URL}/api/documentos/{doc_id}/download", dest_path)
    if ok:
        result["downloads"].append(str(dest_path))

    # Also get JSON content via visualizar endpoint
    if ext == ".json" or ".json" in nome:
        viz = fetch_json(f"{LIVE_URL}/api/documentos/{doc_id}/visualizar")
        conteudo = viz.get("conteudo")
        if conteudo:
            json_path = OUTPUT_DIR / subfolder / f"{doc_id}_conteudo.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(conteudo, f, ensure_ascii=False, indent=2)
            result["downloads"].append(str(json_path))

    return result


def main():
    print("=" * 60)
    print("🚀 Desempenho Document Downloader")
    print(f"   Target: {LIVE_URL}")
    print(f"   Output: {OUTPUT_DIR}")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    desempenho_docs, materias, turmas, atividades = get_all_desempenho_docs()

    if not desempenho_docs:
        print("\n❌ No desempenho documents found on the live server.")
        print("\nThis means the pipeline either:")
        print("  1. Has never been run (not triggered by user)")
        print("  2. Failed silently (executor method missing)")
        print("  3. Documents stored under different tipo values")
        print(f"\n  Materias found: {len(materias)}")
        print(f"  Turmas found: {len(turmas)}")
        print(f"  Atividades found: {len(atividades)}")
        return

    print(f"\n📥 Downloading {len(desempenho_docs)} desempenho documents...")
    summary = []

    for doc in desempenho_docs:
        entity_type = doc.get("_entity_type", "unknown")
        entity_nome = doc.get("_entity_nome", "")
        tipo = doc.get("tipo", "unknown")
        print(f"\n  [{entity_type.upper()}] {entity_nome} — {tipo}")
        result = download_doc(doc, subfolder=entity_type)
        summary.append(result)

    # Save summary
    summary_path = OUTPUT_DIR / f"download_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "live_url": LIVE_URL,
            "total_docs": len(desempenho_docs),
            "downloads": summary
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Done! Summary saved to {summary_path}")
    print(f"\n📊 Download Summary:")
    print(f"   Total documents: {len(desempenho_docs)}")
    print(f"   Output directory: {OUTPUT_DIR}")
    
    # Print file list
    all_files = list(OUTPUT_DIR.rglob("*"))
    print(f"\n📁 All downloaded files ({len(all_files)}):")
    for f in sorted(all_files):
        if f.is_file():
            size_kb = f.stat().st_size // 1024
            print(f"   {f.relative_to(OUTPUT_DIR)} ({size_kb} KB)")


if __name__ == "__main__":
    main()
