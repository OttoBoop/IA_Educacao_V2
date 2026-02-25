"""
Tests for F6-T1: CHAT_GERAL prompt deve referenciar documentos narrativos.

Verifica que o prompt CHAT_GERAL atualizado menciona explicitamente os documentos
narrativos (análises pedagógicas em Markdown geradas pelos stages analíticos):
- Correção narrativa (narrativa_correcao de CORRIGIR)
- Análise de habilidades narrativa (narrativa_habilidades de ANALISAR_HABILIDADES)
- Relatório narrativo (relatorio_narrativo de GERAR_RELATORIO)

Sem esta atualização, o assistente de chat não sabe que esses documentos existem
e não consegue responder perguntas do professor sobre a análise narrativa.

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Task: F6-T1
"""

import re
import pytest


class TestChatGeralPromptNarrativo:
    """
    F6-T1: Prompt CHAT_GERAL deve referenciar documentos narrativos disponíveis.

    O prompt deve informar ao assistente que, além dos documentos estruturados
    (JSON técnico), existem documentos narrativos em Markdown com análise
    pedagógica profunda. O assistente deve poder citar esses documentos ao
    responder o professor.
    """

    def test_prompt_chat_geral_menciona_documentos_narrativos(self):
        """Prompt CHAT_GERAL deve mencionar explicitamente documentos narrativos."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CHAT_GERAL]
        texto_lower = prompt.texto.lower()

        assert any(word in texto_lower for word in [
            "narrativ",
            "análise pedagógica",
            "analise pedagogica",
            "correcao_narrativa",
            "relatorio_narrativo",
            "analise_habilidades_narrativa",
            "markdown",
        ]), (
            "Prompt CHAT_GERAL não menciona documentos narrativos. "
            "O assistente precisa saber que existem análises pedagógicas em Markdown "
            "para referenciar ao responder perguntas do professor sobre o desempenho do aluno. "
            "Adicione menção aos documentos narrativos gerados pelos stages analíticos."
        )

    def test_prompt_chat_geral_renderiza_sem_vars_soltas(self):
        """Prompt CHAT_GERAL deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CHAT_GERAL]
        rendered = prompt.render(
            contexto_documentos=(
                "[Relatório narrativo disponível]\n"
                "Nota final: 7.5/10\n"
                "Análise narrativa: João demonstrou bom domínio de mecânica..."
            ),
            pergunta="Quais foram os principais erros do aluno?",
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt CHAT_GERAL: {vars_soltas}. "
            "Todas as variáveis template devem ser substituídas antes de enviar ao modelo."
        )

    def test_prompt_chat_geral_tem_tom_educacional(self):
        """Prompt CHAT_GERAL deve manter tom educacional e construtivo."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CHAT_GERAL]
        texto_lower = prompt.texto.lower()

        assert any(word in texto_lower for word in [
            "educacion",
            "pedagóg",
            "pedagogic",
            "professor",
            "aluno",
            "construtiv",
            "assistente",
        ]), (
            "Prompt CHAT_GERAL não mantém tom educacional. "
            "O assistente deve ter contexto pedagógico explícito para responder "
            "de forma apropriada ao professor."
        )

    def test_prompt_chat_geral_mantem_variaveis_originais(self):
        """Prompt CHAT_GERAL deve manter as variáveis contexto_documentos e pergunta."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.CHAT_GERAL]

        assert "{{contexto_documentos}}" in prompt.texto, (
            "Variável {{contexto_documentos}} não encontrada no prompt CHAT_GERAL. "
            "Esta variável é essencial — sem ela o assistente não recebe os documentos."
        )
        assert "{{pergunta}}" in prompt.texto, (
            "Variável {{pergunta}} não encontrada no prompt CHAT_GERAL. "
            "Esta variável é essencial — sem ela o assistente não sabe o que responder."
        )
