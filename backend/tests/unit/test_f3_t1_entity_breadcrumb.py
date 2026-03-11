"""
F3-T1: Unit tests — openDesempenhoSettings() must fetch entity names via
the breadcrumb API and the modal must expose a breadcrumb display element.

RED phase — these tests FAIL because:
1. openDesempenhoSettings() does NOT call the breadcrumb API today.
2. There is no breadcrumb display element inside the desempenho modal.

No browser needed — pure file content checks against index_v2.html.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f3_t1_entity_breadcrumb.py -v
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
# F3-T1-A: openDesempenhoSettings() calls the breadcrumb API
# ============================================================

class TestF3T1_OpenDesempenhoSettingsBreadcrumbCall:
    """openDesempenhoSettings() must fetch entity names from /navegacao/breadcrumb/."""

    def test_open_desempenho_settings_calls_breadcrumb_api(self, html_content):
        """openDesempenhoSettings() body must reference the breadcrumb API path."""
        fn_start = html_content.find("function openDesempenhoSettings")
        assert fn_start != -1, (
            "openDesempenhoSettings must be defined in index_v2.html"
        )
        # Grab up to 1000 chars of the function body to inspect
        fn_body = html_content[fn_start:fn_start + 1000]
        assert "/navegacao/breadcrumb/" in fn_body, (
            "openDesempenhoSettings() must call /navegacao/breadcrumb/{tipo}/{id} "
            "to fetch entity names. Currently the function does not reference this endpoint."
        )

    def test_open_desempenho_settings_updates_breadcrumb_element(self, html_content):
        """openDesempenhoSettings() must update a breadcrumb display element after fetching."""
        fn_start = html_content.find("function openDesempenhoSettings")
        assert fn_start != -1, "openDesempenhoSettings must be defined in index_v2.html"
        fn_body = html_content[fn_start:fn_start + 1000]
        assert "desempenho-breadcrumb" in fn_body, (
            "openDesempenhoSettings() must set the content of a 'desempenho-breadcrumb' "
            "element after the API call resolves. Currently it does not reference that element."
        )

    def test_breadcrumb_call_awaited_with_other_prefetch(self, html_content):
        """The breadcrumb fetch must be awaited alongside existing prefetch calls."""
        fn_start = html_content.find("function openDesempenhoSettings")
        assert fn_start != -1, "openDesempenhoSettings must be defined in index_v2.html"
        fn_body = html_content[fn_start:fn_start + 1000]
        # The existing function uses Promise.all() — breadcrumb call should join it
        assert "Promise.all" in fn_body, (
            "openDesempenhoSettings uses Promise.all for concurrent async calls. "
            "The breadcrumb fetch must be included in that Promise.all block."
        )
        assert "/navegacao/breadcrumb/" in fn_body, (
            "Breadcrumb API must be fetched inside the same Promise.all block."
        )


# ============================================================
# F3-T1-B: Modal HTML has a breadcrumb display element
# ============================================================

class TestF3T1_ModalBreadcrumbElement:
    """The desempenho modal header must contain a breadcrumb display element."""

    def test_breadcrumb_element_exists_in_html(self, html_content):
        """index_v2.html must define an element with id='desempenho-breadcrumb'."""
        assert "desempenho-breadcrumb" in html_content, (
            "index_v2.html must have an element with id='desempenho-breadcrumb' "
            "(or contain the string 'desempenho-breadcrumb') for displaying the "
            "entity path in the desempenho modal header. Currently this element is absent."
        )

    def test_breadcrumb_element_inside_desempenho_modal(self, html_content):
        """The breadcrumb element must appear inside the modal-desempenho-settings div."""
        modal_start = html_content.find('id="modal-desempenho-settings"')
        assert modal_start != -1, "modal-desempenho-settings must exist in index_v2.html"
        # Find the breadcrumb position relative to the modal open tag
        breadcrumb_pos = html_content.find("desempenho-breadcrumb", modal_start)
        assert breadcrumb_pos != -1, (
            "desempenho-breadcrumb must appear INSIDE the modal-desempenho-settings block, "
            "not outside it. Currently the element does not exist at all."
        )

    def test_breadcrumb_element_in_modal_header(self, html_content):
        """The breadcrumb element should appear near the modal header, before the modal body."""
        modal_start = html_content.find('id="modal-desempenho-settings"')
        assert modal_start != -1, "modal-desempenho-settings must exist"
        modal_body_start = html_content.find("modal-body", modal_start)
        assert modal_body_start != -1, "modal-body must exist inside the desempenho modal"
        breadcrumb_pos = html_content.find("desempenho-breadcrumb", modal_start)
        assert breadcrumb_pos != -1, "desempenho-breadcrumb element must exist"
        # Breadcrumb should be in the header area, i.e., before the modal-body section
        assert breadcrumb_pos < modal_body_start, (
            "desempenho-breadcrumb must appear in the modal header (before .modal-body), "
            "so the entity path is visible above the configuration controls."
        )


# ============================================================
# F3-T1-C: Breadcrumb text patterns for each level
# ============================================================

class TestF3T1_BreadcrumbLevelText:
    """JS must build the correct breadcrumb suffix text per desempenho level,
    inside a function that also references the desempenho-breadcrumb element."""

    def _find_breadcrumb_builder_body(self, html_content):
        """Return the JS region that builds the desempenho breadcrumb string.

        This must be near the openDesempenhoSettings function or a helper it calls.
        Returns an empty string if no breadcrumb builder exists yet.
        """
        # Look for a contiguous block of ~2000 chars after openDesempenhoSettings
        # that also mentions 'desempenho-breadcrumb' (the display element).
        fn_start = html_content.find("function openDesempenhoSettings")
        if fn_start == -1:
            return ""
        region = html_content[fn_start:fn_start + 3000]
        if "desempenho-breadcrumb" not in region:
            return ""  # breadcrumb builder not wired yet
        return region

    def test_tarefa_level_breadcrumb_text_in_builder(self, html_content):
        """The breadcrumb builder must emit 'Desempenho da tarefa' for tarefa level."""
        region = self._find_breadcrumb_builder_body(html_content)
        assert "Desempenho da tarefa" in region or "desempenho da tarefa" in region.lower(), (
            "The breadcrumb builder (near openDesempenhoSettings) must reference the text "
            "'Desempenho da tarefa' for the tarefa breadcrumb tail. "
            "Currently the builder does not exist or does not contain this string."
        )

    def test_turma_level_breadcrumb_text_in_builder(self, html_content):
        """The breadcrumb builder must emit 'Desempenho da turma' for turma level."""
        region = self._find_breadcrumb_builder_body(html_content)
        assert "Desempenho da turma" in region or "desempenho da turma" in region.lower(), (
            "The breadcrumb builder (near openDesempenhoSettings) must reference the text "
            "'Desempenho da turma' for the turma breadcrumb tail. "
            "Currently the builder does not exist or does not contain this string."
        )

    def test_materia_level_breadcrumb_text_in_builder(self, html_content):
        """The breadcrumb builder must emit 'Desempenho da matéria' for materia level."""
        region = self._find_breadcrumb_builder_body(html_content)
        assert "Desempenho da matéria" in region or "desempenho da materia" in region.lower(), (
            "The breadcrumb builder (near openDesempenhoSettings) must reference the text "
            "'Desempenho da matéria' for the materia breadcrumb tail. "
            "Currently the builder does not exist or does not contain this string."
        )
