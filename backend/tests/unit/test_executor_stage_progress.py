"""
Backend static tests for executor stage progress wiring (F3-T3).

Tests verify that executor.py executar_pipeline_completo:
- Accepts a task_id parameter
- Calls update_stage_progress() for each stage (before/after)
- Calls complete_pipeline_task() at the end
- Checks cancel_requested flag between stages

And that routes_prompts.py correctly passes task_id to the executor:
- executar_pipeline_completo endpoint passes task_id via background_tasks.add_task
- _executar_pipeline_todos_os_alunos_background helper accepts and forwards task_id

F3-T3 from PLAN_Task_Panel_Integration_Fix.md — RED PHASE

These tests SHOULD FAIL until F3-T3 is implemented.

Root cause they guard against:
  executor.executar_pipeline_completo() had no task_id parameter.
  It executed 6 stages with no progress updates → task_registry entries stayed at
  all-pending forever → sidebar would show every stage as ⬜ until the task was
  marked complete, with no intermediate updates visible to the professor.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_executor_stage_progress.py -v
"""

import pytest
from pathlib import Path


@pytest.fixture
def executor_content():
    """Read the executor.py file content."""
    path = Path(__file__).parent.parent.parent / "executor.py"
    assert path.exists(), f"executor.py not found at {path}"
    return path.read_text(encoding="utf-8")


@pytest.fixture
def routes_prompts_content():
    """Read the routes_prompts.py file content."""
    path = Path(__file__).parent.parent.parent / "routes_prompts.py"
    assert path.exists(), f"routes_prompts.py not found at {path}"
    return path.read_text(encoding="utf-8")


def _get_function_body(content, func_marker, window=10000):
    """Extract a slice of content starting at func_marker."""
    pos = content.find(func_marker)
    assert pos > 0, f"'{func_marker}' not found in file"
    return content[pos : pos + window]


class TestExecutorTaskIdParam:
    """Verify executor.executar_pipeline_completo accepts task_id."""

    def test_executar_pipeline_completo_accepts_task_id(self, executor_content):
        """executar_pipeline_completo must declare task_id as an optional parameter.

        Without task_id, the executor cannot call update_stage_progress() or
        complete_pipeline_task() — it doesn't know which task_registry entry to update.
        The sidebar would show all stages as ⬜ forever even as the pipeline runs.
        """
        # Check within the first 700 chars of the function (parameter section)
        func_start = _get_function_body(executor_content, "async def executar_pipeline_completo", window=700)
        assert "task_id" in func_start, (
            "executar_pipeline_completo must declare task_id as an optional parameter. "
            "Example: task_id: Optional[str] = None. "
            "The task_id links this execution to the task_registry entry created by register_pipeline_task()."
        )


class TestStageProgressCalls:
    """Verify the executor calls update_stage_progress and complete_pipeline_task."""

    def test_executor_calls_update_stage_progress(self, executor_content):
        """executar_pipeline_completo must call update_stage_progress() for each stage.

        update_stage_progress(task_id, aluno_id, stage, status) updates task_registry
        so the frontend polling /api/task-progress/{task_id} sees live stage status.
        Without these calls, the sidebar shows all stages as pending indefinitely.
        """
        func_body = _get_function_body(executor_content, "async def executar_pipeline_completo")
        assert "update_stage_progress" in func_body, (
            "executar_pipeline_completo must call update_stage_progress(task_id, aluno_id, stage, status) "
            "before and after each of the 6 pipeline stages. "
            "Import from routes_tasks: from routes_tasks import update_stage_progress"
        )

    def test_executor_calls_complete_pipeline_task(self, executor_content):
        """executar_pipeline_completo must call complete_pipeline_task() when done.

        complete_pipeline_task(task_id) sets task_registry[task_id]['status'] = 'completed'
        so the frontend polling loop knows to stop and the sidebar shows the final state.
        Without this call, polling continues indefinitely even after the pipeline finishes.
        """
        func_body = _get_function_body(executor_content, "async def executar_pipeline_completo")
        assert "complete_pipeline_task" in func_body, (
            "executar_pipeline_completo must call complete_pipeline_task(task_id) at the end "
            "to set task status to 'completed' in task_registry. "
            "Import from routes_tasks: from routes_tasks import complete_pipeline_task"
        )

    def test_executor_checks_cancel_requested(self, executor_content):
        """executar_pipeline_completo must check cancel_requested flag between stages.

        cancel_requested is set by POST /api/task-cancel/{task_id}. The executor must
        check it between stages and stop early if True, calling complete_pipeline_task
        with status='cancelled'. Without this check, cancel clicks have no effect on
        running pipelines.
        """
        func_body = _get_function_body(executor_content, "async def executar_pipeline_completo")
        assert "cancel_requested" in func_body, (
            "executar_pipeline_completo must check task_registry[task_id]['cancel_requested'] "
            "between stages to support pipeline cancellation. "
            "Pattern: if task_id and task_registry.get(task_id, {}).get('cancel_requested'): return/break"
        )


class TestRoutesPipelineWiring:
    """Verify that routes_prompts.py passes task_id to the executor calls."""

    def test_pipeline_completo_route_passes_task_id_to_executor(self, routes_prompts_content):
        """The executar_pipeline_completo route must pass task_id=task_id to the executor.

        background_tasks.add_task(executor.executar_pipeline_completo, task_id=task_id, ...)
        Without passing task_id, the executor receives task_id=None and cannot call
        update_stage_progress() — progress tracking is silently disabled.
        """
        func_body = _get_function_body(routes_prompts_content, "async def executar_pipeline_completo")
        add_task_pos = func_body.find("add_task")
        assert add_task_pos > 0, "add_task() call not found in executar_pipeline_completo"
        add_task_block = func_body[add_task_pos : add_task_pos + 500]
        assert "task_id=task_id" in add_task_block, (
            "background_tasks.add_task(executor.executar_pipeline_completo, ...) must include "
            "task_id=task_id so the executor can call update_stage_progress(). "
            "Currently task_id is registered but not forwarded to the executor."
        )

    def test_turma_helper_accepts_task_id_param(self, routes_prompts_content):
        """_executar_pipeline_todos_os_alunos_background must accept task_id as a parameter.

        The todos-os-alunos background helper must receive task_id from the endpoint and pass it
        to executor.executar_pipeline_completo() for each student so all students'
        stage progress is tracked under the same task_id.
        """
        func_start = _get_function_body(
            routes_prompts_content, "async def _executar_pipeline_todos_os_alunos_background", window=450
        )
        assert "task_id" in func_start, (
            "_executar_pipeline_todos_os_alunos_background must declare task_id as a parameter. "
            "The endpoint passes task_id when calling background_tasks.add_task(helper, task_id=task_id, ...). "
            "The helper then passes task_id to each executor.executar_pipeline_completo() call."
        )

    def test_turma_endpoint_passes_task_id_to_helper(self, routes_prompts_content):
        """executar_pipeline_todos_os_alunos must pass task_id=task_id to _executar_pipeline_todos_os_alunos_background.

        Without passing task_id to the helper, the background loop runs with task_id=None
        and cannot call update_stage_progress() for any student. All stages stay pending.
        """
        func_body = _get_function_body(routes_prompts_content, "async def executar_pipeline_todos_os_alunos")
        add_task_pos = func_body.find("add_task")
        assert add_task_pos > 0, "add_task() call not found in executar_pipeline_todos_os_alunos"
        add_task_block = func_body[add_task_pos : add_task_pos + 500]
        assert "task_id=task_id" in add_task_block, (
            "background_tasks.add_task(_executar_pipeline_todos_os_alunos_background, ...) must include "
            "task_id=task_id so the helper can track progress for each student. "
            "Currently task_id is registered but not forwarded to the background helper."
        )
