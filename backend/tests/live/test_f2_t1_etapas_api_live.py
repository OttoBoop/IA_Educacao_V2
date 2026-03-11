"""
F2-T1: Live test — verify status-etapas API returns all pipeline phases.

RED phase — the API already returns all phases, so this test should PASS
(it documents that the backend is correct; the bug is frontend-only).
"""

import pytest
import requests

from .conftest import LIVE_URL, ATIVIDADE_ID

pytestmark = [pytest.mark.live]

# Use a known aluno_id from Cálculo 1 (EPGE 2021, A1)
# If unknown, the API should still return the phase structure (with executada=False)
ALUNO_ID_PLACEHOLDER = "any_aluno"

EXPECTED_PHASES = [
    "extrair_questoes",
    "extrair_gabarito",
    "extrair_respostas",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]


class TestF2T1_EtapasAPILive:
    """F2-T1: Verify the status-etapas API returns all 6 pipeline phases."""

    def test_status_etapas_returns_all_phases(self):
        """GET /api/executar/status-etapas/{atividade}/{aluno} must return all 6 phases."""
        url = f"{LIVE_URL}/api/executar/status-etapas/{ATIVIDADE_ID}/{ALUNO_ID_PLACEHOLDER}"
        resp = requests.get(url, timeout=60)
        assert resp.status_code == 200, f"status-etapas returned {resp.status_code}"
        data = resp.json()
        etapas = data.get("etapas", {})
        for phase in EXPECTED_PHASES:
            assert phase in etapas, (
                f"Phase '{phase}' missing from status-etapas response. "
                f"Got phases: {list(etapas.keys())}"
            )

    def test_each_phase_has_executada_field(self):
        """Each phase must have an 'executada' boolean field."""
        url = f"{LIVE_URL}/api/executar/status-etapas/{ATIVIDADE_ID}/{ALUNO_ID_PLACEHOLDER}"
        resp = requests.get(url, timeout=60)
        assert resp.status_code == 200
        data = resp.json()
        etapas = data.get("etapas", {})
        for phase in EXPECTED_PHASES:
            if phase in etapas:
                assert "executada" in etapas[phase], (
                    f"Phase '{phase}' missing 'executada' field"
                )
