"""
Frontend structure tests for F8-T1: verify that index_v2.html contains
the required HTML elements for the search/filter bar in the atividade view.

F8-T1: The atividade document view must have a search/filter bar above
       the document list with text search, type filter, and student filter.

These are structural RED/GREEN tests. Runtime UI verification is done via
journey agent in Phase 5 (UX Validation).

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F8-T1)
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
