"""
FD-T1 / FD-T2: Live cascade tests for desempenho pipeline.

FD-T1: Trigger materia desempenho with force_reexec=True — verify the cascade
       creates all levels and all 3 reports have non-blank resposta_raw (>200 chars).

FD-T2: Trigger turma desempenho with force_reexec=True on partial data —
       verify cascade creates missing student docs and turma report is non-blank.

Both tasks: live_test_required=True — real Render API, no mocking.

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_desempenho_cascade_live.py -v -m live
"""
import time
import pytest
import requests

from .conftest import LIVE_URL, MATERIA_ID, TURMA_ID, ATIVIDADE_ID

CASCADE_TIMEOUT = 600  # 10 minutes — cascade triggers multiple LLM calls
POLL_INTERVAL = 15     # seconds between task-progress polls

# Use Gemini 3 Flash — fast, cheap
PROVIDER_ID = "gem3flash001"

pytestmark = [pytest.mark.live]


# ============================================================
# Helpers
# ============================================================

def _trigger_desempenho(level: str, entity_id: str, force_reexec: bool = False) -> str:
    """POST to trigger desempenho pipeline with optional force_reexec. Returns task_id."""
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
    if force_reexec:
        form_data["force_reexec"] = "true"
    resp = requests.post(url, data=form_data, timeout=120)
    assert resp.status_code == 200, (
        f"Trigger {level} desempenho failed: HTTP {resp.status_code} — {resp.text[:300]}"
    )
    task_id = resp.json().get("task_id")
    assert task_id, f"No task_id returned from trigger: {resp.json()}"
    return task_id


def _poll_until_done(task_id: str, timeout: int = CASCADE_TIMEOUT) -> dict:
    """Poll /api/task-progress/{task_id} until status is no longer 'running'."""
    url = f"{LIVE_URL}/api/task-progress/{task_id}"
    deadline = time.time() + timeout
    last_status = "unknown"
    while time.time() < deadline:
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            time.sleep(POLL_INTERVAL)
            continue
        data = resp.json()
        last_status = data.get("status", "unknown")
        if last_status in ("completed", "failed", "error"):
            return data
        time.sleep(POLL_INTERVAL)
    pytest.fail(f"Task {task_id} timed out after {timeout}s — last status: {last_status}")


def _get_latest_desempenho_run(level: str, entity_id: str) -> dict:
    """Fetch the latest desempenho run for a given level+entity."""
    param_map = {
        "tarefa":  "atividade_id",
        "turma":   "turma_id",
        "materia": "materia_id",
    }
    url = f"{LIVE_URL}/api/desempenho/{level}/{entity_id}"
    resp = requests.get(url, timeout=60)
    if resp.status_code == 200:
        return resp.json()
    return {}


# ============================================================
# FD-T1: Cascade from materia — force_reexec triggers full cascade
# ============================================================

class TestFD_T1_CascadeFromMateria:
    """
    FD-T1: Trigger materia desempenho with force_reexec=True.
    The cascade should auto-create all upstream docs (student → tarefa → turma → materia).
    All 3 levels must produce non-blank resposta_raw (>200 chars).
    """

    def test_materia_cascade_force_reexec_completes(self):
        """Trigger materia desempenho with force_reexec → task completes (not failed)."""
        task_id = _trigger_desempenho("materia", MATERIA_ID, force_reexec=True)
        result = _poll_until_done(task_id)
        assert result["status"] == "completed", (
            f"FD-T1: Materia cascade failed — status={result['status']}, "
            f"error={result.get('error', 'none')}"
        )

    def test_tarefa_desempenho_has_content_after_cascade(self):
        """After materia cascade, tarefa-level report must have resposta_raw > 200 chars."""
        # First trigger the full cascade
        task_id = _trigger_desempenho("materia", MATERIA_ID, force_reexec=True)
        _poll_until_done(task_id)

        # Now check tarefa-level desempenho
        run = _get_latest_desempenho_run("tarefa", ATIVIDADE_ID)
        resposta = run.get("resposta_raw", "")
        assert len(resposta) > 200, (
            f"FD-T1: Tarefa desempenho resposta_raw too short ({len(resposta)} chars). "
            f"Expected >200 chars of real content. Content: {resposta[:100]!r}..."
        )

    def test_turma_desempenho_has_content_after_cascade(self):
        """After materia cascade, turma-level report must have resposta_raw > 200 chars."""
        run = _get_latest_desempenho_run("turma", TURMA_ID)
        resposta = run.get("resposta_raw", "")
        assert len(resposta) > 200, (
            f"FD-T1: Turma desempenho resposta_raw too short ({len(resposta)} chars). "
            f"Expected >200 chars of real content. Content: {resposta[:100]!r}..."
        )


# ============================================================
# FD-T2: Cascade from turma — partial docs scenario
# ============================================================

class TestFD_T2_CascadeFromTurma:
    """
    FD-T2: Trigger turma desempenho with force_reexec=True.
    Even if some student docs exist, cascade should re-create them
    and produce a non-blank turma report.
    """

    def test_turma_cascade_force_reexec_completes(self):
        """Trigger turma desempenho with force_reexec → task completes."""
        task_id = _trigger_desempenho("turma", TURMA_ID, force_reexec=True)
        result = _poll_until_done(task_id)
        assert result["status"] == "completed", (
            f"FD-T2: Turma cascade failed — status={result['status']}, "
            f"error={result.get('error', 'none')}"
        )

    def test_turma_resposta_raw_is_not_blank(self):
        """After turma cascade, resposta_raw must not be whitespace-only (FA-T2 fix)."""
        run = _get_latest_desempenho_run("turma", TURMA_ID)
        resposta = run.get("resposta_raw", "")
        assert resposta.strip(), (
            f"FD-T2: Turma desempenho resposta_raw is blank/whitespace. "
            f"FA-T2 fix may not be deployed. Raw: {resposta!r}"
        )
        assert len(resposta) > 200, (
            f"FD-T2: Turma desempenho resposta_raw too short ({len(resposta)} chars). "
            f"Expected >200 chars of real content."
        )

    def test_cache_control_header_present(self):
        """FB-T2 fix: serve_frontend has no-cache header so browsers don't serve stale HTML."""
        resp = requests.get(LIVE_URL, timeout=60)
        assert resp.status_code == 200
        cc = resp.headers.get("cache-control", "")
        assert "no-cache" in cc.lower(), (
            f"FD-T2: Cache-Control header missing or wrong. "
            f"Expected 'no-cache, must-revalidate', got: {cc!r}"
        )
