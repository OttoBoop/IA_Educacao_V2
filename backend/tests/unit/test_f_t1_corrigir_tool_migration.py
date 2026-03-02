"""
Test F-T1: Migrate CORRIGIR to tool-use dual output

F-T1: Replace two-pass narrative with single executar_com_tools() call,
tools_to_use=["create_document", "execute_python_code"]. Add tool-use
instructions to system prompt for structured JSON schema + PDF creation.

Tests:
- STAGE_TOOLS config has CORRIGIR → dual tools
- CORRIGIR removed from NARRATIVA_PROMPT_MAP (two-pass replaced)
- Tool-use instructions include JSON schema fields for CORRIGIR
- STAGE_OUTPUT_FORMATS has correct entry for correcao

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f_t1_corrigir_tool_migration.py -v
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, EtapaProcessamento


# TEST 1: STAGE_TOOLS configuration for CORRIGIR
class TestCorrigirStageToolsConfig:
    """CORRIGIR must be configured with dual tool-use."""

    def test_stage_tools_dict_exists(self):
        """executor.py must export a STAGE_TOOLS configuration dict."""
        from executor import STAGE_TOOLS
        assert isinstance(STAGE_TOOLS, dict), "STAGE_TOOLS must be a dict"

    def test_corrigir_mapped_to_create_document(self):
        """CORRIGIR must include create_document tool."""
        from executor import STAGE_TOOLS
        tools = STAGE_TOOLS.get(EtapaProcessamento.CORRIGIR, [])
        assert "create_document" in tools

    def test_corrigir_mapped_to_execute_python_code(self):
        """CORRIGIR must include execute_python_code tool."""
        from executor import STAGE_TOOLS
        tools = STAGE_TOOLS.get(EtapaProcessamento.CORRIGIR, [])
        assert "execute_python_code" in tools


# TEST 2: Two-pass narrative removed
class TestCorrigirNarrativeRemoved:
    """CORRIGIR must no longer use two-pass narrative."""

    def test_corrigir_not_in_narrativa_prompt_map(self):
        """CORRIGIR must be removed from NARRATIVA_PROMPT_MAP.
        Tool-use replaces two-pass narrative PDF generation."""
        executor = PipelineExecutor()
        assert EtapaProcessamento.CORRIGIR not in executor.NARRATIVA_PROMPT_MAP, (
            "CORRIGIR must be removed from NARRATIVA_PROMPT_MAP after migration to tool-use."
        )


# TEST 3: Tool-use system prompt instructions
class TestCorrigirToolUseInstructions:
    """Tool-use instructions for CORRIGIR must include JSON schema + PDF guidance."""

    def test_stage_tool_instructions_exists(self):
        """executor.py must export STAGE_TOOL_INSTRUCTIONS dict."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        assert isinstance(STAGE_TOOL_INSTRUCTIONS, dict)

    def test_corrigir_instructions_include_json_schema(self):
        """CORRIGIR instructions must reference key JSON schema fields:
        nota_final/nota, questoes."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.CORRIGIR, "")
        has_nota = "nota" in instructions.lower()
        has_questoes = "questoes" in instructions.lower() or "questoes" in instructions.lower()
        assert has_nota, f"CORRIGIR instructions must reference nota/nota_final. Got: {instructions[:200]}"
        assert has_questoes, f"CORRIGIR instructions must reference questoes. Got: {instructions[:200]}"

    def test_corrigir_instructions_include_pdf_guidance(self):
        """CORRIGIR instructions must include PDF generation guidance (reportlab/execute_python_code)."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.CORRIGIR, "")
        has_pdf = "pdf" in instructions.lower() or "execute_python_code" in instructions
        assert has_pdf, f"CORRIGIR instructions must reference PDF generation"


# TEST 4: STAGE_OUTPUT_FORMATS (should already pass)
class TestCorrigirStageOutputFormats:
    """STAGE_OUTPUT_FORMATS must have correct entry for correcao."""

    def test_stage_output_formats_has_correcao(self):
        """correcao must include JSON and PDF formats."""
        from document_generators import STAGE_OUTPUT_FORMATS, OutputFormat
        formats = STAGE_OUTPUT_FORMATS.get("correcao", [])
        assert OutputFormat.JSON in formats, "correcao must include JSON"
        assert OutputFormat.PDF in formats, "correcao must include PDF"
