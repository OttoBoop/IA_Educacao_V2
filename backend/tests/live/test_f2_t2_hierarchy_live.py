"""
F2-T2 Live tests: verify that the backend APIs required for level-dependent
hierarchy nesting already return the correct data.

These tests hit the live Render deployment and confirm:
  - GET /api/atividades?turma_id={TURMA_ID} returns atividades (needed for turma grouping)
  - GET /api/turmas?materia_id={MATERIA_ID} returns turmas (needed for materia grouping)

The backend APIs are expected to already return the correct data (the bug is
frontend-only — prefetchDesempenhoEtapasState() doesn't call these endpoints
for turma/materia levels). These tests SHOULD PASS on the live deployment.

Run: cd IA_Educacao_V2/backend && python -m pytest tests/live/test_f2_t2_hierarchy_live.py -v -m live
"""

import pytest
import requests

from .conftest import LIVE_URL, MATERIA_ID, TURMA_ID

pytestmark = [pytest.mark.live]

REQUEST_TIMEOUT = 30  # seconds


# ── Test 1: atividades API for turma ────────────────────────────────────────


class TestTurmaAtividadesAPI:
    """Verify /api/atividades?turma_id returns atividades for the known turma.

    F2-T2 turma level requires fetching atividades to use as group headers.
    This test confirms the data exists in the live backend before the frontend
    is updated to request it.
    """

    def test_turma_atividades_api_returns_data(self):
        """GET /api/atividades?turma_id={TURMA_ID} must return at least 1 atividade.

        This endpoint is already called by the tarefa branch. Confirming it works
        for TURMA_ID validates the data source for the F2-T2 turma grouping.
        """
        url = f"{LIVE_URL}/api/atividades"
        params = {"turma_id": TURMA_ID}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

        assert resp.status_code == 200, (
            f"GET /api/atividades?turma_id={TURMA_ID} returned HTTP {resp.status_code}. "
            f"Response body: {resp.text[:300]}"
        )

        data = resp.json()
        # Accept either 'atividades' key or a list directly
        atividades = data.get("atividades") or data if isinstance(data, list) else []

        assert len(atividades) > 0, (
            f"GET /api/atividades?turma_id={TURMA_ID} returned 0 atividades. "
            f"Response: {data}. "
            "\nF2-T2 turma hierarchy nesting requires at least 1 atividade to group "
            "alunos under. Check that TURMA_ID in conftest.py points to a turma "
            "that has atividades (EPGE 2021 should have A1 - Cálculo 1)."
        )

    def test_turma_atividades_have_id_and_nome(self):
        """Each atividade returned for the turma must have id and nome fields.

        F2-T2 renders atividade.nome as the group header and uses atividade.id
        to fetch docs for each atividade. Both fields are mandatory.
        """
        url = f"{LIVE_URL}/api/atividades"
        params = {"turma_id": TURMA_ID}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        assert resp.status_code == 200

        data = resp.json()
        atividades = data.get("atividades") or (data if isinstance(data, list) else [])

        assert atividades, f"No atividades returned for turma {TURMA_ID}"

        for atv in atividades:
            assert "id" in atv, (
                f"Atividade missing 'id' field: {atv}. "
                "F2-T2 needs atividade.id to fetch alunos + docs per atividade."
            )
            # nome may be stored as 'nome' or 'name'
            has_name = "nome" in atv or "name" in atv
            assert has_name, (
                f"Atividade missing 'nome'/'name' field: {atv}. "
                "F2-T2 renders the atividade name as a group header."
            )


# ── Test 2: turmas API for materia ───────────────────────────────────────────


class TestMateriaTurmasAPI:
    """Verify /api/turmas?materia_id returns turmas for the known materia.

    F2-T2 materia level requires fetching turmas to use as the outermost
    group headers (Turma → Atividade → Aluno → Phases).
    """

    def test_materia_turmas_api_returns_data(self):
        """GET /api/turmas?materia_id={MATERIA_ID} must return at least 1 turma.

        This confirms the data exists before the frontend is updated to call it.
        """
        url = f"{LIVE_URL}/api/turmas"
        params = {"materia_id": MATERIA_ID}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)

        assert resp.status_code == 200, (
            f"GET /api/turmas?materia_id={MATERIA_ID} returned HTTP {resp.status_code}. "
            f"Response body: {resp.text[:300]}"
        )

        data = resp.json()
        turmas = data.get("turmas") or (data if isinstance(data, list) else [])

        assert len(turmas) > 0, (
            f"GET /api/turmas?materia_id={MATERIA_ID} returned 0 turmas. "
            f"Response: {data}. "
            "\nF2-T2 materia hierarchy nesting requires at least 1 turma to group "
            "atividades under. Check that MATERIA_ID in conftest.py points to "
            "'Cálculo 1', which should have at least EPGE 2021."
        )

    def test_materia_turmas_have_id_and_nome(self):
        """Each turma returned for the materia must have id and nome fields.

        F2-T2 renders turma.nome as the outermost group header and uses turma.id
        to fetch atividades per turma. Both fields are mandatory.
        """
        url = f"{LIVE_URL}/api/turmas"
        params = {"materia_id": MATERIA_ID}
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        assert resp.status_code == 200

        data = resp.json()
        turmas = data.get("turmas") or (data if isinstance(data, list) else [])

        assert turmas, f"No turmas returned for materia {MATERIA_ID}"

        for turma in turmas:
            assert "id" in turma, (
                f"Turma missing 'id' field: {turma}. "
                "F2-T2 needs turma.id to fetch atividades per turma."
            )
            has_name = "nome" in turma or "name" in turma
            assert has_name, (
                f"Turma missing 'nome'/'name' field: {turma}. "
                "F2-T2 renders the turma name as the outermost group header."
            )
