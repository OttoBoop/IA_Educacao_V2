"""
B4/C4/D4: Integration tests for the three Relatório de Desempenho executor methods.

Tests verify the WIRING between executor methods and storage:
- Mock the AI (executar_com_tools) but let _salvar_resultado run naturally
- Verify storage.salvar_documento called with correct TipoDocumento
- Verify warning JSON structure (avisos with student names, reasons, counts, status)
- Verify coverage gap information for turma/matéria levels

RED Phase:
- Doc-save tests verify existing wiring through _salvar_resultado (may PASS)
- Warning JSON tests FAIL because current implementation returns counts only,
  not detailed avisos with student names, reasons, or PARCIAL/COMPLETO status

Run: cd IA_Educacao_V2/backend && pytest tests/integration/test_b4_c4_d4_desempenho_integration.py -v
"""

import pytest
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def narrative_files():
    """Create real temporary .md files with narrative content.

    Uses real files (not mock_open) so _salvar_resultado can also write
    its temp files without interference.
    """
    files = []
    contents = [
        ("aluno-001", "# Relatório — Maria\n\nMaria demonstrou excelente domínio dos conceitos."),
        ("aluno-002", "# Relatório — João\n\nJoão apresentou dificuldades em geometria."),
        ("aluno-003", "# Relatório — Pedro\n\nPedro teve desempenho mediano na avaliação."),
    ]
    for aluno_id, content in contents:
        f = tempfile.NamedTemporaryFile(
            mode='w', suffix='.md', delete=False, encoding='utf-8',
        )
        f.write(content)
        f.close()
        files.append({"aluno_id": aluno_id, "path": f.name})
    yield files
    for f in files:
        try:
            os.unlink(f["path"])
        except OSError:
            pass


def _make_doc(aluno_id: str, path: str):
    """Create a mock RELATORIO_NARRATIVO document with a real file path."""
    from models import TipoDocumento
    doc = MagicMock()
    doc.tipo = TipoDocumento.RELATORIO_NARRATIVO
    doc.aluno_id = aluno_id
    doc.caminho_arquivo = path
    return doc


@pytest.fixture
def executor_integration():
    """PipelineExecutor with AI mocked but _salvar_resultado running naturally.

    This tests the full wiring: executor method → _salvar_resultado → storage.salvar_documento.
    Only the AI call (executar_com_tools) and PDF generation (_gerar_formatos_extras) are mocked.
    """
    from executor import PipelineExecutor, ResultadoExecucao

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None

    # Mock prompt
    mock_prompt = MagicMock()
    mock_prompt.id = "test-prompt-id"
    mock_prompt.render.return_value = "rendered prompt text"
    mock_prompt.render_sistema.return_value = "rendered system prompt"
    executor.prompt_manager.get_prompt_padrao.return_value = mock_prompt

    # Mock executar_com_tools (AI call)
    mock_resultado = ResultadoExecucao(
        sucesso=True,
        etapa="desempenho",
        resposta_raw="# Relatório de Desempenho\n\nConteúdo gerado pelo LLM...",
        provider="anthropic",
        modelo="claude-sonnet-4-5-20250514",
        tokens_entrada=500,
        tokens_saida=1000,
        tempo_ms=3500.0,
    )
    executor.executar_com_tools = AsyncMock(return_value=mock_resultado)

    # Mock _gerar_formatos_extras (skip PDF generation)
    executor._gerar_formatos_extras = AsyncMock()

    # Mock storage.salvar_documento to return a valid doc
    mock_saved_doc = MagicMock()
    mock_saved_doc.id = "doc-desempenho-integration-123"
    executor.storage.salvar_documento.return_value = mock_saved_doc

    return executor


def _extract_tipos_from_salvar_calls(storage_mock) -> list:
    """Extract TipoDocumento values from storage.salvar_documento calls."""
    tipos = []
    for call in storage_mock.salvar_documento.call_args_list:
        tipo_arg = call.kwargs.get("tipo")
        if tipo_arg is None and len(call.args) > 1:
            tipo_arg = call.args[1]
        if tipo_arg:
            tipos.append(tipo_arg)
    return tipos


# ============================================================
# B4 — Integration tests: gerar_relatorio_desempenho_tarefa
# ============================================================

class TestDesempenhoTarefaIntegration:
    """B4: Integration tests for gerar_relatorio_desempenho_tarefa.

    Verifies:
    1. storage.salvar_documento called with TipoDocumento.RELATORIO_DESEMPENHO_TAREFA
    2. Warning JSON (avisos) includes student names, reasons
    3. Result includes PARCIAL/COMPLETO status
    """

    def _setup_tarefa_context(self, executor, ativ_id="ativ-001"):
        """Wire standard context mocks for a tarefa test."""
        atividade = MagicMock(nome="Prova 1", turma_id="turma-001")
        turma = MagicMock(nome="Turma A", materia_id="mat-001")
        materia = MagicMock(nome="Matemática", id="mat-001")
        executor.storage.get_atividade.return_value = atividade
        executor.storage.get_turma.return_value = turma
        executor.storage.get_materia.return_value = materia

    async def test_b4_doc_saved_with_tipo_desempenho_tarefa(
        self, executor_integration, narrative_files,
    ):
        """After successful LLM call, storage.salvar_documento must be called
        with TipoDocumento.RELATORIO_DESEMPENHO_TAREFA.

        Verifies wiring through _salvar_resultado (NOT mocked in this test).
        """
        from models import TipoDocumento

        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]
        self._setup_tarefa_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-001",
        )

        assert result["sucesso"] is True
        tipos = _extract_tipos_from_salvar_calls(executor_integration.storage)
        assert TipoDocumento.RELATORIO_DESEMPENHO_TAREFA in tipos, (
            f"storage.salvar_documento must be called with "
            f"TipoDocumento.RELATORIO_DESEMPENHO_TAREFA. Tipos used: {tipos}"
        )

    async def test_b4_result_includes_avisos_with_excluded_student_ids(
        self, executor_integration, narrative_files,
    ):
        """When some students are excluded (unreadable files), result must include
        'avisos' list with each excluded student's aluno_id.

        Currently FAILS: implementation returns counts only, not detailed avisos.
        """
        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        doc3 = _make_doc("aluno-003", "/non/existent/path/narrativa.md")
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2, doc3]
        self._setup_tarefa_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-001",
        )

        assert result["sucesso"] is True
        assert "avisos" in result, (
            "Result must include 'avisos' list when students are excluded. "
            f"Got keys: {list(result.keys())}"
        )
        avisos = result["avisos"]
        assert isinstance(avisos, list)
        assert len(avisos) >= 1, (
            f"Expected at least 1 aviso for excluded student, got {len(avisos)}"
        )
        aviso_ids = [a.get("aluno_id") for a in avisos]
        assert "aluno-003" in aviso_ids, (
            f"Excluded student 'aluno-003' must appear in avisos. Got: {aviso_ids}"
        )

    async def test_b4_avisos_include_exclusion_reason(
        self, executor_integration, narrative_files,
    ):
        """Each aviso must include a 'motivo' (reason) for the exclusion."""
        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        doc3 = _make_doc("aluno-003", "/non/existent/path.md")
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2, doc3]
        self._setup_tarefa_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-001",
        )

        avisos = result.get("avisos", [])
        assert len(avisos) >= 1, "Must have at least 1 aviso"
        for aviso in avisos:
            assert "motivo" in aviso, (
                f"Each aviso must include 'motivo' (reason for exclusion). "
                f"Got keys: {list(aviso.keys())}"
            )
            assert aviso["motivo"], "motivo must not be empty"

    async def test_b4_result_status_parcial_when_some_excluded(
        self, executor_integration, narrative_files,
    ):
        """Result must have status='PARCIAL' when some students were excluded."""
        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        doc3 = _make_doc("aluno-003", "/non/existent/path.md")
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2, doc3]
        self._setup_tarefa_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-001",
        )

        assert "status" in result, (
            f"Result must include 'status' field (PARCIAL or COMPLETO). "
            f"Got keys: {list(result.keys())}"
        )
        assert result["status"] == "PARCIAL", (
            f"When some students are excluded, status must be 'PARCIAL'. "
            f"Got: {result.get('status')}"
        )

    async def test_b4_result_status_completo_when_all_included(
        self, executor_integration, narrative_files,
    ):
        """Result must have status='COMPLETO' when all students were successfully included."""
        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]
        self._setup_tarefa_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_tarefa(
            atividade_id="ativ-001",
        )

        assert "status" in result, (
            f"Result must include 'status' field. Got keys: {list(result.keys())}"
        )
        assert result["status"] == "COMPLETO", (
            f"When all students are included, status must be 'COMPLETO'. "
            f"Got: {result.get('status')}"
        )


# ============================================================
# C4 — Integration tests: gerar_relatorio_desempenho_turma
# ============================================================

class TestDesempenhoTurmaIntegration:
    """C4: Integration tests for gerar_relatorio_desempenho_turma.

    Verifies:
    1. storage.salvar_documento called with TipoDocumento.RELATORIO_DESEMPENHO_TURMA
    2. Warning JSON (avisos) for excluded students
    3. Coverage gap info for atividades
    4. PARCIAL/COMPLETO status
    """

    def _setup_turma_context(self, executor):
        """Wire standard context mocks for a turma test."""
        turma = MagicMock(nome="Turma A", materia_id="mat-001")
        materia = MagicMock(nome="Matemática", id="mat-001")
        executor.storage.get_turma.return_value = turma
        executor.storage.get_materia.return_value = materia

    async def test_c4_doc_saved_with_tipo_desempenho_turma(
        self, executor_integration, narrative_files,
    ):
        """storage.salvar_documento must be called with RELATORIO_DESEMPENHO_TURMA."""
        from models import TipoDocumento

        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]
        self._setup_turma_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_turma(
            turma_id="turma-001",
        )

        assert result["sucesso"] is True
        tipos = _extract_tipos_from_salvar_calls(executor_integration.storage)
        assert TipoDocumento.RELATORIO_DESEMPENHO_TURMA in tipos, (
            f"Must save with RELATORIO_DESEMPENHO_TURMA. Tipos: {tipos}"
        )

    async def test_c4_result_includes_avisos_for_excluded_students(
        self, executor_integration, narrative_files,
    ):
        """Result must include 'avisos' list with excluded student details."""
        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        aluno3 = MagicMock(id="aluno-003", nome="Pedro")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2, aluno3]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        # 2 readable + 1 unreadable
        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        doc3 = _make_doc("aluno-003", "/non/existent/path.md")
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2, doc3]
        self._setup_turma_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_turma(
            turma_id="turma-001",
        )

        assert result["sucesso"] is True
        assert "avisos" in result, (
            f"Result must include 'avisos' list. Got keys: {list(result.keys())}"
        )
        avisos = result["avisos"]
        aviso_ids = [a.get("aluno_id") for a in avisos]
        assert "aluno-003" in aviso_ids, (
            f"Excluded student 'aluno-003' must appear in avisos. Got: {aviso_ids}"
        )

    async def test_c4_result_includes_atividades_com_lacunas(
        self, executor_integration, narrative_files,
    ):
        """Result must include 'atividades_com_lacunas' listing atividades with
        incomplete student coverage.

        When an atividade has narratives from some students but not all enrolled,
        it should be flagged as having a coverage gap.
        """
        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        ativ2 = MagicMock(id="ativ-002", nome="Prova 2")
        executor_integration.storage.listar_atividades.return_value = [ativ1, ativ2]

        # ativ-001: both alunos have docs. ativ-002: only aluno-001 has doc
        doc1_ativ1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2_ativ1 = _make_doc("aluno-002", narrative_files[1]["path"])
        doc1_ativ2 = _make_doc("aluno-001", narrative_files[2]["path"])

        def listar_docs_side_effect(atividade_id, tipo=None):
            if atividade_id == "ativ-001":
                return [doc1_ativ1, doc2_ativ1]
            elif atividade_id == "ativ-002":
                return [doc1_ativ2]
            return []

        executor_integration.storage.listar_documentos.side_effect = listar_docs_side_effect
        self._setup_turma_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_turma(
            turma_id="turma-001",
        )

        assert result["sucesso"] is True
        assert "atividades_com_lacunas" in result, (
            f"Result must include 'atividades_com_lacunas' when some atividades "
            f"have partial student coverage. Got keys: {list(result.keys())}"
        )

    async def test_c4_result_status_field(
        self, executor_integration, narrative_files,
    ):
        """Result must include status='PARCIAL' or 'COMPLETO'."""
        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]
        self._setup_turma_context(executor_integration)

        result = await executor_integration.gerar_relatorio_desempenho_turma(
            turma_id="turma-001",
        )

        assert result["sucesso"] is True
        assert "status" in result, (
            f"Result must include 'status' field. Got keys: {list(result.keys())}"
        )
        assert result["status"] in ("PARCIAL", "COMPLETO"), (
            f"status must be 'PARCIAL' or 'COMPLETO'. Got: {result.get('status')}"
        )


# ============================================================
# D4 — Integration tests: gerar_relatorio_desempenho_materia
# ============================================================

class TestDesempenhoMateriaIntegration:
    """D4: Integration tests for gerar_relatorio_desempenho_materia.

    Verifies:
    1. storage.salvar_documento called with TipoDocumento.RELATORIO_DESEMPENHO_MATERIA
    2. Coverage info per turma
    3. Warning JSON (avisos) for coverage gaps
    4. PARCIAL/COMPLETO status
    """

    async def test_d4_doc_saved_with_tipo_desempenho_materia(
        self, executor_integration, narrative_files,
    ):
        """storage.salvar_documento must be called with RELATORIO_DESEMPENHO_MATERIA."""
        from models import TipoDocumento

        turma1 = MagicMock(id="turma-001", nome="Turma A")
        turma2 = MagicMock(id="turma-002", nome="Turma B")
        executor_integration.storage.listar_turmas.return_value = [turma1, turma2]

        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]

        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_integration.storage.get_materia.return_value = materia_mock

        result = await executor_integration.gerar_relatorio_desempenho_materia(
            materia_id="mat-001",
        )

        assert result["sucesso"] is True
        tipos = _extract_tipos_from_salvar_calls(executor_integration.storage)
        assert TipoDocumento.RELATORIO_DESEMPENHO_MATERIA in tipos, (
            f"Must save with RELATORIO_DESEMPENHO_MATERIA. Tipos: {tipos}"
        )

    async def test_d4_result_includes_cobertura_por_turma(
        self, executor_integration, narrative_files,
    ):
        """Result must include 'cobertura' with per-turma coverage info."""
        turma1 = MagicMock(id="turma-001", nome="Turma A")
        turma2 = MagicMock(id="turma-002", nome="Turma B")
        executor_integration.storage.listar_turmas.return_value = [turma1, turma2]

        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]

        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_integration.storage.get_materia.return_value = materia_mock

        result = await executor_integration.gerar_relatorio_desempenho_materia(
            materia_id="mat-001",
        )

        assert result["sucesso"] is True
        assert "cobertura" in result, (
            f"Result must include 'cobertura' field with per-turma coverage info. "
            f"Got keys: {list(result.keys())}"
        )
        cobertura = result["cobertura"]
        assert isinstance(cobertura, (list, dict)), (
            f"cobertura must be a list or dict. Got: {type(cobertura)}"
        )

    async def test_d4_result_includes_avisos_for_coverage_gaps(
        self, executor_integration, narrative_files,
    ):
        """Result must include 'avisos' when turmas/atividades have coverage gaps."""
        turma1 = MagicMock(id="turma-001", nome="Turma A")
        turma2 = MagicMock(id="turma-002", nome="Turma B")
        executor_integration.storage.listar_turmas.return_value = [turma1, turma2]

        # Turma A: 2 alunos. Turma B: 1 aluno.
        def listar_alunos_side_effect(turma_id):
            if turma_id == "turma-001":
                return [MagicMock(id="aluno-001"), MagicMock(id="aluno-002")]
            elif turma_id == "turma-002":
                return [MagicMock(id="aluno-003")]
            return []

        executor_integration.storage.listar_alunos.side_effect = listar_alunos_side_effect

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        # Turma A alunos readable, Turma B aluno-003 has unreadable file
        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        doc3 = _make_doc("aluno-003", "/non/existent/path.md")
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2, doc3]

        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_integration.storage.get_materia.return_value = materia_mock

        result = await executor_integration.gerar_relatorio_desempenho_materia(
            materia_id="mat-001",
        )

        assert result["sucesso"] is True
        assert "avisos" in result, (
            f"Result must include 'avisos' for coverage gaps. "
            f"Got keys: {list(result.keys())}"
        )

    async def test_d4_result_status_field(
        self, executor_integration, narrative_files,
    ):
        """Result must include status='PARCIAL' or 'COMPLETO'."""
        turma1 = MagicMock(id="turma-001", nome="Turma A")
        turma2 = MagicMock(id="turma-002", nome="Turma B")
        executor_integration.storage.listar_turmas.return_value = [turma1, turma2]

        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_integration.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_integration.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_doc("aluno-001", narrative_files[0]["path"])
        doc2 = _make_doc("aluno-002", narrative_files[1]["path"])
        executor_integration.storage.listar_documentos.return_value = [doc1, doc2]

        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_integration.storage.get_materia.return_value = materia_mock

        result = await executor_integration.gerar_relatorio_desempenho_materia(
            materia_id="mat-001",
        )

        assert result["sucesso"] is True
        assert "status" in result, (
            f"Result must include 'status' field. Got keys: {list(result.keys())}"
        )
        assert result["status"] in ("PARCIAL", "COMPLETO"), (
            f"status must be 'PARCIAL' or 'COMPLETO'. Got: {result.get('status')}"
        )
