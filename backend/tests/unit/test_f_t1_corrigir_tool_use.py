"""
Test F-T1: Migrate CORRIGIR to tool-use dual output.

Tests that the CORRIGIR pipeline stage has been migrated FROM the two-pass system
(AI call → JSON, then separate AI call → narrative PDF) TO a single
executar_com_tools() call with tools_to_use=["create_document", "execute_python_code"].

What each test verifies:
1. CORRIGIR uses tool-use execution path — executar_com_tools() is called with the
   correct tools when CORRIGIR is invoked (not _executar_multimodal()).
2. Two-pass narrative NOT called for CORRIGIR — _gerar_narrativa_pdf() must NOT be
   invoked for CORRIGIR after the migration.
3. System prompt includes tool-use instructions — the system_prompt passed to
   executar_com_tools() contains JSON schema + PDF generation instructions.
4. STAGE_OUTPUT_FORMATS has correcao — sanity check that document_generators already
   maps "correcao" to [JSON, PDF] (this should already pass).
5. CORRIGIR no longer in NARRATIVA_PROMPT_MAP — after migration, CORRIGIR must be
   removed from the two-pass map.

All tests 1-3 and 5 MUST FAIL before implementation because:
- CORRIGIR currently calls _executar_multimodal(), not executar_com_tools()
- CORRIGIR IS in NARRATIVA_PROMPT_MAP (two-pass still active)
- The system prompt does NOT include tool-use instructions yet

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f_t1_corrigir_tool_use.py -v
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, call

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
    doc.id = "doc-corrigir-001"
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
    materia.nome = "Matemática"
    executor.storage.get_materia.return_value = materia

    # Make prompt_manager return a prompt for CORRIGIR
    prompt = MagicMock()
    prompt.id = "default_corrigir"
    prompt.texto = "Corrija a prova do aluno com base no gabarito."
    prompt.texto_sistema = "Você é um corretor especializado."
    executor.prompt_manager.get_prompt_padrao.return_value = prompt
    executor.prompt_manager.get_prompt.return_value = prompt

    return executor


def _make_successful_tool_result():
    """Build a ResultadoExecucao that represents a successful tool-use run."""
    return ResultadoExecucao(
        sucesso=True,
        etapa="tools",
        resposta_raw='{"nota": 8.5, "questoes": []}',
        resposta_parsed={"nota": 8.5, "questoes": []},
        tokens_entrada=500,
        tokens_saida=300,
        tempo_ms=2500.0,
        documento_id="doc-corrigir-001"
    )


# ============================================================
# TEST 1: CORRIGIR USES TOOL-USE EXECUTION PATH
# ============================================================

class TestCorrigirUsesToolUseExecutionPath:
    """F-T1a: When CORRIGIR is executed, it must call executar_com_tools()
    with tools_to_use containing 'create_document' and 'execute_python_code'.

    Currently FAILS because corrigir() calls executar_etapa() → _executar_multimodal()
    and executar_com_tools() is never invoked.
    """

    async def test_corrigir_calls_executar_com_tools(self):
        """corrigir() must route through executar_com_tools(), not _executar_multimodal().

        After F-T1 implementation, calling executor.corrigir() must result in
        executar_com_tools() being called exactly once.
        """
        executor = _make_executor_with_mocks()

        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.corrigir(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        mock_tool_call.assert_called_once(), (
            "corrigir() must call executar_com_tools() exactly once. "
            "Currently it calls executar_etapa() → _executar_multimodal() instead — "
            "this is the two-pass path that F-T1 must replace."
        )

    async def test_corrigir_passes_create_document_tool(self):
        """executar_com_tools() called from corrigir() must receive 'create_document' in tools_to_use.

        The tool-use path requires 'create_document' so the AI can emit structured JSON.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.corrigir(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, (
            "executar_com_tools() was never called — corrigir() must be migrated to tool-use path."
        )
        _, kwargs = mock_tool_call.call_args
        tools_to_use = kwargs.get("tools_to_use") or (
            mock_tool_call.call_args.args[6] if len(mock_tool_call.call_args.args) > 6 else None
        )
        # Try positional args too since call signature varies
        call_args = mock_tool_call.call_args
        # Extract tools_to_use from keyword or positional arguments
        tools = call_args.kwargs.get("tools_to_use")
        if tools is None and len(call_args.args) > 0:
            # Find it in positional args (7th positional based on signature)
            pass

        assert tools is not None, (
            "executar_com_tools() must receive tools_to_use as a keyword argument. "
            f"Called with args={call_args.args}, kwargs={call_args.kwargs}"
        )
        assert "create_document" in tools, (
            f"tools_to_use must include 'create_document' for structured JSON output. "
            f"Got: {tools!r}"
        )

    async def test_corrigir_passes_execute_python_code_tool(self):
        """executar_com_tools() called from corrigir() must receive 'execute_python_code' in tools_to_use.

        The tool-use path requires 'execute_python_code' so the AI can generate a PDF
        via E2B sandbox — replacing the old two-pass narrative PDF.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.corrigir(
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

    async def test_corrigir_does_not_call_executar_multimodal(self):
        """After migration, corrigir() must NOT call _executar_multimodal() anymore.

        _executar_multimodal() is the old single-pass AI call path. After F-T1,
        CORRIGIR must bypass it entirely.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ):
            with patch.object(
                executor, "_executar_multimodal", new_callable=AsyncMock
            ) as mock_multimodal:
                await executor.corrigir(
                    atividade_id="atividade-001",
                    aluno_id="aluno-001",
                )

        mock_multimodal.assert_not_called(), (
            "_executar_multimodal() must NOT be called after F-T1 migration. "
            "CORRIGIR must use the tool-use path instead."
        )


# ============================================================
# TEST 2: TWO-PASS NARRATIVE NOT CALLED FOR CORRIGIR
# ============================================================

class TestTwoPassNarrativeNotCalledForCorrigir:
    """F-T1b: After migration, _gerar_narrativa_pdf() must NOT be called for CORRIGIR.

    The two-pass system's second call (_gerar_narrativa_pdf) is replaced by the
    execute_python_code tool within the single executar_com_tools() call.

    Currently FAILS because _salvar_resultado() still checks NARRATIVA_PROMPT_MAP
    and CORRIGIR IS in that map, so it calls _gerar_narrativa_pdf().
    """

    async def test_gerar_narrativa_pdf_not_called_for_corrigir(self):
        """_gerar_narrativa_pdf() must NOT be invoked when corrigir() is called.

        After F-T1, the PDF is generated inside executar_com_tools() via the
        execute_python_code tool, so _gerar_narrativa_pdf() is no longer needed
        for CORRIGIR.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ):
            with patch.object(
                executor, "_gerar_narrativa_pdf", new_callable=AsyncMock
            ) as mock_narrativa:
                await executor.corrigir(
                    atividade_id="atividade-001",
                    aluno_id="aluno-001",
                )

        mock_narrativa.assert_not_called(), (
            "_gerar_narrativa_pdf() must NOT be called for CORRIGIR after F-T1. "
            "The PDF is now generated inside executar_com_tools() via execute_python_code tool. "
            "Currently this fails because CORRIGIR is still in NARRATIVA_PROMPT_MAP."
        )

    async def test_salvar_resultado_does_not_trigger_narrative_for_corrigir(self):
        """_salvar_resultado() called with CORRIGIR must skip the narrative PDF path.

        Even if _salvar_resultado() is called directly (not via corrigir()), it must
        not trigger the two-pass narrative for CORRIGIR.
        """
        executor = _make_executor_with_mocks()

        with patch.object(
            executor, "_gerar_narrativa_pdf", new_callable=AsyncMock
        ) as mock_narrativa:
            with patch.object(
                executor, "_gerar_formatos_extras", new_callable=AsyncMock
            ):
                await executor._salvar_resultado(
                    etapa=EtapaProcessamento.CORRIGIR,
                    atividade_id="atividade-001",
                    aluno_id="aluno-001",
                    resposta_raw='{"nota": 8.5, "questoes": []}',
                    resposta_parsed={"nota": 8.5, "questoes": []},
                    provider="anthropic",
                    modelo="claude-sonnet-4-5-20250929",
                    prompt_id="default_corrigir",
                    tokens=1500,
                    tempo_ms=3000.0,
                    gerar_formatos_extras=True,
                )

        mock_narrativa.assert_not_called(), (
            "_salvar_resultado() must not call _gerar_narrativa_pdf() for CORRIGIR "
            "after F-T1 migration. Currently CORRIGIR is in NARRATIVA_PROMPT_MAP "
            "so _gerar_narrativa_pdf() IS triggered — this is what F-T1 must remove."
        )


# ============================================================
# TEST 3: SYSTEM PROMPT INCLUDES TOOL-USE INSTRUCTIONS
# ============================================================

class TestSystemPromptIncludesToolUseInstructions:
    """F-T1c: The system_prompt passed to executar_com_tools() for CORRIGIR must
    contain instructions for JSON schema output + PDF generation.

    Currently FAILS because corrigir() doesn't call executar_com_tools() at all.
    After F-T1, the system prompt must guide the AI to use create_document for
    structured JSON and execute_python_code for PDF generation.
    """

    async def test_system_prompt_is_passed_to_executar_com_tools(self):
        """executar_com_tools() must receive a non-empty system_prompt when called for CORRIGIR."""
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.corrigir(
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
        correction JSON.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.corrigir(
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

    async def test_system_prompt_mentions_json_schema(self):
        """system_prompt passed to executar_com_tools() must describe the expected JSON schema.

        The AI needs schema guidance to produce a valid correction JSON that downstream
        consumers can parse.
        """
        executor = _make_executor_with_mocks()
        tool_result = _make_successful_tool_result()

        with patch.object(
            executor, "executar_com_tools", new_callable=AsyncMock, return_value=tool_result
        ) as mock_tool_call:
            await executor.corrigir(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        # The system prompt must reference the JSON output structure
        json_keywords = ["json", "JSON", "schema", "nota", "questoes"]
        found = any(kw in system_prompt for kw in json_keywords)
        assert found, (
            f"system_prompt must include JSON schema instructions (json/schema/nota/questoes). "
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
            await executor.corrigir(
                atividade_id="atividade-001",
                aluno_id="aluno-001",
            )

        assert mock_tool_call.called, "executar_com_tools() was never called."
        call_args = mock_tool_call.call_args
        system_prompt = call_args.kwargs.get("system_prompt", "")

        pdf_keywords = ["pdf", "PDF", "execute_python_code", "relatório", "relatorio", "narrativa"]
        found = any(kw in system_prompt for kw in pdf_keywords)
        assert found, (
            f"system_prompt must include PDF generation instructions. "
            f"Expected one of: {pdf_keywords}. "
            f"Got system_prompt: {system_prompt[:300]!r}"
        )


# ============================================================
# TEST 4: STAGE_OUTPUT_FORMATS HAS CORRECAO (SANITY CHECK)
# ============================================================

class TestStageOutputFormatsHasCorrecao:
    """F-T1d: Sanity check — STAGE_OUTPUT_FORMATS already maps 'correcao' to JSON+PDF.

    This test should already PASS before implementation (it's a verification that
    the document_generators module is correctly configured).
    """

    def test_correcao_in_stage_output_formats(self):
        """STAGE_OUTPUT_FORMATS must have an entry for 'correcao'."""
        assert "correcao" in STAGE_OUTPUT_FORMATS, (
            f"document_generators.STAGE_OUTPUT_FORMATS must have a 'correcao' key. "
            f"Available keys: {list(STAGE_OUTPUT_FORMATS.keys())}"
        )

    def test_correcao_includes_json_format(self):
        """'correcao' stage must include OutputFormat.JSON."""
        formats = STAGE_OUTPUT_FORMATS.get("correcao", [])
        assert OutputFormat.JSON in formats, (
            f"STAGE_OUTPUT_FORMATS['correcao'] must include OutputFormat.JSON. "
            f"Got: {formats!r}"
        )

    def test_correcao_includes_pdf_format(self):
        """'correcao' stage must include OutputFormat.PDF."""
        formats = STAGE_OUTPUT_FORMATS.get("correcao", [])
        assert OutputFormat.PDF in formats, (
            f"STAGE_OUTPUT_FORMATS['correcao'] must include OutputFormat.PDF. "
            f"Got: {formats!r}"
        )


# ============================================================
# TEST 5: CORRIGIR NO LONGER IN NARRATIVA_PROMPT_MAP
# ============================================================

class TestCorrigirRemovedFromNarrativaPromptMap:
    """F-T1e: After migration, CORRIGIR must be removed from NARRATIVA_PROMPT_MAP.

    Currently FAILS because CORRIGIR IS in the map:
        NARRATIVA_PROMPT_MAP = {
            EtapaProcessamento.CORRIGIR: "internal_narrativa_corrigir",  ← must be removed
            ...
        }

    Removing it ensures _salvar_resultado() never triggers the two-pass path for CORRIGIR.
    """

    def test_corrigir_not_in_narrativa_prompt_map(self):
        """EtapaProcessamento.CORRIGIR must NOT be a key in PipelineExecutor.NARRATIVA_PROMPT_MAP.

        After F-T1, the two-pass narrative for CORRIGIR is replaced by executar_com_tools().
        Keeping CORRIGIR in NARRATIVA_PROMPT_MAP would cause the old second AI call to run
        in parallel, wasting tokens and producing duplicate PDFs.
        """
        assert EtapaProcessamento.CORRIGIR not in PipelineExecutor.NARRATIVA_PROMPT_MAP, (
            "EtapaProcessamento.CORRIGIR must be removed from PipelineExecutor.NARRATIVA_PROMPT_MAP "
            "after F-T1 migration. Currently it maps to "
            f"'{PipelineExecutor.NARRATIVA_PROMPT_MAP.get(EtapaProcessamento.CORRIGIR)}'. "
            "The two-pass narrative PDF for CORRIGIR is replaced by execute_python_code tool-use."
        )

    def test_gerar_relatorio_removed_from_narrativa_prompt_map(self):
        """GERAR_RELATORIO removed by F-T3 — tool-use replaces two-pass narrative."""
        assert EtapaProcessamento.GERAR_RELATORIO not in PipelineExecutor.NARRATIVA_PROMPT_MAP, (
            "GERAR_RELATORIO must be removed from NARRATIVA_PROMPT_MAP (F-T3 complete)."
        )

    def test_narrativa_prompt_map_empty_after_f_t1_f_t2_f_t3(self):
        """After F-T1+F-T2+F-T3, all analytical stages migrated — map must be empty."""
        current_map = PipelineExecutor.NARRATIVA_PROMPT_MAP
        assert len(current_map) == 0, (
            f"After F-T1+F-T2+F-T3, NARRATIVA_PROMPT_MAP must be empty. "
            f"Currently has {len(current_map)}: {list(current_map.keys())}"
        )
