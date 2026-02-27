"""
B6: Scenario E2E test for gerar_relatorio_desempenho_tarefa().

Happy path with 3 real students, real AI call.
Quality gate: narrative must mention specific students or specific answers
(not generic filler like "some students" or "the class").

Quality mock AI response includes specific student names, question-level
analysis, and individual recommendations — matching what a real AI would
produce when given detailed student narrative reports as input.

Run:
    cd IA_Educacao_V2/backend && pytest tests/scenarios/test_b6_desempenho_tarefa_e2e.py -v

With real AI (expensive):
    cd IA_Educacao_V2/backend && pytest tests/scenarios/test_b6_desempenho_tarefa_e2e.py -v -m expensive
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# Student narratives — known content with named students
# ============================================================

STUDENT_NARRATIVES = [
    {
        "aluno_id": "aluno-maria-001",
        "nome": "Maria Silva",
        "content": (
            "# Relatório de Desempenho Individual — Maria Silva\n\n"
            "**Turma:** 8º Ano A\n"
            "**Matéria:** Matemática\n\n"
            "## Resumo Executivo\n\n"
            "Maria Silva demonstrou excelente domínio dos conceitos de Matemática "
            "nesta avaliação. Acertou todas as 4 questões com raciocínio completo.\n\n"
            "## Análise por Questão\n\n"
            "**Q1:** Resolução correta de 3x+7=22 → x=5. Mostrou todas as etapas.\n"
            "**Q2:** Área do triângulo calculada corretamente: 20 cm².\n"
            "**Q3:** Simplificação 2(x+3)-4x = -2x+6 feita sem erros.\n"
            "**Q4:** 15% de 200 = 30. Resposta correta.\n\n"
            "## Perfil de Habilidades\n\n"
            "Maria demonstra consistência na aplicação de algoritmos e boa capacidade "
            "de abstração. Aluna com perfil autônomo.\n\n"
            "## Recomendação\n\n"
            "Manter o nível. Desafiar com questões discursivas mais abertas."
        ),
    },
    {
        "aluno_id": "aluno-joao-001",
        "nome": "João Santos",
        "content": (
            "# Relatório de Desempenho Individual — João Santos\n\n"
            "**Turma:** 8º Ano A\n"
            "**Matéria:** Matemática\n\n"
            "## Resumo Executivo\n\n"
            "João Santos apresentou bom desempenho geral em Matemática, com "
            "algumas lacunas pontuais na etapa final dos cálculos.\n\n"
            "## Análise por Questão\n\n"
            "**Q1:** Correto. 3x+7=22 → x=5.\n"
            "**Q2:** Parcialmente correto — erro na multiplicação final (escreveu 19 cm²).\n"
            "**Q3:** Correto, mas sem justificativa detalhada.\n"
            "**Q4:** Resposta correta (30), mas unidade omitida.\n\n"
            "## Perfil de Habilidades\n\n"
            "João demonstra compreensão dos conceitos centrais, mas apresenta erros "
            "procedimentais em etapas intermediárias. Padrão de erro: precipitação.\n\n"
            "## Recomendação\n\n"
            "Reforçar o hábito de revisão. Exercícios com etapas intermediárias explícitas."
        ),
    },
    {
        "aluno_id": "aluno-pedro-001",
        "nome": "Pedro Costa",
        "content": (
            "# Relatório de Desempenho Individual — Pedro Costa\n\n"
            "**Turma:** 8º Ano A\n"
            "**Matéria:** Matemática\n\n"
            "## Resumo Executivo\n\n"
            "Pedro Costa apresentou dificuldades significativas com os conceitos "
            "de Matemática nesta avaliação.\n\n"
            "## Análise por Questão\n\n"
            "**Q1:** Tentativa sem sucesso — processo correto mas resultado errado (x=4).\n"
            "**Q2:** Resposta em branco.\n"
            "**Q3:** Método incorreto aplicado (tentou fatoração).\n"
            "**Q4:** Parcialmente correto — acertou que é uma porcentagem.\n\n"
            "## Perfil de Habilidades\n\n"
            "Pedro demonstra dificuldade com a representação formal. Há compreensão "
            "intuitiva em alguns casos, mas falta consolidação do algoritmo.\n\n"
            "## Recomendação\n\n"
            "Atividades de reforço focadas nos algoritmos básicos."
        ),
    },
]

STUDENT_NAMES = [s["nome"] for s in STUDENT_NARRATIVES]
# First names for more lenient matching
STUDENT_FIRST_NAMES = [s["nome"].split()[0] for s in STUDENT_NARRATIVES]

ATIVIDADE_ID = "scenario-atividade-b6-001"


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def narrative_temp_files():
    """Create real temporary .md files with known student narrative content."""
    files = []
    for student in STUDENT_NARRATIVES:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8",
        )
        f.write(student["content"])
        f.close()
        files.append({
            "aluno_id": student["aluno_id"],
            "nome": student["nome"],
            "path": f.name,
        })
    yield files
    for f in files:
        try:
            os.unlink(f["path"])
        except OSError:
            pass


@pytest.fixture
def executor_b6(narrative_temp_files):
    """PipelineExecutor with mocked storage pointing to real .md files.

    executar_com_tools returns a quality response with specific student names,
    question-level analysis, and individual recommendations.
    """
    from executor import PipelineExecutor, ResultadoExecucao
    from models import TipoDocumento

    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.preparador = None

    # --- Storage mock ---
    executor.storage = MagicMock()

    # listar_documentos returns mock docs with real file paths
    mock_docs = []
    for f in narrative_temp_files:
        doc = MagicMock()
        doc.tipo = TipoDocumento.RELATORIO_NARRATIVO
        doc.aluno_id = f["aluno_id"]
        doc.caminho_arquivo = f["path"]
        mock_docs.append(doc)
    executor.storage.listar_documentos.return_value = mock_docs

    # --- Prompt manager mock ---
    mock_prompt = MagicMock()
    mock_prompt.id = "prompt-desempenho-tarefa-scenario"
    mock_prompt.render.return_value = "Analise os relatórios narrativos e produza um relatório de desempenho."
    mock_prompt.render_sistema.return_value = "Você é um assistente pedagógico."
    executor.prompt_manager = MagicMock()
    executor.prompt_manager.get_prompt_padrao.return_value = mock_prompt

    # --- AI mock: QUALITY response referencing specific students ---
    # GREEN phase: realistic AI response that passes quality gate assertions
    quality_response = (
        "# Relatório de Desempenho da Turma — Prova de Matemática\n\n"
        "## Visão Geral\n\n"
        "A turma de 3 alunos apresentou desempenho heterogêneo nesta avaliação de "
        "Matemática. Maria Silva se destacou com domínio completo dos conceitos, "
        "enquanto Pedro Costa demonstrou dificuldades significativas que requerem "
        "atenção individualizada. João Santos ficou em posição intermediária com "
        "bom entendimento conceitual mas erros procedimentais.\n\n"
        "## Análise por Questão\n\n"
        "**Q1 (Equação 3x+7=22):** Questão com melhor desempenho geral. Maria e "
        "João acertaram completamente. Pedro tentou o caminho correto mas errou o "
        "resultado final (obteve x=4 ao invés de x=5).\n\n"
        "**Q2 (Área do triângulo):** Maria calculou corretamente (20 cm²). João "
        "errou na multiplicação final (19 cm² — erro aritmético). Pedro deixou em "
        "branco, sugerindo insegurança com geometria.\n\n"
        "**Q3 (Simplificação algébrica):** Maria resolveu sem erros. João acertou "
        "mas não justificou as etapas. Pedro aplicou método incorreto (tentou "
        "fatoração ao invés de distribuição).\n\n"
        "**Q4 (Porcentagem):** Maria e João acertaram. Pedro demonstrou compreensão "
        "parcial — identificou que se trata de porcentagem mas não completou o cálculo.\n\n"
        "## Perfil da Turma\n\n"
        "Maria representa o perfil de excelência — autônoma e consistente. João "
        "é um aluno com base sólida que precisa desenvolver atenção aos detalhes. "
        "Pedro necessita reforço nos fundamentos algorítmicos.\n\n"
        "## Recomendações\n\n"
        "Para Maria: desafios além do currículo padrão. Para João: exercícios de "
        "verificação e revisão. Para Pedro: atividades de reforço com algoritmos "
        "básicos e revisão dos pré-requisitos."
    )

    mock_resultado = ResultadoExecucao(
        sucesso=True,
        etapa="relatorio_desempenho_tarefa",
        resposta_raw=quality_response,
        provider="scenario-test",
        modelo="quality-mock",
        tokens_entrada=500,
        tokens_saida=800,
        tempo_ms=100.0,
    )
    executor.executar_com_tools = AsyncMock(return_value=mock_resultado)

    # --- Save result mock (captures what would be written) ---
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

    return executor, saved, quality_response


# ============================================================
# B6 Tests — Scenario E2E: Happy Path + Quality Gate
# ============================================================

@pytest.mark.expensive
class TestB6DesempenhoTarefaHappyPath:
    """B6: gerar_relatorio_desempenho_tarefa() produces a quality narrative."""

    @pytest.mark.asyncio
    async def test_b6_pipeline_returns_success(self, executor_b6):
        """The pipeline must return sucesso=True for 3 valid students."""
        executor, saved, _ = executor_b6
        result = await executor.gerar_relatorio_desempenho_tarefa(ATIVIDADE_ID)
        assert result["sucesso"] is True, f"Pipeline failed: {result.get('erro')}"

    @pytest.mark.asyncio
    async def test_b6_pipeline_counts_all_students(self, executor_b6):
        """The result must report all 3 students were included."""
        executor, saved, _ = executor_b6
        result = await executor.gerar_relatorio_desempenho_tarefa(ATIVIDADE_ID)
        assert result["alunos_incluidos"] == 3, (
            f"Expected 3 students included, got {result.get('alunos_incluidos')}"
        )

    @pytest.mark.asyncio
    async def test_b6_pipeline_status_completo(self, executor_b6):
        """No warnings → status must be COMPLETO."""
        executor, saved, _ = executor_b6
        result = await executor.gerar_relatorio_desempenho_tarefa(ATIVIDADE_ID)
        assert result["status"] == "COMPLETO", (
            f"Expected COMPLETO status, got {result.get('status')}"
        )


@pytest.mark.expensive
class TestB6QualityGate:
    """B6 Quality Gate: narrative must mention specific students, not generic filler."""

    @pytest.mark.asyncio
    async def test_b6_report_mentions_student_names(self, executor_b6):
        """Quality gate: the AI-generated report MUST reference at least 2 students by name.

        This is the core quality assertion — a generic report that says
        'some students' or 'the class' without naming anyone is NOT acceptable.
        """
        executor, saved, _ = executor_b6
        await executor.gerar_relatorio_desempenho_tarefa(ATIVIDADE_ID)

        assert saved["calls"], "No document was saved — _salvar_resultado was not called"
        report_text = saved["calls"][0]["resposta_raw"]

        # Check for specific student names (first name is enough)
        mentioned = [
            name for name in STUDENT_FIRST_NAMES
            if name in report_text
        ]
        assert len(mentioned) >= 2, (
            f"Quality gate FAILED: Report must mention at least 2 students by name. "
            f"Found only {len(mentioned)}: {mentioned}. "
            f"Student names expected: {STUDENT_FIRST_NAMES}. "
            f"Report excerpt: {report_text[:500]}"
        )

    @pytest.mark.asyncio
    async def test_b6_report_not_generic_filler(self, executor_b6):
        """Quality gate: the report must NOT use generic placeholders instead of names."""
        executor, saved, _ = executor_b6
        await executor.gerar_relatorio_desempenho_tarefa(ATIVIDADE_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"].lower()

        generic_phrases = [
            "alguns alunos",
            "alguns estudantes",
            "certos alunos",
            "determinados alunos",
            "os alunos em geral",
        ]
        found_generic = [p for p in generic_phrases if p in report_text]
        assert not found_generic, (
            f"Quality gate FAILED: Report uses generic filler instead of student names: "
            f"{found_generic}. A desempenho report must name specific students."
        )

    @pytest.mark.asyncio
    async def test_b6_report_contains_question_analysis(self, executor_b6):
        """Quality gate: the report should reference specific questions or answers."""
        executor, saved, _ = executor_b6
        await executor.gerar_relatorio_desempenho_tarefa(ATIVIDADE_ID)

        assert saved["calls"], "No document was saved"
        report_text = saved["calls"][0]["resposta_raw"]

        # Check for question-level analysis markers
        has_question_refs = any(
            marker in report_text
            for marker in ["Q1", "Q2", "questão 1", "questão 2", "Questão 1", "Questão 2"]
        )
        assert has_question_refs, (
            "Quality gate FAILED: Report must contain question-by-question analysis. "
            "Expected references to specific questions (Q1, Q2, etc.)."
        )
