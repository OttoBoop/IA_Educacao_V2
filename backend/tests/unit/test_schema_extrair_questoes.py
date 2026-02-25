"""
Tests for F1-T1: New JSON schema for EXTRAIR_QUESTOES with tipo_raciocinio field.

Verifica que o schema de extração de questões inclui o campo tipo_raciocinio
para classificar o tipo de raciocínio exigido pela questão (memória, aplicação,
análise, síntese, avaliação), fornecendo contexto pedagógico rico para os
stages analíticos (CORRIGIR, ANALISAR_HABILIDADES, GERAR_RELATORIO).

O campo `tipo_raciocinio` permite que o stage CORRIGIR e ANALISAR_HABILIDADES
saibam, por exemplo, que um erro em questão de "análise" é mais grave do que
em questão de "memória", e calibrem a análise narrativa adequadamente.

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Task: F1-T1
"""

import re
import pytest


# ============================================================
# F1-T1 — EXTRAIR_QUESTOES: campo tipo_raciocinio
# ============================================================

class TestQuestaoTipoRaciocinio:
    """
    F1-T1: Questão extraída deve incluir campo tipo_raciocinio.

    O campo classifica o tipo de raciocínio exigido pela questão:
    - memória: reprodução de fato/dado (ex: "Quem escreveu Dom Casmurro?")
    - aplicação: usar fórmula/procedimento conhecido
    - análise: decompor problema em partes (ex: interpretar gráfico)
    - síntese: combinar conceitos de domínios diferentes
    - avaliação: emitir julgamento fundamentado

    Esta taxonomia ajuda os stages analíticos a contextualizar o erro:
    errar uma questão de "aplicação" (sabe o conceito, errou a execução)
    tem intervenção diferente de errar uma de "memória" (não sabe o conteúdo).
    """

    def test_questao_model_tem_campo_tipo_raciocinio(self):
        """Questao model deve ter campo tipo_raciocinio."""
        from pipeline_validation import Questao

        campos = Questao.__fields__
        assert "tipo_raciocinio" in campos, (
            "Questao model não tem campo 'tipo_raciocinio'. "
            "Este campo classifica o tipo de raciocínio exigido: memória, aplicação, "
            "análise, síntese, avaliação — contexto essencial para análise pedagógica."
        )

    def test_questao_schema_json_inclui_tipo_raciocinio(self):
        """Schema JSON da Questao deve incluir tipo_raciocinio em properties."""
        from pipeline_validation import Questao

        schema = Questao.schema()
        assert "tipo_raciocinio" in schema["properties"], (
            "Questao.schema()['properties'] não inclui 'tipo_raciocinio'. "
            "O schema deve refletir o novo campo para que a IA o produza "
            "e o validador Pydantic o aceite."
        )

    def test_questao_aceita_tipo_raciocinio_ao_instanciar(self):
        """Questao deve aceitar e preservar tipo_raciocinio ao ser instanciada."""
        from pipeline_validation import Questao, TipoQuestao

        questao = Questao(
            numero=1,
            enunciado="Calcule a velocidade de um objeto com massa 5 kg e força resultante de 20 N após 3 segundos.",
            tipo=TipoQuestao.DISSERTATIVA,
            pontuacao=2.0,
            tipo_raciocinio="aplicação",
        )

        assert hasattr(questao, "tipo_raciocinio"), (
            "Questao instanciada não tem atributo 'tipo_raciocinio'."
        )
        assert questao.tipo_raciocinio == "aplicação", (
            "Questao não preservou o valor de tipo_raciocinio após instanciação. "
            f"Esperado: 'aplicação', obtido: {questao.tipo_raciocinio!r}"
        )

    def test_questao_tipo_raciocinio_opcional(self):
        """Questao deve poder ser instanciada sem tipo_raciocinio (campo opcional)."""
        from pipeline_validation import Questao, TipoQuestao

        # Não deve levantar exceção — campo deve ser Optional
        questao = Questao(
            numero=1,
            enunciado="Qual é a capital do Brasil?",
            tipo=TipoQuestao.DISSERTATIVA,
            pontuacao=1.0,
        )

        assert hasattr(questao, "tipo_raciocinio"), (
            "Questao sem tipo_raciocinio deveria ter o atributo (com valor None)."
        )
        # Deve ser None quando não fornecido
        assert questao.tipo_raciocinio is None, (
            "tipo_raciocinio deve ser None quando não fornecido — campo é Optional."
        )

    def test_prompt_extrair_questoes_menciona_tipo_raciocinio(self):
        """Prompt EXTRAIR_QUESTOES deve mencionar tipo_raciocinio no JSON schema."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        assert "tipo_raciocinio" in prompt.texto, (
            "Prompt EXTRAIR_QUESTOES não menciona 'tipo_raciocinio'. "
            "O prompt deve solicitar este campo para que a IA o inclua no JSON retornado. "
            "Sem isso, o modelo não saberá que deve classificar o tipo de raciocínio."
        )

    def test_prompt_extrair_questoes_renderiza_sem_vars_soltas(self):
        """Prompt EXTRAIR_QUESTOES deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        rendered = prompt.render(
            conteudo_documento="1. Qual é a velocidade da luz? 2. Calcule a força resultante.",
            materia="Física",
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt EXTRAIR_QUESTOES: {vars_soltas}. "
            "Todas as variáveis template devem ser substituídas antes de enviar ao modelo."
        )
