"""
Frontend structure tests for F8-T1 + F8-T2: verify that index_v2.html contains
the required HTML elements and JS functions for the search/filter bar.

F8-T1: The atividade document view must have a search/filter bar above
       the document list with text search, type filter, and student filter.
F8-T2: JS: implement client-side filtering logic that filters the document
       list by display_name substring, TipoDocumento, and student.

These are structural RED/GREEN tests. Runtime UI verification is done via
journey agent in Phase 5 (UX Validation).

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F8-T1, F8-T2)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import re
import pytest
from pathlib import Path


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def html_content():
    """Read the current index_v2.html content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


# ============================================================
# F8-T1: Search/filter bar HTML in atividade view
# ============================================================

class TestSearchFilterBar:
    """
    F8-T1: The atividade document view must have a search/filter bar
    with text search input, type dropdown, and student dropdown.
    The bar is rendered inside showAtividade() output.
    """

    def test_atividade_view_has_filter_bar_container(self, html_content):
        """
        showAtividade() must render a filter bar container with
        id="doc-filter-bar" in its HTML output.
        """
        func_start = html_content.find("async function showAtividade(")
        assert func_start != -1, "showAtividade function not found"
        func_body = html_content[func_start:func_start + 5000]

        assert "doc-filter-bar" in func_body, (
            "showAtividade() must render a filter bar with id='doc-filter-bar'. "
            "This container holds the search input and filter dropdowns."
        )

    def test_filter_bar_has_text_search_input(self, html_content):
        """
        The filter bar must contain a text input for searching documents
        by display_name (id="filter-doc-search").
        """
        assert 'id="filter-doc-search"' in html_content, (
            "Filter bar must contain <input id='filter-doc-search'>. "
            "This text input filters documents by display_name substring."
        )

    def test_filter_bar_has_tipo_dropdown(self, html_content):
        """
        The filter bar must contain a select dropdown for filtering by
        document type (id="filter-doc-tipo").
        """
        assert 'id="filter-doc-tipo"' in html_content, (
            "Filter bar must contain <select id='filter-doc-tipo'>. "
            "This dropdown filters documents by TipoDocumento."
        )

    def test_filter_bar_has_aluno_dropdown(self, html_content):
        """
        The filter bar must contain a select dropdown for filtering by
        student (id="filter-doc-aluno").
        """
        assert 'id="filter-doc-aluno"' in html_content, (
            "Filter bar must contain <select id='filter-doc-aluno'>. "
            "This dropdown filters documents by student name."
        )

    def test_search_input_has_placeholder(self, html_content):
        """
        The text search input must have a placeholder text indicating
        its purpose (e.g., "Buscar por nome...").
        """
        # Find the filter-doc-search input tag
        pattern = r'<input[^>]*id="filter-doc-search"[^>]*>'
        match = re.search(pattern, html_content)
        assert match, "Could not find <input id='filter-doc-search'> in HTML."
        input_tag = match.group(0)

        assert 'placeholder=' in input_tag, (
            f"Search input must have a placeholder attribute. Got: {input_tag}"
        )


# ============================================================
# F8-T2: Client-side filtering logic
# ============================================================

class TestDocumentFilteringLogic:
    """
    F8-T2: JS must implement client-side filtering that filters the
    document list by display_name substring, TipoDocumento dropdown,
    and student dropdown. Filters are client-side (no API call).
    """

    def test_filter_function_exists(self, html_content):
        """
        There must be a JS function that applies document filters.
        Named something like applyDocFilters(), filterDocuments(), etc.
        """
        has_filter_func = re.search(
            r'function\s+\w*[Ff]ilter\w*[Dd]oc\w*\s*\(',
            html_content
        ) or re.search(
            r'function\s+applyDocFilters\s*\(',
            html_content
        ) or re.search(
            r'function\s+\w*[Dd]oc\w*[Ff]ilter\w*\s*\(',
            html_content
        )

        assert has_filter_func, (
            "There must be a JS function for document filtering (e.g., "
            "applyDocFilters(), filterDocuments(), filterDocList()). "
            "This function reads the 3 filter inputs and shows/hides docs."
        )

    def test_filter_function_reads_search_input(self, html_content):
        """
        The filter function must read the text search value from
        filter-doc-search to filter by display_name substring.
        """
        # Find any filter-related function that references filter-doc-search
        filter_funcs = re.finditer(
            r'function\s+(\w*[Ff]ilter\w*[Dd]oc\w*|\w*[Dd]oc\w*[Ff]ilter\w*|applyDocFilters)\s*\([^)]*\)\s*\{',
            html_content
        )
        found_search_ref = False
        for match in filter_funcs:
            func_start = match.start()
            func_body = html_content[func_start:func_start + 3000]
            if 'filter-doc-search' in func_body:
                found_search_ref = True
                break

        assert found_search_ref, (
            "The filter function must read from 'filter-doc-search' input "
            "to filter documents by display_name substring match."
        )

    def test_filter_function_reads_tipo_dropdown(self, html_content):
        """
        The filter function must read the tipo dropdown value from
        filter-doc-tipo to filter by document type.
        """
        filter_funcs = re.finditer(
            r'function\s+(\w*[Ff]ilter\w*[Dd]oc\w*|\w*[Dd]oc\w*[Ff]ilter\w*|applyDocFilters)\s*\([^)]*\)\s*\{',
            html_content
        )
        found_tipo_ref = False
        for match in filter_funcs:
            func_start = match.start()
            func_body = html_content[func_start:func_start + 3000]
            if 'filter-doc-tipo' in func_body:
                found_tipo_ref = True
                break

        assert found_tipo_ref, (
            "The filter function must read from 'filter-doc-tipo' dropdown "
            "to filter documents by TipoDocumento."
        )

    def test_filter_function_reads_aluno_dropdown(self, html_content):
        """
        The filter function must read the aluno dropdown value from
        filter-doc-aluno to filter by student.
        """
        filter_funcs = re.finditer(
            r'function\s+(\w*[Ff]ilter\w*[Dd]oc\w*|\w*[Dd]oc\w*[Ff]ilter\w*|applyDocFilters)\s*\([^)]*\)\s*\{',
            html_content
        )
        found_aluno_ref = False
        for match in filter_funcs:
            func_start = match.start()
            func_body = html_content[func_start:func_start + 3000]
            if 'filter-doc-aluno' in func_body:
                found_aluno_ref = True
                break

        assert found_aluno_ref, (
            "The filter function must read from 'filter-doc-aluno' dropdown "
            "to filter documents by student."
        )

    def test_filter_inputs_have_event_listeners(self, html_content):
        """
        All 3 filter inputs must have event listeners wired so the filter
        function is called when the user types or selects.
        """
        # Check for addEventListener or onchange/oninput wiring for the filter inputs
        has_search_listener = (
            re.search(r'filter-doc-search[^;]*\.addEventListener\s*\(', html_content) or
            re.search(r'filter-doc-search[^;]*\.oninput\s*=', html_content) or
            re.search(r'filter-doc-search[^;]*\.onkeyup\s*=', html_content) or
            re.search(r'id="filter-doc-search"[^>]*oninput=', html_content)
        )
        has_tipo_listener = (
            re.search(r'filter-doc-tipo[^;]*\.addEventListener\s*\(', html_content) or
            re.search(r'filter-doc-tipo[^;]*\.onchange\s*=', html_content) or
            re.search(r'id="filter-doc-tipo"[^>]*onchange=', html_content)
        )
        has_aluno_listener = (
            re.search(r'filter-doc-aluno[^;]*\.addEventListener\s*\(', html_content) or
            re.search(r'filter-doc-aluno[^;]*\.onchange\s*=', html_content) or
            re.search(r'id="filter-doc-aluno"[^>]*onchange=', html_content)
        )

        assert has_search_listener, (
            "filter-doc-search must have an input/keyup event listener "
            "to trigger filtering as the user types."
        )
        assert has_tipo_listener, (
            "filter-doc-tipo must have a change event listener "
            "to trigger filtering when the type is selected."
        )
        assert has_aluno_listener, (
            "filter-doc-aluno must have a change event listener "
            "to trigger filtering when a student is selected."
        )

    def test_tipo_dropdown_populated_from_data(self, html_content):
        """
        After showAtividade() loads data, the tipo dropdown must be
        populated with document type options from TIPO_LABELS or the
        loaded data. Look for code that populates filter-doc-tipo options.
        """
        # Look for code that adds options to filter-doc-tipo
        has_populate = (
            re.search(r'filter-doc-tipo[^;]*\.innerHTML\s*[+=]', html_content) or
            re.search(r'filter-doc-tipo[^;]*\.appendChild', html_content) or
            re.search(r'filter-doc-tipo[^;]*\.add\s*\(', html_content) or
            re.search(r'filter-doc-tipo[^;]*\.insertAdjacentHTML', html_content) or
            re.search(r'TIPO_LABELS[^;]*filter-doc-tipo', html_content) or
            re.search(r'filter-doc-tipo[^;]*TIPO_LABELS', html_content)
        )

        assert has_populate, (
            "The tipo dropdown (filter-doc-tipo) must be dynamically populated "
            "with document type options after data loads. Use TIPO_LABELS to "
            "generate option elements."
        )

    def test_aluno_dropdown_populated_from_data(self, html_content):
        """
        After showAtividade() loads data, the aluno dropdown must be
        populated with student options from the loaded atividade data.
        """
        has_populate = (
            re.search(r'filter-doc-aluno[^;]*\.innerHTML\s*[+=]', html_content) or
            re.search(r'filter-doc-aluno[^;]*\.appendChild', html_content) or
            re.search(r'filter-doc-aluno[^;]*\.add\s*\(', html_content) or
            re.search(r'filter-doc-aluno[^;]*\.insertAdjacentHTML', html_content) or
            re.search(r'alunos[^;]*filter-doc-aluno', html_content) or
            re.search(r'filter-doc-aluno[^;]*aluno', html_content)
        )

        assert has_populate, (
            "The aluno dropdown (filter-doc-aluno) must be dynamically populated "
            "with student options from the loaded atividade data."
        )
