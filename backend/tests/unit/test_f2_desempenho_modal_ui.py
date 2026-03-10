"""
F2-T1 / F2-T2: Structural tests for the desempenho modal etapas a executar UI.

Verifies:
- F2-T1: Modal has an etapas section with a collapse/expand tree container
- F2-T2: JS function exists for toggling the per-student per-stage tree

No browser needed — pure file content checks against index_v2.html.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f2_desempenho_modal_ui.py -v
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
# F2-T1: Modal HTML shell — etapas section present
# ============================================================

class TestF2T1DesempenhoModalEtapasShell:
    """F2-T1: Desempenho modal must have an 'etapas a executar' section."""

    def test_etapas_section_container_exists(self, html_content):
        """The modal must have a container element for the etapas tree."""
        assert "desempenho-etapas-section" in html_content, (
            "index_v2.html must have id='desempenho-etapas-section' (or class) "
            "inside modal-desempenho-settings for the per-student per-stage tree."
        )

    def test_etapas_tree_container_exists(self, html_content):
        """The modal must have a container that holds the student/stage tree rows."""
        assert "desempenho-etapas-tree" in html_content, (
            "index_v2.html must have id='desempenho-etapas-tree' as the container "
            "that will be populated with per-student per-stage rows."
        )

    def test_etapas_section_label_exists(self, html_content):
        """The modal must have a readable label for the etapas section."""
        assert "Etapas a Executar" in html_content or "etapas a executar" in html_content.lower(), (
            "index_v2.html must contain 'Etapas a Executar' label "
            "inside the desempenho modal."
        )

    def test_etapas_section_inside_desempenho_modal(self, html_content):
        """The etapas section must appear after modal-desempenho-settings opening tag."""
        modal_start = html_content.find('id="modal-desempenho-settings"')
        modal_end = html_content.find('</div>', html_content.find('modal-footer', modal_start))
        assert modal_start != -1, "modal-desempenho-settings must exist"
        etapas_pos = html_content.find("desempenho-etapas-section", modal_start)
        assert etapas_pos != -1 and etapas_pos < modal_end + 500, (
            "desempenho-etapas-section must be inside the desempenho modal, "
            "not outside of it."
        )

    def test_collapse_toggle_element_exists(self, html_content):
        """The etapas section must have a collapse/expand toggle element."""
        assert "desempenho-etapas-toggle" in html_content, (
            "index_v2.html must have id='desempenho-etapas-toggle' "
            "(button or link) for expanding/collapsing the etapas tree."
        )


# ============================================================
# F2-T2: Collapse/expand JS function present
# ============================================================

class TestF2T2DesempenhoModalCollapseJS:
    """F2-T2: JS collapse/expand function for per-student per-stage tree."""

    def test_toggle_etapas_function_exists(self, html_content):
        """A JS function for toggling the etapas tree must exist."""
        assert "toggleDesempenhoEtapas" in html_content or "desempenhoEtapasToggle" in html_content, (
            "index_v2.html must define a JS function for toggling the desempenho "
            "etapas tree (e.g., toggleDesempenhoEtapas)."
        )

    def test_etapas_collapsed_by_default(self, html_content):
        """The etapas tree container must start collapsed (hidden by default)."""
        # Check that the tree div has a hidden/collapsed class or display:none
        assert 'desempenho-etapas-tree' in html_content, "tree container must exist"
        # Look for the tree element with a collapsed state indicator
        tree_idx = html_content.find('desempenho-etapas-tree')
        nearby = html_content[tree_idx:tree_idx + 200]
        has_hidden = (
            'display:none' in nearby or
            'display: none' in nearby or
            'collapsed' in nearby or
            'hidden' in nearby
        )
        assert has_hidden, (
            "desempenho-etapas-tree must start collapsed (display:none or 'collapsed' class). "
            "Users click the toggle to expand."
        )

    def test_render_etapas_student_row_function_exists(self, html_content):
        """A JS function must exist for rendering per-student stage rows."""
        assert "renderDesempenhoEtapasRow" in html_content or "renderEtapasDesempenhoAluno" in html_content, (
            "index_v2.html must define a function for rendering "
            "per-student per-stage checkboxes in the desempenho modal."
        )

    def test_stage_checkboxes_rendered_in_tree(self, html_content):
        """The JS must reference the 3 student pipeline stages (corrigir, analisar, relatorio)."""
        assert "corrigir" in html_content and "analisar" in html_content, (
            "The etapas tree JS must reference 'corrigir' and 'analisar' stages "
            "as selectable options for the per-student pipeline."
        )
