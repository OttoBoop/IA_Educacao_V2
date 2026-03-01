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
