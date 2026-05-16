"""
Measured cost helpers for NOVO CR.

This module only calculates cost from measured token splits. It does not
invent input/output splits from legacy total-only token counts.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, Optional

from model_catalog import model_catalog
from models import Documento
from storage import storage
from token_usage import TokenUsageRecord, token_usage_store


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
        "erro_execucao": metadata.get("erro_pipeline") or metadata.get("erro_execucao"),
        "erro_tipo": metadata.get("erro_tipo"),
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


def _cost_for_usage(record: TokenUsageRecord) -> Dict[str, Any]:
    base = {
        "documento_id": None,
        "usage_record_id": record.id,
        "tipo": "token_usage",
        "atividade_id": record.atividade_id,
        "aluno_id": record.aluno_id,
        "provider": record.provider,
        "modelo": record.modelo,
        "tokens_entrada": int(record.tokens_entrada or 0),
        "tokens_saida": int(record.tokens_saida or 0),
        "tokens_total": record.tokens_total,
        "cost_run_id": record.cost_run_id,
        "status": record.status,
        "erro_execucao": record.erro,
        "erro_codigo": record.erro_codigo,
        "source": record.source,
    }

    if not record.provider or not record.modelo:
        return {**base, "custo_status": "blocked", "erro": "provider_model_missing"}

    if record.tokens_entrada <= 0 and record.tokens_saida <= 0:
        return {**base, "custo_status": "blocked", "erro": "token_split_missing"}

    model_ref = f"{record.provider}/{record.modelo}"
    estimated = model_catalog.calculate_cost(
        model_ref=model_ref,
        input_tokens=record.tokens_entrada,
        output_tokens=record.tokens_saida,
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


def _cost_signature(row: Dict[str, Any]) -> tuple:
    """Fields that must match when multiple documents belong to one AI run."""

    return (
        row.get("provider"),
        row.get("modelo"),
        row.get("model_ref"),
        row.get("tokens_entrada"),
        row.get("tokens_saida"),
        round(float(row.get("custo_usd", 0.0)), 12),
    )


def _documents_for_run(rows: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [
        {
            "documento_id": row["documento_id"],
            "tipo": row["tipo"],
            "status": row["status"],
            "custo_status": row["custo_status"],
            "erro": row.get("erro") or row.get("erro_execucao"),
            "erro_execucao": row.get("erro_execucao"),
            "erro_tipo": row.get("erro_tipo"),
        }
        for row in rows
        if row.get("documento_id")
    ]


def _usage_records_for_run(rows: Iterable[Dict[str, Any]]) -> list[Dict[str, Any]]:
    return [
        {
            "usage_record_id": row["usage_record_id"],
            "status": row["status"],
            "custo_status": row["custo_status"],
            "erro": row.get("erro"),
            "erro_execucao": row.get("erro_execucao"),
        }
        for row in rows
        if row.get("usage_record_id")
    ]


def _sample_for_run(run_id: str, rows: list[Dict[str, Any]], representative: Dict[str, Any]) -> Dict[str, Any]:
    sample = dict(representative)
    documents = _documents_for_run(rows)
    usage_records = _usage_records_for_run(rows)
    sample["cost_run_id"] = run_id
    sample["documentos"] = documents
    sample["documentos_ids"] = [doc["documento_id"] for doc in documents]
    sample["documentos_contagem"] = len(documents)
    sample["token_usage"] = usage_records
    sample["token_usage_ids"] = [record["usage_record_id"] for record in usage_records]
    sample["token_usage_contagem"] = len(usage_records)
    return sample


def _blocked_reason(rows: list[Dict[str, Any]]) -> str:
    reasons = sorted({row.get("erro") or "unknown" for row in rows})
    return reasons[0] if len(reasons) == 1 else "mixed_blocked"


def build_cost_summary(
    documentos: Optional[Iterable[Documento]] = None,
    limit: int = 500,
    token_usage_records: Optional[Iterable[TokenUsageRecord]] = None,
) -> Dict[str, Any]:
    docs = list(documentos if documentos is not None else storage.listar_todos_documentos(limit=limit))
    usage_records = list(
        token_usage_records
        if token_usage_records is not None
        else ([] if documentos is not None else token_usage_store.list_records(limit=limit))
    )
    document_rows = [_cost_for(doc, _metadata(doc)) for doc in docs]
    usage_rows = [_cost_for_usage(record) for record in usage_records]
    rows = document_rows + usage_rows
    rows_by_run: Dict[str, list[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        rows_by_run[row["cost_run_id"]].append(row)

    total_usd = 0.0
    total_input = 0
    total_output = 0
    counted_runs = 0
    blocked = Counter()
    by_provider: Dict[str, Dict[str, Any]] = {}
    samples: list[Dict[str, Any]] = []
    alerts: list[Dict[str, Any]] = []

    for run_id, run_rows in rows_by_run.items():
        ok_rows = [row for row in run_rows if row["custo_status"] == "ok"]
        if not ok_rows:
            reason = _blocked_reason(run_rows)
            blocked[reason] += 1
            sample = _sample_for_run(run_id, run_rows, run_rows[0])
            sample["custo_status"] = "blocked"
            sample["erro"] = reason
            sample["erros"] = sorted({row.get("erro") or "unknown" for row in run_rows})
            samples.append(sample)
            continue

        signatures = {_cost_signature(row) for row in ok_rows}
        if len(signatures) != 1:
            blocked["run_metadata_conflict"] += 1
            sample = _sample_for_run(run_id, run_rows, ok_rows[0])
            sample["custo_status"] = "blocked"
            sample["erro"] = "run_metadata_conflict"
            samples.append(sample)
            alerts.append(
                {
                    "tipo": "run_metadata_conflict",
                    "cost_run_id": run_id,
                    "documentos_ids": sample["documentos_ids"],
                    "token_usage_ids": sample["token_usage_ids"],
                }
            )
            continue

        row = ok_rows[0]
        if len(ok_rows) != len(run_rows):
            alerts.append(
                {
                    "tipo": "run_mixed_cost_status",
                    "cost_run_id": run_id,
                    "documentos_ids": [item["documento_id"] for item in run_rows if item.get("documento_id")],
                    "token_usage_ids": [item["usage_record_id"] for item in run_rows if item.get("usage_record_id")],
                    "erros": sorted({item.get("erro") or "unknown" for item in run_rows if item["custo_status"] != "ok"}),
                }
            )

        counted_runs += 1
        total_usd += float(row["custo_usd"])
        total_input += row["tokens_entrada"]
        total_output += row["tokens_saida"]
        samples.append(_sample_for_run(run_id, run_rows, row))

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
        "token_usage_backend": token_usage_store.status(),
        "documentos_analisados": len(document_rows),
        "token_usage_analisados": len(usage_rows),
        "runs_analisados": len(rows_by_run),
        "runs_precificados": counted_runs,
        "runs_bloqueados": sum(blocked.values()),
        "bloqueios": dict(blocked),
        "tokens_entrada": total_input,
        "tokens_saida": total_output,
        "custo_usd": round(total_usd, 6),
        "por_provider": sorted(by_provider.values(), key=lambda item: item["provider"]),
        "amostras": samples[:50],
        "alertas": alerts[:50],
    }
