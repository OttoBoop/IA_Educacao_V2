"""
Test F-T2: Migrate ANALISAR_HABILIDADES to tool-use dual output

F-T2: Same pattern as F-T1. JSON schema: habilidades[], indicadores, recomendacoes.
Update STAGE_OUTPUT_FORMATS.

Tests:
- STAGE_TOOLS config has ANALISAR_HABILIDADES → dual tools
- ANALISAR_HABILIDADES removed from NARRATIVA_PROMPT_MAP
- Tool-use instructions include ANALISAR schema fields
- STAGE_OUTPUT_FORMATS has correct entry

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f_t2_analisar_tool_migration.py -v
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, EtapaProcessamento


class TestAnalisarStageToolsConfig:
    """ANALISAR_HABILIDADES must be configured with dual tool-use."""

    def test_stage_tools_has_analisar(self):
        """STAGE_TOOLS must include ANALISAR_HABILIDADES."""
        from executor import STAGE_TOOLS
        assert EtapaProcessamento.ANALISAR_HABILIDADES in STAGE_TOOLS

    def test_analisar_mapped_to_create_document(self):
        """ANALISAR must include create_document tool."""
        from executor import STAGE_TOOLS
        tools = STAGE_TOOLS.get(EtapaProcessamento.ANALISAR_HABILIDADES, [])
        assert "create_document" in tools

    def test_analisar_mapped_to_execute_python_code(self):
        """ANALISAR must include execute_python_code tool."""
        from executor import STAGE_TOOLS
        tools = STAGE_TOOLS.get(EtapaProcessamento.ANALISAR_HABILIDADES, [])
        assert "execute_python_code" in tools


class TestAnalisarNarrativeRemoved:
    """ANALISAR_HABILIDADES must no longer use two-pass narrative."""

    def test_analisar_not_in_narrativa_prompt_map(self):
        """ANALISAR_HABILIDADES must be removed from NARRATIVA_PROMPT_MAP."""
        executor = PipelineExecutor()
        assert EtapaProcessamento.ANALISAR_HABILIDADES not in executor.NARRATIVA_PROMPT_MAP, (
            "ANALISAR_HABILIDADES must be removed from NARRATIVA_PROMPT_MAP."
        )


class TestAnalisarToolUseInstructions:
    """Tool-use instructions must include ANALISAR-specific JSON schema."""

    def test_analisar_instructions_include_habilidades(self):
        """Instructions must reference habilidades (skills analysis)."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.ANALISAR_HABILIDADES, "")
        assert "habilidades" in instructions.lower(), (
            f"ANALISAR instructions must reference 'habilidades'. Got: {instructions[:200]}"
        )

    def test_analisar_instructions_include_indicadores(self):
        """Instructions must reference indicadores."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.ANALISAR_HABILIDADES, "")
        assert "indicadores" in instructions.lower(), (
            f"ANALISAR instructions must reference 'indicadores'. Got: {instructions[:200]}"
        )

    def test_analisar_instructions_include_recomendacoes(self):
        """Instructions must reference recomendacoes."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.ANALISAR_HABILIDADES, "")
        assert "recomendacoes" in instructions.lower() or "recomendações" in instructions.lower(), (
            f"ANALISAR instructions must reference 'recomendacoes'. Got: {instructions[:200]}"
        )

    def test_analisar_instructions_include_pdf_guidance(self):
        """Instructions must include PDF generation guidance."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.ANALISAR_HABILIDADES, "")
        has_pdf = "pdf" in instructions.lower() or "execute_python_code" in instructions
        assert has_pdf, "ANALISAR instructions must reference PDF generation"


class TestAnalisarStageOutputFormats:
    """STAGE_OUTPUT_FORMATS must have correct entry."""

    def test_stage_output_formats_has_analise_habilidades(self):
        """analise_habilidades must include JSON and PDF."""
        from document_generators import STAGE_OUTPUT_FORMATS, OutputFormat
        formats = STAGE_OUTPUT_FORMATS.get("analise_habilidades", [])
        assert OutputFormat.JSON in formats
        assert OutputFormat.PDF in formats
