"""
F1-T6 / F1-T7: Live integration tests for desempenho executor fix.

F1-T6: Tarefa desempenho completes successfully (no "0 narrativas legíveis" error)
       after the PyMuPDF (fitz) fix is deployed and student docs exist.

F1-T7: All 3 desempenho levels (tarefa/turma/materia) return completed
       reports on the live Render deployment.

Both tasks: live_test_required=True — no mocking, real Render API only.

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f1_desempenho_api.py -v -m live
"""
import time
import pytest
import requests

from .conftest import LIVE_URL, MATERIA_ID, TURMA_ID, ATIVIDADE_ID

GENERATION_TIMEOUT = 300  # 5 minutes — desempenho LLM calls can be slow
POLL_INTERVAL = 10        # seconds between task-progress polls

# Use Gemini 3 Flash — fast, cheap. Live server ID verified via /api/providers/disponiveis
PROVIDER_ID = "gem3flash001"

pytestmark = [pytest.mark.live]


# ============================================================
# Helpers
# ============================================================

def _trigger_desempenho(level: str, entity_id: str) -> str:
    """POST to trigger desempenho pipeline. Returns task_id or raises on failure."""
    path_map = {
        "tarefa":  "/api/executar/pipeline-desempenho-tarefa",
        "turma":   "/api/executar/pipeline-desempenho-turma",
        "materia": "/api/executar/pipeline-desempenho-materia",
    }
    param_map = {
        "tarefa":  "atividade_id",
        "turma":   "turma_id",
        "materia": "materia_id",
    }
    url = LIVE_URL + path_map[level]
    form_data = {
        param_map[level]: entity_id,
        "provider_id": PROVIDER_ID,
    }
    resp = requests.post(url, data=form_data, timeout=30)
    assert resp.status_code == 200, (
        f"Trigger {level} desempenho failed: HTTP {resp.status_code} — {resp.text[:300]}"
    )
    task_id = resp.json().get("task_id")
    assert task_id, f"No task_id returned from trigger: {resp.json()}"
    return task_id


def _poll_until_done(task_id: str, timeout: int = GENERATION_TIMEOUT) -> dict:
    """Poll /api/task-progress/{task_id} until status is no longer 'running'. Returns final task."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        try:
            resp = requests.get(f"{LIVE_URL}/api/task-progress/{task_id}", timeout=15)
            if resp.ok:
                task = resp.json()
                if task.get("status") not in ("running", "pending", None):
                    return task
        except requests.RequestException:
            pass  # retry on transient errors
    return {}


def _get_desempenho_runs(level: str, entity_id: str) -> list:
    """GET /api/desempenho/{level}/{entity_id}. Returns runs list or []."""
    url = f"{LIVE_URL}/api/desempenho/{level}/{entity_id}"
    try:
        resp = requests.get(url, timeout=15)
        if resp.ok:
            return resp.json().get("runs", [])
    except requests.RequestException:
        pass
    return []


# ============================================================
# F1-T6: Tarefa desempenho completes without "0 narrativas"
# ============================================================

class TestF1T6DesempenhoTarefaIntegration:
    """F1-T6: Tarefa desempenho completes via direct API — fitz fix must be deployed."""

    @pytest.mark.live
    def test_tarefa_desempenho_completes_without_0_narrativas(self):
        """
        Trigger tarefa desempenho via API, poll until done, assert completed.

        RED: fails because executor still uses open() on binary PDFs
             (UnicodeDecodeError silently caught → "0 narrativas legíveis" → status=failed).
        GREEN: passes after fitz fix is deployed AND student RELATORIO_FINAL docs exist.

        provider: gemini-3-flash-preview (fast, low cost)
        """
        task_id = _trigger_desempenho("tarefa", ATIVIDADE_ID)

        task = _poll_until_done(task_id)
        assert task, (
            f"Task {task_id} did not complete within {GENERATION_TIMEOUT}s. "
            "Render may be slow or the background task is hanging."
        )

        status = task.get("status")
        error = task.get("error", "")

        assert status == "completed", (
            f"Tarefa desempenho FAILED.\n"
            f"  status = {status!r}\n"
            f"  error  = {error!r}\n\n"
            f"  Common causes:\n"
            f"  - '0 narrativas legíveis': fitz fix (F1-T4) not deployed yet\n"
            f"    → git -C IA_Educacao_V2 push origin main\n"
            f"  - 'insufficient docs': atividade {ATIVIDADE_ID} has no student\n"
            f"    RELATORIO_FINAL docs → update conftest.py with a materia that has docs"
        )

        # Also verify runs were persisted
        runs = _get_desempenho_runs("tarefa", ATIVIDADE_ID)
        assert runs, (
            f"Task {task_id} completed but GET /api/desempenho/tarefa/{ATIVIDADE_ID} "
            "returned no runs. Check executor _salvar_resultado() call."
        )


# ============================================================
# F1-T7: All 3 desempenho levels return completed runs
# ============================================================

class TestF1T7AllDesempenhoLevels:
    """F1-T7: All 3 levels complete on Render — depends on F1-T6 passing first."""

    @pytest.mark.live
    def test_tarefa_desempenho_has_runs(self):
        """Tarefa level: GET runs returns at least 1 run with docs."""
        runs = _get_desempenho_runs("tarefa", ATIVIDADE_ID)
        assert runs, (
            f"No tarefa desempenho runs for atividade {ATIVIDADE_ID}. "
            "Run test_tarefa_desempenho_completes_without_0_narrativas first."
        )
        assert any(run.get("docs") for run in runs), (
            "Tarefa runs exist but none contain docs. "
            "Check executor _salvar_resultado output."
        )

    @pytest.mark.live
    def test_turma_desempenho_completes(self):
        """Turma level: trigger desempenho, poll, verify completed with docs."""
        task_id = _trigger_desempenho("turma", TURMA_ID)

        task = _poll_until_done(task_id)
        assert task, f"Turma task {task_id} did not complete within {GENERATION_TIMEOUT}s"

        status = task.get("status")
        error = task.get("error", "")
        assert status == "completed", (
            f"Turma desempenho FAILED: status={status!r}, error={error!r}"
        )

        runs = _get_desempenho_runs("turma", TURMA_ID)
        assert runs and any(run.get("docs") for run in runs), (
            f"Turma desempenho completed but no docs found for turma {TURMA_ID}."
        )

    @pytest.mark.live
    def test_materia_desempenho_completes(self):
        """Matéria level: trigger desempenho, poll, verify completed with docs."""
        task_id = _trigger_desempenho("materia", MATERIA_ID)

        task = _poll_until_done(task_id)
        assert task, f"Materia task {task_id} did not complete within {GENERATION_TIMEOUT}s"

        status = task.get("status")
        error = task.get("error", "")
        assert status == "completed", (
            f"Materia desempenho FAILED: status={status!r}, error={error!r}"
        )

        runs = _get_desempenho_runs("materia", MATERIA_ID)
        assert runs and any(run.get("docs") for run in runs), (
            f"Materia desempenho completed but no docs found for materia {MATERIA_ID}."
        )
