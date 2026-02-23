"""
PROVA AI - Task Progress Tracking API

Provides endpoints to track background task progress.
- GET /api/task-progress/{task_id}

F1-T1 from PLAN_Task_Panel_Sidebar_UI.md
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# In-memory registry of running/completed tasks.
# Keyed by task_id. Each entry is a dict with:
# task_id, type, atividade_id, turma_id, status,
# cancel_requested, students, created_at
task_registry = {}


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
