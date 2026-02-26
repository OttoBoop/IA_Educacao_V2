"""
B1/C1/D1: Tests for the three new Relatório de Desempenho prompt entries in PROMPTS_PADRAO.

Tests verify that each new aggregate-level prompt:
- Is registered as a key in PROMPTS_PADRAO
- Has is_padrao=True
- Has texto_sistema with a substantive pedagogical/aggregate-analysis role (> 100 chars)
- Has texto with substantive narrative instructions (> 800 chars)
- Has texto_sistema mentioning desempenho/turma/matéria/aggregate context
- Renders without unsubstituted {{variable}} placeholders

B1 — RELATORIO_DESEMPENHO_TAREFA: aggregate of all students for one atividade.
C1 — RELATORIO_DESEMPENHO_TURMA:  aggregate of all students across all atividades in one turma.
D1 — RELATORIO_DESEMPENHO_MATERIA: aggregate across all turmas for one matéria.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_b1_c1_d1_desempenho_prompts.py -v
"""

import re
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# B1 — RELATORIO_DESEMPENHO_TAREFA
# ============================================================

class TestPromptRelatorioDesempenhoTarefa:
    """
    B1: PROMPTS_PADRAO must contain RELATORIO_DESEMPENHO_TAREFA.

    This prompt produces a qualitative narrative for a single atividade,
    synthesizing individual student narratives into a class-level picture:
    question-by-question breakdown, specific student examples, and
    actionable pedagogical insights — no generic filler.
    """

    def test_b1_key_exists_in_prompts_padrao(self):
        """EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA must be a key in PROMPTS_PADRAO."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        assert EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA in PROMPTS_PADRAO, (
            "PROMPTS_PADRAO must contain a PromptTemplate for RELATORIO_DESEMPENHO_TAREFA. "
            "Add it to prompts.py alongside the other PROMPTS_PADRAO entries."
        )

    def test_b1_is_padrao_true(self):
        """The RELATORIO_DESEMPENHO_TAREFA prompt must have is_padrao=True."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA]
        assert prompt.is_padrao is True, (
            "PromptTemplate for RELATORIO_DESEMPENHO_TAREFA must have is_padrao=True "
            "so it is seeded into the database by _seed_prompts_padrao()."
        )

    def test_b1_has_texto_sistema(self):
        """RELATORIO_DESEMPENHO_TAREFA must have a substantive texto_sistema (> 100 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA]
        assert prompt.texto_sistema is not None, (
            "RELATORIO_DESEMPENHO_TAREFA must have texto_sistema. "
            "Without a system prompt, the model won't adopt an aggregate analysis role."
        )
        assert len(prompt.texto_sistema) > 100, (
            f"texto_sistema too short ({len(prompt.texto_sistema)} chars). "
            "Must establish the agent's role as an aggregate-level analyst."
        )

    def test_b1_texto_sistema_mentions_turma_or_aggregate(self):
        """texto_sistema for TAREFA must reference class-level / aggregate analysis."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA]
        assert prompt.texto_sistema is not None, "texto_sistema is None"
        lower = prompt.texto_sistema.lower()
        assert any(word in lower for word in [
            "turma", "desempenho", "aggregate", "coletivo", "class",
            "alunos", "conjunto", "narrativa", "síntese", "sintese"
        ]), (
            "texto_sistema must mention class-level analysis context. "
            "It should establish the agent as a class-level analyst, not a per-student corrector."
        )

    def test_b1_texto_substantivo(self):
        """Prompt texto for RELATORIO_DESEMPENHO_TAREFA must be substantive (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA]
        assert len(prompt.texto) > 800, (
            f"Prompt texto too short ({len(prompt.texto)} chars). "
            "Must include narrative-over-statistics philosophy, question-by-question breakdown "
            "instructions, and specific example requirements."
        )

    def test_b1_renders_without_leftover_vars(self):
        """RELATORIO_DESEMPENHO_TAREFA must render without unsubstituted {{variable}} placeholders."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA]
        rendered = prompt.render(
            relatorios_narrativos="[Relatório Aluno 1: ...]\n[Relatório Aluno 2: ...]",
            atividade="Prova 1 - Mecânica",
            materia="Física",
            total_alunos=5,
            alunos_incluidos=4,
            alunos_excluidos=1,
        )
        leftover = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not leftover, (
            f"Unsubstituted variables in RELATORIO_DESEMPENHO_TAREFA render: {leftover}. "
            "All {{variable}} placeholders must be substituted by prompt.render()."
        )


# ============================================================
# C1 — RELATORIO_DESEMPENHO_TURMA
# ============================================================

class TestPromptRelatorioDesempenhoTurma:
    """
    C1: PROMPTS_PADRAO must contain RELATORIO_DESEMPENHO_TURMA.

    This prompt produces a holistic narrative for one turma across all its atividades:
    progress over time, persistent problems, class profile, and individual evolution —
    all four dimensions, all narrative, no statistics tables.
    """

    def test_c1_key_exists_in_prompts_padrao(self):
        """EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA must be a key in PROMPTS_PADRAO."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        assert EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA in PROMPTS_PADRAO, (
            "PROMPTS_PADRAO must contain a PromptTemplate for RELATORIO_DESEMPENHO_TURMA. "
            "Add it to prompts.py alongside the other PROMPTS_PADRAO entries."
        )

    def test_c1_is_padrao_true(self):
        """The RELATORIO_DESEMPENHO_TURMA prompt must have is_padrao=True."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA]
        assert prompt.is_padrao is True

    def test_c1_has_texto_sistema(self):
        """RELATORIO_DESEMPENHO_TURMA must have a substantive texto_sistema (> 100 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA]
        assert prompt.texto_sistema is not None, (
            "RELATORIO_DESEMPENHO_TURMA must have texto_sistema. "
            "Without a system prompt, the model won't adopt a turma-level holistic analyst role."
        )
        assert len(prompt.texto_sistema) > 100, (
            f"texto_sistema too short ({len(prompt.texto_sistema)} chars)."
        )

    def test_c1_texto_sistema_mentions_turma_or_holistic(self):
        """texto_sistema for TURMA must reference turma-level or holistic analysis."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA]
        assert prompt.texto_sistema is not None
        lower = prompt.texto_sistema.lower()
        assert any(word in lower for word in [
            "turma", "holístic", "holistico", "holistic", "progrès",
            "progresso", "evolução", "evolucao", "coletivo", "conjunto", "síntese", "sintese"
        ]), (
            "texto_sistema must mention turma-level or holistic analysis. "
            "The agent must be positioned as a class-level narrative analyst."
        )

    def test_c1_texto_substantivo(self):
        """Prompt texto for RELATORIO_DESEMPENHO_TURMA must be substantive (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA]
        assert len(prompt.texto) > 800, (
            f"Prompt texto too short ({len(prompt.texto)} chars). "
            "Must include all four dimensions: progress, persistent problems, class profile, "
            "individual evolution — all narrative."
        )

    def test_c1_renders_without_leftover_vars(self):
        """RELATORIO_DESEMPENHO_TURMA must render without unsubstituted {{variable}} placeholders."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA]
        rendered = prompt.render(
            relatorios_narrativos="[Relatório Aluno 1 Prova 1: ...]\n[Relatório Aluno 1 Prova 2: ...]",
            turma="Turma A 2025",
            materia="Física",
            total_alunos=5,
            atividades_cobertas="Prova 1, Prova 2, Prova 3",
        )
        leftover = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not leftover, (
            f"Unsubstituted variables in RELATORIO_DESEMPENHO_TURMA render: {leftover}."
        )


# ============================================================
# D1 — RELATORIO_DESEMPENHO_MATERIA
# ============================================================

class TestPromptRelatorioDesempenhoMateria:
    """
    D1: PROMPTS_PADRAO must contain RELATORIO_DESEMPENHO_MATERIA.

    This prompt produces a unified narrative comparing all turmas in one matéria:
    cross-turma patterns, curriculum effectiveness evaluation —
    turmas referenced by name, one unified document synthesizing all classes.
    """

    def test_d1_key_exists_in_prompts_padrao(self):
        """EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA must be a key in PROMPTS_PADRAO."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        assert EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA in PROMPTS_PADRAO, (
            "PROMPTS_PADRAO must contain a PromptTemplate for RELATORIO_DESEMPENHO_MATERIA. "
            "Add it to prompts.py alongside the other PROMPTS_PADRAO entries."
        )

    def test_d1_is_padrao_true(self):
        """The RELATORIO_DESEMPENHO_MATERIA prompt must have is_padrao=True."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA]
        assert prompt.is_padrao is True

    def test_d1_has_texto_sistema(self):
        """RELATORIO_DESEMPENHO_MATERIA must have a substantive texto_sistema (> 100 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA]
        assert prompt.texto_sistema is not None, (
            "RELATORIO_DESEMPENHO_MATERIA must have texto_sistema. "
            "Without a system prompt, the model won't adopt a matéria-level cross-class analyst role."
        )
        assert len(prompt.texto_sistema) > 100, (
            f"texto_sistema too short ({len(prompt.texto_sistema)} chars)."
        )

    def test_d1_texto_sistema_mentions_materia_or_cross_turma(self):
        """texto_sistema for MATERIA must reference cross-turma or matéria-level analysis."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA]
        assert prompt.texto_sistema is not None
        lower = prompt.texto_sistema.lower()
        assert any(word in lower for word in [
            "matéria", "materia", "turma", "currículo", "curriculo",
            "disciplina", "cross", "comparativ", "síntese", "sintese", "efetividade"
        ]), (
            "texto_sistema must mention matéria-level or cross-turma analysis. "
            "The agent must be positioned as a curriculum/subject-level analyst."
        )

    def test_d1_texto_substantivo(self):
        """Prompt texto for RELATORIO_DESEMPENHO_MATERIA must be substantive (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA]
        assert len(prompt.texto) > 800, (
            f"Prompt texto too short ({len(prompt.texto)} chars). "
            "Must include cross-turma comparison, curriculum effectiveness analysis, "
            "turmas referenced by name, and narrative philosophy."
        )

    def test_d1_renders_without_leftover_vars(self):
        """RELATORIO_DESEMPENHO_MATERIA must render without unsubstituted {{variable}} placeholders."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        prompt = PROMPTS_PADRAO[EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA]
        rendered = prompt.render(
            relatorios_narrativos="[Relatórios Turma A: ...]\n[Relatórios Turma B: ...]",
            materia="Física",
            turmas="Turma A 2025, Turma B 2025",
            total_turmas=2,
        )
        leftover = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not leftover, (
            f"Unsubstituted variables in RELATORIO_DESEMPENHO_MATERIA render: {leftover}."
        )
