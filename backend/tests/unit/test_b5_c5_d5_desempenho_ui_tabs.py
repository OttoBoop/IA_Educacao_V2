"""
B5/C5/D5: Structural tests for the Relatório de Desempenho UI tabs in index_v2.html.

Verifies the frontend contains the required HTML and JS for the three
desempenho tabs: atividade view (B5), turma view (C5), matéria view (D5).

No browser needed — pure file content checks.

RED Phase: These tests FAIL because the UI tabs do not exist yet.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_b5_c5_d5_desempenho_ui_tabs.py -v
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
# B5 — "Desempenho da Turma" tab in atividade view
# ============================================================

class TestB5DesempenhoTarefaTab:
    """B5: Atividade view must have a 'Desempenho da Turma' tab with run button + doc viewer."""

    def test_b5_tab_label_exists(self, html_content):
        """The 'Desempenho da Turma' tab text must appear in the HTML."""
        assert "Desempenho da Turma" in html_content, (
            "index_v2.html must contain 'Desempenho da Turma' tab label "
            "in the atividade view."
        )

    def test_b5_run_button_calls_desempenho_tarefa_api(self, html_content):
        """A button must trigger the pipeline-desempenho-tarefa endpoint."""
        assert "pipeline-desempenho-tarefa" in html_content, (
            "index_v2.html must reference 'pipeline-desempenho-tarefa' endpoint "
            "for the run button in the atividade desempenho tab."
        )

    def test_b5_tab_switch_function_exists(self, html_content):
        """A JS function must handle switching to the desempenho tab in atividade view."""
        assert "showAtividadeTab" in html_content, (
            "index_v2.html must define a 'showAtividadeTab' function "
            "to handle tab switching in the atividade view."
        )

    def test_b5_desempenho_tarefa_content_container(self, html_content):
        """A container for the desempenho tarefa tab content must exist."""
        assert "atividade-desempenho-content" in html_content, (
            "index_v2.html must have an element with id 'atividade-desempenho-content' "
            "to hold the desempenho tarefa tab content."
        )


# ============================================================
# C5 — "Relatório de Desempenho" tab in turma view
# ============================================================

class TestC5DesempenhoTurmaTab:
    """C5: Turma view must have a 'Relatório de Desempenho' tab with run button + doc viewer."""

    def test_c5_tab_label_in_turma_tabs(self, html_content):
        """The turma tabs must include 'Desempenho' as a third tab."""
        # The turma view already has 'Atividades' and 'Alunos' tabs.
        # A third 'Desempenho' tab must be added.
        assert "showTurmaTab('desempenho'" in html_content, (
            "index_v2.html must add a 'desempenho' tab option to showTurmaTab "
            "in the turma view tabs."
        )

    def test_c5_run_button_calls_desempenho_turma_api(self, html_content):
        """A button must trigger the pipeline-desempenho-turma endpoint."""
        assert "pipeline-desempenho-turma" in html_content, (
            "index_v2.html must reference 'pipeline-desempenho-turma' endpoint "
            "for the run button in the turma desempenho tab."
        )

    def test_c5_turma_desempenho_content_section(self, html_content):
        """The turma tab handler must render desempenho content."""
        assert "tab === 'desempenho'" in html_content, (
            "showTurmaTab must handle the 'desempenho' case to render "
            "the desempenho turma content."
        )


# ============================================================
# D5 — "Relatório de Desempenho" tab in matéria view
# ============================================================

class TestD5DesempenhoMateriaTab:
    """D5: Matéria view must have a 'Relatório de Desempenho' tab with run button + doc viewer."""

    def test_d5_materia_has_tabs(self, html_content):
        """The matéria view must have a tab navigation (currently has none)."""
        assert "showMateriaTab" in html_content, (
            "index_v2.html must define a 'showMateriaTab' function "
            "for tab navigation in the matéria view."
        )

    def test_d5_run_button_calls_desempenho_materia_api(self, html_content):
        """A button must trigger the pipeline-desempenho-materia endpoint."""
        assert "pipeline-desempenho-materia" in html_content, (
            "index_v2.html must reference 'pipeline-desempenho-materia' endpoint "
            "for the run button in the matéria desempenho tab."
        )

    def test_d5_materia_desempenho_content_container(self, html_content):
        """A container for the desempenho matéria tab content must exist."""
        assert "materia-desempenho-content" in html_content, (
            "index_v2.html must have an element with id 'materia-desempenho-content' "
            "to hold the desempenho matéria tab content."
        )


# ============================================================
# Shared: Document viewer for desempenho reports
# ============================================================

class TestDesempenhoDocViewer:
    """All three desempenho tabs must support viewing the generated report."""

    def test_desempenho_doc_type_in_labels(self, html_content):
        """The document type labels must include desempenho report types."""
        assert "relatorio_desempenho" in html_content.lower() or "RELATORIO_DESEMPENHO" in html_content, (
            "index_v2.html must reference relatorio_desempenho document type "
            "for rendering the generated reports."
        )

    def test_executar_desempenho_function_exists(self, html_content):
        """A JS function to execute desempenho pipelines must exist."""
        assert "executarDesempenho" in html_content, (
            "index_v2.html must define an 'executarDesempenho' function "
            "that handles running the desempenho pipeline from the UI."
        )
