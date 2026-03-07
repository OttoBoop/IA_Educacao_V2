"""
Unit tests for routes_tasks.py — Task Progress Tracking API.

Tests verify:
- task_registry stores tasks correctly
- GET /api/task-progress/{task_id} returns correct structure
- TaskProgress model has required fields

F1-T1 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_routes_tasks.py -v
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    from main_v2 import app
    with TestClient(app) as c:
        yield c


class TestTaskProgressEndpoint:
    """Tests for GET /api/task-progress/{task_id}."""

    def test_endpoint_exists(self, client):
        """The /api/task-progress/{task_id} endpoint must exist and return task-specific response."""
        response = client.get("/api/task-progress/nonexistent-task")
        # The endpoint must return a task-specific error, not FastAPI's generic "Not Found"
        data = response.json()
        assert "task_id" in str(data).lower() or "tarefa" in str(data).lower(), (
            "Endpoint should return task-specific error message, not generic 404"
        )

    def test_returns_correct_structure_for_known_task(self, client):
        """When a task exists in registry, endpoint returns full progress structure."""
        from routes_tasks import task_registry

        # Manually register a test task
        task_registry["test-task-123"] = {
            "task_id": "test-task-123",
            "type": "pipeline-completo",
            "atividade_id": "ativ-001",
            "turma_id": None,
            "status": "running",
            "cancel_requested": False,
            "students": {
                "aluno-001": {
                    "nome": "João Silva",
                    "stages": {
                        "extrair_questoes": "completed",
                        "extrair_gabarito": "running",
                        "extrair_respostas": "pending",
                        "corrigir": "pending",
                        "analisar_habilidades": "pending",
                        "gerar_relatorio": "pending",
                    }
                }
            },
            "created_at": "2026-02-23T10:00:00",
        }

        try:
            response = client.get("/api/task-progress/test-task-123")
            assert response.status_code == 200

            data = response.json()
            assert data["task_id"] == "test-task-123"
            assert data["status"] == "running"
            assert "students" in data
            assert "aluno-001" in data["students"]

            student = data["students"]["aluno-001"]
            assert "stages" in student
            assert student["stages"]["extrair_questoes"] == "completed"
            assert student["stages"]["extrair_gabarito"] == "running"
        finally:
            # Clean up
            task_registry.pop("test-task-123", None)

    def test_returns_404_for_unknown_task(self, client):
        """Unknown task_id should return 404 with task-specific descriptive message."""
        response = client.get("/api/task-progress/nonexistent-task-xyz")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        # Must be a task-specific message, not FastAPI's generic "Not Found"
        assert "nonexistent-task-xyz" in data["detail"] or "tarefa" in data["detail"].lower(), (
            "404 detail must reference the task_id or mention 'tarefa'"
        )


class TestTaskCancelEndpoint:
    """Tests for POST /api/task-cancel/{task_id}. F1-T2."""

    def test_cancel_endpoint_exists(self, client):
        """POST /api/task-cancel/{id} must return task-specific response, not generic 404."""
        response = client.post("/api/task-cancel/nonexistent-task")
        data = response.json()
        # Must be a task-specific error, not FastAPI's generic "Not Found"
        assert "task_id" in str(data).lower() or "tarefa" in str(data).lower(), (
            "Cancel endpoint should return task-specific error, not generic 404"
        )

    def test_cancel_sets_flag(self, client):
        """Cancelling a running task sets cancel_requested to True."""
        from routes_tasks import task_registry

        task_registry["cancel-test-001"] = {
            "task_id": "cancel-test-001",
            "type": "pipeline-completo",
            "status": "running",
            "cancel_requested": False,
            "students": {},
        }
        try:
            response = client.post("/api/task-cancel/cancel-test-001")
            assert response.status_code == 200
            assert task_registry["cancel-test-001"]["cancel_requested"] is True
        finally:
            task_registry.pop("cancel-test-001", None)

    def test_cancel_returns_404_for_unknown(self, client):
        """Unknown task_id returns 404 with task-specific message."""
        response = client.post("/api/task-cancel/unknown-cancel-xyz")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "unknown-cancel-xyz" in data["detail"] or "tarefa" in data["detail"].lower()

    def test_cancel_response_confirms_cancellation(self, client):
        """Cancel response includes confirmation that cancel was requested."""
        from routes_tasks import task_registry

        task_registry["cancel-confirm-test"] = {
            "task_id": "cancel-confirm-test",
            "type": "pipeline-completo",
            "status": "running",
            "cancel_requested": False,
            "students": {},
        }
        try:
            response = client.post("/api/task-cancel/cancel-confirm-test")
            data = response.json()
            assert data.get("cancel_requested") is True or "cancel" in str(data).lower()
        finally:
            task_registry.pop("cancel-confirm-test", None)


class TestTaskRegistryModule:
    """Tests for the task_registry dict and helper functions."""

    def test_task_registry_is_dict(self):
        """task_registry must be an importable dict."""
        from routes_tasks import task_registry
        assert isinstance(task_registry, dict)

    def test_task_registry_starts_empty(self):
        """task_registry should start empty (no persistence)."""
        from routes_tasks import task_registry
        # Clear any leftover from other tests
        task_registry.clear()
        assert len(task_registry) == 0


class TestRegisterPipelineTaskStudentNames:
    """A1: register_pipeline_task() must store student nome per student entry.

    Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A1
    """

    def test_register_stores_nome_when_student_names_provided(self):
        """register_pipeline_task() stores nome in each student entry when student_names dict given."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-test-001",
            aluno_ids=["aluno-aaa", "aluno-bbb"],
            student_names={"aluno-aaa": "Maria Silva", "aluno-bbb": "João Santos"},
        )
        try:
            task = task_registry[task_id]
            assert task["students"]["aluno-aaa"]["nome"] == "Maria Silva", (
                "Student nome must be stored in task_registry entry"
            )
            assert task["students"]["aluno-bbb"]["nome"] == "João Santos"
        finally:
            task_registry.pop(task_id, None)

    def test_register_nome_empty_string_when_not_in_student_names(self):
        """Student not in student_names dict gets empty string nome (not KeyError)."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-test-002",
            aluno_ids=["aluno-ccc", "aluno-ddd"],
            student_names={"aluno-ccc": "Ana Lima"},  # aluno-ddd not in dict
        )
        try:
            task = task_registry[task_id]
            assert task["students"]["aluno-ccc"]["nome"] == "Ana Lima"
            # aluno-ddd missing from student_names → fallback to empty string, not KeyError
            assert "nome" in task["students"]["aluno-ddd"]
            assert task["students"]["aluno-ddd"]["nome"] == ""
        finally:
            task_registry.pop(task_id, None)

    def test_register_nome_empty_when_student_names_not_provided(self):
        """When student_names=None (default), all students get nome='' (backward compatible)."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-test-003",
            aluno_ids=["aluno-eee"],
        )
        try:
            task = task_registry[task_id]
            assert "nome" in task["students"]["aluno-eee"], (
                "nome field must always be present in student entry"
            )
            assert task["students"]["aluno-eee"]["nome"] == ""
        finally:
            task_registry.pop(task_id, None)

    def test_register_stages_still_present_alongside_nome(self):
        """Adding nome must not remove the stages dict from student entry."""
        from routes_tasks import register_pipeline_task, task_registry

        task_id = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-test-004",
            aluno_ids=["aluno-fff"],
            student_names={"aluno-fff": "Carlos Mendes"},
        )
        try:
            student = task_registry[task_id]["students"]["aluno-fff"]
            assert "stages" in student, "stages dict must still be present"
            assert "nome" in student, "nome field must be present"
            assert student["nome"] == "Carlos Mendes"
            assert isinstance(student["stages"], dict)
        finally:
            task_registry.pop(task_id, None)


class TestGetAllTasksEndpoint:
    """A3: GET /api/tasks must return all task_registry entries.

    Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Task A3
    """

    def test_endpoint_exists_and_returns_200(self, client):
        """GET /api/tasks must return 200 (not generic 404)."""
        response = client.get("/api/tasks")
        assert response.status_code == 200, (
            f"GET /api/tasks must return 200, got {response.status_code}"
        )

    def test_returns_list(self, client):
        """Response body must be a list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), f"Expected list, got {type(data)}"

    def test_returns_all_tasks_in_registry(self, client):
        """All tasks currently in task_registry must appear in the response."""
        from routes_tasks import task_registry, register_pipeline_task

        task_id_a = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-list-001",
            aluno_ids=[],
        )
        task_id_b = register_pipeline_task(
            task_type="pipeline_desempenho_tarefa",
            atividade_id="ativ-list-002",
            aluno_ids=[],
        )
        try:
            response = client.get("/api/tasks")
            assert response.status_code == 200
            data = response.json()
            task_ids_returned = [t["task_id"] for t in data]
            assert task_id_a in task_ids_returned, "task_id_a must appear in /api/tasks response"
            assert task_id_b in task_ids_returned, "task_id_b must appear in /api/tasks response"
        finally:
            task_registry.pop(task_id_a, None)
            task_registry.pop(task_id_b, None)

    def test_each_entry_has_required_fields(self, client):
        """Each task entry must include task_id, type, status, and students."""
        from routes_tasks import task_registry, register_pipeline_task

        task_id = register_pipeline_task(
            task_type="pipeline",
            atividade_id="ativ-fields-001",
            aluno_ids=["aluno-001"],
            student_names={"aluno-001": "Ana Teste"},
        )
        try:
            response = client.get("/api/tasks")
            assert response.status_code == 200
            data = response.json()
            task = next((t for t in data if t["task_id"] == task_id), None)
            assert task is not None, "Registered task must appear in response"
            assert "task_id" in task
            assert "type" in task
            assert "status" in task
            assert "students" in task
            assert task["type"] == "pipeline"
            assert task["status"] == "running"
        finally:
            task_registry.pop(task_id, None)
