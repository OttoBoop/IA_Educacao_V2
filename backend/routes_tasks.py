"""
PROVA AI - Task Progress Tracking API

Provides endpoints to track background task progress.
- GET /api/task-progress/{task_id}
- POST /api/task-cancel/{task_id}

Helper functions for pipeline integration:
- register_pipeline_task()
- update_stage_progress()
- complete_pipeline_task()

F1-T1, F1-T2, F1-T3 from PLAN_Task_Panel_Sidebar_UI.md
"""

import uuid
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# In-memory registry of running/completed tasks.
# Keyed by task_id. Each entry is a dict with:
# task_id, type, atividade_id, turma_id, status,
# cancel_requested, students, created_at
task_registry = {}

PIPELINE_STAGES = [
    "extrair_questoes",
    "extrair_gabarito",
    "extrair_respostas",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]


# ── Endpoints ────────────────────────────────────────────────


@router.get("/api/task-progress/{task_id}")
async def get_task_progress(task_id: str):
    """Returns progress for a task by task_id."""
    task = task_registry.get(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Tarefa '{task_id}' não encontrada"},
        )
    return task


@router.post("/api/task-cancel/{task_id}")
async def cancel_task(task_id: str):
    """Sets cancel_requested flag on a running task."""
    task = task_registry.get(task_id)
    if task is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Tarefa '{task_id}' não encontrada"},
        )
    task["cancel_requested"] = True
    return {"task_id": task_id, "cancel_requested": True}


# ── Helper functions for pipeline integration ────────────────


def register_pipeline_task(task_type, atividade_id, aluno_ids, turma_id=None):
    """Register a new pipeline task in the registry.

    Returns the generated task_id.
    """
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    students = {}
    for aluno_id in aluno_ids:
        students[aluno_id] = {
            "stages": {stage: "pending" for stage in PIPELINE_STAGES},
        }
    task_registry[task_id] = {
        "task_id": task_id,
        "type": task_type,
        "atividade_id": atividade_id,
        "turma_id": turma_id,
        "status": "running",
        "cancel_requested": False,
        "students": students,
        "created_at": datetime.now().isoformat(),
    }
    return task_id


def update_stage_progress(task_id, aluno_id, stage, status):
    """Update a specific stage status for a student in a task."""
    task = task_registry.get(task_id)
    if task and aluno_id in task["students"]:
        task["students"][aluno_id]["stages"][stage] = status


def complete_pipeline_task(task_id, status="completed"):
    """Mark a pipeline task as completed or failed."""
    task = task_registry.get(task_id)
    if task:
        task["status"] = status
