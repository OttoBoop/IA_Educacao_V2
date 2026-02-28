"""
Tests for the Desempenho API endpoints (A-T1 + A-T2).

A-T1: GET /api/desempenho/{level}/{entity_id}
  - Returns only desempenho docs for the given entity (server-side filtering)
  - Groups documents by pipeline run
  - Includes has_atividades flag for empty-state UI logic
  - Validates level parameter (tarefa/turma/materia)

A-T2: DELETE /api/desempenho/run/{run_id}
  - Deletes all documents belonging to a pipeline run
  - Returns 404 for non-existent run

Plan: docs/PLAN_Desempenho_Tab_UX_Overhaul.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_desempenho_api_endpoints.py -v
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models import TipoDocumento, Documento, StatusProcessamento


# ============================================================
# Helpers
# ============================================================

def _make_desempenho_doc(
    doc_id: str,
    tipo: TipoDocumento,
    atividade_id: str,
    criado_em: datetime = None,
    nome_arquivo: str = "relatorio_desempenho.md",
) -> Documento:
    """Create a Documento instance for testing."""
    return Documento(
        id=doc_id,
        tipo=tipo,
        atividade_id=atividade_id,
        nome_arquivo=nome_arquivo,
        caminho_arquivo=f"data/{nome_arquivo}",
        criado_em=criado_em or datetime(2026, 2, 27, 12, 8, 25),
        atualizado_em=criado_em or datetime(2026, 2, 27, 12, 8, 25),
        criado_por="sistema",
        status=StatusProcessamento.CONCLUIDO,
    )


def _make_narrativo_doc(doc_id: str, atividade_id: str, aluno_id: str) -> Documento:
    """Create a RELATORIO_NARRATIVO doc (indicates graded work exists)."""
    return Documento(
        id=doc_id,
        tipo=TipoDocumento.RELATORIO_NARRATIVO,
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        nome_arquivo="relatorio_narrativo.md",
        caminho_arquivo="data/relatorio_narrativo.md",
        criado_em=datetime(2026, 2, 27, 10, 0, 0),
        atualizado_em=datetime(2026, 2, 27, 10, 0, 0),
        criado_por="sistema",
        status=StatusProcessamento.CONCLUIDO,
    )


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    from fastapi.testclient import TestClient
    from main_v2 import app
    with TestClient(app) as c:
        yield c


# ============================================================
# A-T1: GET /api/desempenho/{level}/{entity_id}
# ============================================================

class TestDesempenhoGetEndpoint:
    """A-T1: GET /api/desempenho/{level}/{entity_id}

    Tests that the endpoint exists, returns structured data,
    filters correctly, and groups docs by pipeline run.
    """

    # --- Endpoint existence ---

    def test_endpoint_exists_tarefa(self, client):
        """GET /api/desempenho/tarefa/{id} must exist (not return generic 404)."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            "GET /api/desempenho/tarefa/{{id}} endpoint must exist in routes_extras.py"
        )

    def test_endpoint_exists_turma(self, client):
        """GET /api/desempenho/turma/{id} must exist."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_atividades.return_value = []
            mock_storage.listar_alunos.return_value = []
            mock_storage.get_turma.return_value = MagicMock(id="turma-001", nome="Turma A")
            response = client.get("/api/desempenho/turma/turma-001")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            "GET /api/desempenho/turma/{{id}} endpoint must exist."
        )

    def test_endpoint_exists_materia(self, client):
        """GET /api/desempenho/materia/{id} must exist."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_turmas.return_value = []
            mock_storage.get_materia.return_value = MagicMock(id="mat-001", nome="Matemática")
            response = client.get("/api/desempenho/materia/mat-001")
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            "GET /api/desempenho/materia/{{id}} endpoint must exist."
        )

    # --- Response structure ---

    def test_response_has_runs_and_meta(self, client):
        """Response JSON must contain 'runs', 'has_atividades', and 'meta' keys."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert "runs" in data, "Response must include 'runs' array"
        assert "has_atividades" in data, "Response must include 'has_atividades' flag"
        assert "meta" in data, "Response must include 'meta' object"

    def test_runs_is_list(self, client):
        """'runs' must be a list."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert isinstance(data["runs"], list), "runs must be a list"

    # --- Filtering ---

    def test_returns_only_desempenho_docs(self, client):
        """Endpoint must return only RELATORIO_DESEMPENHO_TAREFA docs for tarefa level,
        not student docs, not base docs, not other desempenho levels."""
        desempenho_doc = _make_desempenho_doc(
            "doc-desemp-1", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001"
        )
        student_doc = _make_narrativo_doc("doc-narr-1", "ativ-001", "aluno-001")
        other_level_doc = _make_desempenho_doc(
            "doc-turma-1", TipoDocumento.RELATORIO_DESEMPENHO_TURMA, "ativ-001"
        )

        with patch("routes_extras.storage") as mock_storage:
            # listar_documentos returns all docs for the atividade
            mock_storage.listar_documentos.return_value = [desempenho_doc, student_doc, other_level_doc]
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        all_doc_ids = []
        for run in data["runs"]:
            for doc in run["docs"]:
                all_doc_ids.append(doc["id"])

        assert "doc-desemp-1" in all_doc_ids, "Must include desempenho tarefa doc"
        assert "doc-narr-1" not in all_doc_ids, "Must NOT include narrative student docs"
        assert "doc-turma-1" not in all_doc_ids, "Must NOT include other-level desempenho docs"

    # --- Run grouping ---

    def test_groups_docs_by_run_timestamp(self, client):
        """Documents created within a short time window (same pipeline run)
        should be grouped into the same run."""
        t1 = datetime(2026, 2, 27, 12, 8, 25)
        t2 = datetime(2026, 2, 27, 12, 8, 26)  # 1 second later — same run
        t3 = datetime(2026, 2, 28, 14, 0, 0)   # Next day — different run

        doc1 = _make_desempenho_doc("doc-1", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001", t1)
        doc2 = _make_desempenho_doc("doc-2", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001", t2)
        doc3 = _make_desempenho_doc("doc-3", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001", t3)

        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = [doc1, doc2, doc3]
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert len(data["runs"]) == 2, (
            f"Expected 2 runs (docs 1+2 grouped, doc 3 separate), got {len(data['runs'])}"
        )

    def test_each_run_has_required_fields(self, client):
        """Each run object must have 'id', 'date', and 'docs' fields."""
        doc = _make_desempenho_doc("doc-1", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001")

        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = [doc]
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert len(data["runs"]) >= 1, "Should have at least 1 run"
        run = data["runs"][0]
        assert "id" in run, "Run must have 'id' field"
        assert "date" in run, "Run must have 'date' field"
        assert "docs" in run, "Run must have 'docs' array"
        assert len(run["docs"]) >= 1, "Run must contain at least 1 doc"

    # --- has_atividades flag ---

    def test_has_atividades_true_when_narratives_exist(self, client):
        """has_atividades should be true when RELATORIO_NARRATIVO docs exist
        (indicating graded work has been done)."""
        narrativo = _make_narrativo_doc("doc-narr-1", "ativ-001", "aluno-001")

        with patch("routes_extras.storage") as mock_storage:
            # Return narrative doc when checking for graded work
            mock_storage.listar_documentos.return_value = [narrativo]
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert data["has_atividades"] is True, (
            "has_atividades should be True when graded work (narratives) exists"
        )

    def test_has_atividades_false_when_no_narratives(self, client):
        """has_atividades should be false when no RELATORIO_NARRATIVO docs exist."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert data["has_atividades"] is False, (
            "has_atividades should be False when no graded work exists"
        )

    # --- Meta object ---

    def test_meta_contains_entity_info(self, client):
        """Meta object should contain entity_id, level, and counts."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        meta = data["meta"]
        assert meta["entity_id"] == "ativ-001"
        assert meta["level"] == "tarefa"

    # --- Invalid level ---

    def test_invalid_level_returns_400(self, client):
        """A level that isn't tarefa/turma/materia should return 400."""
        response = client.get("/api/desempenho/invalido/some-id")
        assert response.status_code == 400, (
            f"Expected 400 for invalid level, got {response.status_code}"
        )

    # --- Empty runs ---

    def test_empty_runs_when_no_desempenho_docs(self, client):
        """If no desempenho docs exist, runs should be an empty list."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.get("/api/desempenho/tarefa/ativ-001")

        data = response.json()
        assert data["runs"] == [], "runs should be empty when no desempenho docs exist"

    # --- Turma-level queries ---

    def test_turma_level_scans_all_atividades(self, client):
        """Turma-level query must find desempenho docs across all atividades of the turma."""
        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        ativ2 = MagicMock(id="ativ-002", nome="Prova 2")

        doc_turma = _make_desempenho_doc(
            "doc-turma-1", TipoDocumento.RELATORIO_DESEMPENHO_TURMA, "ativ-001"
        )

        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_atividades.return_value = [ativ1, ativ2]
            mock_storage.listar_alunos.return_value = [MagicMock(id="a1")]
            mock_storage.get_turma.return_value = MagicMock(id="turma-001", nome="Turma A")
            # Return desempenho doc only for ativ-001
            def side_effect_docs(atividade_id, tipo=None, **kwargs):
                if atividade_id == "ativ-001" and tipo == TipoDocumento.RELATORIO_DESEMPENHO_TURMA:
                    return [doc_turma]
                return []
            mock_storage.listar_documentos.side_effect = side_effect_docs
            response = client.get("/api/desempenho/turma/turma-001")

        data = response.json()
        all_doc_ids = [doc["id"] for run in data["runs"] for doc in run["docs"]]
        assert "doc-turma-1" in all_doc_ids, "Must find turma desempenho doc via atividade scan"


# ============================================================
# A-T2: DELETE /api/desempenho/run/{run_id}
# ============================================================

class TestDesempenhoDeleteRunEndpoint:
    """A-T2: DELETE /api/desempenho/run/{run_id}?level=...&entity_id=...

    Tests that the endpoint deletes all documents belonging to a pipeline run
    and returns appropriate responses.
    """

    def test_delete_endpoint_exists(self, client):
        """DELETE /api/desempenho/run/{run_id} must exist and accept level+entity_id params."""
        t = datetime(2026, 2, 27, 12, 8, 25)
        doc = _make_desempenho_doc("doc-1", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001", t)

        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = [doc]
            mock_storage.deletar_documento.return_value = True
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.delete(
                "/api/desempenho/run/run-20260227-120825",
                params={"level": "tarefa", "entity_id": "ativ-001"},
            )
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. "
            "DELETE /api/desempenho/run/{{run_id}} endpoint must exist."
        )

    def test_delete_returns_404_for_nonexistent_run(self, client):
        """Deleting a run_id that doesn't match any grouped run should return 404."""
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = []
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.delete(
                "/api/desempenho/run/run-99990101-000000",
                params={"level": "tarefa", "entity_id": "ativ-001"},
            )
        assert response.status_code == 404, (
            f"Expected 404 for nonexistent run, got {response.status_code}"
        )

    def test_delete_removes_all_docs_in_run(self, client):
        """All documents in the matching run must be deleted via deletar_documento."""
        t = datetime(2026, 2, 27, 12, 8, 25)
        doc1 = _make_desempenho_doc("doc-1", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001", t)
        doc2 = _make_desempenho_doc(
            "doc-2", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001",
            datetime(2026, 2, 27, 12, 8, 26),  # 1 second later — same run
        )
        # Run id uses the newest doc's timestamp (sorted descending): 120826
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = [doc1, doc2]
            mock_storage.deletar_documento.return_value = True
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.delete(
                "/api/desempenho/run/run-20260227-120826",
                params={"level": "tarefa", "entity_id": "ativ-001"},
            )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert mock_storage.deletar_documento.call_count == 2, (
            f"Must call deletar_documento for each doc in the run. "
            f"Expected 2 calls, got {mock_storage.deletar_documento.call_count}"
        )

    def test_delete_returns_deleted_count(self, client):
        """Successful delete should return the count of deleted documents."""
        t = datetime(2026, 2, 27, 12, 8, 25)
        doc = _make_desempenho_doc("doc-1", TipoDocumento.RELATORIO_DESEMPENHO_TAREFA, "ativ-001", t)

        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos.return_value = [doc]
            mock_storage.deletar_documento.return_value = True
            mock_storage.get_atividade.return_value = MagicMock(id="ativ-001", nome="Prova 1", turma_id="t1")
            response = client.delete(
                "/api/desempenho/run/run-20260227-120825",
                params={"level": "tarefa", "entity_id": "ativ-001"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data, "Response must include deleted_count"
        assert data["deleted_count"] == 1, f"Expected 1 deleted doc, got {data['deleted_count']}"

    def test_delete_requires_level_and_entity_id(self, client):
        """DELETE without level and entity_id query params should fail."""
        response = client.delete("/api/desempenho/run/run-20260227-120825")
        assert response.status_code in [400, 422], (
            f"Expected 400/422 when level and entity_id are missing, got {response.status_code}"
        )

    def test_delete_invalid_level_returns_400(self, client):
        """DELETE with invalid level should return 400."""
        response = client.delete(
            "/api/desempenho/run/run-20260227-120825",
            params={"level": "invalido", "entity_id": "ativ-001"},
        )
        assert response.status_code == 400, (
            f"Expected 400 for invalid level, got {response.status_code}"
        )
