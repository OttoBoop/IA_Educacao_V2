"""
Script para limpar documentos órfãos (banco tem registro mas arquivo não existe)

Uso:
    python limpar_orfaos.py --url https://ia-educacao-v2.onrender.com
    python limpar_orfaos.py --url http://localhost:8000 --dry-run
"""

import requests
import argparse
from typing import List, Dict

def get_all_documents(base_url: str) -> List[Dict]:
    """Busca todos os documentos de todas as atividades"""
    print("Buscando árvore de navegação...")
    r = requests.get(f"{base_url}/api/navegacao/arvore", timeout=30)
    r.raise_for_status()
    tree = r.json()

    all_docs = []
    for materia in tree.get("materias", []):
        for turma in materia.get("turmas", []):
            for atividade in turma.get("atividades", []):
                atividade_id = atividade["id"]
                print(f"  Buscando docs de {atividade['nome']}...")

                r = requests.get(
                    f"{base_url}/api/documentos",
                    params={"atividade_id": atividade_id},
                    timeout=30
                )
                if r.status_code == 200:
                    docs = r.json().get("documentos", [])
                    all_docs.extend(docs)

    return all_docs

def check_file_exists(base_url: str, doc_id: str) -> bool:
    """Verifica se o arquivo do documento existe"""
    r = requests.get(
        f"{base_url}/api/documentos/{doc_id}/download",
        timeout=30,
        stream=True
    )
    return r.status_code == 200

def delete_document(base_url: str, doc_id: str) -> bool:
    """Deleta um documento"""
    r = requests.delete(f"{base_url}/api/documentos/{doc_id}", timeout=30)
    return r.status_code == 200

def main():
    parser = argparse.ArgumentParser(description="Limpar documentos órfãos")
    parser.add_argument("--url", required=True, help="URL base da API")
    parser.add_argument("--dry-run", action="store_true", help="Apenas simular, não deletar")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    print(f"URL: {base_url}")
    print(f"Modo: {'DRY-RUN (simulação)' if args.dry_run else 'REAL (vai deletar!)'}")
    print("=" * 60)

    # Buscar todos os documentos
    docs = get_all_documents(base_url)
    print(f"\nTotal de documentos no banco: {len(docs)}")

    # Verificar quais não existem
    orphans = []
    for i, doc in enumerate(docs):
        doc_id = doc["id"]
        nome = doc.get("nome_arquivo", "?")
        tipo = doc.get("tipo", "?")

        exists = check_file_exists(base_url, doc_id)
        status = "OK" if exists else "ÓRFÃO"

        if not exists:
            orphans.append(doc)

        print(f"  [{i+1}/{len(docs)}] {tipo}: {nome} - {status}")

    print("\n" + "=" * 60)
    print(f"Documentos OK: {len(docs) - len(orphans)}")
    print(f"Documentos ÓRFÃOS: {len(orphans)}")

    if not orphans:
        print("\nNenhum documento órfão encontrado!")
        return

    # Deletar órfãos
    if args.dry_run:
        print("\n[DRY-RUN] Documentos que seriam deletados:")
        for doc in orphans:
            print(f"  - {doc['tipo']}: {doc['nome_arquivo']} (ID: {doc['id']})")
    else:
        print(f"\nDeletando {len(orphans)} documentos órfãos...")
        deleted = 0
        for doc in orphans:
            if delete_document(base_url, doc["id"]):
                print(f"  Deletado: {doc['nome_arquivo']}")
                deleted += 1
            else:
                print(f"  ERRO ao deletar: {doc['nome_arquivo']}")

        print(f"\nTotal deletado: {deleted}/{len(orphans)}")

if __name__ == "__main__":
    main()
