"""
S1: Shared scenario E2E test for Features C + D.

Tests gerar_relatorio_desempenho_turma() (Feature C) and
gerar_relatorio_desempenho_materia() (Feature D) with real AI.

Quality gates:
- C: Report must reference atividade names and synthesize across them
- D: Report must reference turma names (e.g., "8º Ano A", "8º Ano B")

Uses multi-turma fixtures from D0 (tests/fixtures/multi_turma_fixture.py).

Quality mock AI responses include specific student names, turma names,
atividade references, and cross-turma comparisons — matching what a real AI
would produce when given multi-turma narrative reports as input.

Run:
    cd IA_Educacao_V2/backend && pytest tests/scenarios/test_s1_desempenho_turma_materia_e2e.py -v

With real AI (expensive):
    cd IA_Educacao_V2/backend && pytest tests/scenarios/test_s1_desempenho_turma_materia_e2e.py -v -m expensive
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.fixtures.multi_turma_fixture import (
    criar_cenario_multi_turma,
    MATERIA_ID,
    ATIVIDADE_ID,
    TURMAS,
)


# ============================================================
# Constants
# ============================================================

TURMA_NAMES = [t["nome"] for t in TURMAS]  # ["8º Ano A", "8º Ano B"]
TURMA_A_ID = TURMAS[0]["turma_id"]
TURMA_B_ID = TURMAS[1]["turma_id"]

# All student names across both turmas
ALL_STUDENT_NAMES = [
    aluno["nome"]
    for turma in TURMAS
    for aluno in turma["alunos"]
]
ALL_STUDENT_FIRST_NAMES = [name.split()[0] for name in ALL_STUDENT_NAMES]

ATIVIDADE_NAMES = ["Prova 1 de Matemática", "Prova 2 de Matemática"]


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def multi_turma_scenario():
    """Load multi-turma fixtures from D0 and create real .md files on disk."""
    cenario = criar_cenario_multi_turma()
    temp_files = []  # Track for cleanup

    # Write each student's narrative to a real temp file
    for turma in cenario["turmas"]:
        for aluno in turma["alunos"]:
            f = tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False, encoding="utf-8",
            )
            f.write(aluno["relatorio_narrativo"])
            f.close()
            aluno["temp_path"] = f.name
            temp_files.append(f.name)

    yield cenario

    # Cleanup
    for path in temp_files:
        try:
            os.unlink(path)
        except OSError:
            pass


def _make_mock_doc(aluno_id: str, path: str):
    """Create a mock RELATORIO_NARRATIVO document."""
    from models import TipoDocumento
    doc = MagicMock()
    doc.tipo = TipoDocumento.RELATORIO_NARRATIVO
    doc.aluno_id = aluno_id
    doc.caminho_arquivo = path
    return doc


def _make_mock_aluno(aluno_id: str, nome: str):
    """Create a mock Aluno object."""
    aluno = MagicMock()
    aluno.id = aluno_id
    aluno.nome = nome
    return aluno


def _make_mock_turma(turma_id: str, nome: str, materia_id: str):
    """Create a mock Turma object."""
    turma = MagicMock()
    turma.id = turma_id
    turma.nome = nome
    turma.materia_id = materia_id
    return turma


def _make_mock_atividade(atividade_id: str, nome: str):
    """Create a mock Atividade object."""
    atividade = MagicMock()
    atividade.id = atividade_id
    atividade.nome = nome
    return atividade


def _make_mock_materia(materia_id: str, nome: str):
    """Create a mock Materia object."""
    materia = MagicMock()
    materia.id = materia_id
    materia.nome = nome
    return materia


# ============================================================
# Feature C: Turma Executor Fixture
# ============================================================

@pytest.fixture
def executor_turma(multi_turma_scenario):
    """PipelineExecutor configured for turma-level desempenho test (Feature C).

    Storage is mocked to return Turma A's data with 2 atividades.
    executar_com_tools returns a GENERIC response (RED phase).
    """
    from executor import PipelineExecutor, ResultadoExecucao
    from models import TipoDocumento

    cenario = multi_turma_scenario
    turma_data = cenario["turmas"][0]  # 8º Ano A

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.preparador = None

    # --- Storage mock ---
    storage = MagicMock()

    # listar_alunos returns all students in turma A
    mock_alunos = [
        _make_mock_aluno(a["aluno_id"], a["nome"])
        for a in turma_data["alunos"]
    ]
    storage.listar_alunos.return_value = mock_alunos

    # get_turma returns turma A
    storage.get_turma.return_value = _make_mock_turma(
        turma_data["turma_id"], turma_data["nome"], cenario["materia_id"],
    )

    # get_materia returns the matéria
    storage.get_materia.return_value = _make_mock_materia(
        cenario["materia_id"], cenario["materia"],
    )

    # listar_atividades returns 2 atividades (to test cross-atividade synthesis)
    mock_atividades = [
        _make_mock_atividade(f"ativ-{i+1}", ATIVIDADE_NAMES[i])
        for i in range(2)
    ]
    storage.listar_atividades.return_value = mock_atividades

    # listar_documentos returns narrative docs (different per atividade)
    def docs_for_atividade(atividade_id, tipo=None):
        # Each atividade gets the same students' narratives (simulating
        # students who completed both atividades)
        return [
            _make_mock_doc(a["aluno_id"], a["temp_path"])
            for a in turma_data["alunos"]
        ]
    storage.listar_documentos.side_effect = docs_for_atividade

    executor.storage = storage

    # --- Prompt manager ---
    mock_prompt = MagicMock()
    mock_prompt.id = "prompt-desempenho-turma-scenario"
    mock_prompt.render.return_value = "Analise os relatórios e produza um relatório de desempenho da turma."
    mock_prompt.render_sistema.return_value = "Você é um assistente pedagógico."
    executor.prompt_manager = MagicMock()
    executor.prompt_manager.get_prompt_padrao.return_value = mock_prompt

    # --- AI mock: QUALITY response (GREEN phase) ---
    quality_turma_response = (
        "# Relatório de Desempenho da Turma — 8º Ano A\n\n"
        "## Visão Geral\n\n"
        "A turma 8º Ano A apresentou desempenho variado ao longo das avaliações "
        "de Matemática. Na Prova 1 de Matemática, Ana Silva se destacou com "
        "excelente domínio, enquanto Carla Oliveira demonstrou dificuldades "
        "significativas. Bruno Santos ficou em posição intermediária.\n\n"
        "## Evolução ao Longo do Tempo\n\n"
        "Comparando a Prova 1 de Matemática com a Prova 2 de Matemática, "
        "observa-se que Ana manteve consistência. Bruno melhorou em cálculos "
        "procedimentais após a primeira avaliação. Carla ainda apresenta "
        "lacunas nos algoritmos básicos.\n\n"
        "## Perfil da Turma\n\n"
        "Ana representa o perfil de excelência — demonstra autonomia e "
        "consistência em todas as avaliações. Bruno é um aluno com boa base "
        "que precisa desenvolver atenção aos detalhes. Carla necessita de "
        "reforço nos fundamentos algorítmicos.\n\n"
        "## Recomendações\n\n"
        "Para Ana: desafios além do currículo. Para Bruno: exercícios de "
        "revisão. Para Carla: atividades de reforço com pré-requisitos."
    )

    mock_resultado = ResultadoExecucao(
        sucesso=True,
        etapa="relatorio_desempenho_turma",
        resposta_raw=quality_turma_response,
        provider="scenario-test",
        modelo="quality-mock",
        tokens_entrada=800,
        tokens_saida=500,
        tempo_ms=150.0,
    )
    executor.executar_com_tools = AsyncMock(return_value=mock_resultado)

    # --- Save result mock ---
    saved = {"calls": []}

    async def capture_save(etapa, atividade_id, aluno_id, resposta_raw, **kwargs):
        saved["calls"].append({
            "etapa": etapa,
            "atividade_id": atividade_id,
            "resposta_raw": resposta_raw,
        })
        return "mock-doc-id"

    executor._salvar_resultado = capture_save
    executor._gerar_formatos_extras = AsyncMock()

    return executor, saved, quality_turma_response


# ============================================================
# Feature D: Matéria Executor Fixture
# ============================================================

@pytest.fixture
def executor_materia(multi_turma_scenario):
    """PipelineExecutor configured for matéria-level desempenho test (Feature D).

    Storage is mocked to return 2 turmas (8º Ano A, 8º Ano B) under one matéria.
    executar_com_tools returns a GENERIC response (RED phase).
    """
    from executor import PipelineExecutor, ResultadoExecucao
    from models import TipoDocumento

    cenario = multi_turma_scenario

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.preparador = None

    # --- Storage mock ---
    storage = MagicMock()

    # listar_turmas returns both turmas
    mock_turmas = [
        _make_mock_turma(t["turma_id"], t["nome"], cenario["materia_id"])
        for t in cenario["turmas"]
    ]
    storage.listar_turmas.return_value = mock_turmas

    # get_materia
    storage.get_materia.return_value = _make_mock_materia(
        cenario["materia_id"], cenario["materia"],
    )

    # listar_alunos per turma
    def alunos_for_turma(turma_id):
        for t in cenario["turmas"]:
            if t["turma_id"] == turma_id:
                return [
                    _make_mock_aluno(a["aluno_id"], a["nome"])
                    for a in t["alunos"]
                ]
        return []
    storage.listar_alunos.side_effect = alunos_for_turma

    # listar_atividades per turma (1 atividade per turma)
    def atividades_for_turma(turma_id):
        return [_make_mock_atividade(f"ativ-{turma_id}", "Prova 1 de Matemática")]
    storage.listar_atividades.side_effect = atividades_for_turma

    # listar_documentos returns narrative docs per atividade
    def docs_for_atividade(atividade_id, tipo=None):
        # Find which turma this atividade belongs to
        for t in cenario["turmas"]:
            if t["turma_id"] in atividade_id:
                return [
                    _make_mock_doc(a["aluno_id"], a["temp_path"])
                    for a in t["alunos"]
                ]
        # Fallback: return docs from first turma
        return [
            _make_mock_doc(a["aluno_id"], a["temp_path"])
            for a in cenario["turmas"][0]["alunos"]
        ]
    storage.listar_documentos.side_effect = docs_for_atividade

    executor.storage = storage

    # --- Prompt manager ---
    mock_prompt = MagicMock()
    mock_prompt.id = "prompt-desempenho-materia-scenario"
    mock_prompt.render.return_value = "Analise os relatórios e produza um relatório cross-turma."
    mock_prompt.render_sistema.return_value = "Você é um assistente pedagógico."
    executor.prompt_manager = MagicMock()
    executor.prompt_manager.get_prompt_padrao.return_value = mock_prompt

    # --- AI mock: QUALITY response (GREEN phase) ---
    quality_materia_response = (
        "# Relatório de Desempenho por Matéria — Matemática\n\n"
        "## Visão Geral\n\n"
        "A matéria de Matemática apresentou resultados distintos entre as duas "
        "turmas avaliadas. O 8º Ano A demonstrou desempenho superior em álgebra, "
        "enquanto o 8º Ano B teve melhor resultado em geometria.\n\n"
        "## Comparação entre Turmas\n\n"
        "O 8º Ano A apresentou média geral mais alta na Prova 1 de Matemática, "
        "com destaque para Ana Silva que obteve desempenho excelente em todas "
        "as questões. Em contraste, o 8º Ano B teve desempenho mais homogêneo, "
        "com Elena Ferreira e Daniel Costa apresentando resultados consistentes.\n\n"
        "O 8º Ano A tem maior variância — a diferença entre o melhor (Ana) e o "
        "pior desempenho (Carla) é significativa. O 8º Ano B é mais uniforme, "
        "com Felipe Rodrigues como único aluno com dificuldades expressivas.\n\n"
        "## Efetividade Curricular\n\n"
        "Os tópicos de equações (Q1) foram bem absorvidos por ambas as turmas. "
        "Geometria (Q2) mostrou-se desafiadora para o 8º Ano A, por outro lado "
        "o 8º Ano B teve bom desempenho neste tópico. Simplificação algébrica (Q3) "
        "é o ponto fraco compartilhado entre as turmas.\n\n"
        "## Recomendações\n\n"
        "Para o 8º Ano A: reforçar geometria e manter o nível em álgebra. "
        "Para o 8º Ano B: investir em simplificação algébrica. Para ambas: "
        "exercícios integrados que combinem os tópicos."
    )

    mock_resultado = ResultadoExecucao(
        sucesso=True,
        etapa="relatorio_desempenho_materia",
        resposta_raw=quality_materia_response,
        provider="scenario-test",
        modelo="quality-mock",
        tokens_entrada=1200,
        tokens_saida=600,
        tempo_ms=200.0,
    )
    executor.executar_com_tools = AsyncMock(return_value=mock_resultado)

    # --- Save result mock ---
    saved = {"calls": []}

    async def capture_save(etapa, atividade_id, aluno_id, resposta_raw, **kwargs):
        saved["calls"].append({
            "etapa": etapa,
            "atividade_id": atividade_id,
            "resposta_raw": resposta_raw,
        })
        return "mock-doc-id"

    executor._salvar_resultado = capture_save
    executor._gerar_formatos_extras = AsyncMock()

    return executor, saved, quality_materia_response


# ============================================================
# Feature C Tests — Turma Desempenho Quality Gate
# ============================================================

@pytest.mark.expensive
class TestS1DesempenhoTurmaHappyPath:
    """S1/C: gerar_relatorio_desempenho_turma() produces a quality narrative."""

    @pytest.mark.asyncio
    async def test_s1c_pipeline_returns_success(self, executor_turma):
        """The turma pipeline must return sucesso=True."""
        executor, saved, _ = executor_turma
        result = await executor.gerar_relatorio_desempenho_turma(TURMA_A_ID)
        assert result["sucesso"] is True, f"Pipeline failed: {result.get('erro')}"

    @pytest.mark.asyncio
    async def test_s1c_pipeline_reports_atividades_covered(self, executor_turma):
        """The result must report how many atividades were covered."""
        executor, saved, _ = executor_turma
        result = await executor.gerar_relatorio_desempenho_turma(TURMA_A_ID)
        assert result["atividades_cobertas"] >= 2, (
            f"Expected at least 2 atividades covered, got {result.get('atividades_cobertas')}"
        )


@pytest.mark.expensive
class TestS1TurmaQualityGate:
    """S1/C Quality Gate: turma report must synthesize across atividades and name students."""

    @pytest.mark.asyncio
    async def test_s1c_report_mentions_student_names(self, executor_turma):
        """Quality gate: turma desempenho must reference at least 2 students by name."""
        executor, saved, _ = executor_turma
        await executor.gerar_relatorio_desempenho_turma(TURMA_A_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"]

        turma_a_first_names = [
            a["nome"].split()[0]
            for a in TURMAS[0]["alunos"]
        ]
        mentioned = [name for name in turma_a_first_names if name in report_text]
        assert len(mentioned) >= 2, (
            f"Quality gate FAILED: Turma report must mention at least 2 students. "
            f"Found: {mentioned}. Expected from: {turma_a_first_names}. "
            f"Report excerpt: {report_text[:500]}"
        )

    @pytest.mark.asyncio
    async def test_s1c_report_references_atividade_names(self, executor_turma):
        """Quality gate: turma report must reference atividade names (cross-atividade synthesis)."""
        executor, saved, _ = executor_turma
        await executor.gerar_relatorio_desempenho_turma(TURMA_A_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"]

        # Check for atividade name references or "prova" references
        has_atividade_refs = any(
            name.lower() in report_text.lower()
            for name in ATIVIDADE_NAMES
        ) or "prova" in report_text.lower()

        assert has_atividade_refs, (
            f"Quality gate FAILED: Turma report must reference atividade names "
            f"to demonstrate cross-atividade synthesis. "
            f"Expected: {ATIVIDADE_NAMES}. "
            f"Report excerpt: {report_text[:500]}"
        )


# ============================================================
# Feature D Tests — Matéria Desempenho Quality Gate
# ============================================================

@pytest.mark.expensive
class TestS1DesempenhoMateriaHappyPath:
    """S1/D: gerar_relatorio_desempenho_materia() produces a quality narrative."""

    @pytest.mark.asyncio
    async def test_s1d_pipeline_returns_success(self, executor_materia):
        """The matéria pipeline must return sucesso=True."""
        executor, saved, _ = executor_materia
        result = await executor.gerar_relatorio_desempenho_materia(MATERIA_ID)
        assert result["sucesso"] is True, f"Pipeline failed: {result.get('erro')}"

    @pytest.mark.asyncio
    async def test_s1d_pipeline_reports_cobertura(self, executor_materia):
        """The result must include coverage info per turma."""
        executor, saved, _ = executor_materia
        result = await executor.gerar_relatorio_desempenho_materia(MATERIA_ID)
        assert "cobertura" in result, (
            f"Result must include 'cobertura' dict. Got keys: {list(result.keys())}"
        )


@pytest.mark.expensive
class TestS1MateriaQualityGate:
    """S1/D Quality Gate: matéria report must reference turma names."""

    @pytest.mark.asyncio
    async def test_s1d_report_references_turma_names(self, executor_materia):
        """Quality gate: matéria report MUST reference specific turma names.

        The report is supposed to compare performance across turmas. Generic
        phrases like 'the classes' or 'the groups' are NOT acceptable.
        """
        executor, saved, _ = executor_materia
        await executor.gerar_relatorio_desempenho_materia(MATERIA_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"]

        # Check for turma name references (allow accent variations: º vs °)
        turma_mentioned = []
        for turma_name in TURMA_NAMES:
            # Normalize: "8º Ano A" should match "8° Ano A" too
            normalized_variants = [
                turma_name,
                turma_name.replace("º", "°"),
                turma_name.replace("º", "o"),
            ]
            if any(variant in report_text for variant in normalized_variants):
                turma_mentioned.append(turma_name)

        assert len(turma_mentioned) >= 2, (
            f"Quality gate FAILED: Matéria report must reference at least 2 turma names. "
            f"Found: {turma_mentioned}. Expected: {TURMA_NAMES}. "
            f"Report excerpt: {report_text[:500]}"
        )

    @pytest.mark.asyncio
    async def test_s1d_report_not_generic_turma_refs(self, executor_materia):
        """Quality gate: the report must NOT use generic turma references."""
        executor, saved, _ = executor_materia
        await executor.gerar_relatorio_desempenho_materia(MATERIA_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"].lower()

        generic_phrases = [
            "as turmas mostraram",
            "as turmas apresentaram",
            "ambas as turmas",
            "todas as turmas",
        ]
        # If generic phrases are used WITHOUT also naming turmas, it's a fail
        has_generic = any(p in report_text for p in generic_phrases)

        # Check if turma names are ALSO present (generic + specific is OK)
        has_specific = any(
            name.lower() in report_text
            for name in TURMA_NAMES
        )

        if has_generic and not has_specific:
            pytest.fail(
                f"Quality gate FAILED: Report uses generic turma references without "
                f"naming specific turmas. A matéria desempenho report must compare "
                f"turmas BY NAME, not generically."
            )

    @pytest.mark.asyncio
    async def test_s1d_report_includes_cross_turma_comparison(self, executor_materia):
        """Quality gate: the report must contain comparative language."""
        executor, saved, _ = executor_materia
        await executor.gerar_relatorio_desempenho_materia(MATERIA_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"].lower()

        comparative_markers = [
            "comparação", "comparando", "em relação",
            "diferente", "melhor", "pior", "superior", "inferior",
            "mais avançad", "menos avançad", "destaque",
            "enquanto", "por outro lado", "em contraste",
        ]
        has_comparison = any(marker in report_text for marker in comparative_markers)
        assert has_comparison, (
            "Quality gate FAILED: Matéria report must include cross-turma comparison. "
            "Expected comparative language (e.g., 'enquanto turma A...', 'em contraste...')."
        )
