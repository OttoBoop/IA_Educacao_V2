"""
Structural tests for NOVO CR branding in backend miscellaneous files.

D-T1: Backend .py header docstrings must say 'NOVO CR' (not 'PROVA AI').
D-T2: CLI output strings in test_data_generator.py and test_runner.py.
D-T3: start.sh branding strings.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_rebrand_backend_misc.py -v
"""

from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent.parent
PROJECT_DIR = BACKEND_DIR.parent  # IA_Educacao_V2/

# ── D-T1: Backend .py header docstrings ──────────────────────

# All backend .py files (excluding tests/) with "PROVA AI" in header docstring
HEADER_FILES = [
    BACKEND_DIR / "anexos.py",
    BACKEND_DIR / "chat_service.py",
    BACKEND_DIR / "document_generators.py",
    BACKEND_DIR / "executor.py",
    BACKEND_DIR / "logging_config.py",
    BACKEND_DIR / "main_v2.py",
    BACKEND_DIR / "model_catalog.py",
    BACKEND_DIR / "models.py",
    BACKEND_DIR / "pipeline_validation.py",
    BACKEND_DIR / "pipeline_validation_min.py",
    BACKEND_DIR / "prompts.py",
    BACKEND_DIR / "routes_chat.py",
    BACKEND_DIR / "routes_extras.py",
    BACKEND_DIR / "routes_pipeline.py",
    BACKEND_DIR / "routes_prompts.py",
    BACKEND_DIR / "routes_resultados.py",
    BACKEND_DIR / "routes_tasks.py",
    BACKEND_DIR / "storage.py",
    BACKEND_DIR / "test_runner.py",
    BACKEND_DIR / "visualizador.py",
]


def _read(path: Path) -> str:
    assert path.exists(), f"File not found: {path}"
    return path.read_text(encoding="utf-8")


class TestBackendHeaderDocstrings:
    """D-T1: All backend .py file headers must say 'NOVO CR'."""

    @pytest.mark.parametrize("filepath", HEADER_FILES, ids=lambda p: p.name)
    def test_header_has_novo_cr(self, filepath):
        """Header docstring should say 'NOVO CR'."""
        content = _read(filepath)
        header = content.split('"""')[1]  # First docstring
        assert "NOVO CR" in header

    @pytest.mark.parametrize("filepath", HEADER_FILES, ids=lambda p: p.name)
    def test_header_no_old_prova_ai(self, filepath):
        """Header docstring must not say 'PROVA AI'."""
        content = _read(filepath)
        header = content.split('"""')[1]
        assert "PROVA AI" not in header


# ── D-T2: CLI output strings ────────────────────────────────

TEST_DATA_GEN = BACKEND_DIR / "test_data_generator.py"
TEST_RUNNER = BACKEND_DIR / "test_runner.py"


class TestDataGeneratorCLIStrings:
    """D-T2: test_data_generator.py CLI strings must say 'NOVO CR'."""

    def test_module_description_novo_cr(self):
        """Module description (line ~6) should reference 'NOVO CR'."""
        content = _read(TEST_DATA_GEN)
        assert "sistema NOVO CR" in content or "NOVO CR" in content.split('"""')[1]

    def test_module_description_no_old(self):
        """Module description must not reference 'Prova AI'."""
        content = _read(TEST_DATA_GEN)
        first_docstring = content.split('"""')[1]
        assert "Prova AI" not in first_docstring

    def test_class_docstring_novo_cr(self):
        """TestDataGenerator class docstring should say 'NOVO CR'."""
        content = _read(TEST_DATA_GEN)
        assert "NOVO CR" in content.split('class TestDataGenerator')[1].split('"""')[1]

    def test_class_docstring_no_old(self):
        """TestDataGenerator class docstring must not say 'Prova AI'."""
        content = _read(TEST_DATA_GEN)
        class_doc = content.split('class TestDataGenerator')[1].split('"""')[1]
        assert "Prova AI" not in class_doc

    def test_print_banner_novo_cr(self):
        """Print banner should say 'NOVO CR'."""
        content = _read(TEST_DATA_GEN)
        assert "GERADOR DE DADOS DE TESTE - NOVO CR" in content

    def test_print_banner_no_old(self):
        """Print banner must not say 'PROVA AI'."""
        content = _read(TEST_DATA_GEN)
        assert "GERADOR DE DADOS DE TESTE - PROVA AI" not in content

    def test_argparse_description_novo_cr(self):
        """Argparse description should say 'NOVO CR'."""
        content = _read(TEST_DATA_GEN)
        assert "NOVO CR" in content.split("argparse.ArgumentParser")[1].split(")")[0]

    def test_argparse_description_no_old(self):
        """Argparse description must not say 'Prova AI'."""
        content = _read(TEST_DATA_GEN)
        argparse_call = content.split("argparse.ArgumentParser")[1].split(")")[0]
        assert "Prova AI" not in argparse_call


class TestRunnerCLIStrings:
    """D-T2: test_runner.py CLI strings must say 'NOVO CR'."""

    def test_header_novo_cr(self):
        """Module header should say 'NOVO CR'."""
        content = _read(TEST_RUNNER)
        header = content.split('"""')[1]
        assert "NOVO CR" in header

    def test_header_no_old(self):
        """Module header must not say 'PROVA AI'."""
        content = _read(TEST_RUNNER)
        header = content.split('"""')[1]
        assert "PROVA AI" not in header

    def test_argparse_description_novo_cr(self):
        """Argparse description should say 'NOVO CR'."""
        content = _read(TEST_RUNNER)
        assert "NOVO CR - Executor de Testes" in content

    def test_argparse_description_no_old(self):
        """Argparse description must not say 'Prova AI'."""
        content = _read(TEST_RUNNER)
        assert "Prova AI - Executor de Testes" not in content


# ── D-T3: start.sh branding ─────────────────────────────────

START_SH = PROJECT_DIR / "start.sh"


class TestStartShBranding:
    """D-T3: start.sh must say 'NOVO CR'."""

    def test_comment_header_novo_cr(self):
        """Comment header should say 'NOVO CR'."""
        content = _read(START_SH)
        assert "NOVO CR - Script de" in content

    def test_comment_header_no_old(self):
        """Comment header must not say 'Prova AI'."""
        content = _read(START_SH)
        assert "Prova AI - Script de" not in content

    def test_echo_banner_novo_cr(self):
        """Echo banner should say 'NOVO CR'."""
        content = _read(START_SH)
        assert "NOVO CR - Inicializando" in content

    def test_echo_banner_no_old(self):
        """Echo banner must not say 'Prova AI'."""
        content = _read(START_SH)
        assert "Prova AI - Inicializando" not in content
