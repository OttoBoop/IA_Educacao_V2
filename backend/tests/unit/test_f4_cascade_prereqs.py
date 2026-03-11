"""
F4-T1 RED: _cascade_prereqs() has two bugs in the turma + materia branches.

Bug 1 (turma line 2878, materia line 2897):
    listar_documentos(entity_id) is called with turma_id / materia_id.
    But listar_documentos() expects atividade_id as first param (storage.py:1356).
    Passing turma_id / materia_id → WHERE atividade_id = <turma_id> → returns NOTHING.
    Result: skip sets always empty, cascade never skips, wastes API credits.

Bug 2 (turma line 2881, materia line 2900):
    Skip decision checks RELATORIO_DESEMPENHO_TAREFA / RELATORIO_DESEMPENHO_TURMA.
    But gerar_relatorio_desempenho_turma/materia needs RELATORIO_FINAL per-student.
    An atividade can have DESEMPENHO_TAREFA without student RELATORIO_FINAL docs.
    Result: if Bug 1 is fixed, cascade wrongly skips atividades/turmas.

Entity IDs use Matemática V hierarchy for realism.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f4_cascade_prereqs.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.fixture
def mock_executor():
    """Create a PipelineExecutor with mocked storage and async methods."""
    from executor import PipelineExecutor

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.executar_pipeline_completo = AsyncMock(
        return_value={"gerar_relatorio": MagicMock(sucesso=True)}
    )
    executor.gerar_relatorio_desempenho_tarefa = AsyncMock(
        return_value={"sucesso": True}
    )
    executor.gerar_relatorio_desempenho_turma = AsyncMock(
        return_value={"sucesso": True}
    )
    return executor


# ============================================================
# Test 1: Turma branch must query docs PER atividade (Bug 1)
# ============================================================


class TestF4T1_TurmaCascadeQueriesDocsPerAtividade:
    """
    Bug 1 (turma): listar_documentos(entity_id) called with turma_id.
    Fix: iterate atividades and call listar_documentos(atividade.id) for each.
    """

    @pytest.mark.asyncio
    async def test_turma_cascade_calls_listar_documentos_per_atividade(
        self, mock_executor
    ):
        """
        For turma cascade with 2 atividades (Matemática V — Cálculo 1),
        listar_documentos must be called with each atividade.id, not turma_id.

        Current code: listar_documentos("turma_mat_v_calc1") — returns nothing.
        Expected: listar_documentos("atv_prova1_mat_v") and
                  listar_documentos("atv_prova2_mat_v").
        """
        turma_id = "turma_mat_v_calc1"
        atv1 = MagicMock(id="atv_prova1_mat_v", nome="Prova 1 - Matemática V")
        atv2 = MagicMock(id="atv_prova2_mat_v", nome="Prova 2 - Matemática V")

        mock_executor.storage.listar_atividades.return_value = [atv1, atv2]
        mock_executor.storage.listar_documentos.return_value = []

        # Mock for recursive tarefa cascade (so it doesn't error)
        mock_executor.storage.get_atividade.side_effect = lambda eid: MagicMock(
            id=eid, turma_id=turma_id
        )
        mock_executor.storage.listar_alunos.return_value = [
            MagicMock(id="aluno_ana", nome="Ana Silva"),
        ]

        await mock_executor._cascade_prereqs(
            level="turma",
            entity_id=turma_id,
            provider_id="gem3flash001",
        )

        # Collect all first-positional args to listar_documentos
        doc_calls = mock_executor.storage.listar_documentos.call_args_list
        called_ids = [c[0][0] for c in doc_calls]

        assert turma_id not in called_ids, (
            f"F4-T1 BUG 1: listar_documentos was called with turma_id "
            f"'{turma_id}' — this is wrong because listar_documentos expects "
            f"atividade_id as first param (storage.py:1356).\n"
            f"Actual calls: {doc_calls}\n"
            f"Fix: call listar_documentos(atividade.id) inside the atividade loop."
        )


# ============================================================
# Test 2: Turma branch must check RELATORIO_FINAL (Bug 2)
# ============================================================


class TestF4T1_TurmaCascadeChecksRelatorioFinal:
    """
    Bug 2 (turma): skip decision checks RELATORIO_DESEMPENHO_TAREFA.
    But gerar_relatorio_desempenho_turma needs RELATORIO_FINAL per student.
    Fix: check RELATORIO_FINAL per-student per-atividade.
    """

    @pytest.mark.asyncio
    async def test_turma_does_not_skip_when_desempenho_tarefa_exists_but_no_relatorio_final(
        self, mock_executor
    ):
        """
        Scenario: atividade in Matemática V has RELATORIO_DESEMPENHO_TAREFA
        but students lack RELATORIO_FINAL. Cascade must NOT skip.

        Current code: checks RELATORIO_DESEMPENHO_TAREFA → skips atividade.
        Expected: gerar_relatorio_desempenho_tarefa must still be called.
        """
        from models import TipoDocumento

        turma_id = "turma_mat_v_calc1"
        atv1 = MagicMock(id="atv_prova1_mat_v", nome="Prova 1 - Matemática V")

        # Doc says "tarefa desempenho was generated" — but students may lack RELATORIO_FINAL
        doc_desempenho = MagicMock()
        doc_desempenho.atividade_id = "atv_prova1_mat_v"
        doc_desempenho.tipo = TipoDocumento.RELATORIO_DESEMPENHO_TAREFA
        doc_desempenho.aluno_id = None
        doc_desempenho.turma_id = turma_id

        mock_executor.storage.listar_atividades.return_value = [atv1]
        # Return the desempenho doc regardless of how listar_documentos is called
        mock_executor.storage.listar_documentos.return_value = [doc_desempenho]

        # Mock for recursive tarefa cascade
        mock_executor.storage.get_atividade.return_value = MagicMock(
            id="atv_prova1_mat_v", turma_id=turma_id
        )
        mock_executor.storage.listar_alunos.return_value = [
            MagicMock(id="aluno_ana", nome="Ana Silva"),
        ]

        await mock_executor._cascade_prereqs(
            level="turma",
            entity_id=turma_id,
            provider_id="gem3flash001",
        )

        # The atividade must NOT be skipped — tarefa desempenho must be regenerated
        assert mock_executor.gerar_relatorio_desempenho_tarefa.call_count >= 1, (
            f"F4-T1 BUG 2: gerar_relatorio_desempenho_tarefa was NOT called.\n"
            f"The turma cascade skipped atv_prova1_mat_v because "
            f"RELATORIO_DESEMPENHO_TAREFA exists.\n"
            f"But this doesn't guarantee RELATORIO_FINAL docs exist per-student.\n"
            f"Root cause: executor.py:2881 checks RELATORIO_DESEMPENHO_TAREFA "
            f"instead of RELATORIO_FINAL.\n"
            f"Fix: check RELATORIO_FINAL per-student per-atividade."
        )


# ============================================================
# Test 3: Materia branch must NOT call listar_documentos with materia_id (Bug 1)
# ============================================================


class TestF4T1_MateriaCascadeQueriesPerTurmaAtividades:
    """
    Bug 1 (materia): listar_documentos(entity_id) called with materia_id.
    Fix: for each turma, iterate atividades and call listar_documentos(atividade.id).
    """

    @pytest.mark.asyncio
    async def test_materia_cascade_does_not_call_listar_documentos_with_materia_id(
        self, mock_executor
    ):
        """
        For materia cascade (Matemática V), listar_documentos must NOT be
        called with materia_id. It must be called per-atividade within each turma.

        Current code: listar_documentos("materia_mat_v") — returns nothing.
        Expected: listar_documentos("atv_prova1_mat_v") etc.
        """
        materia_id = "materia_mat_v"
        turma_id = "turma_mat_v_calc1"
        atv1 = MagicMock(id="atv_prova1_mat_v", nome="Prova 1 - Matemática V")

        turma = MagicMock(id=turma_id, nome="Cálculo 1", materia_id=materia_id)

        mock_executor.storage.listar_turmas.return_value = [turma]
        mock_executor.storage.listar_atividades.return_value = [atv1]
        mock_executor.storage.listar_documentos.return_value = []

        # Mocks for recursive turma → tarefa cascade
        mock_executor.storage.get_atividade.return_value = MagicMock(
            id="atv_prova1_mat_v", turma_id=turma_id
        )
        mock_executor.storage.listar_alunos.return_value = [
            MagicMock(id="aluno_ana", nome="Ana Silva"),
        ]

        await mock_executor._cascade_prereqs(
            level="materia",
            entity_id=materia_id,
            provider_id="gem3flash001",
        )

        # Collect first-positional args to listar_documentos
        doc_calls = mock_executor.storage.listar_documentos.call_args_list
        called_ids = [c[0][0] for c in doc_calls]

        assert materia_id not in called_ids, (
            f"F4-T1 BUG 1 (materia): listar_documentos was called with "
            f"materia_id '{materia_id}' — this is wrong because "
            f"listar_documentos expects atividade_id (storage.py:1356).\n"
            f"Actual calls: {doc_calls}\n"
            f"Fix: for each turma, iterate atividades and call "
            f"listar_documentos(atividade.id) per-atividade."
        )
