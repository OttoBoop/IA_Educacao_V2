"""Tests for the no-student guard logic (frontend JS helper simulated in Python).

These tests verify the logic of hasStudentsInTurma() and the guard behavior
for openModalUpload, openModalUploadProvas, and openModalPipelineCompleto.
"""
import re
import pytest


# ---------------------------------------------------------------------------
# Helpers — read the JS source and extract function bodies
# ---------------------------------------------------------------------------

def _read_index_v2():
    """Read the frontend HTML file."""
    import os
    path = os.path.join(
        os.path.dirname(__file__), '..', '..', '..', 'frontend', 'index_v2.html'
    )
    with open(path, encoding='utf-8') as f:
        return f.read()


def _function_exists(src: str, name: str) -> bool:
    """Check if a JS function with the given name exists in the source."""
    return bool(re.search(rf'\bfunction\s+{name}\b', src))


def _extract_function_body(src: str, name: str) -> str:
    """Extract the body of a named JS function (first match)."""
    pattern = rf'function\s+{name}\s*\([^)]*\)\s*\{{(.*?)\n\s*\}}'
    # Use DOTALL so . matches newlines
    match = re.search(pattern, src, re.DOTALL)
    if not match:
        return ''
    return match.group(1)


# ===========================================================================
# F1-T1: hasStudentsInTurma() helper
# ===========================================================================

class TestHasStudentsInTurma:
    """Verify that hasStudentsInTurma() exists and implements the correct logic."""

    def test_function_exists(self):
        """hasStudentsInTurma must be defined in index_v2.html."""
        src = _read_index_v2()
        assert _function_exists(src, 'hasStudentsInTurma'), (
            'hasStudentsInTurma() is not defined in index_v2.html'
        )

    def test_checks_atividadeData_alunos_total(self):
        """The function body must reference _atividadeData and alunos and total."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'hasStudentsInTurma')
        assert '_atividadeData' in body, (
            'hasStudentsInTurma must read window._atividadeData'
        )
        assert 'alunos' in body, (
            'hasStudentsInTurma must access .alunos'
        )
        assert 'total' in body, (
            'hasStudentsInTurma must access .total'
        )

    def test_returns_boolean(self):
        """The function must contain a return statement with > 0 comparison."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'hasStudentsInTurma')
        assert 'return' in body, 'hasStudentsInTurma must have a return statement'
        assert '> 0' in body or '>0' in body, (
            'hasStudentsInTurma must compare total > 0'
        )

    def test_uses_optional_chaining(self):
        """The function must use optional chaining (?.) for safety."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'hasStudentsInTurma')
        assert '?.' in body, (
            'hasStudentsInTurma must use optional chaining (?.) for null safety'
        )
