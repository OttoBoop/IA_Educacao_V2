"""
Tests for internal narrative prompts (Pass 2 — Two-Pass Pipeline).

Verifies that the 3 internal narrative prompts exist, have correct structure,
and render template variables correctly.

Related plan: Fix Narrative Pipeline — Merge Rich Narratives into Existing PDFs
Task: T4
"""

import pytest


class TestInternalNarrativePromptsExist:
    """T4: PROMPTS_NARRATIVA_INTERNA must contain 3 internal narrative prompts."""

    def test_corrigir_narrative_prompt_exists(self):
        from prompts import PROMPTS_NARRATIVA_INTERNA
        assert "internal_narrativa_corrigir" in PROMPTS_NARRATIVA_INTERNA

    def test_analisar_habilidades_narrative_prompt_exists(self):
        from prompts import PROMPTS_NARRATIVA_INTERNA
        assert "internal_narrativa_analisar_habilidades" in PROMPTS_NARRATIVA_INTERNA

    def test_gerar_relatorio_narrative_prompt_exists(self):
        from prompts import PROMPTS_NARRATIVA_INTERNA
        assert "internal_narrativa_gerar_relatorio" in PROMPTS_NARRATIVA_INTERNA

    def test_each_prompt_has_sistema_and_texto(self):
        from prompts import PROMPTS_NARRATIVA_INTERNA
        for prompt_id, prompt in PROMPTS_NARRATIVA_INTERNA.items():
            assert "sistema" in prompt, f"{prompt_id} missing 'sistema' key"
            assert "texto" in prompt, f"{prompt_id} missing 'texto' key"
            assert len(prompt["sistema"]) > 100, f"{prompt_id} sistema too short"
            assert len(prompt["texto"]) > 100, f"{prompt_id} texto too short"


class TestNarrativePromptRendering:
    """T4: render_narrativa_prompt() must substitute template variables."""

    def test_render_corrigir_substitutes_all_vars(self):
        from prompts import render_narrativa_prompt

        rendered = render_narrativa_prompt(
            "internal_narrativa_corrigir",
            resultado_json='{"nota": 7.5}',
            nome_aluno="Maria Silva",
            materia="Física"
        )
        assert rendered is not None
        assert "Maria Silva" in rendered["texto"]
        assert "Física" in rendered["texto"]
        assert '{"nota": 7.5}' in rendered["texto"]
        assert "{{resultado_json}}" not in rendered["texto"]
        assert "{{nome_aluno}}" not in rendered["texto"]

    def test_render_analisar_habilidades_substitutes_all_vars(self):
        from prompts import render_narrativa_prompt

        rendered = render_narrativa_prompt(
            "internal_narrativa_analisar_habilidades",
            resultado_json='{"habilidades": {}}',
            nome_aluno="João",
            materia="Matemática"
        )
        assert rendered is not None
        assert "João" in rendered["texto"]
        assert "{{nome_aluno}}" not in rendered["texto"]

    def test_render_gerar_relatorio_substitutes_all_vars(self):
        from prompts import render_narrativa_prompt

        rendered = render_narrativa_prompt(
            "internal_narrativa_gerar_relatorio",
            resultado_json='{"nota_final": 8.0}',
            nome_aluno="Ana",
            materia="Biologia",
            atividade="Prova 2",
            nota_final="8.0"
        )
        assert rendered is not None
        assert "Ana" in rendered["texto"]
        assert "Biologia" in rendered["texto"]
        assert "Prova 2" in rendered["texto"]
        assert "{{nome_aluno}}" not in rendered["texto"]

    def test_render_nonexistent_prompt_returns_none(self):
        from prompts import render_narrativa_prompt

        result = render_narrativa_prompt("nonexistent_prompt")
        assert result is None

    def test_prompts_instruct_markdown_output(self):
        """Internal prompts must instruct Markdown output, NOT JSON."""
        from prompts import PROMPTS_NARRATIVA_INTERNA
        for prompt_id, prompt in PROMPTS_NARRATIVA_INTERNA.items():
            sistema_lower = prompt["sistema"].lower()
            assert "markdown" in sistema_lower, (
                f"{prompt_id} sistema must mention Markdown output format"
            )
            assert "não json" in sistema_lower or "nao json" in sistema_lower, (
                f"{prompt_id} sistema must explicitly say NOT JSON"
            )
