"""Guards for PDF-quality instructions in analytical tool-use stages."""

from types import SimpleNamespace
import json

import fitz
import pytest

from executor import PipelineExecutor, PDF_SANDBOX_RULES, STAGE_TOOL_INSTRUCTIONS
from models import TipoDocumento
from prompts import EtapaProcessamento, PROMPTS_PADRAO


def test_corrigir_pdf_instructions_forbid_clipped_feedback():
    instructions = STAGE_TOOL_INSTRUCTIONS[EtapaProcessamento.CORRIGIR].lower()

    assert "nao pode cortar" in instructions
    assert "feedback" in instructions
    assert "word-wrap" in instructions or "paragraph" in instructions
    assert "texto[:80]" in instructions
    assert "placeholders" in instructions


def test_corrigir_prompt_exposes_header_metadata_to_pdf_generation():
    prompt_text = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR].texto.lower()

    assert "**aluno:** {{nome_aluno}}" in prompt_text
    assert "**matéria:** {{materia}}" in prompt_text
    assert "**atividade:** {{atividade}}" in prompt_text
    assert "nunca use placeholders" in prompt_text


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


def test_core_pdf_instructions_forbid_open_write_and_absolute_paths():
    for etapa in (
        EtapaProcessamento.CORRIGIR,
        EtapaProcessamento.ANALISAR_HABILIDADES,
        EtapaProcessamento.GERAR_RELATORIO,
    ):
        instructions = STAGE_TOOL_INSTRUCTIONS[etapa].lower()

        assert PDF_SANDBOX_RULES.lower() in instructions
        assert "/mnt/data" in instructions
        assert "/tmp" in instructions
        assert "open(..., 'w')" in instructions
        assert "open(..., 'wb')" in instructions
        assert "canvas.canvas" in instructions
        assert "simpledoctemplate" in instructions


@pytest.mark.parametrize(
    "etapa",
    (
        EtapaProcessamento.CORRIGIR,
        EtapaProcessamento.ANALISAR_HABILIDADES,
        EtapaProcessamento.GERAR_RELATORIO,
    ),
)
def test_active_stage_prompts_and_tool_instructions_share_warning_contract(etapa):
    prompt_text = PROMPTS_PADRAO[etapa].texto.lower()
    instructions = STAGE_TOOL_INSTRUCTIONS[etapa].lower()

    for field in ("_avisos_documento", "_avisos_questao"):
        assert field in prompt_text
        assert field in instructions


def test_relatorio_prompt_and_tool_instruction_require_lineage():
    prompt_text = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO].texto.lower()
    instructions = STAGE_TOOL_INSTRUCTIONS[EtapaProcessamento.GERAR_RELATORIO].lower()

    assert "_fontes_utilizadas" in prompt_text
    assert "_fontes_utilizadas" in instructions


def _write_pdf(path, text):
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(fitz.Rect(40, 40, 560, 800), text, fontsize=11)
    pdf.save(str(path))
    pdf.close()


class _FakeStorage:
    def __init__(self, paths):
        self.paths = paths

    def resolver_caminho_documento(self, doc):
        return self.paths[doc.id]


def _doc(doc_id, ext):
    return SimpleNamespace(id=doc_id, extensao=ext, nome_arquivo=f"{doc_id}{ext}")


def _executor_with_paths(paths):
    executor = PipelineExecutor()
    executor.storage = _FakeStorage(paths)
    return executor


def test_pdf_json_consistency_rejects_wrong_correction_grade(tmp_path):
    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3},
                    {"numero": 3, "nota": 0},
                ],
            }
        ),
        encoding="utf-8",
    )
    _write_pdf(
        pdf_path,
        "Nota final: 9.0 / 10.0\n"
        "Questão 1 — Acerto | Nota: 3.0\n"
        "Questão 3 — Erro | Nota: 2.0\n",
    )
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.CORRECAO,
    )

    assert any("nota_final 9.0" in error for error in errors)
    assert any("questão 3" in error and "nota 2.0" in error for error in errors)


def test_pdf_json_consistency_rejects_na_report_grade(tmp_path):
    json_path = tmp_path / "relatorio.json"
    pdf_path = tmp_path / "relatorio.pdf"
    json_path.write_text(json.dumps({"nota_final": 8}), encoding="utf-8")
    _write_pdf(pdf_path, "Relatório\nNota final: N/A\nProficiência geral: 80%\n")
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.RELATORIO_FINAL,
    )

    assert any("nota_final N/A" in error for error in errors)


def test_pdf_json_consistency_accepts_matching_grade_and_question_notes(tmp_path):
    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3},
                    {"numero": 3, "nota": 0},
                ],
            }
        ),
        encoding="utf-8",
    )
    _write_pdf(
        pdf_path,
        "Nota final: 8.0 / 10.0\n"
        "Questão 1 — Acerto | Nota: 3.0\n"
        "Questão 3 — Erro | Nota: 0.0\n",
    )
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.CORRECAO,
    )

    assert errors == []


def test_pdf_json_consistency_rejects_placeholder_correction_header(tmp_path):
    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3},
                    {"numero": 3, "nota": 0},
                ],
            }
        ),
        encoding="utf-8",
    )
    _write_pdf(
        pdf_path,
        "Correção da Avaliação\n"
        "Aluno: — | Matéria: — | Data: —\n"
        "Nota final: 8\n"
        "Questão 1 - Acerto\nNota: 3\n"
        "Questão 3 - Erro\nNota: 0\n",
    )
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.CORRECAO,
    )

    assert any("placeholder no cabeçalho para aluno" in error for error in errors)
    assert any("placeholder no cabeçalho para materia" in error for error in errors)
    assert any("placeholder no cabeçalho para data" in error for error in errors)


def test_pdf_json_consistency_rejects_truncated_correction_feedback(tmp_path):
    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [{"numero": 1, "nota": 3}],
                "feedback_geral": (
                    "Diana demonstrou bom entendimento geral das operações matemáticas. "
                    "Ela resolveu corretamente a maior parte da prova, mas deve praticar "
                    "a conversão de porcentagens para frações decimais e mostrar passos "
                    "intermediários com mais clareza para facilitar a validação."
                ),
            }
        ),
        encoding="utf-8",
    )
    _write_pdf(
        pdf_path,
        "Nota Final: 8.0\nQuestão 1 - Nota: 3.0\n"
        "Feedback Geral:\nDiana demonstrou bom entendimento geral das operações matemáticas. "
        "Ela resolveu corretamente a maior parte",
    )
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.CORRECAO,
    )

    assert any("truncar Feedback Geral" in error for error in errors)
    assert any("sem pontuação final" in error for error in errors)


def test_pdf_json_consistency_accepts_pedagogical_general_opinion_heading(tmp_path):
    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    feedback = (
        "Diana demonstrou um excelente desempenho geral, com domínio sólido em álgebra, "
        "potenciação e geometria. O erro na questão de porcentagem parece ser um deslize "
        "de cálculo ou de aplicação da taxa, visto que as outras competências mais complexas "
        "foram atingidas com sucesso. Recomenda-se revisar a conversão de porcentagem para "
        "valores decimais ou fracionários."
    )
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [{"numero": 1, "nota": 3}],
                "feedback_geral": feedback,
            }
        ),
        encoding="utf-8",
    )
    _write_pdf(
        pdf_path,
        "Nota Final: 8.0\nQuestão 1 - Nota: 3.0\nParecer Pedagógico Geral\n" + feedback,
    )
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.CORRECAO,
    )

    assert errors == []


def test_pdf_json_consistency_accepts_non_truncated_feedback_paraphrase(tmp_path):
    json_path = tmp_path / "correcao.json"
    pdf_path = tmp_path / "correcao.pdf"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {"numero": 1, "nota": 3},
                    {"numero": 2, "nota": 3},
                    {"numero": 3, "nota": 0},
                    {"numero": 4, "nota": 2},
                ],
                "feedback_geral": (
                    "O aluno demonstrou um bom domínio na resolução de equações "
                    "lineares, expressões numéricas com ordem de operações e cálculo "
                    "de área de triângulos. O único ponto a ser revisado é a precisão "
                    "no cálculo de porcentagens, onde um erro aritmético foi identificado. "
                    "Com uma revisão focada nas operações de multiplicação e conversão "
                    "de porcentagens, o desempenho pode ser aprimorado para a excelência."
                ),
            }
        ),
        encoding="utf-8",
    )
    _write_pdf(
        pdf_path,
        "Nota Final: 8.0 / 10.0\n"
        "Questão 1\nNota: 3.0\nQuestão 2\nNota: 3.0\n"
        "Questão 3\nNota: 0.0\nQuestão 4\nNota: 2.0\n"
        "Feedback Geral:\n"
        "Diana, seu desempenho nesta avaliação foi muito bom, demonstrando forte "
        "domínio em equações lineares de primeiro grau, ordem de operações e cálculo "
        "da área de triângulos. Você acertou a maioria das questões com precisão. "
        "O único ponto a ser revisado é o cálculo de porcentagens. Sugiro praticar "
        "mais a conversão e a multiplicação para garantir a exatidão. Continue assim!",
    )
    json_doc = _doc("json", ".json")
    pdf_doc = _doc("pdf", ".pdf")
    executor = _executor_with_paths({"json": json_path, "pdf": pdf_path})

    errors = executor._validar_consistencia_pdf_json_tool_outputs(
        {"create_document": [json_doc], "execute_python_code": [pdf_doc]},
        TipoDocumento.CORRECAO,
    )

    assert errors == []
