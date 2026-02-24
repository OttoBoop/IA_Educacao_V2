"""
Unit tests for pipeline progress helper functions in routes_tasks.py.

Tests verify:
- register_pipeline_task() creates correct task entry
- update_stage_progress() updates per-student per-stage status
- complete_pipeline_task() marks task as done

F1-T3 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_pipeline_progress.py -v
"""

import pytest


PIPELINE_STAGES = [
    "extrair_questoes",
    "extrair_gabarito",
    "extrair_respostas",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]


class TestRegisterPipelineTask:
    """Tests for the register_pipeline_task helper function."""

    def test_function_exists(self):
        """register_pipeline_task must be importable from routes_tasks."""
        from routes_tasks import register_pipeline_task
        assert callable(register_pipeline_task)

    def test_creates_entry_in_registry(self):
        """Calling register_pipeline_task creates an entry in task_registry."""
        from routes_tasks import task_registry, register_pipeline_task

        task_id = register_pipeline_task(
            task_type="pipeline-completo",
            atividade_id="ativ-test-001",
            aluno_ids=["aluno-a", "aluno-b"],
        )
        try:
            assert task_id in task_registry
            task = task_registry[task_id]
            assert task["type"] == "pipeline-completo"
            assert task["atividade_id"] == "ativ-test-001"
            assert task["status"] == "running"
            assert task["cancel_requested"] is False
        finally:
            task_registry.pop(task_id, None)

    def test_initializes_all_students(self):
        """Each student gets an entry with all 6 stages set to 'pending'."""
        from routes_tasks import task_registry, register_pipeline_task

        task_id = register_pipeline_task(
            task_type="pipeline-completo",
            atividade_id="ativ-test-002",
            aluno_ids=["aluno-x", "aluno-y", "aluno-z"],
        )
        try:
            task = task_registry[task_id]
            assert "students" in task
            for aluno_id in ["aluno-x", "aluno-y", "aluno-z"]:
                assert aluno_id in task["students"]
                stages = task["students"][aluno_id]["stages"]
                for stage in PIPELINE_STAGES:
                    assert stages[stage] == "pending", (
                        f"Stage {stage} for {aluno_id} should be 'pending'"
                    )
        finally:
            task_registry.pop(task_id, None)

    def test_returns_unique_task_id(self):
        """Each call returns a unique task_id."""
        from routes_tasks import task_registry, register_pipeline_task

        id1 = register_pipeline_task("pipeline-completo", "ativ-1", ["a1"])
        id2 = register_pipeline_task("pipeline-completo", "ativ-2", ["a2"])
        try:
            assert id1 != id2
        finally:
            task_registry.pop(id1, None)
            task_registry.pop(id2, None)


class TestUpdateStageProgress:
    """Tests for the update_stage_progress helper function."""

    def test_function_exists(self):
        """update_stage_progress must be importable from routes_tasks."""
        from routes_tasks import update_stage_progress
        assert callable(update_stage_progress)

    def test_updates_stage_status(self):
        """Calling update_stage_progress changes a student's stage status."""
        from routes_tasks import task_registry, register_pipeline_task, update_stage_progress

        task_id = register_pipeline_task("pipeline-completo", "ativ-upd", ["aluno-1"])
        try:
            update_stage_progress(task_id, "aluno-1", "extrair_questoes", "running")
            stages = task_registry[task_id]["students"]["aluno-1"]["stages"]
            assert stages["extrair_questoes"] == "running"

            update_stage_progress(task_id, "aluno-1", "extrair_questoes", "completed")
            assert stages["extrair_questoes"] == "completed"
        finally:
            task_registry.pop(task_id, None)

    def test_does_not_affect_other_stages(self):
        """Updating one stage leaves others unchanged."""
        from routes_tasks import task_registry, register_pipeline_task, update_stage_progress

        task_id = register_pipeline_task("pipeline-completo", "ativ-iso", ["aluno-1"])
        try:
            update_stage_progress(task_id, "aluno-1", "corrigir", "running")
            stages = task_registry[task_id]["students"]["aluno-1"]["stages"]
            assert stages["corrigir"] == "running"
            assert stages["extrair_questoes"] == "pending"
            assert stages["gerar_relatorio"] == "pending"
        finally:
            task_registry.pop(task_id, None)


class TestCompletePipelineTask:
    """Tests for the complete_pipeline_task helper function."""

    def test_function_exists(self):
        """complete_pipeline_task must be importable from routes_tasks."""
        from routes_tasks import complete_pipeline_task
        assert callable(complete_pipeline_task)

    def test_marks_task_completed(self):
        """complete_pipeline_task sets task status to 'completed'."""
        from routes_tasks import task_registry, register_pipeline_task, complete_pipeline_task

        task_id = register_pipeline_task("pipeline-completo", "ativ-done", ["aluno-1"])
        try:
            complete_pipeline_task(task_id)
            assert task_registry[task_id]["status"] == "completed"
        finally:
            task_registry.pop(task_id, None)

    def test_marks_task_failed(self):
        """complete_pipeline_task can mark a task as 'failed'."""
        from routes_tasks import task_registry, register_pipeline_task, complete_pipeline_task

        task_id = register_pipeline_task("pipeline-completo", "ativ-fail", ["aluno-1"])
        try:
            complete_pipeline_task(task_id, status="failed")
            assert task_registry[task_id]["status"] == "failed"
        finally:
            task_registry.pop(task_id, None)
