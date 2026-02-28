"""
B-T1 / B-T2 / B-T3: Structural tests for the Desempenho Tab UI Overhaul.

B-T1: Tab HTML rewrite — card layout + loadDesempenhoData() replacing loadDesempenhoDocs()
B-T2: renderDesempenhoRuns() — grouped-by-run doc display with per-doc and per-run actions
B-T3: Empty state + no-data disable logic based on has_atividades flag

These are pure file-content checks (no browser needed).

RED Phase: These tests FAIL because the UI overhaul is not yet implemented.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_desempenho_ui_overhaul.py -v
"""

from pathlib import Path

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


# ============================================================
# B-T1: Tab HTML rewrite — card layout + new API
# ============================================================

class TestBT1TabHtmlCardLayout:
    """B-T1: All 3 desempenho tabs must use a card layout and the new API endpoint."""

    def test_bt1_load_desempenho_data_function_exists(self, html_content):
        """loadDesempenhoData() must exist — replaces the old loadDesempenhoDocs() for tab loading."""
        assert "function loadDesempenhoData(" in html_content or "async function loadDesempenhoData(" in html_content, (
            "index_v2.html must define a 'loadDesempenhoData' function "
            "that fetches data from the new /api/desempenho/ endpoint."
        )

    def test_bt1_uses_new_desempenho_api_endpoint(self, html_content):
        """The new function must call /api/desempenho/ (not /documentos/todos)."""
        assert "/api/desempenho/" in html_content, (
            "index_v2.html must reference '/api/desempenho/' endpoint "
            "for loading desempenho data server-side."
        )

    def test_bt1_materia_tab_calls_load_desempenho_data(self, html_content):
        """showMateriaTab desempenho handler must call loadDesempenhoData (not loadDesempenhoDocs)."""
        # Find the materia desempenho tab handler section
        assert "loadDesempenhoData('materia'" in html_content, (
            "showMateriaTab('desempenho') must call loadDesempenhoData('materia', materiaId) "
            "instead of the old loadDesempenhoDocs."
        )

    def test_bt1_turma_tab_calls_load_desempenho_data(self, html_content):
        """showTurmaTab desempenho handler must call loadDesempenhoData (not loadDesempenhoDocs)."""
        assert "loadDesempenhoData('turma'" in html_content, (
            "showTurmaTab('desempenho') must call loadDesempenhoData('turma', turmaId) "
            "instead of the old loadDesempenhoDocs."
        )

    def test_bt1_atividade_tab_calls_load_desempenho_data(self, html_content):
        """showAtividadeTab desempenho handler must call loadDesempenhoData (not loadDesempenhoDocs)."""
        assert "loadDesempenhoData('tarefa'" in html_content, (
            "showAtividadeTab('desempenho') must call loadDesempenhoData('tarefa', atividadeId) "
            "instead of the old loadDesempenhoDocs."
        )

    def test_bt1_desempenho_runs_container_materia(self, html_content):
        """Materia desempenho tab must have a container for rendered runs."""
        assert "desempenho-runs-materia" in html_content, (
            "index_v2.html must have a container with id 'desempenho-runs-materia' "
            "to hold the grouped-by-run document display."
        )

    def test_bt1_desempenho_runs_container_turma(self, html_content):
        """Turma desempenho tab must have a container for rendered runs."""
        assert "desempenho-runs-turma" in html_content, (
            "index_v2.html must have a container with id 'desempenho-runs-turma' "
            "to hold the grouped-by-run document display."
        )

    def test_bt1_desempenho_runs_container_tarefa(self, html_content):
        """Atividade desempenho tab must have a container for rendered runs."""
        assert "desempenho-runs-tarefa" in html_content, (
            "index_v2.html must have a container with id 'desempenho-runs-tarefa' "
            "to hold the grouped-by-run document display."
        )

    def test_bt1_generate_button_area(self, html_content):
        """Each tab must have a dedicated generate button area (for progress indicator later)."""
        assert "desempenho-generate-area" in html_content, (
            "index_v2.html must have a 'desempenho-generate-area' container "
            "for the generate button (will become progress indicator in B-T4)."
        )


# ============================================================
# B-T2: renderDesempenhoRuns() — grouped doc display
# ============================================================

class TestBT2RenderDesempenhoRuns:
    """B-T2: renderDesempenhoRuns() must render grouped-by-run documents with actions."""

    def test_bt2_render_function_exists(self, html_content):
        """renderDesempenhoRuns function must be defined."""
        assert "function renderDesempenhoRuns(" in html_content, (
            "index_v2.html must define a 'renderDesempenhoRuns' function "
            "that takes runs[] and renders grouped doc display."
        )

    def test_bt2_per_run_excluir_button(self, html_content):
        """Each run group must have an 'Excluir Run' button to delete the entire run."""
        assert "Excluir Run" in html_content, (
            "renderDesempenhoRuns must render an 'Excluir Run' button "
            "for each pipeline run group."
        )

    def test_bt2_doc_type_label_mapping(self, html_content):
        """renderDesempenhoRuns must map doc types to friendly labels (not raw enum names)."""
        # Must have a mapping from RELATORIO_DESEMPENHO_* to user-friendly label
        assert "desempenhoDocLabel" in html_content or "docTypeLabel" in html_content or "tipoLabel" in html_content, (
            "renderDesempenhoRuns must have a type-to-label mapping function "
            "(e.g., desempenhoDocLabel or docTypeLabel) for friendly doc type display."
        )

    def test_bt2_delete_run_calls_api(self, html_content):
        """The 'Excluir Run' button must call the DELETE /api/desempenho/run/ endpoint."""
        assert "deleteDesempenhoRun" in html_content or "/api/desempenho/run/" in html_content, (
            "The Excluir Run button must trigger a DELETE call to "
            "/api/desempenho/run/{run_id} via a deleteDesempenhoRun function."
        )


# ============================================================
# B-T3: Empty state + no-data disable logic
# ============================================================

class TestBT3EmptyStateNoData:
    """B-T3: When has_atividades=false, disable button. When runs=[] but has_atividades=true, show empty state."""

    def test_bt3_empty_state_with_generate_prompt(self, html_content):
        """When no reports exist but atividades exist, show empty state with active generate button."""
        # Must show a specific empty state with the new loadDesempenhoData flow
        assert "Nenhum relatório gerado" in html_content and "loadDesempenhoData" in html_content, (
            "loadDesempenhoData must show 'Nenhum relatório gerado' "
            "when runs array is empty but atividades exist."
        )

    def test_bt3_no_atividades_message(self, html_content):
        """When no atividades are graded, show explanatory disabled message."""
        assert "Nenhuma atividade corrigida" in html_content, (
            "loadDesempenhoData must show 'Nenhuma atividade corrigida' "
            "when has_atividades is false."
        )

    def test_bt3_has_atividades_flag_check(self, html_content):
        """Code must check has_atividades flag from API response."""
        assert "has_atividades" in html_content, (
            "loadDesempenhoData must check the 'has_atividades' flag "
            "from the API response to determine button state."
        )

    def test_bt3_button_disabled_when_no_atividades(self, html_content):
        """Generate button must be disabled when no atividades exist."""
        assert "disabled" in html_content and "has_atividades" in html_content, (
            "The 'Gerar Relatório' button must be disabled when "
            "has_atividades is false."
        )
