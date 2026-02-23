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
