"""
Backend static tests for async pipeline-todos-os-alunos conversion (F3-T2).

Tests verify that routes_prompts.py for executar_pipeline_todos_os_alunos:
- The executar_pipeline_todos_os_alunos endpoint accepts a BackgroundTasks parameter
- Uses background_tasks.add_task() instead of awaiting the executor directly in a loop
- Calls register_pipeline_task() before starting the background task
- Returns { task_id, status: "started" } immediately

F3-T2 from PLAN_Task_Panel_Integration_Fix.md — RED PHASE

These tests SHOULD FAIL until F3-T2 is implemented.

Root cause they guard against:
  /executar/pipeline-todos-os-alunos was fully synchronous:
  - looped over all students, awaiting executor.executar_pipeline_completo() for each
  - blocked the HTTP request for the entire duration (minutes × N students)
  - never called register_pipeline_task(), so task_registry was always empty
  - returned { sucesso, mensagem, total_alunos, total_sucesso, total_falhas, resultados }
  - no task_id was returned to the frontend → sidebar could never poll for progress

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_backend_async_turma.py -v
"""

import pytest
from pathlib import Path


@pytest.fixture
def routes_prompts_content():
    """Read the routes_prompts.py file content."""
    path = Path(__file__).parent.parent.parent / "routes_prompts.py"
    assert path.exists(), f"routes_prompts.py not found at {path}"
    return path.read_text(encoding="utf-8")


def _get_function_body(content, func_marker, window=6000):
    """Extract a slice of content starting at func_marker."""
    pos = content.find(func_marker)
    assert pos > 0, f"'{func_marker}' not found in routes_prompts.py"
    return content[pos : pos + window]


class TestTurmaBackgroundTaskConversion:
    """Verify the pipeline-todos-os-alunos endpoint is converted to use FastAPI BackgroundTasks."""

    def test_turma_endpoint_accepts_background_tasks_param(self, routes_prompts_content):
        """executar_pipeline_todos_os_alunos endpoint must accept a BackgroundTasks parameter.

        The parameter allows FastAPI to inject the background task runner so the
        endpoint can hand off the loop of N student pipelines and return task_id
        immediately — without blocking until all N pipelines complete (can take many minutes).
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_todos_os_alunos"
        )
        assert "BackgroundTasks" in func_body or "background_tasks" in func_body, (
            "The todos-os-alunos endpoint must declare a BackgroundTasks parameter. "
            "Example: async def executar_pipeline_todos_os_alunos(background_tasks: BackgroundTasks, ...). "
            "FastAPI injects the runner automatically via dependency injection."
        )

    def test_turma_endpoint_uses_add_task(self, routes_prompts_content):
        """Endpoint must use background_tasks.add_task() to run pipeline asynchronously.

        background_tasks.add_task(some_helper, alunos, ...) runs the multi-student
        pipeline after the HTTP response is returned — so the professor sees task_id
        immediately instead of waiting several minutes × N students.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_todos_os_alunos"
        )
        assert "add_task" in func_body, (
            "The todos-os-alunos endpoint must call background_tasks.add_task(...) "
            "instead of directly awaiting executor.executar_pipeline_completo() in a for loop. "
            "Move the student loop to a background helper function."
        )

    def test_turma_endpoint_does_not_await_pipeline_in_loop(self, routes_prompts_content):
        """The todos-os-alunos endpoint must NOT directly await executor.executar_pipeline_completo.

        Directly awaiting in a for-loop blocks the HTTP request for all students
        (pipeline duration × number of students, easily 10+ minutes).
        The student loop must be moved to a BackgroundTask helper function.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_todos_os_alunos"
        )
        assert "await executor.executar_pipeline_completo" not in func_body, (
            "executar_pipeline_todos_os_alunos must NOT directly await executor.executar_pipeline_completo(). "
            "This blocks the HTTP request for all students' pipelines. "
            "Move the student for-loop to a background task helper function."
        )


class TestTurmaTaskRegistration:
    """Verify the todos-os-alunos endpoint calls register_pipeline_task() before starting execution."""

    def test_turma_endpoint_calls_register_pipeline_task(self, routes_prompts_content):
        """executar_pipeline_todos_os_alunos must call register_pipeline_task() before the background task.

        The registration must happen synchronously (before returning the response) so
        /api/task-progress/{task_id} returns data immediately when the frontend starts polling.
        All student IDs must be registered so the sidebar shows all students with pending stages.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_todos_os_alunos"
        )
        assert "register_pipeline_task" in func_body, (
            "executar_pipeline_todos_os_alunos must call register_pipeline_task(task_type, atividade_id, aluno_ids) "
            "before starting the BackgroundTask. "
            "Pass all student IDs so task_registry shows all students with pending stages."
        )


class TestTurmaImmediateResponse:
    """Verify the todos-os-alunos endpoint returns task_id immediately instead of sync pipeline result."""

    def test_turma_endpoint_returns_task_id_field(self, routes_prompts_content):
        """executar_pipeline_todos_os_alunos must include task_id in the response.

        The task_id is used by the frontend to:
        1. Call taskQueue.addBackendTask(task_id, initialPendingState) → populates sidebar
        2. Call startPolling(task_id) → starts 3-second interval to fetch /api/task-progress/{task_id}
        Without task_id in the response, neither step can happen.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_todos_os_alunos"
        )
        assert (
            '"task_id"' in func_body
            or "'task_id'" in func_body
        ), (
            "executar_pipeline_todos_os_alunos must return { 'task_id': task_id, 'status': 'started' }. "
            "This replaces the old sync response: { sucesso, mensagem, total_alunos, ... }."
        )

    def test_turma_endpoint_returns_started_status(self, routes_prompts_content):
        """The immediate response must have status 'started'.

        'started' signals the background pipeline loop is running for all students.
        Progress is tracked via task_registry + polling — not in the HTTP response body.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_todos_os_alunos"
        )
        assert (
            '"started"' in func_body
            or "'started'" in func_body
        ), (
            "executar_pipeline_todos_os_alunos must return { ..., 'status': 'started' }. "
            "This replaces the old sync response format: "
            "{ sucesso, mensagem, total_alunos, total_sucesso, total_falhas, resultados }."
        )
