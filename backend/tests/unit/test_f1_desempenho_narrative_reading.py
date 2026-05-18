"""
F1-T2 / F1-T3 / F1-T4: Tests for PDF narrative reading in desempenho executor.

Verifies:
- F1-T2: make_pdf_with_text() creates a PDF fixture that fitz can extract text from
- F1-T3: make_pdf_empty() creates a PDF fixture that fitz extracts as empty string
- F1-T4: gerar_relatorio_desempenho_tarefa() uses fitz (not open()) to read PDFs,
         so binary PDFs no longer produce "0 narrativas legíveis"

No live API calls — pure unit tests with local PDF fixtures.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_f1_desempenho_narrative_reading.py -v
"""

import pytest
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import fitz  # PyMuPDF — must be installed (PyMuPDF>=1.25.0 in requirements.txt)


# ============================================================
# Fixture helpers (F1-T2 + F1-T3)
# ============================================================

def make_pdf_with_text(path: Path, text: str) -> Path:
    """Create a minimal PDF with extractable text — F1-T2 fixture."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), text, fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def make_pdf_empty(path: Path) -> Path:
    """Create a PDF with no text content (blank page only) — F1-T3 fixture."""
    doc = fitz.open()
    doc.new_page()
    doc.save(str(path))
    doc.close()
    return path


# ============================================================
# F1-T2: Fixture A — PDF with extractable text
# ============================================================

class TestF1T2FixtureA:
    """F1-T2: make_pdf_with_text must produce a PDF that fitz can read."""

    def test_valid_pdf_yields_text_via_fitz(self, tmp_path):
        """Fixture A yields text when opened with fitz."""
        pdf_path = make_pdf_with_text(tmp_path / "relatorio_a.pdf", "Ana Silva tem bom desempenho.")
        doc = fitz.open(str(pdf_path))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert "desempenho" in text.lower()

    def test_valid_pdf_is_binary_not_text(self, tmp_path):
        """Confirms the bug: open(pdf, 'r', encoding='utf-8') raises an error on real PDFs."""
        pdf_path = make_pdf_with_text(tmp_path / "relatorio_a.pdf", "Ana Silva tem bom desempenho.")
        with pytest.raises((UnicodeDecodeError, ValueError)):
            with open(str(pdf_path), "r", encoding="utf-8") as f:
                f.read()


# ============================================================
# F1-T3: Fixture B — PDF with empty content
# ============================================================

class TestF1T3FixtureB:
    """F1-T3: make_pdf_empty must produce a PDF that fitz extracts as empty string."""

    def test_empty_pdf_extracts_empty_string_via_fitz(self, tmp_path):
        """Fixture B yields empty string when opened with fitz."""
        pdf_path = make_pdf_empty(tmp_path / "relatorio_b.pdf")
        doc = fitz.open(str(pdf_path))
        text = "".join(page.get_text() for page in doc)
        doc.close()
        assert text.strip() == ""


# ============================================================
# Shared mock fixture for executor tests
# ============================================================

@pytest.fixture
def executor_mocked():
    """PipelineExecutor with fully mocked dependencies — no DB, no LLM."""
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = MagicMock()
    executor.prompt_manager = MagicMock()
    executor.preparador = None
    executor.executar_com_tools = AsyncMock()
    executor._salvar_resultado = AsyncMock()
    return executor


def _setup_context_mocks(executor_mocked):
    """Set up storage context mocks (atividade, turma, materia, prompt)."""
    atividade = MagicMock(nome="Prova 1", turma_id="turma_1")
    turma = MagicMock(materia_id="materia_1")
    materia = MagicMock(id="materia_1", nome="Matemática")
    executor_mocked.storage.get_atividade.return_value = atividade
    executor_mocked.storage.get_turma.return_value = turma
    executor_mocked.storage.get_materia.return_value = materia

    prompt_mock = MagicMock()
    prompt_mock.id = "prompt_123"
    prompt_mock.render.return_value = "prompt text"
    prompt_mock.render_sistema.return_value = None
    executor_mocked.prompt_manager.get_prompt_padrao.return_value = prompt_mock

    llm_result = MagicMock(
        sucesso=True,
        resposta_raw="relatório gerado",
        provider="anthropic",
        modelo="claude",
        tokens_entrada=100,
        tokens_saida=200,
        tempo_ms=1000,
        alertas=[],
        erro=None,
    )
    executor_mocked.executar_com_tools.return_value = llm_result


# ============================================================
# F1-T4: Executor reads PDF narratives using fitz
# ============================================================

class TestF1T4ExecutorReadsPDFNarratives:
    """F1-T4: gerar_relatorio_desempenho_tarefa must use fitz, not open(), to read PDFs."""

    @pytest.mark.asyncio
    async def test_two_valid_pdfs_produce_two_conteudos(self, tmp_path, executor_mocked):
        """When two RELATORIO_FINAL docs are valid PDFs, executor populates conteudos and succeeds."""
        pdf1 = make_pdf_with_text(tmp_path / "doc1.pdf", "Ana Silva tem ótimo desempenho na prova.")
        pdf2 = make_pdf_with_text(tmp_path / "doc2.pdf", "Bruno Santos precisa melhorar nos cálculos.")

        doc1 = MagicMock(aluno_id="aluno_1")
        doc2 = MagicMock(aluno_id="aluno_2")
        executor_mocked.storage.listar_documentos.return_value = [doc1, doc2]
        executor_mocked.storage.resolver_caminho_documento.side_effect = [pdf1, pdf2]
        _setup_context_mocks(executor_mocked)

        result = await executor_mocked.gerar_relatorio_desempenho_tarefa("atividade_123")

        # F1-T4 GREEN: executor extracts narratives → succeeds
        assert result["sucesso"] is True, (
            f"Expected sucesso=True but got: {result}. "
            "Executor is still using open() on binary PDFs instead of fitz."
        )
        assert result["alunos_incluidos"] == 2
        assert result["alunos_excluidos"] == 0

    @pytest.mark.asyncio
    async def test_empty_pdf_counted_as_missing_not_crash(self, tmp_path, executor_mocked):
        """Empty PDF (no text) → counted as missing (avisos), not crash. 1 valid + 1 empty fails threshold."""
        pdf_valid = make_pdf_with_text(tmp_path / "doc1.pdf", "Ana Silva tem bom desempenho.")
        pdf_empty = make_pdf_empty(tmp_path / "doc2.pdf")

        doc1 = MagicMock(aluno_id="aluno_1")
        doc2 = MagicMock(aluno_id="aluno_2")
        executor_mocked.storage.listar_documentos.return_value = [doc1, doc2]
        executor_mocked.storage.resolver_caminho_documento.side_effect = [pdf_valid, pdf_empty]
        _setup_context_mocks(executor_mocked)

        result = await executor_mocked.gerar_relatorio_desempenho_tarefa("atividade_123")

        # 1 valid + 1 empty = 1 conteudo < 2 → fails threshold, but gracefully
        assert result["sucesso"] is False
        assert "1" in result["erro"], (
            f"Expected error about '1' readable narrative, got: {result['erro']}. "
            "After fix, empty PDFs should be counted as missing (not as a valid narrative)."
        )

    @pytest.mark.asyncio
    async def test_tarefa_uses_one_latest_legible_report_per_student(self, tmp_path, executor_mocked):
        """Historical RELATORIO_FINAL versions must not be counted as extra students."""
        pdf_ana_old = make_pdf_with_text(tmp_path / "ana_old.pdf", "Versao antiga da Ana.")
        pdf_ana_new = make_pdf_with_text(tmp_path / "ana_new.pdf", "Versao nova da Ana.")
        pdf_bruno = make_pdf_with_text(tmp_path / "bruno.pdf", "Relatorio do Bruno.")

        doc_ana_old = SimpleNamespace(
            id="ana-old",
            aluno_id="aluno_1",
            criado_em=datetime(2026, 5, 18, 10, 0, 0),
        )
        doc_ana_new = SimpleNamespace(
            id="ana-new",
            aluno_id="aluno_1",
            criado_em=datetime(2026, 5, 18, 11, 0, 0),
        )
        doc_bruno = SimpleNamespace(
            id="bruno",
            aluno_id="aluno_2",
            criado_em=datetime(2026, 5, 18, 9, 0, 0),
        )
        paths = {
            "ana-old": pdf_ana_old,
            "ana-new": pdf_ana_new,
            "bruno": pdf_bruno,
        }

        executor_mocked.storage.listar_documentos.return_value = [
            doc_ana_old,
            doc_bruno,
            doc_ana_new,
        ]
        executor_mocked.storage.resolver_caminho_documento.side_effect = (
            lambda doc: paths[doc.id]
        )
        _setup_context_mocks(executor_mocked)
        executor_mocked.storage.listar_alunos.return_value = [
            SimpleNamespace(id="aluno_1", nome="Ana"),
            SimpleNamespace(id="aluno_2", nome="Bruno"),
        ]

        result = await executor_mocked.gerar_relatorio_desempenho_tarefa("atividade_123")

        assert result["sucesso"] is True
        assert result["total_alunos"] == 2
        assert result["alunos_incluidos"] == 2
        assert result["alunos_excluidos"] == 0
        variaveis = executor_mocked.prompt_manager.get_prompt_padrao.return_value.render.call_args.kwargs
        assert variaveis["total_alunos"] == "2"
        assert variaveis["alunos_incluidos"] == "2"
        assert "Versao nova da Ana" in variaveis["relatorios_narrativos"]
        assert "Versao antiga da Ana" not in variaveis["relatorios_narrativos"]

    @pytest.mark.asyncio
    async def test_tarefa_records_unreadable_latest_before_using_older_report(self, tmp_path, executor_mocked):
        """If newest report is broken, using an older legible version must be visible."""
        broken = tmp_path / "ana_new_broken.pdf"
        broken.write_text("not a pdf", encoding="utf-8")
        pdf_ana_old = make_pdf_with_text(tmp_path / "ana_old.pdf", "Ana legivel antiga.")
        pdf_bruno = make_pdf_with_text(tmp_path / "bruno.pdf", "Bruno legivel.")

        doc_ana_new = SimpleNamespace(
            id="ana-new-broken",
            aluno_id="aluno_1",
            criado_em=datetime(2026, 5, 18, 11, 0, 0),
        )
        doc_ana_old = SimpleNamespace(
            id="ana-old",
            aluno_id="aluno_1",
            criado_em=datetime(2026, 5, 18, 10, 0, 0),
        )
        doc_bruno = SimpleNamespace(
            id="bruno",
            aluno_id="aluno_2",
            criado_em=datetime(2026, 5, 18, 9, 0, 0),
        )
        paths = {
            "ana-new-broken": broken,
            "ana-old": pdf_ana_old,
            "bruno": pdf_bruno,
        }

        executor_mocked.storage.listar_documentos.return_value = [
            doc_ana_old,
            doc_bruno,
            doc_ana_new,
        ]
        executor_mocked.storage.resolver_caminho_documento.side_effect = (
            lambda doc: paths[doc.id]
        )
        _setup_context_mocks(executor_mocked)
        executor_mocked.storage.listar_alunos.return_value = [
            SimpleNamespace(id="aluno_1", nome="Ana"),
            SimpleNamespace(id="aluno_2", nome="Bruno"),
        ]

        result = await executor_mocked.gerar_relatorio_desempenho_tarefa("atividade_123")

        assert result["sucesso"] is True
        assert result["status"] == "PARCIAL"
        assert result["alunos_incluidos"] == 2
        assert any(
            aviso.get("documento_id") == "ana-new-broken"
            and "ilegível" in aviso.get("motivo", "")
            for aviso in result["avisos"]
        )

    @pytest.mark.asyncio
    async def test_tarefa_ignores_newer_non_pdf_versions_when_pdf_exists(self, tmp_path, executor_mocked):
        """JSON/MD versions of RELATORIO_FINAL must not make a valid PDF narrative partial."""
        pdf_ana = make_pdf_with_text(tmp_path / "ana.pdf", "Ana legivel em PDF.")
        pdf_bruno = make_pdf_with_text(tmp_path / "bruno.pdf", "Bruno legivel em PDF.")
        json_ana = tmp_path / "ana.json"
        json_ana.write_text('{"resumo": "versao json"}', encoding="utf-8")

        doc_ana_json = SimpleNamespace(
            id="ana-json",
            aluno_id="aluno_1",
            extensao=".json",
            criado_em=datetime(2026, 5, 18, 12, 0, 0),
        )
        doc_ana_pdf = SimpleNamespace(
            id="ana-pdf",
            aluno_id="aluno_1",
            extensao=".pdf",
            criado_em=datetime(2026, 5, 18, 11, 0, 0),
        )
        doc_bruno_pdf = SimpleNamespace(
            id="bruno-pdf",
            aluno_id="aluno_2",
            extensao=".pdf",
            criado_em=datetime(2026, 5, 18, 10, 0, 0),
        )
        paths = {
            "ana-json": json_ana,
            "ana-pdf": pdf_ana,
            "bruno-pdf": pdf_bruno,
        }

        executor_mocked.storage.listar_documentos.return_value = [
            doc_ana_json,
            doc_ana_pdf,
            doc_bruno_pdf,
        ]
        executor_mocked.storage.resolver_caminho_documento.side_effect = (
            lambda doc: paths[doc.id]
        )
        _setup_context_mocks(executor_mocked)
        executor_mocked.storage.listar_alunos.return_value = [
            SimpleNamespace(id="aluno_1", nome="Ana"),
            SimpleNamespace(id="aluno_2", nome="Bruno"),
        ]

        result = await executor_mocked.gerar_relatorio_desempenho_tarefa("atividade_123")

        assert result["sucesso"] is True
        assert result["status"] == "COMPLETO"
        assert result["avisos"] == []
        variaveis = executor_mocked.prompt_manager.get_prompt_padrao.return_value.render.call_args.kwargs
        assert "Ana legivel em PDF" in variaveis["relatorios_narrativos"]
        assert "versao json" not in variaveis["relatorios_narrativos"]
