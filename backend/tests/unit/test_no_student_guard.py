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
    """Extract the body of a named JS function (first match).

    Handles both sync and async functions.
    """
    # Match both 'function name(...)' and 'async function name(...)'
    pattern = rf'(?:async\s+)?function\s+{name}\s*\([^)]*\)\s*\{{'
    match = re.search(pattern, src)
    if not match:
        return ''
    # Find the matching closing brace by counting braces
    start = match.end()
    depth = 1
    i = start
    while i < len(src) and depth > 0:
        if src[i] == '{':
            depth += 1
        elif src[i] == '}':
            depth -= 1
        i += 1
    return src[start:i - 1]


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


# ===========================================================================
# F1-T2: Guard on openModalUpload() for modo='aluno'
# ===========================================================================

NO_STUDENT_TOAST_MSG = 'Nenhum aluno na turma. Adicione alunos antes de enviar provas.'


class TestOpenModalUploadGuard:
    """Verify that openModalUpload() blocks when modo='aluno' and no students."""

    def test_guard_calls_hasStudentsInTurma(self):
        """openModalUpload must call hasStudentsInTurma() in its body."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUpload')
        assert 'hasStudentsInTurma' in body, (
            'openModalUpload must call hasStudentsInTurma()'
        )

    def test_guard_only_for_aluno_mode(self):
        """The guard must be conditional on modo === 'aluno' (not block base uploads)."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUpload')
        # The hasStudentsInTurma check must appear inside a modo === 'aluno' conditional
        # Find the position of hasStudentsInTurma and check it's inside an aluno check
        guard_pos = body.find('hasStudentsInTurma')
        assert guard_pos != -1, 'hasStudentsInTurma not found in openModalUpload'
        # The aluno mode check must come before the guard
        aluno_check = body.find("'aluno'")
        if aluno_check == -1:
            aluno_check = body.find('"aluno"')
        assert aluno_check != -1, 'modo aluno check not found in openModalUpload'
        assert aluno_check < guard_pos, (
            'The aluno mode check must come before the hasStudentsInTurma guard'
        )

    def test_guard_shows_warning_toast(self):
        """The guard must show a Portuguese warning toast."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUpload')
        assert NO_STUDENT_TOAST_MSG in body, (
            f'openModalUpload must show toast: "{NO_STUDENT_TOAST_MSG}"'
        )
        assert "'warning'" in body or '"warning"' in body, (
            'Toast must use warning type'
        )

    def test_guard_returns_early(self):
        """The guard must return early (before openModal) when no students."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUpload')
        guard_pos = body.find('hasStudentsInTurma')
        assert guard_pos != -1
        # There must be a 'return' after the guard check
        after_guard = body[guard_pos:]
        return_pos = after_guard.find('return')
        open_modal_pos = after_guard.find('openModal(')
        assert return_pos != -1, (
            'openModalUpload must have a return statement after the guard'
        )
        assert return_pos < open_modal_pos, (
            'The early return must come before openModal call'
        )


# ===========================================================================
# F1-T4: Guard on openModalPipelineCompleto() for both modes
# ===========================================================================

class TestOpenModalPipelineCompletoGuard:
    """Verify that openModalPipelineCompleto() blocks when no students (both modes)."""

    def test_guard_calls_hasStudentsInTurma(self):
        """openModalPipelineCompleto must call hasStudentsInTurma() in its body."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalPipelineCompleto')
        assert 'hasStudentsInTurma' in body, (
            'openModalPipelineCompleto must call hasStudentsInTurma()'
        )

    def test_guard_shows_warning_toast(self):
        """The guard must show a Portuguese warning toast."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalPipelineCompleto')
        assert NO_STUDENT_TOAST_MSG in body, (
            f'openModalPipelineCompleto must show toast: "{NO_STUDENT_TOAST_MSG}"'
        )
        assert "'warning'" in body or '"warning"' in body, (
            'Toast must use warning type'
        )

    def test_guard_returns_early(self):
        """The guard must return early (before openModal) when no students."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalPipelineCompleto')
        guard_pos = body.find('hasStudentsInTurma')
        assert guard_pos != -1, 'hasStudentsInTurma not found in openModalPipelineCompleto'
        after_guard = body[guard_pos:]
        return_pos = after_guard.find('return')
        open_modal_pos = after_guard.find('openModal(')
        assert return_pos != -1, (
            'openModalPipelineCompleto must have a return statement after the guard'
        )
        assert return_pos < open_modal_pos, (
            'The early return must come before openModal call'
        )

    def test_guard_is_unconditional(self):
        """The guard must fire before any mode-specific logic (blocks both aluno and turma)."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalPipelineCompleto')
        guard_pos = body.find('hasStudentsInTurma')
        assert guard_pos != -1, 'hasStudentsInTurma not found'
        # The guard must come before any pipeline-modo reference
        modo_ref = body.find('pipeline-modo')
        if modo_ref != -1:
            assert guard_pos < modo_ref, (
                'The hasStudentsInTurma guard must come before mode-specific logic'
            )


# ===========================================================================
# F1-T3: Guard on openModalUploadProvas()
# ===========================================================================

class TestOpenModalUploadProvasGuard:
    """Verify that openModalUploadProvas() blocks when no students."""

    def test_guard_calls_hasStudentsInTurma(self):
        """openModalUploadProvas must call hasStudentsInTurma() in its body."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUploadProvas')
        assert 'hasStudentsInTurma' in body, (
            'openModalUploadProvas must call hasStudentsInTurma()'
        )

    def test_guard_shows_warning_toast(self):
        """The guard must show a Portuguese warning toast."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUploadProvas')
        assert NO_STUDENT_TOAST_MSG in body, (
            f'openModalUploadProvas must show toast: "{NO_STUDENT_TOAST_MSG}"'
        )
        assert "'warning'" in body or '"warning"' in body, (
            'Toast must use warning type'
        )

    def test_guard_returns_early(self):
        """The guard must return early (before openModal) when no students."""
        src = _read_index_v2()
        body = _extract_function_body(src, 'openModalUploadProvas')
        guard_pos = body.find('hasStudentsInTurma')
        assert guard_pos != -1, 'hasStudentsInTurma not found in openModalUploadProvas'
        after_guard = body[guard_pos:]
        return_pos = after_guard.find('return')
        open_modal_pos = after_guard.find('openModal(')
        assert return_pos != -1, (
            'openModalUploadProvas must have a return statement after the guard'
        )
        assert return_pos < open_modal_pos, (
            'The early return must come before openModal call'
        )
