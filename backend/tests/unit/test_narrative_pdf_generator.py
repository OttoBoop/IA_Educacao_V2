"""
Tests for narrative_markdown_to_pdf() — converts rich Markdown to styled PDF.

Part of the fix for the narrative pipeline: instead of saving .md files that
professors can't read, convert narrative Markdown to professional PDFs.

Related plan: Fix Narrative Pipeline — Merge Rich Narratives into Existing PDFs
Task: T2
"""

import pytest


class TestNarrativeMarkdownToPdf:
    """
    T2: narrative_markdown_to_pdf() must convert Markdown text to PDF bytes.

    The function receives a Markdown string (from Pass 2 narrative prompt)
    and a title, and returns PDF bytes ready to save to storage.
    """

    def test_returns_bytes(self):
        """Must return bytes, not str or None."""
        from document_generators import narrative_markdown_to_pdf

        result = narrative_markdown_to_pdf(
            md_text="## Análise\n\nO aluno demonstrou domínio parcial.",
            title="Correção Narrativa"
        )
        assert isinstance(result, bytes), (
            f"narrative_markdown_to_pdf must return bytes, got {type(result)}"
        )

    def test_returns_non_empty(self):
        """Must return non-empty bytes (a valid PDF has content)."""
        from document_generators import narrative_markdown_to_pdf

        result = narrative_markdown_to_pdf(
            md_text="## Teste\n\nConteúdo.",
            title="Teste"
        )
        assert len(result) > 0, "PDF bytes must not be empty"

    def test_output_is_valid_pdf(self):
        """PDF bytes must start with the %PDF magic header."""
        from document_generators import narrative_markdown_to_pdf

        result = narrative_markdown_to_pdf(
            md_text="## Questão 1\n\nAluno acertou parcialmente.",
            title="Análise"
        )
        assert result[:5] == b'%PDF-', (
            f"Output does not start with %PDF- header. First 10 bytes: {result[:10]}"
        )

    def test_handles_portuguese_characters(self):
        """Must handle Portuguese accented characters without crashing."""
        from document_generators import narrative_markdown_to_pdf

        md_with_accents = (
            "## Avaliação Pedagógica\n\n"
            "**Análise:** O aluno demonstrou compreensão parcial da equação química.\n\n"
            "- Memorização e ordenação sequencial de conhecimento factual\n"
            "- Identificação de estruturas celulares características\n"
            "- Balanceamento de equações químicas e representação simbólica\n"
            "- Aplicação de conceito abstrato a exemplo prático real\n\n"
            "### Recomendação\n\n"
            "Praticar exercícios de conversão de unidades — o raciocínio está correto."
        )

        result = narrative_markdown_to_pdf(md_with_accents, title="Análise de Habilidades")
        assert isinstance(result, bytes) and len(result) > 100, (
            "Must produce valid PDF with Portuguese characters"
        )

    def test_handles_complex_markdown(self):
        """Must handle headings, bold, bullets, and nested structures."""
        from document_generators import narrative_markdown_to_pdf

        complex_md = (
            "## Visão Geral\n\n"
            "João é um aluno que demonstra **potencial alto** em raciocínio lógico.\n\n"
            "## O que a Prova Revelou\n\n"
            "- **Questão 1:** Aplicou corretamente a lei de Boyle\n"
            "- **Questão 2:** Erro de unidade (atm vs Pa) — não é conceitual\n"
            "- **Questão 3:** Deixou em branco — possível falta de tempo\n\n"
            "### Padrões Identificados\n\n"
            "Os erros são **sistemáticos** no domínio de conversão de unidades.\n\n"
            "## Para João\n\n"
            "Você tem um raciocínio forte. O que falta é atenção às unidades."
        )

        result = narrative_markdown_to_pdf(complex_md, title="Relatório — João Silva")
        assert result[:5] == b'%PDF-', "Complex Markdown must produce valid PDF"

    def test_handles_empty_markdown_gracefully(self):
        """Should not crash on empty Markdown — produce a PDF with just the title."""
        from document_generators import narrative_markdown_to_pdf

        result = narrative_markdown_to_pdf(md_text="", title="Relatório Vazio")
        assert isinstance(result, bytes) and len(result) > 0, (
            "Empty Markdown should still produce a valid PDF (with title)"
        )


class TestNarrativeMarkdownToPdfFallback:
    """
    The fallback function should produce a PDF from JSON data
    when narrative generation fails (Pass 2 error).
    """

    def test_generate_pdf_still_works_for_correcao(self):
        """Existing generate_pdf() must still work for correcao data (fallback path)."""
        from document_generators import generate_pdf

        correcao_data = {
            "nota": 7.5,
            "nota_maxima": 10,
            "questoes": [
                {"numero": 1, "nota": 2.5, "nota_maxima": 2.5, "status": "correta",
                 "feedback": "Resposta correta"},
            ]
        }

        result = generate_pdf(correcao_data, title="Correção", doc_type="correcao")
        assert isinstance(result, bytes) and result[:5] == b'%PDF-', (
            "generate_pdf must still work as fallback for correcao"
        )

    def test_generate_pdf_still_works_for_analise(self):
        """Existing generate_pdf() must still work for analise_habilidades data."""
        from document_generators import generate_pdf

        analise_data = {
            "habilidades": {
                "dominadas": ["Mecânica clássica"],
                "em_desenvolvimento": ["Termodinâmica"],
                "nao_demonstradas": ["Óptica"],
            }
        }

        result = generate_pdf(analise_data, title="Análise", doc_type="analise_habilidades")
        assert isinstance(result, bytes) and result[:5] == b'%PDF-', (
            "generate_pdf must still work as fallback for analise_habilidades"
        )
