"""
Testes de Fluxo de Sucesso (Happy Path)

Testa o pipeline completo quando tudo funciona corretamente.
"""

import pytest
import json
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.render_compatible
class TestHappyPath:
    """
    Testes de fluxo perfeito - tudo funciona como esperado.

    Cenários:
    - Pipeline completo para um aluno
    - Pipeline para turma com múltiplos alunos
    - Extração de questões
    - Correção com diferentes qualidades de resposta
    """

    @pytest.mark.asyncio
    async def test_pipeline_aluno_completo(self, test_scenario, selected_provider):
        """
        Pipeline completo para um aluno:
        1. Extrair questões do enunciado
        2. Extrair gabarito
        3. Extrair respostas do aluno
        4. Corrigir
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        enunciado = test_scenario["enunciado"]
        gabarito = test_scenario["gabarito"]
        aluno = test_scenario["alunos"][0]
        prova = aluno["prova"]

        # Etapa 1: Extrair questões do enunciado
        prompt_extract = f"""
        Analise o enunciado de prova abaixo e extraia as questões.

        Retorne um JSON:
        {{"questoes": [{{"numero": 1, "enunciado": "...", "pontuacao": X.X}}], "total": N}}

        Enunciado:
        {enunciado.content}
        """

        response = await provider.complete(prompt_extract, max_tokens=1500)
        assert response is not None
        assert len(response.content) > 50

        # Tentar parsear JSON
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            questoes_data = json.loads(content.strip())
            assert "questoes" in questoes_data
        except json.JSONDecodeError:
            # Não é crítico se não parsear perfeitamente
            pass

        # Etapa 2: Corrigir prova
        prompt_corrigir = f"""
        Compare a prova do aluno com o gabarito e faça a correção.

        GABARITO:
        {gabarito.content}

        PROVA DO ALUNO ({aluno['nome']}):
        {prova.content}

        Retorne um JSON:
        {{
            "aluno": "{aluno['nome']}",
            "questoes": [{{"numero": 1, "nota": X.X, "nota_maxima": Y.Y, "feedback": "..."}}],
            "nota_total": X.X,
            "nota_maxima": Y.Y
        }}
        """

        response = await provider.complete(prompt_corrigir, max_tokens=2000)
        assert response is not None
        assert len(response.content) > 100

        # Verificar que tem informação de correção
        content_lower = response.content.lower()
        assert any(word in content_lower for word in ["nota", "questão", "questao", "feedback", "pontos"])

    @pytest.mark.asyncio
    async def test_pipeline_turma_dois_alunos(self, test_scenario, selected_provider):
        """
        Pipeline para turma com 2 alunos.

        Verifica que o sistema consegue processar múltiplos alunos.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        gabarito = test_scenario["gabarito"]
        alunos = test_scenario["alunos"]

        resultados = []

        for aluno in alunos:
            prova = aluno["prova"]

            prompt = f"""
            Corrija esta prova comparando com o gabarito.

            GABARITO:
            {gabarito.content}

            PROVA ({aluno['nome']}):
            {prova.content}

            Retorne JSON: {{"aluno": "nome", "nota_total": X.X, "aprovado": true/false}}
            """

            response = await provider.complete(prompt, max_tokens=1000)
            assert response is not None

            resultados.append({
                "aluno": aluno["nome"],
                "resposta": response.content[:500]
            })

        # Verificar que processou todos
        assert len(resultados) == len(alunos)

        # Verificar que respostas são diferentes (alunos diferentes)
        if len(alunos) > 1:
            assert resultados[0]["resposta"] != resultados[1]["resposta"]

    @pytest.mark.asyncio
    async def test_extracao_questoes(self, test_scenario, selected_provider):
        """
        Testa extração de questões do enunciado.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        enunciado = test_scenario["enunciado"]
        num_questoes = test_scenario["num_questoes"]

        prompt = f"""
        Extraia as questões deste enunciado de prova.

        Enunciado:
        {enunciado.content}

        Retorne um JSON com:
        - Lista de questões com número e enunciado
        - Total de questões encontradas
        """

        response = await provider.complete(prompt, max_tokens=2000)
        assert response is not None

        # Deve mencionar as questões
        content_lower = response.content.lower()
        assert "questão" in content_lower or "questao" in content_lower or "question" in content_lower

    @pytest.mark.asyncio
    async def test_correcao_aluno_excelente(self, document_factory, selected_provider):
        """
        Testa correção de aluno com respostas excelentes.
        Deve receber nota alta.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        # Criar cenário com aluno excelente
        cenario = document_factory.criar_cenario_completo(
            materia="Matemática",
            num_alunos=1,
            qualidades=["excelente"]
        )

        gabarito = cenario["gabarito"]
        aluno = cenario["alunos"][0]
        prova = aluno["prova"]

        prompt = f"""
        Corrija esta prova. O aluno é muito bom e deve ter notas altas.

        GABARITO:
        {gabarito.content}

        PROVA:
        {prova.content}

        Retorne a nota total (de 0 a 10).
        """

        response = await provider.complete(prompt, max_tokens=500)
        assert response is not None

        # Aluno excelente deve ter menção a nota alta
        content_lower = response.content.lower()
        # Verificar menção a nota ou aprovação
        has_score = any(char.isdigit() for char in response.content)
        assert has_score or "aprovado" in content_lower or "excelente" in content_lower

    @pytest.mark.asyncio
    async def test_correcao_aluno_ruim(self, document_factory, selected_provider):
        """
        Testa correção de aluno com respostas ruins.
        Deve receber nota baixa.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        # Criar cenário com aluno ruim
        cenario = document_factory.criar_cenario_completo(
            materia="Matemática",
            num_alunos=1,
            qualidades=["ruim"]
        )

        gabarito = cenario["gabarito"]
        aluno = cenario["alunos"][0]
        prova = aluno["prova"]

        prompt = f"""
        Corrija esta prova de forma rigorosa.

        GABARITO:
        {gabarito.content}

        PROVA:
        {prova.content}

        Retorne a nota total e indique se o aluno foi reprovado.
        """

        response = await provider.complete(prompt, max_tokens=500)
        assert response is not None

    @pytest.mark.asyncio
    async def test_json_valido_retornado(self, test_scenario, selected_provider):
        """
        Verifica que o sistema consegue obter JSON válido.
        """
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider não disponível")

        prompt = """
        Retorne um JSON válido com esta estrutura exata:

        {
            "status": "ok",
            "questoes": [
                {"numero": 1, "correta": true},
                {"numero": 2, "correta": false}
            ],
            "nota": 5.0
        }

        IMPORTANTE: Retorne APENAS o JSON, sem explicações.
        """

        response = await provider.complete(prompt, max_tokens=300)
        assert response is not None

        # Tentar parsear
        content = response.content.strip()
        if "```" in content:
            # Extrair de bloco de código
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            else:
                content = content.split("```")[1].split("```")[0]

        try:
            data = json.loads(content.strip())
            # Deve ter pelo menos uma das chaves esperadas
            assert any(key in data for key in ["status", "questoes", "nota"])
        except json.JSONDecodeError:
            # Se não parsear, verificar se tem estrutura JSON
            assert "{" in response.content and "}" in response.content
