"""
B2/C2/D2: Unit tests for the three new Relatório de Desempenho executor methods.

Tests verify that each new aggregate-level executor method:
- Exists on PipelineExecutor
- Is an async (coroutine) method
- Has the correct parameter signature
- Hard-fails with a clear error when fewer than the required minimum entities have results

B2 — gerar_relatorio_desempenho_tarefa(atividade_id, provider_id=None):
    Hard fail when < 2 students have RELATORIO_NARRATIVO for the atividade.

C2 — gerar_relatorio_desempenho_turma(turma_id, provider_id=None):
    Hard fail when < 2 students have results in the turma.

D2 — gerar_relatorio_desempenho_materia(materia_id, provider_id=None):
    Hard fail when < 2 turmas have results for the matéria.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_b2_c2_d2_desempenho_executor.py -v
"""

import inspect
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# Shared fixture
# ============================================================

@pytest.fixture
def executor_com_mock():
    """PipelineExecutor com storage totalmente mockado — sem banco de dados."""
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None
    return executor


# ============================================================
# B2 — gerar_relatorio_desempenho_tarefa
# ============================================================

class TestGeradorDesempenhoTarefa:
    """
    B2: PipelineExecutor must have gerar_relatorio_desempenho_tarefa().

    This method fetches all RELATORIO_NARRATIVO documents for an atividade,
    synthesizes them with the RELATORIO_DESEMPENHO_TAREFA prompt, and saves
    the result as TipoDocumento.RELATORIO_DESEMPENHO_TAREFA.

    Hard fail if fewer than 2 students have the required narratives.
    """

    def test_b2_method_exists(self):
        """gerar_relatorio_desempenho_tarefa must exist on PipelineExecutor."""
        from executor import PipelineExecutor
        assert hasattr(PipelineExecutor, "gerar_relatorio_desempenho_tarefa"), (
            "PipelineExecutor must have a method gerar_relatorio_desempenho_tarefa. "
            "Add it to executor.py in the Relatório de Desempenho section."
        )

    def test_b2_method_is_async(self):
        """gerar_relatorio_desempenho_tarefa must be an async coroutine method."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "gerar_relatorio_desempenho_tarefa", None)
        assert method is not None, "Method does not exist yet"
        assert inspect.iscoroutinefunction(method), (
            "gerar_relatorio_desempenho_tarefa must be async (coroutine function). "
            "It calls await self.executar_com_tools() internally."
        )

    def test_b2_method_signature(self):
        """gerar_relatorio_desempenho_tarefa must accept (self, atividade_id, provider_id=None)."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "gerar_relatorio_desempenho_tarefa", None)
        assert method is not None, "Method does not exist yet"
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "atividade_id" in params, (
            "gerar_relatorio_desempenho_tarefa must have 'atividade_id' parameter. "
            f"Actual params: {params}"
        )
        assert "provider_id" in params, (
            "gerar_relatorio_desempenho_tarefa must have 'provider_id' parameter. "
            f"Actual params: {params}"
        )
        provider_param = sig.parameters["provider_id"]
        assert provider_param.default is None, (
            "provider_id must default to None. "
            f"Actual default: {provider_param.default}"
        )

    async def test_b2_hard_fail_when_fewer_than_2_students_have_relatorio_narrativo(
        self, executor_com_mock
    ):
        """Must return sucesso=False when fewer than 2 RELATORIO_NARRATIVO docs exist for atividade.

        The method fetches all RELATORIO_NARRATIVO documents for the atividade.
        If fewer than 2 are found, execution must stop immediately with a clear error
        message — the aggregate report requires at least 2 students to be meaningful.
        """
        from models import TipoDocumento

        # Simulate only 1 student having a RELATORIO_NARRATIVO
        single_narrativo = MagicMock()
        single_narrativo.tipo = TipoDocumento.RELATORIO_NARRATIVO
        executor_com_mock.storage.listar_documentos.return_value = [single_narrativo]

        result = await executor_com_mock.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-001",
        )

        assert result.get("sucesso") is False, (
            "gerar_relatorio_desempenho_tarefa must return {'sucesso': False, ...} "
            "when fewer than 2 students have RELATORIO_NARRATIVO. "
            f"Got: {result}"
        )
        assert result.get("erro"), (
            "Result must include an 'erro' key with a descriptive message. "
            f"Got: {result}"
        )

    async def test_b2_hard_fail_when_zero_students_have_relatorio_narrativo(
        self, executor_com_mock
    ):
        """Must also fail when zero students have RELATORIO_NARRATIVO docs."""
        executor_com_mock.storage.listar_documentos.return_value = []

        result = await executor_com_mock.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-002",
        )

        assert result.get("sucesso") is False, (
            "gerar_relatorio_desempenho_tarefa must return {'sucesso': False, ...} "
            "when zero students have RELATORIO_NARRATIVO. "
            f"Got: {result}"
        )


# ============================================================
# C2 — gerar_relatorio_desempenho_turma
# ============================================================

class TestGeradorDesempenhoTurma:
    """
    C2: PipelineExecutor must have gerar_relatorio_desempenho_turma().

    This method fetches RELATORIO_NARRATIVO documents for all students in a turma
    across all atividades, synthesizes them with the RELATORIO_DESEMPENHO_TURMA prompt,
    and saves the result as TipoDocumento.RELATORIO_DESEMPENHO_TURMA.

    Hard fail if fewer than 2 students have any results.
    """

    def test_c2_method_exists(self):
        """gerar_relatorio_desempenho_turma must exist on PipelineExecutor."""
        from executor import PipelineExecutor
        assert hasattr(PipelineExecutor, "gerar_relatorio_desempenho_turma"), (
            "PipelineExecutor must have a method gerar_relatorio_desempenho_turma. "
            "Add it to executor.py in the Relatório de Desempenho section."
        )

    def test_c2_method_is_async(self):
        """gerar_relatorio_desempenho_turma must be an async coroutine method."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "gerar_relatorio_desempenho_turma", None)
        assert method is not None, "Method does not exist yet"
        assert inspect.iscoroutinefunction(method), (
            "gerar_relatorio_desempenho_turma must be async. "
            "It calls await self.executar_com_tools() internally."
        )

    def test_c2_method_signature(self):
        """gerar_relatorio_desempenho_turma must accept (self, turma_id, provider_id=None)."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "gerar_relatorio_desempenho_turma", None)
        assert method is not None, "Method does not exist yet"
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "turma_id" in params, (
            "gerar_relatorio_desempenho_turma must have 'turma_id' parameter. "
            f"Actual params: {params}"
        )
        assert "provider_id" in params, (
            "gerar_relatorio_desempenho_turma must have 'provider_id' parameter. "
            f"Actual params: {params}"
        )
        provider_param = sig.parameters["provider_id"]
        assert provider_param.default is None, (
            "provider_id must default to None. "
            f"Actual default: {provider_param.default}"
        )

    async def test_c2_hard_fail_when_fewer_than_2_students_have_results(
        self, executor_com_mock
    ):
        """Must return sucesso=False when fewer than 2 students have RELATORIO_NARRATIVO in turma.

        The method needs all students' narratives across all atividades.
        With only 1 student having results, an aggregate report is meaningless —
        so the method must hard-fail before calling the LLM.
        """
        # Only 1 aluno in the turma
        single_aluno = MagicMock()
        single_aluno.id = "aluno-001"
        single_aluno.nome = "Aluno Único"
        executor_com_mock.storage.listar_alunos.return_value = [single_aluno]

        # That 1 aluno has no narrative documents
        executor_com_mock.storage.listar_documentos.return_value = []

        result = await executor_com_mock.gerar_relatorio_desempenho_turma(
            turma_id="turma-001",
        )

        assert result.get("sucesso") is False, (
            "gerar_relatorio_desempenho_turma must return {'sucesso': False, ...} "
            "when fewer than 2 students have results. "
            f"Got: {result}"
        )
        assert result.get("erro"), (
            "Result must include an 'erro' key with a descriptive message. "
            f"Got: {result}"
        )

    async def test_c2_hard_fail_when_zero_students_in_turma(
        self, executor_com_mock
    ):
        """Must fail when turma has zero students."""
        executor_com_mock.storage.listar_alunos.return_value = []

        result = await executor_com_mock.gerar_relatorio_desempenho_turma(
            turma_id="turma-002",
        )

        assert result.get("sucesso") is False, (
            "gerar_relatorio_desempenho_turma must return {'sucesso': False, ...} "
            "when turma has zero students. "
            f"Got: {result}"
        )


# ============================================================
# D2 — gerar_relatorio_desempenho_materia
# ============================================================

class TestGeradorDesempenhoMateria:
    """
    D2: PipelineExecutor must have gerar_relatorio_desempenho_materia().

    This method fetches RELATORIO_DESEMPENHO_TURMA (or RELATORIO_NARRATIVO) documents
    across all turmas of a matéria, synthesizes them with the RELATORIO_DESEMPENHO_MATERIA
    prompt, and saves the result as TipoDocumento.RELATORIO_DESEMPENHO_MATERIA.

    Hard fail if fewer than 2 turmas have results — a cross-turma comparison
    requires at least 2 turmas to compare.
    """

    def test_d2_method_exists(self):
        """gerar_relatorio_desempenho_materia must exist on PipelineExecutor."""
        from executor import PipelineExecutor
        assert hasattr(PipelineExecutor, "gerar_relatorio_desempenho_materia"), (
            "PipelineExecutor must have a method gerar_relatorio_desempenho_materia. "
            "Add it to executor.py in the Relatório de Desempenho section."
        )

    def test_d2_method_is_async(self):
        """gerar_relatorio_desempenho_materia must be an async coroutine method."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "gerar_relatorio_desempenho_materia", None)
        assert method is not None, "Method does not exist yet"
        assert inspect.iscoroutinefunction(method), (
            "gerar_relatorio_desempenho_materia must be async. "
            "It calls await self.executar_com_tools() internally."
        )

    def test_d2_method_signature(self):
        """gerar_relatorio_desempenho_materia must accept (self, materia_id, provider_id=None)."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "gerar_relatorio_desempenho_materia", None)
        assert method is not None, "Method does not exist yet"
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        assert "materia_id" in params, (
            "gerar_relatorio_desempenho_materia must have 'materia_id' parameter. "
            f"Actual params: {params}"
        )
        assert "provider_id" in params, (
            "gerar_relatorio_desempenho_materia must have 'provider_id' parameter. "
            f"Actual params: {params}"
        )
        provider_param = sig.parameters["provider_id"]
        assert provider_param.default is None, (
            "provider_id must default to None. "
            f"Actual default: {provider_param.default}"
        )

    async def test_d2_hard_fail_when_fewer_than_2_turmas_have_results(
        self, executor_com_mock
    ):
        """Must return sucesso=False when fewer than 2 turmas have results for the matéria.

        A cross-turma desempenho report requires at least 2 turmas to synthesize.
        If only 1 turma has data, the method must hard-fail immediately — no LLM call.
        """
        # Only 1 turma exists for this matéria
        single_turma = MagicMock()
        single_turma.id = "turma-001"
        single_turma.nome = "Turma A"
        executor_com_mock.storage.listar_turmas.return_value = [single_turma]

        # That turma has no narrative documents
        executor_com_mock.storage.listar_documentos.return_value = []
        executor_com_mock.storage.listar_alunos.return_value = []

        result = await executor_com_mock.gerar_relatorio_desempenho_materia(
            materia_id="materia-001",
        )

        assert result.get("sucesso") is False, (
            "gerar_relatorio_desempenho_materia must return {'sucesso': False, ...} "
            "when fewer than 2 turmas have results. "
            f"Got: {result}"
        )
        assert result.get("erro"), (
            "Result must include an 'erro' key with a descriptive message. "
            f"Got: {result}"
        )

    async def test_d2_hard_fail_when_zero_turmas_exist(
        self, executor_com_mock
    ):
        """Must fail when matéria has zero turmas."""
        executor_com_mock.storage.listar_turmas.return_value = []

        result = await executor_com_mock.gerar_relatorio_desempenho_materia(
            materia_id="materia-002",
        )

        assert result.get("sucesso") is False, (
            "gerar_relatorio_desempenho_materia must return {'sucesso': False, ...} "
            "when matéria has zero turmas. "
            f"Got: {result}"
        )
