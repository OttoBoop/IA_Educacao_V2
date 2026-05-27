"""
NOVO CR - Task Progress Tracking API

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


@router.get("/api/tasks")
async def list_all_tasks():
    """Returns all tasks currently in the registry (for sidebar restore-on-load)."""
    return list(task_registry.values())


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


def register_pipeline_task(
    task_type,
    atividade_id,
    aluno_ids,
    turma_id=None,
    materia_id=None,
    materia_nome=None,
    turma_nome=None,
    atividade_nome=None,
    student_names=None,
):
    """Register a new pipeline task in the registry.

    student_names: optional dict mapping {aluno_id: nome_string}.
    When provided, each student entry gets a 'nome' field.

    materia_id: required for pipeline_desempenho_materia tasks so the
    frontend hierarchy renderer can group them under the correct materia node.

    Returns the generated task_id.
    """
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    names = student_names or {}
    students = {}
    for aluno_id in aluno_ids:
        students[aluno_id] = {
            "nome": names.get(aluno_id, ""),
            "stages": {stage: "pending" for stage in PIPELINE_STAGES},
            "stage_errors": {},
        }
    task_registry[task_id] = {
        "task_id": task_id,
        "type": task_type,
        "atividade_id": atividade_id,
        "turma_id": turma_id,
        "materia_id": materia_id,
        "materia_nome": materia_nome,
        "turma_nome": turma_nome,
        "atividade_nome": atividade_nome,
        "status": "running",
        "cancel_requested": False,
        "students": students,
        "created_at": datetime.now().isoformat(),
    }
    return task_id


def update_stage_progress(task_id, aluno_id, stage, status, error=None):
    """Update a specific stage status for a student in a task.

    Auto-creates a student entry if missing so background cascades
    (desempenho_turma/materia) that discover alunos at runtime can
    still report progress without pre-populating aluno_ids upfront.
    """
    task = task_registry.get(task_id)
    if task:
        students = task.setdefault("students", {})
        if aluno_id not in students:
            students[aluno_id] = {
                "nome": "",
                "stages": {s: "pending" for s in PIPELINE_STAGES},
                "stage_errors": {},
            }
        student = students[aluno_id]
        student["stages"][stage] = status
        stage_errors = student.setdefault("stage_errors", {})
        stage_skips = student.setdefault("stage_skips", {})
        if status == "failed" and error:
            if isinstance(error, dict):
                payload = dict(error)
            else:
                payload = {"mensagem": str(error)}
            payload.setdefault("etapa", stage)
            payload.setdefault("status", status)
            stage_errors[stage] = payload
            stage_skips.pop(stage, None)
        elif status == "skipped":
            if isinstance(error, dict):
                payload = dict(error)
            else:
                payload = {"mensagem": str(error or "Etapa pulada")}
            payload.setdefault("etapa", stage)
            payload.setdefault("status", status)
            stage_skips[stage] = payload
            stage_errors.pop(stage, None)
        elif status in {"running", "completed", "pending"}:
            stage_errors.pop(stage, None)
            stage_skips.pop(stage, None)


def _summarize_task_stages(task):
    """Count per-stage statuses so batch tasks cannot hide partial failures."""
    summary = {
        "students_total": 0,
        "stages_total": 0,
        "completed_stages": 0,
        "failed_stages": 0,
        "skipped_stages": 0,
        "pending_stages": 0,
        "running_stages": 0,
        "students_failed": [],
        "students_pending": [],
    }
    for aluno_id, student in (task.get("students") or {}).items():
        summary["students_total"] += 1
        stages = student.get("stages") or {}
        student_failed = False
        student_pending = False
        for status in stages.values():
            summary["stages_total"] += 1
            if status == "completed":
                summary["completed_stages"] += 1
            elif status == "failed":
                summary["failed_stages"] += 1
                student_failed = True
            elif status == "skipped":
                summary["skipped_stages"] += 1
            elif status == "running":
                summary["running_stages"] += 1
                student_pending = True
            else:
                summary["pending_stages"] += 1
                student_pending = True
        if student_failed:
            summary["students_failed"].append(aluno_id)
        if student_pending:
            summary["students_pending"].append(aluno_id)
    return summary


def complete_pipeline_task(task_id, status="completed", error=None, result=None):
    """Mark a pipeline task as completed or failed."""
    task = task_registry.get(task_id)
    BATCH_TYPES = {
        "pipeline_todos_os_alunos",
        "pipeline_desempenho_tarefa",
        "pipeline_desempenho_turma",
        "pipeline_desempenho_materia",
    }
    if task:
        if task.get("type") in BATCH_TYPES and status in {"completed", "failed"}:
            summary = _summarize_task_stages(task)
            task["summary"] = summary
            has_incomplete = bool(summary["pending_stages"] or summary["running_stages"])
            has_failed = bool(summary["failed_stages"])

            if has_incomplete and not (status == "failed" and not has_failed):
                task["status"] = "running"
                if error:
                    task["last_error"] = error
                if result:
                    task["result"] = result
                return

            if has_failed or status == "failed":
                task["status"] = "failed"
                task["error"] = error or (
                    "Pipeline em lote terminou com falhas: "
                    f"{summary['failed_stages']} etapa(s) falharam em "
                    f"{len(summary['students_failed'])} aluno(s)."
                )
                if result:
                    task["result"] = result
                return

        task["status"] = status
        if error:
            task["error"] = error
        if result:
            task["result"] = result
