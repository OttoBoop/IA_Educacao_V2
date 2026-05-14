"""
Measured cost helpers for NOVO CR.

This module only calculates cost from measured token splits. It does not
invent input/output splits from legacy total-only token counts.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, Optional

from model_catalog import model_catalog
from models import Documento
from storage import storage


def _metadata(doc: Documento) -> Dict[str, Any]:
    return doc.metadata if isinstance(doc.metadata, dict) else {}


def _token_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _cost_for(doc: Documento, metadata: Dict[str, Any]) -> Dict[str, Any]:
    input_tokens = _token_int(metadata.get("tokens_entrada"))
    output_tokens = _token_int(metadata.get("tokens_saida"))
    total_tokens = _token_int(metadata.get("tokens_total") or doc.tokens_usados)

    base = {
        "documento_id": doc.id,
        "tipo": doc.tipo.value,
        "atividade_id": doc.atividade_id,
        "aluno_id": doc.aluno_id,
        "provider": doc.ia_provider,
        "modelo": doc.ia_modelo,
        "tokens_entrada": input_tokens,
        "tokens_saida": output_tokens,
        "tokens_total": total_tokens,
        "cost_run_id": metadata.get("cost_run_id") or doc.id,
        "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
    }

    if not doc.ia_provider or not doc.ia_modelo:
        return {**base, "custo_status": "blocked", "erro": "provider_model_missing"}

    if input_tokens <= 0 and output_tokens <= 0:
        return {**base, "custo_status": "blocked", "erro": "token_split_missing"}

    model_ref = f"{doc.ia_provider}/{doc.ia_modelo}"
    estimated = model_catalog.calculate_cost(
        model_ref=model_ref,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        requests_per_day=1,
    )
    if "error" in estimated:
        return {**base, "custo_status": "blocked", "erro": "pricing_missing", "model_ref": model_ref}

    return {
        **base,
        "custo_status": "ok",
        "model_ref": model_ref,
        "custo_usd": estimated["cost_per_request"],
        "input_cost_used": estimated["input_cost_used"],
        "output_cost_used": estimated["output_cost_used"],
    }


def build_cost_summary(documentos: Optional[Iterable[Documento]] = None, limit: int = 500) -> Dict[str, Any]:
    docs = list(documentos if documentos is not None else storage.listar_todos_documentos(limit=limit))
    rows = [_cost_for(doc, _metadata(doc)) for doc in docs]

    counted_runs = set()
    total_usd = 0.0
    total_input = 0
    total_output = 0
    counted_rows = 0
    blocked = Counter()

    by_provider: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        run_id = row["cost_run_id"]
        if row["custo_status"] != "ok":
            blocked[row.get("erro", "unknown")] += 1
            continue
        if run_id in counted_runs:
            continue
        counted_runs.add(run_id)
        counted_rows += 1
        total_usd += float(row["custo_usd"])
        total_input += row["tokens_entrada"]
        total_output += row["tokens_saida"]

        provider_key = row["provider"] or "unknown"
        provider = by_provider.setdefault(
            provider_key,
            {"provider": provider_key, "runs": 0, "tokens_entrada": 0, "tokens_saida": 0, "custo_usd": 0.0},
        )
        provider["runs"] += 1
        provider["tokens_entrada"] += row["tokens_entrada"]
        provider["tokens_saida"] += row["tokens_saida"]
        provider["custo_usd"] += float(row["custo_usd"])

    for provider in by_provider.values():
        provider["custo_usd"] = round(provider["custo_usd"], 6)

    return {
        "storage_backend": storage._backend_label(),
        "persistent_storage": storage._backend_label() == "postgresql",
        "catalog_loaded": bool(model_catalog.providers),
        "documentos_analisados": len(rows),
        "runs_precificados": counted_rows,
        "runs_bloqueados": sum(blocked.values()),
        "bloqueios": dict(blocked),
        "tokens_entrada": total_input,
        "tokens_saida": total_output,
        "custo_usd": round(total_usd, 6),
        "por_provider": sorted(by_provider.values(), key=lambda item: item["provider"]),
        "amostras": rows[:50],
    }
