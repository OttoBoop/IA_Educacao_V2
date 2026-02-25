"""
Tests for F2-T1: New schemas for EXTRAIR_GABARITO (conceito_central) and
EXTRAIR_RESPOSTAS (raciocinio_parcial).

Verifica que:
- EXTRAIR_GABARITO: RespostaGabarito inclui campo conceito_central
  (conceito pedagógico principal testado pela questão — ajuda ANALISAR_HABILIDADES
  a mapear lacunas conceituais, não apenas pontuação)

- EXTRAIR_RESPOSTAS: RespostaAluno inclui campo raciocinio_parcial
  (descrição do raciocínio parcial identificado na resposta do aluno, mesmo
  quando a resposta está errada — evidência crítica para análise pedagógica)

Ambos os campos fornecem contexto rico para que os stages analíticos produzam
análise narrativa de qualidade, não apenas checklists de pontos.

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Task: F2-T1
"""

import re
import pytest


# ============================================================
# F2-T1 — EXTRAIR_GABARITO: campo conceito_central
# ============================================================

class TestRespostaGabaritoConceitoCentral:
    """
    F2-T1 (EXTRAIR_GABARITO): RespostaGabarito deve incluir conceito_central.

    O campo conceito_central identifica o conceito pedagógico principal
    testado pela questão. Isso permite que:
    - ANALISAR_HABILIDADES mapeie lacunas conceituais específicas
    - GERAR_RELATORIO diferencie erros em conceitos fundamentais vs. periféricos
    - O professor saiba qual conceito precisa ser reforçado
    """

    def test_resposta_gabarito_model_tem_conceito_central(self):
        """RespostaGabarito model deve ter campo conceito_central."""
        from pipeline_validation import RespostaGabarito

        campos = RespostaGabarito.__fields__
        assert "conceito_central" in campos, (
            "RespostaGabarito model não tem campo 'conceito_central'. "
            "Este campo identifica o conceito pedagógico principal testado pela questão — "
            "essencial para que ANALISAR_HABILIDADES mapeie lacunas conceituais reais."
        )

    def test_resposta_gabarito_schema_json_inclui_conceito_central(self):
        """Schema JSON da RespostaGabarito deve incluir conceito_central em properties."""
        from pipeline_validation import RespostaGabarito

        schema = RespostaGabarito.schema()
        assert "conceito_central" in schema["properties"], (
            "RespostaGabarito.schema()['properties'] não inclui 'conceito_central'. "
            "O schema deve refletir o novo campo para validação do output da IA."
        )

    def test_resposta_gabarito_aceita_conceito_central(self):
        """RespostaGabarito deve aceitar e preservar conceito_central."""
        from pipeline_validation import RespostaGabarito

        conceito = "Conservação de energia cinética em colisões elásticas"
        resposta = RespostaGabarito(
            questao_numero=1,
            resposta_correta="c",
            justificativa="Em colisões elásticas, energia cinética é conservada.",
            conceito_central=conceito,
        )

        assert hasattr(resposta, "conceito_central"), (
            "RespostaGabarito instanciada não tem atributo 'conceito_central'."
        )
        assert resposta.conceito_central == conceito, (
            f"RespostaGabarito não preservou conceito_central. "
            f"Esperado: {conceito!r}, obtido: {resposta.conceito_central!r}"
        )

    def test_resposta_gabarito_conceito_central_opcional(self):
        """RespostaGabarito deve poder ser instanciada sem conceito_central (campo opcional)."""
        from pipeline_validation import RespostaGabarito

        # Não deve levantar exceção — campo deve ser Optional
        resposta = RespostaGabarito(
            questao_numero=1,
            resposta_correta="a",
        )

        assert hasattr(resposta, "conceito_central"), (
            "RespostaGabarito sem conceito_central deveria ter o atributo (com valor None)."
        )
        assert resposta.conceito_central is None, (
            "conceito_central deve ser None quando não fornecido — campo é Optional."
        )

    def test_prompt_extrair_gabarito_menciona_conceito_central(self):
        """Prompt EXTRAIR_GABARITO deve mencionar conceito_central no JSON schema."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_GABARITO]
        assert "conceito_central" in prompt.texto, (
            "Prompt EXTRAIR_GABARITO não menciona 'conceito_central'. "
            "O prompt deve solicitar este campo para que a IA identifique o conceito "
            "pedagógico principal e o inclua no JSON retornado."
        )


# ============================================================
# F2-T1 — EXTRAIR_RESPOSTAS: campo raciocinio_parcial
# ============================================================

class TestRespostaAlunoRaciociinioParcial:
    """
    F2-T1 (EXTRAIR_RESPOSTAS): RespostaAluno deve incluir raciocinio_parcial.

    O campo raciocinio_parcial captura sinais de raciocínio do aluno
    identificados na prova — mesmo em respostas erradas ou incompletas.

    Exemplos:
    - Resposta errada mas método correto: "O aluno aplicou F=ma corretamente
      mas inverteu a direção do vetor força"
    - Resposta parcial: "O aluno respondeu apenas a primeira parte do problema"
    - Resposta em branco com rascunho: "Há rascunho de setup da equação, mas
      sem conclusão"

    Este campo é evidência crítica para análise narrativa — permite ao
    CORRIGIR e ANALISAR_HABILIDADES distinguir "não sabe" de "sabe mas erra
    na execução".
    """

    def test_resposta_aluno_model_tem_raciocinio_parcial(self):
        """RespostaAluno model deve ter campo raciocinio_parcial."""
        from pipeline_validation import RespostaAluno

        campos = RespostaAluno.__fields__
        assert "raciocinio_parcial" in campos, (
            "RespostaAluno model não tem campo 'raciocinio_parcial'. "
            "Este campo captura sinais de raciocínio do aluno em respostas erradas — "
            "evidência crítica para distinguir 'não sabe' de 'sabe mas erra na execução'."
        )

    def test_resposta_aluno_schema_json_inclui_raciocinio_parcial(self):
        """Schema JSON da RespostaAluno deve incluir raciocinio_parcial em properties."""
        from pipeline_validation import RespostaAluno

        schema = RespostaAluno.schema()
        assert "raciocinio_parcial" in schema["properties"], (
            "RespostaAluno.schema()['properties'] não inclui 'raciocinio_parcial'. "
            "O schema deve refletir o novo campo para validação do output da IA."
        )

    def test_resposta_aluno_aceita_raciocinio_parcial(self):
        """RespostaAluno deve aceitar e preservar raciocinio_parcial."""
        from pipeline_validation import RespostaAluno

        raciocinio = (
            "O aluno aplicou corretamente a 2ª lei de Newton (F=ma), "
            "mas inverteu sinal na direção da força resultante"
        )
        resposta = RespostaAluno(
            questao_numero=2,
            resposta_aluno="A aceleração é -4 m/s²",
            raciocinio_parcial=raciocinio,
        )

        assert hasattr(resposta, "raciocinio_parcial"), (
            "RespostaAluno instanciada não tem atributo 'raciocinio_parcial'."
        )
        assert resposta.raciocinio_parcial == raciocinio, (
            "RespostaAluno não preservou raciocinio_parcial após instanciação."
        )

    def test_resposta_aluno_raciocinio_parcial_opcional(self):
        """RespostaAluno deve poder ser instanciada sem raciocinio_parcial (campo opcional)."""
        from pipeline_validation import RespostaAluno

        # Não deve levantar exceção — campo deve ser Optional
        resposta = RespostaAluno(
            questao_numero=1,
            resposta_aluno="a",
        )

        assert hasattr(resposta, "raciocinio_parcial"), (
            "RespostaAluno sem raciocinio_parcial deveria ter o atributo (com valor None)."
        )
        assert resposta.raciocinio_parcial is None, (
            "raciocinio_parcial deve ser None quando não fornecido — campo é Optional."
        )

    def test_prompt_extrair_respostas_menciona_raciocinio_parcial(self):
        """Prompt EXTRAIR_RESPOSTAS deve mencionar raciocinio_parcial no JSON schema."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_RESPOSTAS]
        assert "raciocinio_parcial" in prompt.texto, (
            "Prompt EXTRAIR_RESPOSTAS não menciona 'raciocinio_parcial'. "
            "O prompt deve solicitar este campo para capturar sinais de raciocínio "
            "do aluno — evidência crítica para análise narrativa pedagógica."
        )
