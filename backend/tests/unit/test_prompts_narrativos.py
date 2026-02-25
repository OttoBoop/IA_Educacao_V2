"""
Testes para os prompts narrativos reescritos dos stages analíticos.

Verifica que os prompts CORRIGIR, ANALISAR_HABILIDADES e GERAR_RELATORIO
foram reescritos com:
- Sistema prompt (texto_sistema) com papel pedagógico explícito
- Instruções substantivas para análise narrativa profunda
- Renderização correta com todas as variáveis

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Tasks: F3-T2, F4-T2, F5-T2
"""

import re
import pytest


# ============================================================
# F3-T2 — CORRIGIR: prompt reescrito com análise narrativa
# ============================================================

class TestPromptCorrigirReescrito:
    """
    F3-T2: Prompt CORRIGIR deve ter sistema prompt pedagógico e
    instruções substantivas para análise narrativa por questão.

    O prompt reescrito deve ir além de "retorne um JSON" — deve
    instruir o agente sobre COMO analisar o raciocínio do aluno,
    distinguir tipos de erro e avaliar potencial com linguagem
    pedagógica.
    """

    def test_prompt_corrigir_tem_texto_sistema(self):
        """Prompt CORRIGIR deve ter texto_sistema (sistema prompt) definido."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
        assert prompt.texto_sistema is not None, (
            "Prompt CORRIGIR não tem texto_sistema. "
            "O sistema prompt deve estabelecer o papel pedagógico do agente — "
            "sem isso, o modelo não tem contexto para uma análise profunda."
        )
        assert len(prompt.texto_sistema) > 100, (
            "texto_sistema muito curto — deve estabelecer papel pedagógico com contexto. "
            f"Comprimento atual: {len(prompt.texto_sistema) if prompt.texto_sistema else 0}"
        )

    def test_prompt_corrigir_sistema_estabelece_papel_pedagogico(self):
        """Sistema prompt do CORRIGIR deve mencionar contexto pedagógico/educacional."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
        assert prompt.texto_sistema is not None, "texto_sistema é None — rode test_prompt_corrigir_tem_texto_sistema primeiro"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "pedagóg", "educacion", "professor", "docente", "aluno", "aprendizado"
        ]), (
            "Sistema prompt não menciona contexto pedagógico/educacional. "
            "Deve estabelecer o agente como professor ou avaliador pedagógico."
        )

    def test_prompt_corrigir_sistema_menciona_raciocinio(self):
        """Sistema prompt do CORRIGIR deve mencionar análise do raciocínio do aluno."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "raciocín", "pensando", "pensamento", "estratégi", "process"
        ]), (
            "Sistema prompt não menciona análise do raciocínio. "
            "Deve instruir o agente a identificar o que o aluno estava pensando."
        )

    def test_prompt_corrigir_renderiza_sem_vars_soltas(self):
        """Prompt CORRIGIR deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
        rendered = prompt.render(
            questao="Qual é a velocidade da luz no vácuo?",
            resposta_esperada="3 × 10^8 m/s (300.000 km/s)",
            resposta_aluno="300.000 km/h",
            criterios="Aceitar respostas equivalentes em qualquer unidade de velocidade",
            nota_maxima=2.0,
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt CORRIGIR: {vars_soltas}. "
            "O render() deve substituir todas as variáveis antes de enviar ao modelo."
        )

    def test_prompt_corrigir_texto_substantivo(self):
        """Texto principal do prompt CORRIGIR deve ser substantivo (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
        assert len(prompt.texto) > 800, (
            f"Prompt CORRIGIR muito curto ({len(prompt.texto)} chars). "
            "Um prompt pedagógico completo deve ter instruções substantivas — "
            "mínimo 800 caracteres para cobrir todas as dimensões de análise."
        )


# ============================================================
# F4-T2 — ANALISAR_HABILIDADES: prompt reescrito com síntese narrativa
# ============================================================

class TestPromptAnalisarHabilidadesReescrito:
    """
    F4-T2: Prompt ANALISAR_HABILIDADES deve ter sistema prompt que establece
    o papel de analista de padrões de aprendizado — não catalogador de habilidades.

    A diferença crítica: o agente deve ser instruído a identificar PADRÕES,
    não inventariar erros por categoria.
    """

    def test_prompt_analisar_habilidades_tem_texto_sistema(self):
        """Prompt ANALISAR_HABILIDADES deve ter texto_sistema definido."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
        assert prompt.texto_sistema is not None, (
            "Prompt ANALISAR_HABILIDADES não tem texto_sistema. "
            "Sem sistema prompt, o modelo não tem contexto para análise de padrões "
            "— gera checklists em vez de síntese pedagógica."
        )
        assert len(prompt.texto_sistema) > 100, (
            "texto_sistema muito curto — deve estabelecer papel com contexto. "
            f"Comprimento atual: {len(prompt.texto_sistema) if prompt.texto_sistema else 0}"
        )

    def test_prompt_analisar_habilidades_sistema_menciona_padroes(self):
        """Sistema prompt do ANALISAR_HABILIDADES deve mencionar padrões de aprendizado."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "padrão", "padrões", "padroes", "aprendizado", "habilidad", "pedagóg"
        ]), (
            "Sistema prompt não menciona análise de padrões de aprendizado. "
            "Deve instruir o agente a identificar padrões, não inventariar habilidades."
        )

    def test_prompt_analisar_habilidades_sistema_distingue_esforco_conhecimento(self):
        """Sistema prompt deve mencionar distinção entre esforço e conhecimento."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "esforço", "esforco", "conteúdo", "conteudo", "conhecimento", "execução"
        ]), (
            "Sistema prompt não menciona distinção entre esforço e conhecimento. "
            "Esta distinção é fundamental: questão em branco ≠ questão errada."
        )

    def test_prompt_analisar_habilidades_renderiza_sem_vars_soltas(self):
        """Prompt ANALISAR_HABILIDADES deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
        rendered = prompt.render(
            correcoes="[Q1: nota 1.5/2, feedback: raciocínio correto mas erro de unidade]",
            nome_aluno="Maria Silva",
            materia="Física",
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt ANALISAR_HABILIDADES: {vars_soltas}"
        )

    def test_prompt_analisar_habilidades_texto_substantivo(self):
        """Texto principal do prompt ANALISAR_HABILIDADES deve ser substantivo (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
        assert len(prompt.texto) > 800, (
            f"Prompt ANALISAR_HABILIDADES muito curto ({len(prompt.texto)} chars). "
            "Um prompt pedagógico completo deve ter instruções substantivas."
        )


# ============================================================
# F5-T2 — GERAR_RELATORIO: prompt reescrito com narrativa holística
# ============================================================

class TestPromptGerarRelatorioReescrito:
    """
    F5-T2: Prompt GERAR_RELATORIO deve ter sistema prompt que establece
    o papel de autor de relatório pedagógico — não gerador de tabelas.

    O relatório deve começar pelo quadro geral (visão do todo) e afunilar
    nos detalhes, em linguagem que o professor pode mostrar ao aluno.
    """

    def test_prompt_gerar_relatorio_tem_texto_sistema(self):
        """Prompt GERAR_RELATORIO deve ter texto_sistema definido."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
        assert prompt.texto_sistema is not None, (
            "Prompt GERAR_RELATORIO não tem texto_sistema. "
            "Sem sistema prompt, o modelo gera tabelas e checklists em vez de narrativa. "
            "O sistema prompt deve estabelecer o papel de autor de relatório pedagógico."
        )
        assert len(prompt.texto_sistema) > 100, (
            "texto_sistema muito curto — deve estabelecer papel com contexto suficiente. "
            f"Comprimento atual: {len(prompt.texto_sistema) if prompt.texto_sistema else 0}"
        )

    def test_prompt_gerar_relatorio_sistema_menciona_narrativa_holistica(self):
        """Sistema prompt do GERAR_RELATORIO deve mencionar narrativa holística."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "narrativa", "relatório", "relatorio", "holístic", "holistic",
            "professor", "quadro geral", "visão geral"
        ]), (
            "Sistema prompt não menciona narrativa ou relatório holístico. "
            "Deve instruir o agente a escrever narrativa, não tabelas."
        )

    def test_prompt_gerar_relatorio_sistema_instrui_comecar_pelo_todo(self):
        """Sistema prompt deve instruir começar pelo quadro geral antes dos detalhes."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "quadro geral", "visão geral", "todo", "geral", "começ", "início", "inicio"
        ]), (
            "Sistema prompt não instrui a começar pelo quadro geral. "
            "A narrativa holística deve ir do todo para o detalhe."
        )

    def test_prompt_gerar_relatorio_renderiza_sem_vars_soltas(self):
        """Prompt GERAR_RELATORIO deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
        rendered = prompt.render(
            nome_aluno="João Silva",
            materia="Física",
            atividade="Prova 1",
            correcoes="[Q1: 2/2 correto, Q2: 1/2 parcial — erro de unidade]",
            analise_habilidades="Bom domínio de mecânica, lacuna em astronomia",
            nota_final="7.5/10",
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt GERAR_RELATORIO: {vars_soltas}"
        )

    def test_prompt_gerar_relatorio_texto_substantivo(self):
        """Texto principal do prompt GERAR_RELATORIO deve ser substantivo (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
        assert len(prompt.texto) > 800, (
            f"Prompt GERAR_RELATORIO muito curto ({len(prompt.texto)} chars). "
            "Um prompt de relatório holístico deve ter instruções substantivas."
        )
