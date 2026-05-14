"""
Cost endpoints for measured NOVO CR usage.

These endpoints expose measured costs only when input/output token splits and
catalog pricing are available. Missing data is returned as a blocking reason.
"""

from fastapi import APIRouter

from cost_tracking import build_cost_summary


router = APIRouter()


@router.get("/api/custos/status", tags=["Custos"])
async def get_cost_status(limit: int = 500):
    summary = build_cost_summary(limit=limit)
    return {
        "ok": summary["catalog_loaded"],
        "storage_backend": summary["storage_backend"],
        "persistent_storage": summary["persistent_storage"],
        "catalog_loaded": summary["catalog_loaded"],
        "runs_precificados": summary["runs_precificados"],
        "runs_bloqueados": summary["runs_bloqueados"],
        "bloqueios": summary["bloqueios"],
    }


@router.get("/api/custos/resumo", tags=["Custos"])
async def get_cost_summary(limit: int = 500):
    return build_cost_summary(limit=limit)
