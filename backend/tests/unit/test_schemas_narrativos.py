"""
Testes para schemas narrativos dos stages analíticos do pipeline.

Verifica que os modelos Pydantic e prompts dos stages CORRIGIR,
ANALISAR_HABILIDADES e GERAR_RELATORIO suportam campos de narrativa
pedagógica (narrativa_correcao, narrativa_habilidades, relatorio_narrativo).

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Tasks: F3-T1, F4-T1, F5-T1
"""

import pytest


# ============================================================
# F3-T1 — CORRIGIR: campo narrativa_correcao
# ============================================================

class TestCorrecaoQuestaoNarrativa:
    """
    F3-T1: Testes para o schema do CORRIGIR com campo narrativa_correcao.

    O stage CORRIGIR deve incluir um campo narrativa_correcao em cada questão
    com análise pedagógica: raciocínio do aluno, tipo de erro, potencial.
    """

    def test_correcao_questao_schema_tem_campo_narrativa_correcao(self):
        """Schema do CorrecaoQuestao deve ter o campo narrativa_correcao."""
        from pipeline_validation import obter_schema_json

        schema = obter_schema_json("corrigir")
        assert schema is not None, "Schema do stage 'corrigir' não encontrado"
        assert "narrativa_correcao" in schema["properties"], (
            "Campo 'narrativa_correcao' ausente no schema de CorrecaoQuestao. "
            "Este campo é necessário para a análise narrativa por questão."
        )

    def test_correcao_questao_preserva_narrativa_nao_vazia(self):
        """CorrecaoQuestao deve aceitar e preservar narrativa_correcao não-vazia."""
        from pipeline_validation import CorrecaoQuestao

        narrativa_exemplo = (
            "## Questão 1 — Análise\n\n"
            "**O que o aluno tentou fazer:** O aluno identificou corretamente que a questão "
            "envolvia pressão atmosférica, e tentou aplicar a lei de Boyle (PV = constante). "
            "O raciocínio está correto no primeiro passo — o erro aparece quando confunde "
            "a unidade de pressão.\n\n"
            "**Tipo de erro:** Erro de unidade/conversão — não é um erro conceitual.\n\n"
            "**Potencial:** Alto. Com atenção às conversões, esta questão seria acertada."
        )

        correcao = CorrecaoQuestao(
            nota=0.5,
            nota_maxima=1.0,
            percentual=50,
            status="parcial",
            feedback="Raciocínio correto, mas erro na unidade.",
            narrativa_correcao=narrativa_exemplo,
        )

        assert hasattr(correcao, "narrativa_correcao"), (
            "CorrecaoQuestao não possui atributo narrativa_correcao"
        )
        assert correcao.narrativa_correcao is not None, (
            "narrativa_correcao retornou None"
        )
        assert len(correcao.narrativa_correcao) > 100, (
            "narrativa_correcao muito curta — deve conter análise pedagógica substantiva"
        )

    def test_prompt_corrigir_especifica_narrativa_correcao(self):
        """O prompt CORRIGIR deve incluir narrativa_correcao no JSON solicitado."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt_corrigir = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
        assert "narrativa_correcao" in prompt_corrigir.texto, (
            "O prompt CORRIGIR não menciona 'narrativa_correcao'. "
            "O prompt deve solicitar este campo na estrutura JSON retornada."
        )


# ============================================================
# F4-T1 — ANALISAR_HABILIDADES: campo narrativa_habilidades
# ============================================================

class TestAnaliseHabilidadesNarrativa:
    """
    F4-T1: Testes para o schema do ANALISAR_HABILIDADES com campo narrativa_habilidades.

    O stage ANALISAR_HABILIDADES deve incluir narrativa_habilidades com
    síntese de padrões, consistência, esforço vs. conhecimento e
    transferência de conceitos — não apenas um checklist de categorias.
    """

    def test_analise_habilidades_schema_tem_campo_narrativa_habilidades(self):
        """Schema do AnaliseHabilidades deve ter o campo narrativa_habilidades."""
        from pipeline_validation import obter_schema_json

        schema = obter_schema_json("analisar_habilidades")
        assert schema is not None, "Schema do stage 'analisar_habilidades' não encontrado"
        assert "narrativa_habilidades" in schema["properties"], (
            "Campo 'narrativa_habilidades' ausente no schema de AnaliseHabilidades. "
            "Este campo é necessário para a síntese narrativa de padrões de aprendizado."
        )

    def test_analise_habilidades_preserva_narrativa_nao_vazia(self):
        """AnaliseHabilidades deve aceitar e preservar narrativa_habilidades não-vazia."""
        from pipeline_validation import AnaliseHabilidades

        narrativa_exemplo = (
            "## Perfil de Aprendizado — João\n\n"
            "**Consistência:** João apresenta padrões de erro consistentes. Em 4 das 6 "
            "questões de cálculo, demonstra o método correto mas comete erros de unidade. "
            "Isso sugere que o processo de resolução está internalizado, mas há uma lacuna "
            "no domínio de grandezas físicas.\n\n"
            "**Esforço vs. Conhecimento:** As questões em branco concentram-se em astronomia. "
            "Isso indica ausência de conteúdo, não falta de esforço — João respondeu todas "
            "as questões de biologia mesmo que parcialmente.\n\n"
            "**Transferência de Conceitos:** Em questões de biologia, João tentou aplicar "
            "raciocínio de física — sinal de tentativa de transferência entre domínios."
        )

        analise = AnaliseHabilidades(
            aluno="João Silva",
            resumo_desempenho="Bom desempenho geral com padrão de erros de unidade.",
            nota_final=7.5,
            nota_maxima=10.0,
            percentual_acerto=75,
            habilidades={
                "dominadas": [{"nome": "Lei de Boyle", "evidencia": "Questões 1, 3"}],
                "em_desenvolvimento": [{"nome": "Conversão de unidades", "evidencia": "Questões 2, 4"}],
                "nao_demonstradas": [{"nome": "Astronomia", "evidencia": "Questões 8, 9 em branco"}],
            },
            narrativa_habilidades=narrativa_exemplo,
        )

        assert hasattr(analise, "narrativa_habilidades"), (
            "AnaliseHabilidades não possui atributo narrativa_habilidades"
        )
        assert analise.narrativa_habilidades is not None, (
            "narrativa_habilidades retornou None"
        )
        assert len(analise.narrativa_habilidades) > 100, (
            "narrativa_habilidades muito curta — deve conter síntese pedagógica substantiva"
        )

    def test_prompt_analisar_habilidades_especifica_narrativa_habilidades(self):
        """O prompt ANALISAR_HABILIDADES deve incluir narrativa_habilidades no JSON solicitado."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
        assert "narrativa_habilidades" in prompt.texto, (
            "O prompt ANALISAR_HABILIDADES não menciona 'narrativa_habilidades'. "
            "O prompt deve solicitar este campo na estrutura JSON retornada."
        )


# ============================================================
# F5-T1 — GERAR_RELATORIO: campo relatorio_narrativo
# ============================================================

class TestRelatorioFinalNarrativa:
    """
    F5-T1: Testes para o schema do GERAR_RELATORIO com campo relatorio_narrativo.

    O stage GERAR_RELATORIO deve incluir relatorio_narrativo com narrativa
    holística que começa pelo quadro geral e afunila nos detalhes —
    combinando nota, habilidades e análise numa leitura fluida.
    """

    def test_relatorio_final_schema_tem_campo_relatorio_narrativo(self):
        """Schema do RelatorioFinal deve ter o campo relatorio_narrativo."""
        from pipeline_validation import obter_schema_json

        schema = obter_schema_json("gerar_relatorio")
        assert schema is not None, "Schema do stage 'gerar_relatorio' não encontrado"
        assert "relatorio_narrativo" in schema["properties"], (
            "Campo 'relatorio_narrativo' ausente no schema de RelatorioFinal. "
            "Este campo é necessário para a narrativa holística do relatório."
        )

    def test_relatorio_narrativo_contem_secao_visao_geral(self):
        """relatorio_narrativo deve conter seção de visão geral do aluno."""
        from pipeline_validation import RelatorioFinal

        relatorio_narrativo = (
            "## Visão Geral\n\n"
            "João demonstrou bom domínio dos conceitos fundamentais de Física, "
            "atingindo 75% da pontuação. Seu desempenho é marcado pela consistência: "
            "domina os métodos de resolução, mas enfrenta dificuldades sistemáticas "
            "com conversão de unidades.\n\n"
            "## Análise por Questão\n\n"
            "Nas questões de mecânica (Q1-Q4), João acertou o raciocínio em todas, "
            "mas perdeu pontos nas conversões. Em astronomia (Q8-Q9), as questões ficaram "
            "em branco — indicando lacuna de conteúdo, não de esforço.\n\n"
            "## Recomendações\n\n"
            "Foco principal: praticar conversão entre sistemas de unidades (SI vs. CGS). "
            "Este é o único bloqueio sistemático para João atingir nota máxima nos "
            "problemas de mecânica e termodinâmica."
        )

        relatorio = RelatorioFinal(
            conteudo="# Relatório de Desempenho\n\nJoão Silva — Física — Prova 1",
            resumo_executivo="João atingiu 75% com padrão de erros de unidade.",
            nota_final="7.5",
            aluno="João Silva",
            materia="Física",
            atividade="Prova 1",
            relatorio_narrativo=relatorio_narrativo,
        )

        assert hasattr(relatorio, "relatorio_narrativo"), (
            "RelatorioFinal não possui atributo relatorio_narrativo"
        )
        assert relatorio.relatorio_narrativo is not None, (
            "relatorio_narrativo retornou None"
        )
        assert len(relatorio.relatorio_narrativo) > 500, (
            "relatorio_narrativo muito curto — deve conter relatório holístico completo"
        )
        assert "## Visão Geral" in relatorio.relatorio_narrativo or \
               "## Visão geral" in relatorio.relatorio_narrativo or \
               "## VISÃO GERAL" in relatorio.relatorio_narrativo.upper(), (
            "relatorio_narrativo deve começar com seção de visão geral do aluno"
        )

    def test_prompt_gerar_relatorio_especifica_relatorio_narrativo(self):
        """O prompt GERAR_RELATORIO deve incluir relatorio_narrativo no JSON solicitado."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
        assert "relatorio_narrativo" in prompt.texto, (
            "O prompt GERAR_RELATORIO não menciona 'relatorio_narrativo'. "
            "O prompt deve solicitar este campo na estrutura JSON retornada."
        )
