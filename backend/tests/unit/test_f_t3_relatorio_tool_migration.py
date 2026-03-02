"""
Test F-T3: Migrate GERAR_RELATORIO to tool-use dual output

F-T3: Same pattern. JSON schema: resumo_geral, pontos_fortes, areas_melhoria, recomendacoes.
Update STAGE_OUTPUT_FORMATS.

Tests:
- STAGE_TOOLS config has GERAR_RELATORIO → dual tools
- GERAR_RELATORIO removed from NARRATIVA_PROMPT_MAP
- Tool-use instructions include RELATORIO schema fields
- STAGE_OUTPUT_FORMATS has correct entry

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_f_t3_relatorio_tool_migration.py -v
"""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, EtapaProcessamento


class TestRelatorioStageToolsConfig:
    """GERAR_RELATORIO must be configured with dual tool-use."""

    def test_stage_tools_has_relatorio(self):
        """STAGE_TOOLS must include GERAR_RELATORIO."""
        from executor import STAGE_TOOLS
        assert EtapaProcessamento.GERAR_RELATORIO in STAGE_TOOLS

    def test_relatorio_mapped_to_create_document(self):
        """RELATORIO must include create_document tool."""
        from executor import STAGE_TOOLS
        tools = STAGE_TOOLS.get(EtapaProcessamento.GERAR_RELATORIO, [])
        assert "create_document" in tools

    def test_relatorio_mapped_to_execute_python_code(self):
        """RELATORIO must include execute_python_code tool."""
        from executor import STAGE_TOOLS
        tools = STAGE_TOOLS.get(EtapaProcessamento.GERAR_RELATORIO, [])
        assert "execute_python_code" in tools


class TestRelatorioNarrativeRemoved:
    """GERAR_RELATORIO must no longer use two-pass narrative."""

    def test_relatorio_not_in_narrativa_prompt_map(self):
        """GERAR_RELATORIO must be removed from NARRATIVA_PROMPT_MAP."""
        executor = PipelineExecutor()
        assert EtapaProcessamento.GERAR_RELATORIO not in executor.NARRATIVA_PROMPT_MAP, (
            "GERAR_RELATORIO must be removed from NARRATIVA_PROMPT_MAP."
        )


class TestRelatorioToolUseInstructions:
    """Tool-use instructions must include RELATORIO-specific JSON schema."""

    def test_relatorio_instructions_include_resumo_geral(self):
        """Instructions must reference resumo_geral."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.GERAR_RELATORIO, "")
        assert "resumo_geral" in instructions.lower() or "resumo geral" in instructions.lower(), (
            f"RELATORIO instructions must reference 'resumo_geral'. Got: {instructions[:200]}"
        )

    def test_relatorio_instructions_include_pontos_fortes(self):
        """Instructions must reference pontos_fortes."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.GERAR_RELATORIO, "")
        assert "pontos_fortes" in instructions.lower() or "pontos fortes" in instructions.lower(), (
            f"RELATORIO instructions must reference 'pontos_fortes'. Got: {instructions[:200]}"
        )

    def test_relatorio_instructions_include_areas_melhoria(self):
        """Instructions must reference areas_melhoria."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.GERAR_RELATORIO, "")
        assert "areas_melhoria" in instructions.lower() or "áreas de melhoria" in instructions.lower() or "areas de melhoria" in instructions.lower(), (
            f"RELATORIO instructions must reference 'areas_melhoria'. Got: {instructions[:200]}"
        )

    def test_relatorio_instructions_include_recomendacoes(self):
        """Instructions must reference recomendacoes."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.GERAR_RELATORIO, "")
        assert "recomendacoes" in instructions.lower() or "recomendações" in instructions.lower(), (
            f"RELATORIO instructions must reference 'recomendacoes'. Got: {instructions[:200]}"
        )

    def test_relatorio_instructions_include_pdf_guidance(self):
        """Instructions must include PDF generation guidance."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.GERAR_RELATORIO, "")
        has_pdf = "pdf" in instructions.lower() or "execute_python_code" in instructions
        assert has_pdf, "RELATORIO instructions must reference PDF generation"


class TestRelatorioStageOutputFormats:
    """STAGE_OUTPUT_FORMATS must have correct entry."""

    def test_stage_output_formats_has_relatorio_final(self):
        """relatorio_final must include JSON and PDF."""
        from document_generators import STAGE_OUTPUT_FORMATS, OutputFormat
        formats = STAGE_OUTPUT_FORMATS.get("relatorio_final", [])
        assert OutputFormat.JSON in formats
        assert OutputFormat.PDF in formats
