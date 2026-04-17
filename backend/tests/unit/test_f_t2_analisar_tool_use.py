"""
Test F-T2: Migrate ANALISAR_HABILIDADES to tool-use dual output.

Tests that the ANALISAR_HABILIDADES pipeline stage has been migrated FROM the two-pass system
(AI call -> JSON, then separate AI call -> narrative PDF) TO a single
executar_com_tools() call with tools_to_use=["create_document", "execute_python_code"].

What each test verifies:
1. ANALISAR_HABILIDADES uses tool-use execution path — executar_com_tools() is called with the
   correct tools when analisar_habilidades() is invoked (not _executar_multimodal()).
2. Two-pass narrative NOT called for ANALISAR_HABILIDADES — _gerar_narrativa_pdf() must NOT be
   invoked for ANALISAR_HABILIDADES after the migration.
3. System prompt includes tool-use instructions — the system_prompt passed to
   executar_com_tools() contains JSON schema + PDF generation instructions.
4. STAGE_OUTPUT_FORMATS has analise_habilidades — sanity check that document_generators already
   maps "analise_habilidades" to [JSON, PDF] (this should already pass).
5. ANALISAR_HABILIDADES no longer in NARRATIVA_PROMPT_MAP — after migration, ANALISAR_HABILIDADES
   must be removed from the two-pass map.

All tests 1-3 and 5 MUST FAIL before implementation because:
- analisar_habilidades() method does not exist — it must be created with executar_com_tools()
- ANALISAR_HABILIDADES IS in NARRATIVA_PROMPT_MAP (two-pass still active)
- The method does not pass a system_prompt with tool-use instructions yet

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f_t2_analisar_tool_use.py -v
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, ResultadoExecucao, EtapaProcessamento
from document_generators import STAGE_OUTPUT_FORMATS, OutputFormat


# ============================================================
# HELPERS
# ============================================================

def _make_executor_with_mocks():
    """Build a PipelineExecutor instance with mocked storage and prompt_manager.

    Uses __new__ to skip __init__ so no real DB connections are made.
    Storage and prompt_manager are replaced with MagicMocks.
    """
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None

    # Make storage return sensible defaults
    doc = MagicMock()
    doc.id = "doc-analisar-001"
    executor.storage.salvar_documento.return_value = doc
    executor.storage.listar_documentos.return_value = []

    # Make get_atividade return a minimal atividade mock
    atividade = MagicMock()
    atividade.turma_id = "turma-001"
    atividade.id = "atividade-001"
    executor.storage.get_atividade.return_value = atividade

    # Make get_turma return a minimal turma mock
    turma = MagicMock()
    turma.materia_id = "materia-001"
    executor.storage.get_turma.return_value = turma

    # Make get_materia return a minimal materia mock
    materia = MagicMock()
    materia.id = "materia-001"
    materia.nome = "Matematica"
    executor.storage.get_materia.return_value = materia

    # Make prompt_manager return a prompt for ANALISAR_HABILIDADES
    prompt = MagicMock()
    prompt.id = "default_analisar_habilidades"
    prompt.texto = "Analise as habilidades do aluno com base na correcao."
    prompt.texto_sistema = "Voce e um especialista em avaliacao pedagógica."
    executor.prompt_manager.get_prompt_padrao.return_value = prompt
    executor.prompt_manager.get_prompt.return_value = prompt

    # Mock _preparar_contexto_json to return a complete context with all
    # pre-requisite documents present. The executor now guards against missing
    # documents (it returns _erro if CORRECAO JSON / EXTRACAO_QUESTOES aren't
    # found) — since this helper fakes storage.listar_documentos as empty,
    # we must bypass the guard by returning a valid context that simulates
    # the prerequisite docs loaded.
    executor._preparar_contexto_json = MagicMock(return_value={
        "questoes_extraidas": '{"questoes": []}',
        "correcoes": '{"nota": 8.5, "questoes": []}',
        "_documentos_carregados": [
            "questoes_extraidas",
            "correcoes",
        ],
    })

    return executor


def _make_successful_tool_result():
    """Build a ResultadoExecucao that represents a successful tool-use run."""
    return ResultadoExecucao(
        sucesso=True,
        etapa="tools",
        resposta_raw='{"habilidades": [], "indicadores": {}, "recomendacoes": []}',
        resposta_parsed={"habilidades": [], "indicadores": {}, "recomendacoes": []},
        tokens_entrada=500,
        tokens_saida=300,
        tempo_ms=2500.0,
        documento_id="doc-analisar-001"
    )


# ============================================================
# TEST 1: ANALISAR_HABILIDADES USES TOOL-USE EXECUTION PATH
# ============================================================

class TestAnalisarHabilidadesUsesToolUseExecutionPath:
    """F-T2a: When ANALISAR_HABILIDADES is executed, it must call executar_com_tools()
    with tools_to_use containing 'create_document' and 'execute_python_code'.

    Currently FAILS because analisar_habilidades() does not exist as a direct method.
    After F-T2, calling executor.analisar_habilidades() must result in
    executar_com_tools() being called exactly once.
    """

    async def test_analisar_habilidades_calls_executar_com_tools(self):
        """analisar_habilidades() must route through executar_com_tools(), not _executar_multimodal().

        After F-T2 implementation, calling executor.analisar_habilidades() must result in
        executar_com_tools() being called exactly once.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        mock_tool_call.assert_called_once(), (
            "analisar_habilidades() must call executar_com_tools() exactly once. "
            "Currently the method does not exist — F-T2 must create it using the "
            "executar_com_tools() path (not executar_etapa() -> _executar_multimodal())."
        )

    async def test_analisar_habilidades_passes_create_document_tool(self):
        """executar_com_tools() called from analisar_habilidades() must receive 'create_document' in tools_to_use.

        The tool-use path requires 'create_document' so the AI can emit structured JSON
        with habilidades, indicadores, and recomendacoes fields.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, (
            "executar_com_tools() was never called — analisar_habilidades() must be "
            "implemented using the tool-use path."
        )
        call_args = mock_tool_call.call_args
        tools = call_args.kwargs.get("tools_to_use")

        assert tools is not None, (
            "executar_com_tools() must receive tools_to_use as a keyword argument. "
            f"Called with args={call_args.args}, kwargs={call_args.kwargs}"
        )
        assert "create_document" in tools, (
            f"tools_to_use must include 'create_document' for structured JSON output. "
            f"Got: {tools!r}"
        )

    async def test_analisar_habilidades_passes_execute_python_code_tool(self):
        """executar_com_tools() called from analisar_habilidades() must receive 'execute_python_code' in tools_to_use.

        The tool-use path requires 'execute_python_code' so the AI can generate a PDF
        via E2B sandbox — replacing the old two-pass narrative PDF.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, (
            "executar_com_tools() was never called."
        )
        call_args = mock_tool_call.call_args
        tools = call_args.kwargs.get("tools_to_use")

        assert tools is not None, (
            "executar_com_tools() must receive tools_to_use as a keyword argument. "
            f"Called with args={call_args.args}, kwargs={call_args.kwargs}"
        )
        assert "execute_python_code" in tools, (
            f"tools_to_use must include 'execute_python_code' for PDF generation via E2B. "
            f"Got: {tools!r}"
        )

    async def test_analisar_habilidades_does_not_call_executar_multimodal(self):
        """After migration, analisar_habilidades() must NOT call _executar_multimodal() anymore.

        _executar_multimodal() is the old single-pass AI call path. After F-T2,
        ANALISAR_HABILIDADES must bypass it entirely.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ):
            with patch.object(
                executor, "_executar_multimodal", new_callable=AsyncMock
            ) as mock_multimodal:
                await executor.analisar_habilidades(
                    atividade_id="atividade-001",
                    aluno_id="aluno-001",
                )

        mock_multimodal.assert_not_called(), (
            "_executar_multimodal() must NOT be called after F-T2 migration. "
            "ANALISAR_HABILIDADES must use the tool-use path instead."
        )

    async def test_analisar_habilidades_accepts_optional_aluno_id(self):
        """analisar_habilidades() must work when aluno_id is None (turma-level analysis).

        The method signature includes aluno_id=None as an optional parameter,
        so calls without aluno_id must succeed without raising.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            # Call without aluno_id — must not raise AttributeError
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
            )

        assert mock_tool_call.called, (
            "analisar_habilidades() must call executar_com_tools() even when aluno_id is omitted."
        )


# ============================================================
# TEST 2: TWO-PASS NARRATIVE NOT CALLED FOR ANALISAR_HABILIDADES
# ============================================================

class TestTwoPassNarrativeNotCalledForAnalisarHabilidades:
    """F-T2b: After migration, _gerar_narrativa_pdf() must NOT be called for ANALISAR_HABILIDADES.

    The two-pass system's second call (_gerar_narrativa_pdf) is replaced by the
    execute_python_code tool within the single executar_com_tools() call.

    Currently FAILS because _salvar_resultado() checks NARRATIVA_PROMPT_MAP
    and ANALISAR_HABILIDADES IS in that map, so it would call _gerar_narrativa_pdf().
    """

    async def test_gerar_narrativa_pdf_not_called_for_analisar_habilidades(self):
        """_gerar_narrativa_pdf() must NOT be invoked when analisar_habilidades() is called.

        After F-T2, the PDF is generated inside executar_com_tools() via the
        execute_python_code tool, so _gerar_narrativa_pdf() is no longer needed
        for ANALISAR_HABILIDADES.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ):
            with patch.object(
                executor, "_gerar_narrativa_pdf", new_callable=AsyncMock
            ) as mock_narrativa:
                await executor.analisar_habilidades(
                    atividade_id="atividade-001",
                    aluno_id="aluno-001",
                )

        mock_narrativa.assert_not_called(), (
            "_gerar_narrativa_pdf() must NOT be called for ANALISAR_HABILIDADES after F-T2. "
            "The PDF is now generated inside executar_com_tools() via execute_python_code tool. "
            "Currently this fails because ANALISAR_HABILIDADES is still in NARRATIVA_PROMPT_MAP."
        )

    async def test_salvar_resultado_does_not_trigger_narrative_for_analisar_habilidades(self):
        """_salvar_resultado() called with ANALISAR_HABILIDADES must skip the narrative PDF path.

        Even if _salvar_resultado() is called directly (not via analisar_habilidades()), it must
        not trigger the two-pass narrative for ANALISAR_HABILIDADES.
        """
        executor = _make_executor_with_mocks()

        with patch.object(
            executor, "_gerar_narrativa_pdf", new_callable=AsyncMock
        ) as mock_narrativa:
            with patch.object(
                executor, "_gerar_formatos_extras", new_callable=AsyncMock
            ):
                await executor._salvar_resultado(
                    etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
                    atividade_id="atividade-001",
                    aluno_id="aluno-001",
                    resposta_raw='{"habilidades": [], "indicadores": {}, "recomendacoes": []}',
                    resposta_parsed={"habilidades": [], "indicadores": {}, "recomendacoes": []},
                    provider="anthropic",
                    modelo="claude-sonnet-4-5-20250929",
                    prompt_id="default_analisar_habilidades",
                    tokens=1500,
                    tempo_ms=3000.0,
                    gerar_formatos_extras=True,
                )

        mock_narrativa.assert_not_called(), (
            "_salvar_resultado() must not call _gerar_narrativa_pdf() for ANALISAR_HABILIDADES "
            "after F-T2 migration. Currently ANALISAR_HABILIDADES is in NARRATIVA_PROMPT_MAP "
            "so _gerar_narrativa_pdf() IS triggered — this is what F-T2 must remove."
        )


# ============================================================
# TEST 3: SYSTEM PROMPT INCLUDES TOOL-USE INSTRUCTIONS
# ============================================================

class TestSystemPromptIncludesToolUseInstructions:
    """F-T2c: The system_prompt passed to executar_com_tools() for ANALISAR_HABILIDADES must
    contain instructions for JSON schema output + PDF generation.

    Currently FAILS because analisar_habilidades() doesn't exist and thus never calls
    executar_com_tools() at all. After F-T2, the system prompt must guide the AI to use
    create_document for structured JSON (habilidades/indicadores/recomendacoes) and
    execute_python_code for PDF generation.
    """

    async def test_system_prompt_is_passed_to_executar_com_tools(self):
        """executar_com_tools() must receive a non-empty system_prompt when called for ANALISAR_HABILIDADES."""
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt")

        assert system_prompt is not None, (
            "executar_com_tools() must receive a system_prompt keyword argument. "
            f"Got kwargs: {call_args.kwargs}"
        )
        assert len(system_prompt.strip()) > 0, (
            "system_prompt must not be empty — it must contain tool-use instructions."
        )

    async def test_system_prompt_mentions_create_document(self):
        """system_prompt passed to executar_com_tools() must mention 'create_document'.

        The AI needs to know to use the create_document tool to emit the structured
        analysis JSON with habilidades, indicadores, and recomendacoes.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        assert "create_document" in system_prompt, (
            f"system_prompt must instruct the AI to use 'create_document' tool. "
            f"Got system_prompt: {system_prompt[:200]!r}"
        )

    async def test_system_prompt_mentions_habilidades_schema_field(self):
        """system_prompt must describe the 'habilidades' JSON schema field.

        The AI needs schema guidance to produce a valid analysis JSON.
        This field is specific to ANALISAR_HABILIDADES and distinguishes it from CORRIGIR.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        assert "habilidades" in system_prompt, (
            f"system_prompt must include 'habilidades' JSON schema field. "
            f"Got system_prompt: {system_prompt[:300]!r}"
        )

    async def test_system_prompt_mentions_indicadores_schema_field(self):
        """system_prompt must describe the 'indicadores' JSON schema field.

        indicadores is one of the three mandatory schema fields for ANALISAR_HABILIDADES
        (alongside habilidades and recomendacoes).
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        assert "indicadores" in system_prompt, (
            f"system_prompt must include 'indicadores' JSON schema field. "
            f"Got system_prompt: {system_prompt[:300]!r}"
        )

    async def test_system_prompt_mentions_recomendacoes_schema_field(self):
        """system_prompt must describe the 'recomendacoes' JSON schema field.

        recomendacoes is one of the three mandatory schema fields for ANALISAR_HABILIDADES.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        recomendacoes_keywords = ["recomendacoes", "recomendações"]
        found = any(kw in system_prompt for kw in recomendacoes_keywords)
        assert found, (
            f"system_prompt must include 'recomendacoes' JSON schema field. "
            f"Got system_prompt: {system_prompt[:300]!r}"
        )

    async def test_system_prompt_mentions_pdf_generation(self):
        """system_prompt passed to executar_com_tools() must mention PDF generation.

        The AI needs instructions to call execute_python_code to produce the PDF
        that replaces the old two-pass narrative PDF.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.analisar_habilidades(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        pdf_keywords = ["pdf", "PDF", "execute_python_code", "relatorio", "relatório", "narrativa"]
        found = any(kw in system_prompt for kw in pdf_keywords)
        assert found, (
            f"system_prompt must include PDF generation instructions. "
            f"Expected one of: {pdf_keywords}. "
            f"Got system_prompt: {system_prompt[:300]!r}"
        )


# ============================================================
# TEST 4: STAGE_OUTPUT_FORMATS HAS ANALISE_HABILIDADES (SANITY CHECK)
# ============================================================

class TestStageOutputFormatsHasAnaliseHabilidades:
    """F-T2d: Sanity check — STAGE_OUTPUT_FORMATS already maps 'analise_habilidades' to JSON+PDF.

    This test should already PASS before implementation (it's a verification that
    the document_generators module is correctly configured).
    """

    def test_analise_habilidades_in_stage_output_formats(self):
        """STAGE_OUTPUT_FORMATS must have an entry for 'analise_habilidades'."""
        assert "analise_habilidades" in STAGE_OUTPUT_FORMATS, (
            f"document_generators.STAGE_OUTPUT_FORMATS must have an 'analise_habilidades' key. "
            f"Available keys: {list(STAGE_OUTPUT_FORMATS.keys())}"
        )

    def test_analise_habilidades_includes_json_format(self):
        """'analise_habilidades' stage must include OutputFormat.JSON."""
        formats = STAGE_OUTPUT_FORMATS.get("analise_habilidades", [])
        assert OutputFormat.JSON in formats, (
            f"STAGE_OUTPUT_FORMATS['analise_habilidades'] must include OutputFormat.JSON. "
            f"Got: {formats!r}"
        )

    def test_analise_habilidades_includes_pdf_format(self):
        """'analise_habilidades' stage must include OutputFormat.PDF."""
        formats = STAGE_OUTPUT_FORMATS.get("analise_habilidades", [])
        assert OutputFormat.PDF in formats, (
            f"STAGE_OUTPUT_FORMATS['analise_habilidades'] must include OutputFormat.PDF. "
            f"Got: {formats!r}"
        )


# ============================================================
# TEST 5: ANALISAR_HABILIDADES NO LONGER IN NARRATIVA_PROMPT_MAP
# ============================================================

class TestAnalisarHabilidadesRemovedFromNarrativaPromptMap:
    """F-T2e: After migration, ANALISAR_HABILIDADES must be removed from NARRATIVA_PROMPT_MAP.

    Currently FAILS because ANALISAR_HABILIDADES IS in the map:
        NARRATIVA_PROMPT_MAP = {
            EtapaProcessamento.ANALISAR_HABILIDADES: "internal_narrativa_analisar_habilidades",  <- must be removed
            EtapaProcessamento.GERAR_RELATORIO: "internal_narrativa_gerar_relatorio",
        }

    Removing it ensures _salvar_resultado() never triggers the two-pass path for ANALISAR_HABILIDADES.
    """

    def test_analisar_habilidades_not_in_narrativa_prompt_map(self):
        """EtapaProcessamento.ANALISAR_HABILIDADES must NOT be a key in PipelineExecutor.NARRATIVA_PROMPT_MAP.

        After F-T2, the two-pass narrative for ANALISAR_HABILIDADES is replaced by executar_com_tools().
        Keeping ANALISAR_HABILIDADES in NARRATIVA_PROMPT_MAP would cause the old second AI call to run
        in parallel, wasting tokens and producing duplicate PDFs.
        """
        assert EtapaProcessamento.ANALISAR_HABILIDADES not in PipelineExecutor.NARRATIVA_PROMPT_MAP, (
            "EtapaProcessamento.ANALISAR_HABILIDADES must be removed from PipelineExecutor.NARRATIVA_PROMPT_MAP "
            "after F-T2 migration. Currently it maps to "
            f"'{PipelineExecutor.NARRATIVA_PROMPT_MAP.get(EtapaProcessamento.ANALISAR_HABILIDADES)}'. "
            "The two-pass narrative PDF for ANALISAR_HABILIDADES is replaced by execute_python_code tool-use."
        )

    def test_gerar_relatorio_still_in_narrativa_prompt_map(self):
        """GERAR_RELATORIO must remain in NARRATIVA_PROMPT_MAP until F-T3 migrates it.

        F-T2 only removes ANALISAR_HABILIDADES. GERAR_RELATORIO stays until F-T3.
        """
        assert EtapaProcessamento.GERAR_RELATORIO in PipelineExecutor.NARRATIVA_PROMPT_MAP, (
            "GERAR_RELATORIO must remain in NARRATIVA_PROMPT_MAP — it is removed by F-T3, not F-T2."
        )

    def test_narrativa_prompt_map_has_one_entry(self):
        """After F-T1+F-T2, only GERAR_RELATORIO remains in NARRATIVA_PROMPT_MAP.

        CORRIGIR was removed in F-T1. ANALISAR_HABILIDADES removed in F-T2.
        GERAR_RELATORIO remains until F-T3.
        """
        current_map = PipelineExecutor.NARRATIVA_PROMPT_MAP
        assert len(current_map) == 1, (
            f"After F-T1+F-T2, NARRATIVA_PROMPT_MAP must have 1 entry. "
            f"Currently has {len(current_map)}: {list(current_map.keys())}"
        )

    def test_corrigir_not_in_narrativa_prompt_map(self):
        """EtapaProcessamento.CORRIGIR must also NOT be in NARRATIVA_PROMPT_MAP (from F-T1).

        This guards against regression — CORRIGIR was already removed in F-T1 and
        must stay removed after F-T2 work.
        """
        assert EtapaProcessamento.CORRIGIR not in PipelineExecutor.NARRATIVA_PROMPT_MAP, (
            "EtapaProcessamento.CORRIGIR must remain removed from NARRATIVA_PROMPT_MAP. "
            "It was migrated to tool-use in F-T1 and must not be re-added."
        )
