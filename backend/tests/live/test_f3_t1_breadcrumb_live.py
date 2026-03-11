"""
F3-T1: Live test — verify the breadcrumb API returns real entity names.

This test should PASS because the backend endpoint already exists.
It documents backend readiness; the failing work is frontend-only (unit tests).

Endpoint: GET /api/navegacao/breadcrumb/{tipo}/{id}
Expected response: list of dicts with 'tipo', 'id', 'nome' keys.

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f3_t1_breadcrumb_live.py -v -m live
"""

import pytest
import requests

from .conftest import LIVE_URL, ATIVIDADE_ID, TURMA_ID, MATERIA_ID

pytestmark = [pytest.mark.live]


class TestF3T1_BreadcrumbAPILive:
    """Verify /api/navegacao/breadcrumb/{tipo}/{id} returns real entity names."""

    def test_breadcrumb_for_atividade_returns_200(self):
        """GET /api/navegacao/breadcrumb/atividade/{id} must return HTTP 200."""
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/atividade/{ATIVIDADE_ID}"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"Expected 200 from breadcrumb API for atividade {ATIVIDADE_ID}, "
            f"got {resp.status_code}. Response: {resp.text[:300]}"
        )

    def test_breadcrumb_for_atividade_returns_list(self):
        """Breadcrumb response body must contain a 'breadcrumb' key with a non-empty list."""
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/atividade/{ATIVIDADE_ID}"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, f"API returned {resp.status_code}"
        data = resp.json()
        # API returns {"breadcrumb": [...]}
        assert isinstance(data, dict) and "breadcrumb" in data, (
            f"Breadcrumb response must be a dict with a 'breadcrumb' key, got: {data}"
        )
        crumbs = data["breadcrumb"]
        assert isinstance(crumbs, list) and len(crumbs) > 0, (
            "breadcrumb list must not be empty for a known atividade ID."
        )

    def _get_crumbs(self, tipo, entity_id):
        """Helper: fetch breadcrumb list for the given tipo/id."""
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/{tipo}/{entity_id}"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, f"API returned {resp.status_code}"
        data = resp.json()
        return data["breadcrumb"]

    def test_each_crumb_has_nome_field(self):
        """Each breadcrumb item must have a 'nome' key with a non-empty string."""
        crumbs = self._get_crumbs("atividade", ATIVIDADE_ID)
        for crumb in crumbs:
            assert "nome" in crumb, (
                f"Breadcrumb item missing 'nome' key: {crumb}"
            )
            assert isinstance(crumb["nome"], str) and crumb["nome"].strip(), (
                f"'nome' must be a non-empty string, got: {crumb['nome']!r}"
            )

    def test_each_crumb_has_tipo_and_id_fields(self):
        """Each breadcrumb item must have 'tipo' and 'id' keys."""
        crumbs = self._get_crumbs("atividade", ATIVIDADE_ID)
        for crumb in crumbs:
            assert "tipo" in crumb, f"Breadcrumb item missing 'tipo': {crumb}"
            assert "id" in crumb, f"Breadcrumb item missing 'id': {crumb}"

    def test_atividade_breadcrumb_includes_materia_and_turma(self):
        """Atividade breadcrumb must contain at least materia and turma ancestors."""
        crumbs = self._get_crumbs("atividade", ATIVIDADE_ID)
        tipos = [c.get("tipo") for c in crumbs]
        assert "materia" in tipos or "matéria" in tipos, (
            f"Atividade breadcrumb must include a 'materia' ancestor. Got tipos: {tipos}"
        )
        assert "turma" in tipos, (
            f"Atividade breadcrumb must include a 'turma' ancestor. Got tipos: {tipos}"
        )

    def test_nome_fields_are_real_names_not_id_hashes(self):
        """Entity names must be human-readable strings, not raw ID hashes."""
        crumbs = self._get_crumbs("atividade", ATIVIDADE_ID)
        for crumb in crumbs:
            nome = crumb.get("nome", "")
            # ID hashes are 16 hex chars; real names are not
            is_hex_hash = len(nome) == 16 and all(c in "0123456789abcdef" for c in nome.lower())
            assert not is_hex_hash, (
                f"'nome' looks like a raw ID hash ({nome!r}) rather than a human-readable name. "
                "The API must resolve entity names, not echo back the ID."
            )

    def test_breadcrumb_for_turma_returns_200(self):
        """GET /api/navegacao/breadcrumb/turma/{id} must also return HTTP 200."""
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/turma/{TURMA_ID}"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"Breadcrumb API for turma returned {resp.status_code}. "
            f"Response: {resp.text[:300]}"
        )

    def test_breadcrumb_for_materia_returns_200(self):
        """GET /api/navegacao/breadcrumb/materia/{id} must also return HTTP 200."""
        url = f"{LIVE_URL}/api/navegacao/breadcrumb/materia/{MATERIA_ID}"
        resp = requests.get(url, timeout=30)
        assert resp.status_code == 200, (
            f"Breadcrumb API for materia returned {resp.status_code}. "
            f"Response: {resp.text[:300]}"
        )
