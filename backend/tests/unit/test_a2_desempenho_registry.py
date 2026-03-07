"""
Unit tests for A2: desempenho task registration in task_registry.

A2 adds materia_id field to register_pipeline_task() so the frontend
hierarchy renderer (A4) can group materia-level desempenho tasks correctly.

Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A2

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_a2_desempenho_registry.py -v
"""

import pytest


class TestDesempenhoTaskRegistryFields:
    """A2: register_pipeline_task() must store materia_id for desempenho tasks."""

    def test_register_pipeline_task_accepts_materia_id(self):
        """register_pipeline_task() should accept materia_id without TypeError."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline_desempenho_materia",
            atividade_id="materia-001",
            aluno_ids=[],
            materia_id="materia-001",
            materia_nome="Matemática",
        )
        try:
            assert task_id in task_registry
        finally:
            task_registry.pop(task_id, None)

    def test_register_stores_materia_id_field(self):
        """task_registry entry must contain materia_id when provided."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline_desempenho_materia",
            atividade_id="materia-abc",
            aluno_ids=[],
            materia_id="materia-abc",
            materia_nome="História",
        )
        try:
            task = task_registry[task_id]
            assert "materia_id" in task, "materia_id must be stored in task_registry entry"
            assert task["materia_id"] == "materia-abc"
        finally:
            task_registry.pop(task_id, None)

    def test_register_materia_id_defaults_to_none(self):
        """materia_id should be None when not provided (backward compatible)."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-001",
            aluno_ids=[],
        )
        try:
            task = task_registry[task_id]
            assert "materia_id" in task, "materia_id field must always be present"
            assert task["materia_id"] is None
        finally:
            task_registry.pop(task_id, None)

    def test_register_desempenho_tarefa_has_type(self):
        """pipeline_desempenho_tarefa task must have type stored for A4 identification."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline_desempenho_tarefa",
            atividade_id="ativ-xyz",
            aluno_ids=[],
            materia_nome="Português",
            turma_nome="Turma A",
            atividade_nome="Prova 1",
        )
        try:
            task = task_registry[task_id]
            assert task["type"] == "pipeline_desempenho_tarefa"
            assert task["materia_nome"] == "Português"
            assert task["turma_nome"] == "Turma A"
            assert task["atividade_nome"] == "Prova 1"
        finally:
            task_registry.pop(task_id, None)

    def test_register_desempenho_turma_stores_turma_and_materia(self):
        """pipeline_desempenho_turma task must have turma_id, turma_nome, materia_nome."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline_desempenho_turma",
            atividade_id="turma-999",
            aluno_ids=[],
            turma_id="turma-999",
            turma_nome="Turma B",
            materia_nome="Ciências",
        )
        try:
            task = task_registry[task_id]
            assert task["type"] == "pipeline_desempenho_turma"
            assert task["turma_id"] == "turma-999"
            assert task["turma_nome"] == "Turma B"
            assert task["materia_nome"] == "Ciências"
            assert task["materia_id"] is None  # turma-level has no materia_id
        finally:
            task_registry.pop(task_id, None)

    def test_register_desempenho_materia_stores_materia_id_and_nome(self):
        """pipeline_desempenho_materia task must have materia_id and materia_nome."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline_desempenho_materia",
            atividade_id="mat-555",
            aluno_ids=[],
            materia_id="mat-555",
            materia_nome="Física",
        )
        try:
            task = task_registry[task_id]
            assert task["type"] == "pipeline_desempenho_materia"
            assert task["materia_id"] == "mat-555"
            assert task["materia_nome"] == "Física"
        finally:
            task_registry.pop(task_id, None)
