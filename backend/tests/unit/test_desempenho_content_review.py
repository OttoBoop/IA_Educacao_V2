"""
C-T1: Automated content review tests for desempenho report generation.

Part 1: Backend bug fix — _check_has_atividades must check RELATORIO_FINAL
         (not deprecated RELATORIO_NARRATIVO) to correctly detect graded work.

Part 2: Executor must use RELATORIO_FINAL when collecting student narratives
         for desempenho report synthesis.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_desempenho_content_review.py -v
"""

from pathlib import Path

import pytest


ROUTES_EXTRAS = Path(__file__).parent.parent.parent / "routes_extras.py"
EXECUTOR = Path(__file__).parent.parent.parent / "executor.py"


@pytest.fixture
def routes_extras_content():
    """Read routes_extras.py source."""
    assert ROUTES_EXTRAS.exists(), f"routes_extras.py not found: {ROUTES_EXTRAS}"
    return ROUTES_EXTRAS.read_text(encoding="utf-8")


@pytest.fixture
def executor_content():
    """Read executor.py source."""
    assert EXECUTOR.exists(), f"executor.py not found: {EXECUTOR}"
    return EXECUTOR.read_text(encoding="utf-8")


# ============================================================
# C-T1a: _check_has_atividades must use RELATORIO_FINAL
# ============================================================

class TestCT1aHasAtividadesType:
    """The _check_has_atividades function must check for RELATORIO_FINAL (not deprecated RELATORIO_NARRATIVO)."""

    def test_check_has_atividades_uses_relatorio_final(self, routes_extras_content):
        """_check_has_atividades must reference RELATORIO_FINAL, not the deprecated RELATORIO_NARRATIVO."""
        # Find the function body
        func_start = routes_extras_content.find("def _check_has_atividades")
        assert func_start != -1, "_check_has_atividades function must exist in routes_extras.py"

        # Find the next function definition to scope the search
        next_func = routes_extras_content.find("\ndef ", func_start + 1)
        if next_func == -1:
            next_func = routes_extras_content.find("\n@", func_start + 1)
        func_body = routes_extras_content[func_start:next_func] if next_func != -1 else routes_extras_content[func_start:]

        assert "RELATORIO_FINAL" in func_body, (
            "_check_has_atividades must use TipoDocumento.RELATORIO_FINAL "
            "to detect graded work. RELATORIO_NARRATIVO is deprecated and "
            "no longer created by the current pipeline."
        )

    def test_check_has_atividades_no_deprecated_narrativo(self, routes_extras_content):
        """_check_has_atividades must NOT reference the deprecated RELATORIO_NARRATIVO."""
        func_start = routes_extras_content.find("def _check_has_atividades")
        assert func_start != -1

        next_func = routes_extras_content.find("\ndef ", func_start + 1)
        if next_func == -1:
            next_func = routes_extras_content.find("\n@", func_start + 1)
        func_body = routes_extras_content[func_start:next_func] if next_func != -1 else routes_extras_content[func_start:]

        assert "RELATORIO_NARRATIVO" not in func_body, (
            "_check_has_atividades still references RELATORIO_NARRATIVO which is deprecated. "
            "It must use RELATORIO_FINAL instead."
        )


# ============================================================
# C-T1b: Executor desempenho functions must use RELATORIO_FINAL
# ============================================================

class TestCT1bExecutorUsesRelatorioFinal:
    """The executor's gerar_relatorio_desempenho_* functions must search for RELATORIO_FINAL."""

    def test_tarefa_executor_uses_relatorio_final(self, executor_content):
        """gerar_relatorio_desempenho_tarefa must search for RELATORIO_FINAL docs."""
        func_start = executor_content.find("def gerar_relatorio_desempenho_tarefa")
        assert func_start != -1, "gerar_relatorio_desempenho_tarefa must exist in executor.py"

        # Scope to this function (find next async def)
        next_func = executor_content.find("\n    async def ", func_start + 1)
        func_body = executor_content[func_start:next_func] if next_func != -1 else executor_content[func_start:]

        assert "RELATORIO_FINAL" in func_body, (
            "gerar_relatorio_desempenho_tarefa must use TipoDocumento.RELATORIO_FINAL "
            "to find student reports. RELATORIO_NARRATIVO is deprecated."
        )

    def test_turma_executor_uses_relatorio_final(self, executor_content):
        """gerar_relatorio_desempenho_turma must search for RELATORIO_FINAL docs."""
        func_start = executor_content.find("def gerar_relatorio_desempenho_turma")
        assert func_start != -1, "gerar_relatorio_desempenho_turma must exist in executor.py"

        next_func = executor_content.find("\n    async def ", func_start + 1)
        func_body = executor_content[func_start:next_func] if next_func != -1 else executor_content[func_start:]

        assert "RELATORIO_FINAL" in func_body, (
            "gerar_relatorio_desempenho_turma must use TipoDocumento.RELATORIO_FINAL "
            "to find student reports. RELATORIO_NARRATIVO is deprecated."
        )

    def test_materia_executor_uses_relatorio_final(self, executor_content):
        """gerar_relatorio_desempenho_materia must search for RELATORIO_FINAL docs."""
        func_start = executor_content.find("def gerar_relatorio_desempenho_materia")
        assert func_start != -1, "gerar_relatorio_desempenho_materia must exist in executor.py"

        next_func = executor_content.find("\n    async def ", func_start + 1)
        func_body = executor_content[func_start:next_func] if next_func != -1 else executor_content[func_start:]

        assert "RELATORIO_FINAL" in func_body, (
            "gerar_relatorio_desempenho_materia must use TipoDocumento.RELATORIO_FINAL "
            "to find student reports. RELATORIO_NARRATIVO is deprecated."
        )

    def test_tarefa_executor_no_deprecated_narrativo(self, executor_content):
        """gerar_relatorio_desempenho_tarefa must NOT reference deprecated RELATORIO_NARRATIVO."""
        func_start = executor_content.find("def gerar_relatorio_desempenho_tarefa")
        assert func_start != -1

        next_func = executor_content.find("\n    async def ", func_start + 1)
        func_body = executor_content[func_start:next_func] if next_func != -1 else executor_content[func_start:]

        assert "RELATORIO_NARRATIVO" not in func_body, (
            "gerar_relatorio_desempenho_tarefa still references deprecated RELATORIO_NARRATIVO. "
            "Must use RELATORIO_FINAL instead."
        )


# ============================================================
# C-T1c: Executor must resolve file paths through storage
# (not open raw caminho_arquivo — fails on Render)
# ============================================================

class TestCT1cExecutorResolvesFilePaths:
    """Executor desempenho functions must use storage.resolver_caminho_documento() to read files."""

    @pytest.fixture
    def executor_desempenho_funcs(self, executor_content):
        """Extract the 3 desempenho function bodies."""
        funcs = {}
        for name in ("gerar_relatorio_desempenho_tarefa",
                      "gerar_relatorio_desempenho_turma",
                      "gerar_relatorio_desempenho_materia"):
            start = executor_content.find(f"def {name}")
            assert start != -1, f"{name} must exist in executor.py"
            end = executor_content.find("\n    async def ", start + 1)
            funcs[name] = executor_content[start:end] if end != -1 else executor_content[start:]
        return funcs

    def test_no_raw_open_caminho_arquivo(self, executor_desempenho_funcs):
        """None of the 3 desempenho funcs must use open(doc.caminho_arquivo) directly."""
        for name, body in executor_desempenho_funcs.items():
            assert "open(doc.caminho_arquivo" not in body, (
                f"{name} uses open(doc.caminho_arquivo, ...) which reads a raw DB path "
                f"that doesn't exist on Render's ephemeral filesystem. Must use "
                f"self.storage.resolver_caminho_documento(doc) first."
            )

    def test_uses_resolver_caminho_documento(self, executor_desempenho_funcs):
        """All 3 desempenho funcs must call resolver_caminho_documento."""
        for name, body in executor_desempenho_funcs.items():
            assert "resolver_caminho_documento" in body, (
                f"{name} must call self.storage.resolver_caminho_documento(doc) to resolve "
                f"file paths through Supabase storage before reading."
            )
