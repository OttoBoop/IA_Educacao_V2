"""
Backend static tests for async pipeline conversion (F3-T1).

Tests verify that routes_prompts.py:
- Imports BackgroundTasks and register_pipeline_task
- The executar_pipeline_completo endpoint accepts a BackgroundTasks parameter
- Uses background_tasks.add_task() instead of awaiting the executor directly
- Calls register_pipeline_task() before starting the background task
- Returns { task_id, status: "started" } immediately

F3-T1 from PLAN_Task_Panel_Integration_Fix.md — RED PHASE

These tests SHOULD FAIL until F3-T1 is implemented.

Root cause they guard against:
  /executar/pipeline-completo was fully synchronous:
  - awaited executor.executar_pipeline_completo() and waited for the full result
  - returned { sucesso, etapas_executadas, etapas_falharam, resultados }
  - never called register_pipeline_task(), so task_registry was always empty
  - no task_id was returned to the frontend → sidebar could never poll for progress

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_backend_async_pipeline.py -v
"""

import re
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


class TestBackgroundTaskConversion:
    """Verify the endpoint is converted to use FastAPI BackgroundTasks."""

    def test_background_tasks_imported(self, routes_prompts_content):
        """FastAPI BackgroundTasks must be imported in routes_prompts.py.

        Without BackgroundTasks, the pipeline cannot be run asynchronously.
        The endpoint must accept BackgroundTasks as a parameter and call
        background_tasks.add_task(executor.executar_pipeline_completo, ...)
        instead of awaiting it directly (which blocks for minutes).
        """
        assert "BackgroundTasks" in routes_prompts_content, (
            "routes_prompts.py must import BackgroundTasks from fastapi. "
            "Add it to the existing fastapi import line: "
            "from fastapi import APIRouter, HTTPException, Form, UploadFile, File, BackgroundTasks"
        )

    def test_endpoint_accepts_background_tasks_param(self, routes_prompts_content):
        """executar_pipeline_completo endpoint must accept a BackgroundTasks parameter.

        The parameter allows FastAPI to inject the background task runner so the
        endpoint can hand off the heavy pipeline execution and return task_id
        immediately — without blocking until the pipeline completes (can take minutes).
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_completo"
        )
        assert "BackgroundTasks" in func_body or "background_tasks" in func_body, (
            "The endpoint function must declare a BackgroundTasks parameter. "
            "Example: async def executar_pipeline_completo(background_tasks: BackgroundTasks, ...). "
            "This is a FastAPI dependency injection — FastAPI provides the runner automatically."
        )

    def test_endpoint_uses_add_task(self, routes_prompts_content):
        """Endpoint must use background_tasks.add_task() to run pipeline asynchronously.

        background_tasks.add_task(executor.executar_pipeline_completo, ...)
        runs the pipeline after the HTTP response is returned — so the professor
        sees task_id immediately instead of waiting several minutes for completion.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_completo"
        )
        assert "add_task" in func_body, (
            "The endpoint must call background_tasks.add_task(executor.executar_pipeline_completo, ...) "
            "instead of directly awaiting it. "
            "Currently: 'resultados = await executor.executar_pipeline_completo(...)' — this blocks. "
            "After fix: 'background_tasks.add_task(executor.executar_pipeline_completo, ...)' — returns immediately."
        )

    def test_endpoint_does_not_await_full_pipeline(self, routes_prompts_content):
        """The endpoint must NOT directly await executor.executar_pipeline_completo.

        Directly awaiting the pipeline blocks the HTTP request for the entire
        pipeline duration (minutes). The pipeline must be handed to BackgroundTasks
        so the endpoint returns task_id immediately and the frontend can start polling.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_completo"
        )
        assert "await executor.executar_pipeline_completo" not in func_body, (
            "executar_pipeline_completo endpoint must NOT directly await "
            "executor.executar_pipeline_completo(). "
            "This blocks the HTTP request for minutes. "
            "Move the call to background_tasks.add_task() instead."
        )


class TestTaskRegistration:
    """Verify the endpoint calls register_pipeline_task() before starting execution."""

    def test_register_pipeline_task_imported(self, routes_prompts_content):
        """register_pipeline_task must be imported from routes_tasks.

        Without this import, the endpoint can't register tasks in task_registry.
        The frontend polls /api/task-progress/{task_id} which reads from task_registry
        — so if the task was never registered, all polls return 404.
        """
        assert "register_pipeline_task" in routes_prompts_content, (
            "register_pipeline_task must be imported from routes_tasks. "
            "Add: from routes_tasks import register_pipeline_task "
            "This function creates the task_registry entry so /api/task-progress/{task_id} works."
        )

    def test_endpoint_calls_register_pipeline_task(self, routes_prompts_content):
        """executar_pipeline_completo must call register_pipeline_task() before the background task.

        The registration must happen synchronously (before returning the response)
        so that by the time the frontend calls addBackendTask() and starts polling,
        the task_registry entry already exists and /api/task-progress/{task_id} returns data.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_completo"
        )
        assert "register_pipeline_task" in func_body, (
            "executar_pipeline_completo must call register_pipeline_task(task_type, atividade_id, [aluno_id]) "
            "before starting the BackgroundTask. "
            "Without this call, task_registry is empty and all poll requests return 404 — "
            "the sidebar would show 'Sem conexão' immediately."
        )


class TestImmediateResponse:
    """Verify the endpoint returns task_id immediately instead of sync pipeline result."""

    def test_endpoint_returns_task_id_field(self, routes_prompts_content):
        """executar_pipeline_completo must include task_id in the response.

        The task_id is used by the frontend:
        1. taskQueue.addBackendTask(task_id, initialPendingState) → populates sidebar
        2. startPolling(task_id) → starts 3-second interval to fetch /api/task-progress/{task_id}
        Without task_id in the response, neither step can happen.
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_completo"
        )
        assert (
            '"task_id"' in func_body
            or "'task_id'" in func_body
        ), (
            "executar_pipeline_completo must return { 'task_id': task_id, 'status': 'started' }. "
            "The task_id is generated by register_pipeline_task() and must be included in the response "
            "so the frontend can call addBackendTask(task_id) and start polling."
        )

    def test_endpoint_returns_started_status(self, routes_prompts_content):
        """The immediate response must have status 'started'.

        The frontend checks the status field to confirm the pipeline started
        and to display an appropriate toast. 'started' signals that the background
        task is running — not 'completed' (which only polling can confirm later).
        """
        func_body = _get_function_body(
            routes_prompts_content, "async def executar_pipeline_completo"
        )
        assert (
            '"started"' in func_body
            or "'started'" in func_body
        ), (
            "executar_pipeline_completo must return { ..., 'status': 'started' }. "
            "This replaces the old sync response format: "
            "{ sucesso, etapas_executadas, etapas_falharam, resultados }. "
            "The pipeline result is now tracked via task_registry + polling."
        )
