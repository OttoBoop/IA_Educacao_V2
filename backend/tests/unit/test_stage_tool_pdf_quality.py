"""Guards for PDF-quality instructions in analytical tool-use stages."""

from executor import STAGE_TOOL_INSTRUCTIONS
from prompts import EtapaProcessamento


def test_corrigir_pdf_instructions_forbid_clipped_feedback():
    instructions = STAGE_TOOL_INSTRUCTIONS[EtapaProcessamento.CORRIGIR].lower()

    assert "nao pode cortar" in instructions
    assert "feedback" in instructions
    assert "word-wrap" in instructions or "paragraph" in instructions
    assert "texto[:80]" in instructions


def test_analisar_pdf_instructions_forbid_clipped_evidence():
    instructions = STAGE_TOOL_INSTRUCTIONS[EtapaProcessamento.ANALISAR_HABILIDADES].lower()

    assert "nao pode cortar" in instructions
    assert "evidencias" in instructions or "recomendacoes" in instructions
    assert "word-wrap" in instructions or "paragraph" in instructions


def test_relatorio_pdf_instructions_keep_grade_and_proficiency_separate():
    instructions = STAGE_TOOL_INSTRUCTIONS[EtapaProcessamento.GERAR_RELATORIO].lower()

    assert "nota_final" in instructions
    assert "proficiencia_geral" in instructions
    assert "metricas separadas" in instructions
    assert "8/10 (75%)" in instructions
    assert "omita o percentual" in instructions
