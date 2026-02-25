"""
Testes para os prompts de extração reescritos (F1-T2, F2-T2, F2-T3).

Verifica que os prompts EXTRAIR_QUESTOES, EXTRAIR_GABARITO e EXTRAIR_RESPOSTAS
foram reescritos com:
- Sistema prompt (texto_sistema) com papel pedagógico explícito
- Instruções substantivas que orientam a IA além de "retorne um JSON"
- Explicações sobre os campos pedagógicos novos (tipo_raciocinio,
  conceito_central, raciocinio_parcial)

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Tasks: F1-T2, F2-T2, F2-T3
"""

import re
import pytest


# ============================================================
# F1-T2 — EXTRAIR_QUESTOES: prompt reescrito
# ============================================================

class TestPromptExtrairQuestoesReescrito:
    """
    F1-T2: Prompt EXTRAIR_QUESTOES deve ter sistema prompt pedagógico e
    instruções que vão além do JSON — explicando COMO classificar questões.

    O prompt atual apenas mostra o schema JSON. O prompt reescrito deve:
    - Estabelecer o papel do agente (sistema prompt)
    - Explicar as 5 categorias de tipo_raciocinio com exemplos
    - Instruir sobre habilidades como descrição de raciocínio esperado
    """

    def test_prompt_extrair_questoes_tem_texto_sistema(self):
        """Prompt EXTRAIR_QUESTOES deve ter texto_sistema definido."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        assert prompt.texto_sistema is not None, (
            "Prompt EXTRAIR_QUESTOES não tem texto_sistema. "
            "O sistema prompt deve estabelecer o papel do agente como analisador "
            "pedagógico de questões — sem isso, o modelo não sabe COMO classificar "
            "o tipo de raciocínio de forma consistente."
        )
        assert len(prompt.texto_sistema) > 100, (
            "texto_sistema muito curto — deve estabelecer papel com contexto. "
            f"Comprimento atual: {len(prompt.texto_sistema) if prompt.texto_sistema else 0}"
        )

    def test_prompt_extrair_questoes_sistema_menciona_classificacao(self):
        """Sistema prompt deve mencionar classificação pedagógica de questões."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "classific", "raciocín", "raciocin", "pedagóg", "pedagogic",
            "habilidad", "questão", "questao", "extraç", "extracao"
        ]), (
            "Sistema prompt não menciona classificação ou análise pedagógica. "
            "Deve contextualizar o agente para classificar questões educacionalmente."
        )

    def test_prompt_extrair_questoes_explica_categorias_tipo_raciocinio(self):
        """Prompt deve explicar as 5 categorias de tipo_raciocinio com exemplos."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        texto_completo = (prompt.texto_sistema or "") + prompt.texto
        texto_lower = texto_completo.lower()

        # Deve mencionar pelo menos 3 das 5 categorias com contexto (não só no JSON)
        categorias = ["memória", "memoria", "aplicação", "aplicacao", "análise", "analise", "síntese", "sintese", "avaliação", "avaliacao"]
        categorias_encontradas = [c for c in categorias if c in texto_lower]
        assert len(categorias_encontradas) >= 3, (
            "Prompt não explica as categorias de tipo_raciocinio. "
            "O agente precisa de definições claras para classificar corretamente: "
            "memória (reprodução), aplicação (usar fórmula), análise (decompor), "
            "síntese (combinar domínios), avaliação (julgamento fundamentado). "
            f"Categorias encontradas: {categorias_encontradas}"
        )

    def test_prompt_extrair_questoes_instrui_habilidades_descritivas(self):
        """Prompt deve instruir que habilidades incluam descrição do raciocínio esperado."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        texto_completo = (prompt.texto_sistema or "") + prompt.texto
        texto_lower = texto_completo.lower()

        assert any(word in texto_lower for word in [
            "raciocínio esperado", "raciocinio esperado",
            "descrição", "descricao", "descreva", "específic", "especific",
            "habilidad"
        ]), (
            "Prompt não instrui sobre habilidades descritivas. "
            "O campo `habilidades` deve incluir descrição do raciocínio esperado, "
            "não só o nome da habilidade — para que os stages analíticos tenham "
            "contexto pedagógico desde o início."
        )

    def test_prompt_extrair_questoes_texto_substantivo(self):
        """Texto principal do prompt EXTRAIR_QUESTOES deve ser substantivo (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_QUESTOES]
        assert len(prompt.texto) > 800, (
            f"Prompt EXTRAIR_QUESTOES muito curto ({len(prompt.texto)} chars). "
            "Um prompt de extração pedagógica deve ter instruções substantivas — "
            "mínimo 800 caracteres para incluir exemplos e orientações de classificação."
        )


# ============================================================
# F2-T2 — EXTRAIR_GABARITO: prompt reescrito
# ============================================================

class TestPromptExtrairGabaritoReescrito:
    """
    F2-T2: Prompt EXTRAIR_GABARITO deve ter sistema prompt e instruções
    que orientem a identificação de conceito_central com exemplos claros.

    O conceito_central não é óbvio — sem instrução adequada, a IA retornará
    o tópico geral em vez do conceito pedagógico específico testado.
    """

    def test_prompt_extrair_gabarito_tem_texto_sistema(self):
        """Prompt EXTRAIR_GABARITO deve ter texto_sistema definido."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_GABARITO]
        assert prompt.texto_sistema is not None, (
            "Prompt EXTRAIR_GABARITO não tem texto_sistema. "
            "O sistema prompt deve estabelecer o papel do agente como extrator "
            "pedagógico de gabaritos — instruindo sobre conceito_central."
        )
        assert len(prompt.texto_sistema) > 100, (
            "texto_sistema muito curto. "
            f"Comprimento atual: {len(prompt.texto_sistema) if prompt.texto_sistema else 0}"
        )

    def test_prompt_extrair_gabarito_sistema_menciona_conceito_pedagogico(self):
        """Sistema prompt deve mencionar conceito pedagógico ou gabarito."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_GABARITO]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "conceito", "pedagóg", "pedagogic", "gabarito", "habilidad",
            "extrat", "resposta", "corret"
        ]), (
            "Sistema prompt não menciona contexto pedagógico ou gabarito. "
            "Deve orientar o agente a identificar conceitos pedagógicos centrais."
        )

    def test_prompt_extrair_gabarito_explica_conceito_central_com_exemplos(self):
        """Prompt deve explicar o que é conceito_central com exemplos concretos."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_GABARITO]
        texto_completo = (prompt.texto_sistema or "") + prompt.texto
        texto_lower = texto_completo.lower()

        # Deve dar contexto do que é conceito_central (além do nome do campo no JSON)
        assert any(word in texto_lower for word in [
            "conceito pedagógico", "conceito pedagogico",
            "principal testado", "conceito central",
            "habilidade testada", "conteúdo", "conteudo"
        ]), (
            "Prompt não explica o que é conceito_central. "
            "O agente precisa entender que conceito_central é o conceito pedagógico "
            "principal testado pela questão — não apenas o tópico geral. "
            "Ex: 'conservação de energia cinética' não apenas 'Física'."
        )

    def test_prompt_extrair_gabarito_texto_substantivo(self):
        """Texto principal do prompt EXTRAIR_GABARITO deve ser substantivo (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_GABARITO]
        assert len(prompt.texto) > 800, (
            f"Prompt EXTRAIR_GABARITO muito curto ({len(prompt.texto)} chars). "
            "Deve ter instruções sobre como identificar conceito_central com exemplos."
        )

    def test_prompt_extrair_gabarito_renderiza_sem_vars_soltas(self):
        """Prompt EXTRAIR_GABARITO deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_GABARITO]
        rendered = prompt.render(
            conteudo_documento="1-a, 2-b, 3-c",
            questoes_extraidas="[{questao_numero: 1, enunciado: 'Qual é ...'}]",
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt EXTRAIR_GABARITO: {vars_soltas}."
        )


# ============================================================
# F2-T3 — EXTRAIR_RESPOSTAS: prompt reescrito
# ============================================================

class TestPromptExtrairRespostasReescrito:
    """
    F2-T3: Prompt EXTRAIR_RESPOSTAS deve ter sistema prompt que estabelece
    o papel de leitor atento de provas — instruindo a identificar raciocínio_parcial
    mesmo em respostas erradas ou incompletas.

    A distinção crítica: raciocinio_parcial não é a resposta errada — é a evidência
    de raciocínio que aparece em meio ao erro.
    """

    def test_prompt_extrair_respostas_tem_texto_sistema(self):
        """Prompt EXTRAIR_RESPOSTAS deve ter texto_sistema definido."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_RESPOSTAS]
        assert prompt.texto_sistema is not None, (
            "Prompt EXTRAIR_RESPOSTAS não tem texto_sistema. "
            "O sistema prompt deve estabelecer o papel do agente como leitor atento "
            "de provas — capaz de identificar raciocínio parcial em respostas erradas."
        )
        assert len(prompt.texto_sistema) > 100, (
            "texto_sistema muito curto. "
            f"Comprimento atual: {len(prompt.texto_sistema) if prompt.texto_sistema else 0}"
        )

    def test_prompt_extrair_respostas_sistema_menciona_raciocinio_parcial(self):
        """Sistema prompt deve mencionar identificação de raciocínio parcial."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_RESPOSTAS]
        assert prompt.texto_sistema is not None, "texto_sistema é None"

        texto_lower = prompt.texto_sistema.lower()
        assert any(word in texto_lower for word in [
            "raciocín", "raciocin", "parcial", "evidênc", "evidenc",
            "pensamento", "estratégi", "process", "aluno"
        ]), (
            "Sistema prompt não menciona raciocínio parcial ou evidências de pensamento. "
            "Deve orientar o agente a capturar sinais de compreensão em respostas erradas."
        )

    def test_prompt_extrair_respostas_explica_raciocinio_parcial_com_exemplos(self):
        """Prompt deve explicar o que é raciocinio_parcial com exemplos concretos."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_RESPOSTAS]
        texto_completo = (prompt.texto_sistema or "") + prompt.texto
        texto_lower = texto_completo.lower()

        # Deve dar orientação além do campo no JSON
        assert any(word in texto_lower for word in [
            "mesmo que errad", "mesmo errand", "mesmo incorret",
            "raciocínio parcial", "raciocinio parcial",
            "evidência", "evidencia", "sinal de", "sinais de",
            "não sabe", "sabe mas", "tentou"
        ]), (
            "Prompt não explica o que é raciocinio_parcial com exemplos. "
            "O agente precisa entender que deve capturar evidências de raciocínio "
            "MESMO EM RESPOSTAS ERRADAS — a distinção entre 'não sabe' e "
            "'sabe mas erra na execução' é essencial para análise pedagógica."
        )

    def test_prompt_extrair_respostas_texto_substantivo(self):
        """Texto principal do prompt EXTRAIR_RESPOSTAS deve ser substantivo (> 800 chars)."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_RESPOSTAS]
        assert len(prompt.texto) > 800, (
            f"Prompt EXTRAIR_RESPOSTAS muito curto ({len(prompt.texto)} chars). "
            "Deve ter instruções substantivas sobre como identificar raciocinio_parcial."
        )

    def test_prompt_extrair_respostas_renderiza_sem_vars_soltas(self):
        """Prompt EXTRAIR_RESPOSTAS deve renderizar sem variáveis não substituídas."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento

        prompt = PROMPTS_PADRAO[EtapaProcessamento.EXTRAIR_RESPOSTAS]
        rendered = prompt.render(
            conteudo_documento="Questão 1: V. Questão 2: em branco.",
            questoes_extraidas="[{numero: 1, enunciado: 'Qual é...'}]",
            nome_aluno="Maria Silva",
        )

        vars_soltas = re.findall(r'\{\{(\w+)\}\}', rendered)
        assert not vars_soltas, (
            f"Variáveis não substituídas no prompt EXTRAIR_RESPOSTAS: {vars_soltas}."
        )
