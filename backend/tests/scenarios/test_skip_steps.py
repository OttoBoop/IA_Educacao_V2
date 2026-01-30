"""
Testes de Execução Parcial do Pipeline

Verifica que é possível pular etapas ou executar apenas partes específicas.
"""

import pytest
import json


@pytest.mark.partial
@pytest.mark.render_compatible
class TestSkipSteps:
    """
    Testes para execução parcial do pipeline.

    Cenários:
    - Executar apenas correção (questões já extraídas)
    - Pular extração de gabarito
    - Re-executar etapa específica
    """

    @pytest.mark.asyncio
    async def test_apenas_corrigir(self, test_scenario, selected_provider):
        """
        Cenário: Questões e gabarito já extraídos previamente.
        Executar apenas a correção.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        # Simular dados já extraídos
        questoes_extraidas = {
            "questoes": [
                {"numero": 1, "enunciado": "Resolva: 3x + 7 = 22", "pontuacao": 2.5},
                {"numero": 2, "enunciado": "Calcule a área de um quadrado de lado 5", "pontuacao": 2.5},
                {"numero": 3, "enunciado": "Qual é 15% de 200?", "pontuacao": 2.5},
                {"numero": 4, "enunciado": "Simplifique: 2(x+3) - 4x", "pontuacao": 2.5}
            ],
            "nota_total": 10
        }

        gabarito_extraido = {
            "respostas": [
                {"numero": 1, "resposta": "x = 5"},
                {"numero": 2, "resposta": "25"},
                {"numero": 3, "resposta": "30"},
                {"numero": 4, "resposta": "-2x + 6"}
            ]
        }

        aluno = test_scenario["alunos"][0]

        # Usar dados já extraídos para correção
        prompt = f"""
        Corrija a prova do aluno usando os dados já extraídos.

        QUESTÕES EXTRAÍDAS:
        {json.dumps(questoes_extraidas, ensure_ascii=False, indent=2)}

        GABARITO EXTRAÍDO:
        {json.dumps(gabarito_extraido, ensure_ascii=False, indent=2)}

        RESPOSTAS DO ALUNO ({aluno['nome']}):
        {aluno['prova'].content}

        Retorne a correção com notas por questão e nota total.
        """

        response = await provider.complete(prompt, max_tokens=1500)
        assert response is not None
        assert len(response.content) > 50

        # Deve ter informação de correção
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["nota", "questão", "questao", "pontos"])

    @pytest.mark.asyncio
    async def test_apenas_extrair_questoes(self, test_scenario, selected_provider):
        """
        Cenário: Executar apenas extração de questões, sem correção.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        enunciado = test_scenario["enunciado"]

        prompt = f"""
        Extraia APENAS as questões deste enunciado.
        NÃO faça correção. Apenas liste as questões encontradas.

        Enunciado:
        {enunciado.content}

        Retorne JSON: {{"questoes": [{{"numero": N, "enunciado": "...", "pontuacao": X}}]}}
        """

        response = await provider.complete(prompt, max_tokens=1500)
        assert response is not None

        # Verificar que tem questões
        content_lower = response.content.lower()
        assert "questão" in content_lower or "questao" in content_lower or "numero" in content_lower

    @pytest.mark.asyncio
    async def test_apenas_gerar_feedback(self, selected_provider):
        """
        Cenário: Correção já feita, gerar apenas feedback detalhado.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        # Simular correção já realizada
        correcao_existente = {
            "aluno": "João Silva",
            "questoes": [
                {"numero": 1, "nota": 2.0, "nota_maxima": 2.5},
                {"numero": 2, "nota": 2.5, "nota_maxima": 2.5},
                {"numero": 3, "nota": 1.0, "nota_maxima": 2.5},
                {"numero": 4, "nota": 0.0, "nota_maxima": 2.5}
            ],
            "nota_total": 5.5,
            "nota_maxima": 10.0
        }

        prompt = f"""
        Baseado nesta correção já realizada, gere um feedback detalhado para o aluno.

        CORREÇÃO:
        {json.dumps(correcao_existente, ensure_ascii=False, indent=2)}

        O feedback deve:
        1. Destacar pontos fortes
        2. Identificar áreas de melhoria
        3. Dar sugestões de estudo
        4. Ser encorajador mas honesto

        Retorne apenas o feedback em texto.
        """

        response = await provider.complete(prompt, max_tokens=1000)
        assert response is not None

        # Deve ter feedback substantivo
        assert len(response.content) > 100

    @pytest.mark.asyncio
    async def test_reprocessar_questao_especifica(self, selected_provider):
        """
        Cenário: Re-corrigir apenas uma questão específica.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        # Contexto da questão
        questao = {
            "numero": 3,
            "enunciado": "Qual é 15% de 200?",
            "resposta_gabarito": "30",
            "resposta_aluno": "300",
            "nota_anterior": 0.0,
            "nota_maxima": 2.5
        }

        prompt = f"""
        Re-avalie esta questão específica:

        QUESTÃO {questao['numero']}:
        {questao['enunciado']}

        RESPOSTA CORRETA: {questao['resposta_gabarito']}
        RESPOSTA DO ALUNO: {questao['resposta_aluno']}

        A avaliação anterior deu nota {questao['nota_anterior']}.
        O aluno pode ter feito um erro de digitação (300 ao invés de 30).

        Reavalie considerando possíveis erros de digitação.
        Retorne: {{"nota": X, "justificativa": "..."}}
        """

        response = await provider.complete(prompt, max_tokens=500)
        assert response is not None

        # Deve ter avaliação
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["nota", "erro", "digitação", "digitacao"])

    @pytest.mark.asyncio
    async def test_pipeline_com_etapa_pulada(self, test_scenario, selected_provider):
        """
        Cenário: Simular pipeline onde uma etapa foi pulada.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        # Simular que temos enunciado mas NÃO temos gabarito extraído
        enunciado = test_scenario["enunciado"]
        aluno = test_scenario["alunos"][0]

        prompt = f"""
        Você precisa corrigir esta prova, mas o gabarito não foi extraído ainda.

        ENUNCIADO (contém as respostas corretas):
        {enunciado.content}

        PROVA DO ALUNO:
        {aluno['prova'].content}

        Primeiro extraia as respostas corretas do enunciado, depois corrija a prova.
        Retorne a nota final.
        """

        response = await provider.complete(prompt, max_tokens=2000)
        assert response is not None

        # Deve ter conseguido fazer ambas as tarefas
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["nota", "questão", "questao", "correto", "errado"])

    @pytest.mark.asyncio
    async def test_verificar_consistencia_etapas(self, test_scenario, selected_provider):
        """
        Cenário: Verificar consistência entre etapas executadas separadamente.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        enunciado = test_scenario["enunciado"]
        gabarito = test_scenario["gabarito"]

        # Etapa 1: Extrair questões
        prompt1 = f"""
        Extraia as questões deste enunciado.
        Retorne JSON: {{"total": N}}

        {enunciado.content}
        """

        response1 = await provider.complete(prompt1, max_tokens=500)

        # Etapa 2: Contar questões no gabarito
        prompt2 = f"""
        Quantas respostas tem neste gabarito?
        Retorne JSON: {{"total": N}}

        {gabarito.content}
        """

        response2 = await provider.complete(prompt2, max_tokens=500)

        assert response1 is not None
        assert response2 is not None

        # Verificar que ambos identificaram questões
        for resp in [response1.content, response2.content]:
            assert any(char.isdigit() for char in resp)
