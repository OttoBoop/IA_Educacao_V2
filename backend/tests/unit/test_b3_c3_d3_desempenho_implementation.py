"""
B3/C3/D3: Tests for the full implementation of the three Relatório de Desempenho
executor methods and their API routes.

These tests verify the HAPPY PATH (≥ 2 entities) — the methods must:
- Call the LLM with the correct prompt
- Return {"sucesso": True, ...} with the result

They also verify the API routes exist in routes_prompts.py.

RED Phase: These tests FAIL because:
- The executor methods currently raise NotImplementedError for the happy path
- The API routes do not yet exist

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_b3_c3_d3_desempenho_implementation.py -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, mock_open

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


BACKEND_ROOT = Path(__file__).parent.parent.parent  # IA_Educacao_V2/backend
ROUTES_PROMPTS = BACKEND_ROOT / "routes_prompts.py"


def _get_routes_content() -> str:
    assert ROUTES_PROMPTS.exists(), f"routes_prompts.py not found at {ROUTES_PROMPTS}"
    return ROUTES_PROMPTS.read_text(encoding="utf-8")


# ============================================================
# Shared fixture
# ============================================================

@pytest.fixture
def executor_com_mock():
    """PipelineExecutor with fully mocked storage — no database."""
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None

    # Mock prompt_manager.get_prompt_padrao to return a usable prompt
    mock_prompt = MagicMock()
    mock_prompt.id = "test-prompt-id"
    mock_prompt.render.return_value = "rendered prompt text"
    mock_prompt.render_sistema.return_value = "rendered system prompt"
    executor.prompt_manager.get_prompt_padrao.return_value = mock_prompt

    # Mock executar_com_tools to return a successful ResultadoExecucao
    from executor import ResultadoExecucao
    mock_resultado = ResultadoExecucao(
        sucesso=True,
        etapa="desempenho",
        resposta_raw="# Relatório de Desempenho\n\nConteúdo gerado...",
        provider="anthropic",
        modelo="claude-sonnet-4-5-20250514",
        tokens_entrada=500,
        tokens_saida=1000,
        tempo_ms=3500.0,
    )
    executor.executar_com_tools = AsyncMock(return_value=mock_resultado)

    # Mock _salvar_resultado to return a document ID
    executor._salvar_resultado = AsyncMock(return_value="doc-desempenho-123")

    return executor


def _make_narrativo_doc(aluno_id: str, caminho: str):
    """Create a mock RELATORIO_NARRATIVO document."""
    from models import TipoDocumento
    doc = MagicMock()
    doc.tipo = TipoDocumento.RELATORIO_NARRATIVO
    doc.aluno_id = aluno_id
    doc.caminho_arquivo = caminho
    return doc


# ============================================================
# B3 — gerar_relatorio_desempenho_tarefa (happy path + route)
# ============================================================

class TestDesempenhoTarefaImplementation:
    """B3: Full implementation of gerar_relatorio_desempenho_tarefa.

    When ≥2 RELATORIO_NARRATIVO documents exist for an atividade,
    the method must call the LLM and return sucesso=True.
    """

    async def test_b3_happy_path_returns_success(self, executor_com_mock):
        """With ≥2 narratives, method must return sucesso=True (not raise NotImplementedError).

        Currently raises NotImplementedError → test FAILS in RED phase.
        """
        doc1 = _make_narrativo_doc("aluno-001", "/fake/narrativa_aluno1.md")
        doc2 = _make_narrativo_doc("aluno-002", "/fake/narrativa_aluno2.md")
        executor_com_mock.storage.listar_documentos.return_value = [doc1, doc2]

        # Context mocks
        atividade_mock = MagicMock(nome="Prova 1", turma_id="turma-001")
        turma_mock = MagicMock(nome="Turma A", materia_id="mat-001")
        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_com_mock.storage.get_atividade.return_value = atividade_mock
        executor_com_mock.storage.get_turma.return_value = turma_mock
        executor_com_mock.storage.get_materia.return_value = materia_mock

        fake_md = "# Relatório do Aluno\n\nConteúdo narrativo..."
        with patch("builtins.open", mock_open(read_data=fake_md)):
            result = await executor_com_mock.gerar_relatorio_desempenho_tarefa(
                atividade_id="ativ-001",
            )

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("sucesso") is True, (
            "gerar_relatorio_desempenho_tarefa must return sucesso=True when ≥2 "
            f"narratives exist. Got: {result}"
        )

    async def test_b3_calls_executar_com_tools(self, executor_com_mock):
        """Method must call executar_com_tools (LLM call) for the happy path."""
        doc1 = _make_narrativo_doc("aluno-001", "/fake/narrativa_aluno1.md")
        doc2 = _make_narrativo_doc("aluno-002", "/fake/narrativa_aluno2.md")
        executor_com_mock.storage.listar_documentos.return_value = [doc1, doc2]

        atividade_mock = MagicMock(nome="Prova 1", turma_id="turma-001")
        turma_mock = MagicMock(nome="Turma A", materia_id="mat-001")
        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_com_mock.storage.get_atividade.return_value = atividade_mock
        executor_com_mock.storage.get_turma.return_value = turma_mock
        executor_com_mock.storage.get_materia.return_value = materia_mock

        fake_md = "# Relatório do Aluno\n\nConteúdo narrativo..."
        with patch("builtins.open", mock_open(read_data=fake_md)):
            await executor_com_mock.gerar_relatorio_desempenho_tarefa(
                atividade_id="ativ-001",
            )

        executor_com_mock.executar_com_tools.assert_called_once()

    def test_b3_api_route_exists_in_routes_prompts(self):
        """routes_prompts.py must define a POST route at /api/executar/pipeline-desempenho-tarefa."""
        content = _get_routes_content()
        assert "/api/executar/pipeline-desempenho-tarefa" in content, (
            "routes_prompts.py must contain a route at '/api/executar/pipeline-desempenho-tarefa'. "
            "Add a POST endpoint for the desempenho-tarefa pipeline."
        )


# ============================================================
# C3 — gerar_relatorio_desempenho_turma (happy path + route)
# ============================================================

class TestDesempenhoTurmaImplementation:
    """C3: Full implementation of gerar_relatorio_desempenho_turma.

    When ≥2 students exist in a turma, the method must gather all their
    RELATORIO_NARRATIVO docs across atividades, call the LLM, and return sucesso=True.
    """

    async def test_c3_happy_path_returns_success(self, executor_com_mock):
        """With ≥2 students in turma, method must return sucesso=True.

        Currently raises NotImplementedError → test FAILS in RED phase.
        """
        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_com_mock.storage.listar_alunos.return_value = [aluno1, aluno2]

        # Atividades for this turma
        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_com_mock.storage.listar_atividades.return_value = [ativ1]

        # Each student has narratives
        doc1 = _make_narrativo_doc("aluno-001", "/fake/aluno1_ativ1.md")
        doc2 = _make_narrativo_doc("aluno-002", "/fake/aluno2_ativ1.md")
        executor_com_mock.storage.listar_documentos.return_value = [doc1, doc2]

        # Context mocks
        turma_mock = MagicMock(nome="Turma A", materia_id="mat-001")
        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_com_mock.storage.get_turma.return_value = turma_mock
        executor_com_mock.storage.get_materia.return_value = materia_mock

        fake_md = "# Relatório do Aluno\n\nConteúdo narrativo..."
        with patch("builtins.open", mock_open(read_data=fake_md)):
            result = await executor_com_mock.gerar_relatorio_desempenho_turma(
                turma_id="turma-001",
            )

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("sucesso") is True, (
            "gerar_relatorio_desempenho_turma must return sucesso=True when ≥2 "
            f"students have narratives. Got: {result}"
        )

    async def test_c3_calls_executar_com_tools(self, executor_com_mock):
        """Method must call executar_com_tools (LLM call) for the happy path."""
        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_com_mock.storage.listar_alunos.return_value = [aluno1, aluno2]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_com_mock.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_narrativo_doc("aluno-001", "/fake/aluno1.md")
        doc2 = _make_narrativo_doc("aluno-002", "/fake/aluno2.md")
        executor_com_mock.storage.listar_documentos.return_value = [doc1, doc2]

        turma_mock = MagicMock(nome="Turma A", materia_id="mat-001")
        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_com_mock.storage.get_turma.return_value = turma_mock
        executor_com_mock.storage.get_materia.return_value = materia_mock

        fake_md = "# Relatório\n\nConteúdo..."
        with patch("builtins.open", mock_open(read_data=fake_md)):
            await executor_com_mock.gerar_relatorio_desempenho_turma(
                turma_id="turma-001",
            )

        executor_com_mock.executar_com_tools.assert_called_once()

    def test_c3_api_route_exists_in_routes_prompts(self):
        """routes_prompts.py must define a POST route at /api/executar/pipeline-desempenho-turma."""
        content = _get_routes_content()
        assert "/api/executar/pipeline-desempenho-turma" in content, (
            "routes_prompts.py must contain a route at '/api/executar/pipeline-desempenho-turma'. "
            "Add a POST endpoint for the desempenho-turma pipeline."
        )


# ============================================================
# D3 — gerar_relatorio_desempenho_materia (happy path + route)
# ============================================================

class TestDesempenhoMateriaImplementation:
    """D3: Full implementation of gerar_relatorio_desempenho_materia.

    When ≥2 turmas exist for a matéria, the method must gather data
    across all turmas, call the LLM, and return sucesso=True.
    """

    async def test_d3_happy_path_returns_success(self, executor_com_mock):
        """With ≥2 turmas, method must return sucesso=True.

        Currently raises NotImplementedError → test FAILS in RED phase.
        """
        turma1 = MagicMock(id="turma-001", nome="Turma A")
        turma2 = MagicMock(id="turma-002", nome="Turma B")
        executor_com_mock.storage.listar_turmas.return_value = [turma1, turma2]

        # Each turma has students
        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        aluno2 = MagicMock(id="aluno-002", nome="João")
        executor_com_mock.storage.listar_alunos.return_value = [aluno1, aluno2]

        # Atividades per turma
        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_com_mock.storage.listar_atividades.return_value = [ativ1]

        # Narratives exist
        doc1 = _make_narrativo_doc("aluno-001", "/fake/aluno1.md")
        doc2 = _make_narrativo_doc("aluno-002", "/fake/aluno2.md")
        executor_com_mock.storage.listar_documentos.return_value = [doc1, doc2]

        # Context mocks
        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_com_mock.storage.get_materia.return_value = materia_mock

        fake_md = "# Relatório\n\nConteúdo..."
        with patch("builtins.open", mock_open(read_data=fake_md)):
            result = await executor_com_mock.gerar_relatorio_desempenho_materia(
                materia_id="mat-001",
            )

        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
        assert result.get("sucesso") is True, (
            "gerar_relatorio_desempenho_materia must return sucesso=True when ≥2 "
            f"turmas have data. Got: {result}"
        )

    async def test_d3_calls_executar_com_tools(self, executor_com_mock):
        """Method must call executar_com_tools (LLM call) for the happy path."""
        turma1 = MagicMock(id="turma-001", nome="Turma A")
        turma2 = MagicMock(id="turma-002", nome="Turma B")
        executor_com_mock.storage.listar_turmas.return_value = [turma1, turma2]

        aluno1 = MagicMock(id="aluno-001", nome="Maria")
        executor_com_mock.storage.listar_alunos.return_value = [aluno1]

        ativ1 = MagicMock(id="ativ-001", nome="Prova 1")
        executor_com_mock.storage.listar_atividades.return_value = [ativ1]

        doc1 = _make_narrativo_doc("aluno-001", "/fake/aluno1.md")
        executor_com_mock.storage.listar_documentos.return_value = [doc1]

        materia_mock = MagicMock(nome="Matemática", id="mat-001")
        executor_com_mock.storage.get_materia.return_value = materia_mock

        fake_md = "# Relatório\n\nConteúdo..."
        with patch("builtins.open", mock_open(read_data=fake_md)):
            await executor_com_mock.gerar_relatorio_desempenho_materia(
                materia_id="mat-001",
            )

        executor_com_mock.executar_com_tools.assert_called_once()

    def test_d3_api_route_exists_in_routes_prompts(self):
        """routes_prompts.py must define a POST route at /api/executar/pipeline-desempenho-materia."""
        content = _get_routes_content()
        assert "/api/executar/pipeline-desempenho-materia" in content, (
            "routes_prompts.py must contain a route at '/api/executar/pipeline-desempenho-materia'. "
            "Add a POST endpoint for the desempenho-materia pipeline."
        )
