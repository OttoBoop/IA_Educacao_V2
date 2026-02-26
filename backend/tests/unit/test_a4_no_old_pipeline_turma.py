"""
A4: Automated grep test — assert zero "pipeline-turma" strings remain in source files.

This test FAILS until A2 (rename task) is complete.

Checks:
  - "pipeline_turma"  (Python identifier form) in all backend .py files
  - "Pipeline Turma"  (UI label form) in all source files
  - "pipeline-turma"  (URL/ID form) in frontend files and backend test files
    Note: routes_prompts.py is excluded from the hyphen check because A3 intentionally
    adds ONE backward-compat redirect route at /api/executar/pipeline-turma — that single
    occurrence is verified separately in test_a3_redirect_pipeline_turma.py.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_a4_no_old_pipeline_turma.py -v
"""

from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent.parent  # IA_Educacao_V2/backend
FRONTEND_ROOT = BACKEND_ROOT.parent / "frontend"    # IA_Educacao_V2/frontend

EXCLUDED_SUBDIRS = {"investor_journey_reports", "__pycache__", ".pytest_cache"}

# Exclude the test files that define the patterns being checked (self-referential)
EXCLUDED_FILES = {
    "test_a4_no_old_pipeline_turma.py",  # this file — contains patterns in docstrings
    "test_a3_redirect_pipeline_turma.py",  # companion — contains "pipeline_turma" in function names
}


def _find_in_file(filepath: Path, pattern: str) -> list:
    """Return list of (line_number, line) for lines containing pattern."""
    matches = []
    try:
        for lineno, line in enumerate(filepath.read_text(encoding="utf-8").splitlines(), start=1):
            if pattern in line:
                matches.append((lineno, line.strip()))
    except Exception:
        pass
    return matches


def _collect_files(root: Path, suffixes=(".py", ".html")) -> list:
    """Yield all files under root with given suffixes, excluding EXCLUDED_SUBDIRS/FILES."""
    result = []
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix not in suffixes:
            continue
        if any(excl in f.parts for excl in EXCLUDED_SUBDIRS):
            continue
        if f.name in EXCLUDED_FILES:
            continue
        result.append(f)
    return result


# ============================================================
# Test: no pipeline_turma (Python identifier) anywhere in backend
# ============================================================

def test_no_pipeline_turma_underscore_in_backend():
    """Assert zero 'pipeline_turma' Python identifier occurrences in backend .py files.

    After A2, all Python function names (executar_pipeline_turma, _executar_pipeline_turma_background)
    and task_type strings ('pipeline_turma') must be renamed.
    """
    matches = {}
    for filepath in _collect_files(BACKEND_ROOT, suffixes=(".py",)):
        found = _find_in_file(filepath, "pipeline_turma")
        if found:
            matches[str(filepath)] = found

    assert not matches, (
        f"Found 'pipeline_turma' in {len(matches)} file(s). Run A2 to rename:\n" +
        "\n".join(
            f"  {f}:{ln}: {line}"
            for f, lines in matches.items()
            for ln, line in lines[:5]
        )
    )


# ============================================================
# Test: no "Pipeline Turma" UI label in any source file
# ============================================================

def test_no_pipeline_turma_label_in_source():
    """Assert zero 'Pipeline Turma' UI label occurrences.

    After A2, buttons, tooltips, help text must read 'Pipeline Todos os Alunos'.
    """
    all_matches = {}
    for filepath in _collect_files(BACKEND_ROOT) + _collect_files(FRONTEND_ROOT):
        found = _find_in_file(filepath, "Pipeline Turma")
        if found:
            all_matches[str(filepath)] = found

    assert not all_matches, (
        f"Found 'Pipeline Turma' in {len(all_matches)} file(s). Run A2 to update labels:\n" +
        "\n".join(
            f"  {f}:{ln}: {line}"
            for f, lines in all_matches.items()
            for ln, line in lines[:5]
        )
    )


# ============================================================
# Test: no pipeline-turma (URL/ID form) in frontend files
# ============================================================

def test_no_pipeline_turma_hyphen_in_frontend():
    """Assert zero 'pipeline-turma' occurrences in frontend source files.

    index_v2.html and capture_tutorial_completo.py must use 'pipeline-todos-os-alunos'
    for all HTML IDs, JS strings, and API calls.
    """
    frontend_files = [
        FRONTEND_ROOT / "index_v2.html",
        FRONTEND_ROOT / "capture_tutorial_completo.py",
    ]
    all_matches = {}
    for filepath in frontend_files:
        if filepath.exists():
            found = _find_in_file(filepath, "pipeline-turma")
            if found:
                all_matches[str(filepath)] = found

    assert not all_matches, (
        f"Found 'pipeline-turma' in {len(all_matches)} frontend file(s). Run A2 to rename:\n" +
        "\n".join(
            f"  {f}:{ln}: {line}"
            for f, lines in all_matches.items()
            for ln, line in lines[:10]
        )
    )


# ============================================================
# Test: no pipeline-turma (URL/ID form) in backend TEST files
# ============================================================

def test_no_pipeline_turma_hyphen_in_tests():
    """Assert zero 'pipeline-turma' occurrences in backend test files.

    Test docstrings and assertions must use the new function names.
    """
    tests_dir = BACKEND_ROOT / "tests"
    all_matches = {}
    for filepath in _collect_files(tests_dir, suffixes=(".py",)):
        found = _find_in_file(filepath, "pipeline-turma")
        if found:
            all_matches[str(filepath)] = found

    assert not all_matches, (
        f"Found 'pipeline-turma' in {len(all_matches)} test file(s). Run A2 to update:\n" +
        "\n".join(
            f"  {f}:{ln}: {line}"
            for f, lines in all_matches.items()
            for ln, line in lines[:5]
        )
    )
