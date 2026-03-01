"""
Tests for JS functions in index_v2.html.

F1-T3: buildDisplayName() JS mirror function matches Python build_display_name()
F1-T4: showToast() also fires console.log
"""

import re
import json
import pytest
from pathlib import Path


# Path to the frontend HTML file
INDEX_V2_PATH = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_source():
    """Load index_v2.html source code."""
    assert INDEX_V2_PATH.exists(), f"index_v2.html not found at {INDEX_V2_PATH}"
    return INDEX_V2_PATH.read_text(encoding="utf-8")


# ============================================================
# F1-T3: buildDisplayName() JS mirror function tests
# ============================================================

class TestBuildDisplayNameJSExists:
    """Verify the JS buildDisplayName function exists in index_v2.html."""

    def test_function_defined(self, html_source):
        """buildDisplayName function is defined in index_v2.html."""
        assert "function buildDisplayName" in html_source or \
               "buildDisplayName = function" in html_source or \
               "buildDisplayName = (" in html_source, \
            "buildDisplayName function not found in index_v2.html"

    def test_accepts_tipo_aluno_materia_turma(self, html_source):
        """Function signature includes tipo, alunoNome, materiaNome, turmaNome params."""
        # Match: function buildDisplayName(tipo, alunoNome, materiaNome, turmaNome)
        pattern = r'function\s+buildDisplayName\s*\(\s*tipo\s*,\s*alunoNome\s*,\s*materiaNome\s*,\s*turmaNome\s*\)'
        assert re.search(pattern, html_source), \
            "buildDisplayName must accept (tipo, alunoNome, materiaNome, turmaNome)"


class TestBuildDisplayNameJSTipoLabels:
    """Verify the JS tipo label mapping matches Python _TIPO_LABELS."""

    def _get_python_labels(self):
        """Get the Python _TIPO_LABELS dict from storage.py."""
        from storage import _TIPO_LABELS
        return _TIPO_LABELS

    def _extract_js_labels(self, html_source):
        """Extract the JS TIPO_LABELS object from the HTML source.

        Looks for a pattern like:
            const TIPO_LABELS = { ... };
        or similar object definition.
        """
        # Match: const TIPO_LABELS = { 'key': 'value', ... }; or TIPO_LABELS object
        pattern = r'(?:const|let|var)\s+TIPO_LABELS\s*=\s*\{([^}]+)\}'
        match = re.search(pattern, html_source)
        if not match:
            return None

        # Parse key-value pairs from the JS object literal
        obj_body = match.group(1)
        labels = {}
        # Match patterns like: 'key': 'value' or "key": "value"
        pair_pattern = r"""['"](\w+)['"]\s*:\s*['"]([^'"]+)['"]"""
        for m in re.finditer(pair_pattern, obj_body):
            labels[m.group(1)] = m.group(2)
        return labels

    def test_js_tipo_labels_object_exists(self, html_source):
        """A TIPO_LABELS constant is defined in index_v2.html."""
        assert "TIPO_LABELS" in html_source, \
            "TIPO_LABELS object not found in index_v2.html"

    def test_all_python_labels_present_in_js(self, html_source):
        """Every key in Python _TIPO_LABELS has a matching key in JS TIPO_LABELS."""
        python_labels = self._get_python_labels()
        js_labels = self._extract_js_labels(html_source)
        assert js_labels is not None, "Could not parse TIPO_LABELS from JS"

        missing = set(python_labels.keys()) - set(js_labels.keys())
        assert not missing, f"JS TIPO_LABELS missing keys: {missing}"

    def test_label_values_match_python(self, html_source):
        """Every value in JS TIPO_LABELS matches the corresponding Python value."""
        python_labels = self._get_python_labels()
        js_labels = self._extract_js_labels(html_source)
        assert js_labels is not None, "Could not parse TIPO_LABELS from JS"

        mismatches = {}
        for key, py_value in python_labels.items():
            js_value = js_labels.get(key)
            if js_value != py_value:
                mismatches[key] = {"python": py_value, "js": js_value}

        assert not mismatches, f"Label mismatches between Python and JS: {mismatches}"


class TestBuildDisplayNameJSLogic:
    """Verify the JS function logic matches Python build_display_name behavior."""

    def test_uses_separator_dash(self, html_source):
        """Function joins parts with ' - ' separator (matching Python)."""
        # Look for the join pattern in the function body
        assert "' - '" in html_source or '" - "' in html_source or \
               "` - `" in html_source, \
            "buildDisplayName must use ' - ' as separator"

    def test_omits_falsy_parts(self, html_source):
        """Function skips null/empty parts (matching Python behavior)."""
        # The function should filter out falsy values before joining
        # Look for a filter or conditional check pattern near buildDisplayName
        func_pattern = r'function\s+buildDisplayName\s*\([^)]*\)\s*\{([\s\S]*?)\n\s{8}\}'
        match = re.search(func_pattern, html_source)
        assert match, "Could not extract buildDisplayName function body"

        body = match.group(1)
        # Should have some kind of filter for null/empty values
        assert "filter" in body or ("if" in body and ("null" in body or "!=" in body or "!" in body)), \
            "buildDisplayName must filter out null/empty parts"


# ============================================================
# F1-T4: showToast() + console.log tests
# ============================================================

class TestShowToastConsoleLog:
    """Verify showToast fires console.log in addition to UI toast."""

    def _extract_show_toast_body(self, html_source):
        """Extract the showToast function body from HTML source."""
        pattern = r'function\s+showToast\s*\([^)]*\)\s*\{([\s\S]*?)\n\s{8}\}'
        match = re.search(pattern, html_source)
        if match:
            return match.group(1)
        return None

    def test_show_toast_contains_console_log(self, html_source):
        """showToast function body contains a console.log call."""
        body = self._extract_show_toast_body(html_source)
        assert body is not None, "Could not extract showToast function body"
        assert "console.log" in body, \
            "showToast must fire console.log with the toast message"

    def test_console_log_includes_message(self, html_source):
        """console.log call in showToast includes the message parameter."""
        body = self._extract_show_toast_body(html_source)
        assert body is not None, "Could not extract showToast function body"
        # The console.log should reference the 'message' parameter
        log_pattern = r'console\.log\([^)]*message[^)]*\)'
        assert re.search(log_pattern, body), \
            "console.log in showToast must include the message parameter"

    def test_console_log_includes_type(self, html_source):
        """console.log call in showToast includes the type parameter."""
        body = self._extract_show_toast_body(html_source)
        assert body is not None, "Could not extract showToast function body"
        # The console.log should reference the 'type' parameter
        log_pattern = r'console\.log\([^)]*type[^)]*\)'
        assert re.search(log_pattern, body), \
            "console.log in showToast must include the type parameter"
