"""Guards for PDF-quality instructions in analytical tool-use stages."""

from types import SimpleNamespace
import json

import fitz

from executor import PipelineExecutor, PDF_SANDBOX_RULES, STAGE_TOOL_INSTRUCTIONS
from models import TipoDocumento
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
        "Feedback Geral:\nDiana demonstrou bom entendimento nas resoluções diret",
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
