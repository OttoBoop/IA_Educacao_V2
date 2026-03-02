"""
Backfill migration script: generate display_names for existing documents.

Reads all documents from the database that have empty display_names,
resolves the metadata chain (atividade → turma → matéria, aluno),
and generates structured display_names using build_display_name().

Does NOT rename physical files — only updates the display_name field in DB.

Usage:
    cd IA_Educacao_V2/backend
    python scripts/backfill_display_names.py [--dry-run]

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F7-T1)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from typing import Dict, Any

from storage import StorageManager, build_display_name
from models import TipoDocumento


def backfill_display_names(storage: StorageManager, dry_run: bool = False) -> Dict[str, Any]:
    """Backfill display_names for all documents with empty display_name.

    Args:
        storage: A StorageManager instance (SQLite or PostgreSQL).
        dry_run: If True, report what would change but don't update DB.

    Returns:
        Summary dict with keys: updated, skipped, errors, total.
    """
    updated = 0
    skipped = 0
    errors = 0
    total = 0

    # Build a cache for metadata lookups to avoid repeated DB hits
    atividade_cache = {}
    turma_cache = {}
    materia_cache = {}
    aluno_cache = {}

    # Iterate through all atividades to find all documents
    materias = storage.listar_materias()
    for materia in materias:
        turmas = storage.listar_turmas(materia.id)
        for turma in turmas:
            atividades = storage.listar_atividades(turma.id)
            for atividade in atividades:
                # Cache the hierarchy
                atividade_cache[atividade.id] = atividade
                turma_cache[turma.id] = turma
                materia_cache[materia.id] = materia

                docs = storage.listar_documentos(atividade.id)
                for doc in docs:
                    total += 1

                    # Skip docs that already have a display_name
                    if doc.display_name:
                        skipped += 1
                        continue

                    # Resolve aluno
                    aluno_nome = None
                    if doc.aluno_id:
                        if doc.aluno_id not in aluno_cache:
                            aluno_cache[doc.aluno_id] = storage.get_aluno(doc.aluno_id)
                        aluno = aluno_cache[doc.aluno_id]
                        aluno_nome = aluno.nome if aluno else None

                    # Build display_name
                    new_display_name = build_display_name(
                        tipo=doc.tipo,
                        aluno_nome=aluno_nome,
                        materia_nome=materia.nome,
                        turma_nome=turma.nome,
                    )

                    if not dry_run:
                        _update_display_name(storage, doc.id, new_display_name)

                    updated += 1

    # Also handle orphaned documents (atividade_id doesn't match any known atividade)
    orphan_result = _backfill_orphaned_docs(storage, atividade_cache, dry_run)
    updated += orphan_result["updated"]
    errors += orphan_result["errors"]
    total += orphan_result["total"]

    return {
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "total": total,
    }


def _backfill_orphaned_docs(
    storage: StorageManager,
    known_atividade_ids: dict,
    dry_run: bool,
) -> Dict[str, int]:
    """Find and backfill documents whose atividade_id doesn't match any known atividade."""
    updated = 0
    errors = 0
    total = 0

    if storage.use_postgresql:
        return {"updated": 0, "errors": 0, "total": 0}

    conn = storage._get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM documentos WHERE (display_name IS NULL OR display_name = '')"
        ).fetchall()

        for row in rows:
            row_dict = dict(row)
            doc_id = row_dict["id"]
            atividade_id = row_dict.get("atividade_id")

            # Skip if already processed via hierarchy traversal
            if atividade_id in known_atividade_ids:
                continue

            total += 1

            # Resolve what we can
            tipo_str = row_dict.get("tipo", "")
            try:
                tipo = TipoDocumento(tipo_str)
            except ValueError:
                tipo_label = tipo_str or "Documento"
                new_display_name = tipo_label
                if not dry_run:
                    _update_display_name(storage, doc_id, new_display_name)
                errors += 1
                continue

            # Try to resolve metadata chain even for orphaned docs
            aluno_nome = None
            materia_nome = None
            turma_nome = None

            aluno_id = row_dict.get("aluno_id")
            if aluno_id:
                aluno = storage.get_aluno(aluno_id)
                aluno_nome = aluno.nome if aluno else "[Aluno desconhecido]"

            atividade = storage.get_atividade(atividade_id) if atividade_id else None
            if atividade:
                turma = storage.get_turma(atividade.turma_id)
                if turma:
                    turma_nome = turma.nome
                    materia = storage.get_materia(turma.materia_id)
                    materia_nome = materia.nome if materia else "[Matéria desconhecida]"
                else:
                    turma_nome = "[Turma desconhecida]"
                    materia_nome = "[Matéria desconhecida]"
            else:
                materia_nome = "[Matéria desconhecida]"
                turma_nome = "[Turma desconhecida]"

            new_display_name = build_display_name(
                tipo=tipo,
                aluno_nome=aluno_nome,
                materia_nome=materia_nome,
                turma_nome=turma_nome,
            )

            if not dry_run:
                _update_display_name(storage, doc_id, new_display_name)

            updated += 1
    finally:
        conn.close()

    return {"updated": updated, "errors": errors, "total": total}


def _update_display_name(storage: StorageManager, doc_id: str, display_name: str):
    """Update a document's display_name in the database."""
    if storage.use_postgresql:
        from supabase_db import supabase_db
        supabase_db.update("documentos", doc_id, {
            "display_name": display_name,
            "atualizado_em": datetime.now().isoformat(),
        })
    else:
        conn = storage._get_connection()
        conn.execute(
            "UPDATE documentos SET display_name = ?, atualizado_em = ? WHERE id = ?",
            (display_name, datetime.now().isoformat(), doc_id)
        )
        conn.commit()
        conn.close()


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Backfill display_names for existing documents")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without modifying DB")
    args = parser.parse_args()

    storage = StorageManager()
    print(f"Starting backfill{'  (DRY RUN)' if args.dry_run else ''}...")

    result = backfill_display_names(storage, dry_run=args.dry_run)

    print(f"\nBackfill complete:")
    print(f"  Total documents: {result['total']}")
    print(f"  Updated: {result['updated']}")
    print(f"  Skipped (already had name): {result['skipped']}")
    print(f"  Errors: {result['errors']}")


if __name__ == "__main__":
    main()
