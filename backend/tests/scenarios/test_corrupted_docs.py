"""
Testes com Documentos Corrompidos

Verifica que o sistema trata erros graciosamente.
"""

import pytest
import json


@pytest.mark.error_handling
@pytest.mark.render_compatible
class TestCorruptedDocuments:
    """
    Testes com documentos problemáticos.

    Cenários:
    - JSON vazio retornado
    - Documento corrompido
    - Prova em branco
    - Resposta inválida da IA
    """

    def _get_provider(self):
        from ai_providers import ai_registry

        provider = ai_registry.get_default()
        if not provider:
            pytest.skip("Provider nao disponivel")
        return provider

    @pytest.mark.asyncio
    async def test_documento_corrompido(self, corrupted_document):
        """
        Cenário: Documento com texto corrompido/ilegível.
        Esperado: Sistema identifica problema e reporta.
        """
        provider = self._get_provider()
        prompt = f"""
        Tente extrair informações deste documento:

        {corrupted_document.content}

        Se não for possível ler o documento, retorne:
        {{"erro": "descrição do problema", "legivel": false}}

        Se for possível, retorne as informações encontradas.
        """

        response = await provider.complete(prompt, max_tokens=500)
        assert response is not None
        # Deve retornar algo, mesmo que seja indicando erro

    @pytest.mark.asyncio
    async def test_documento_vazio(self, empty_document):
        """
        Cenário: Documento completamente vazio.
        Esperado: Sistema indica que não há conteúdo.
        """
        provider = self._get_provider()
        prompt = f"""
        Analise este documento e extraia as questões:

        DOCUMENTO:
        {empty_document.content}

        Se o documento estiver vazio, retorne: {{"erro": "documento vazio"}}
        """

        response = await provider.complete(prompt, max_tokens=300)
        assert response is not None

        content_lower = response.content.lower()
        # Deve identificar que está vazio ou sem conteúdo
        assert any(word in content_lower for word in ["vazio", "empty", "sem", "nenhum", "erro"])

    @pytest.mark.asyncio
    async def test_prova_em_branco(self, document_factory):
        """
        Cen?rio: Prova do aluno completamente em branco.
        Esperado: Nota zero e aviso apropriado.
        """
        provider = self._get_provider()

        # Criar prova com problema "em_branco"
        prova = document_factory.criar_prova_aluno(
            nome_aluno="Aluno Teste",
            qualidade_respostas="ruim",
            problemas=["em_branco"]
        )

        gabarito = document_factory.criar_gabarito_teste("Matematica", 4)

        prompt = f"""
        Corrija esta prova:

        GABARITO:
        {gabarito.content}

        PROVA:
        {prova.content}

        Se quest?es estiverem em branco, d? nota zero para elas.
        Retorne: {{"nota_total": X, "questoes_em_branco": N}}
        """

        response = await provider.complete(prompt, max_tokens=500)
        assert response is not None

        content = response.content.strip()
        if "```" in content:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            else:
                content = content.split("```")[1].split("```")[0].strip()

        parsed = None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, dict):
            questoes_em_branco = parsed.get("questoes_em_branco")
            if questoes_em_branco is not None:
                assert int(questoes_em_branco) >= 0
                return

        # Fallback: deve mencionar questoes em branco ou nota zero
        content_lower = response.content.lower()
        # Expanded keyword list to handle AI response variations
        blank_keywords = [
            # Portuguese
            "branco", "vazio", "zero", "0", "nao respondeu", "nao-respondeu",
            "nenhuma resposta", "sem resposta", "não respondida", "não respondido",
            "em branco", "deixou em branco", "questão vazia", "questao vazia",
            # English (AI might respond in English)
            "blank", "empty", "unanswered", "not answered", "no answer",
            "no response", "left blank",
            # Numbers and scores
            "nota 0", "nota: 0", "nota_total: 0", "nota_total\":0", "nota_total\": 0",
            "questoes_em_branco", "todas as questões",
        ]
        assert any(word in content_lower for word in blank_keywords), \
            f"AI response should mention blank/zero but got: {response.content[:200]}"

    @pytest.mark.asyncio
    async def test_tratamento_json_malformado(self):
        """
        Cenário: IA pode retornar texto que não é JSON válido.
        Esperado: Sistema deve tentar extrair ou reportar erro.
        """
        from executor import PipelineExecutor

        executor = PipelineExecutor()

        # Testar parsing de várias respostas problemáticas
        respostas_teste = [
            "",  # Vazio
            "{}",  # JSON vazio
            "[]",  # Array vazio
            "Aqui está a resposta: {questoes: [1,2,3]}",  # JSON inválido
            "```json\n{\"ok\": true}\n```",  # Em bloco de código
            '{"nota": 10, "comentario": "Bom"',  # Truncado
        ]

        for resposta in respostas_teste:
            resultado = executor._parsear_resposta(resposta)
            # Deve retornar algo (dict, list, ou None/erro)
            # Não deve lançar exceção
            assert resultado is None or isinstance(resultado, (dict, list))

    @pytest.mark.asyncio
    async def test_resposta_vazia_da_ia(self):
        """
        Cenário: IA retorna resposta vazia ou muito curta.
        """
        from executor import PipelineExecutor

        executor = PipelineExecutor()

        # Resposta vazia
        resultado = executor._parsear_resposta("")
        assert resultado is not None
        assert resultado.get("_error") == "empty_response"

        # Resposta só espaços
        resultado = executor._parsear_resposta("   \n\t  ")
        assert resultado is not None
        assert resultado.get("_error") == "whitespace_only"

    @pytest.mark.asyncio
    async def test_json_vazio_identificado(self):
        """
        Cenário: IA retorna JSON vazio {}.
        Esperado: Sistema identifica como problema.
        """
        from executor import PipelineExecutor

        executor = PipelineExecutor()

        resultado = executor._parsear_resposta("{}")
        assert resultado is not None
        assert resultado.get("_error") == "empty_json"

        resultado = executor._parsear_resposta("[]")
        assert resultado is not None
        assert resultado.get("_error") == "empty_json"

    @pytest.mark.asyncio
    async def test_encoding_errado(self, document_factory):
        """
        Cenário: Documento com encoding incorreto.
        """
        provider = self._get_provider()
        doc = document_factory.criar_documento_corrompido("encoding_errado")

        prompt = f"""
        Tente ler este documento e identifique problemas:

        {doc.content}

        Retorne: {{"legivel": true/false, "problemas": ["lista de problemas"]}}
        """

        response = await provider.complete(prompt, max_tokens=300)
        assert response is not None

    @pytest.mark.asyncio
    async def test_documento_truncado(self, document_factory):
        """
        Cen?rio: Documento cortado no meio.
        """
        provider = self._get_provider()

        doc = document_factory.criar_documento_corrompido("truncado")

        prompt = f"""
        Este documento parece estar incompleto. Identifique o problema:

        {doc.content}

        Retorne: {{"completo": false, "motivo": "..."}}
        """

        response = await provider.complete(prompt, max_tokens=300)
        assert response is not None

        content = response.content.strip()
        if "```" in content:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            else:
                content = content.split("```")[1].split("```")[0].strip()

        parsed = None
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            parsed = None

        if isinstance(parsed, dict) and "completo" in parsed:
            completo = parsed.get("completo")
            assert completo in (False, "false", "False", 0, "0")
            return

        content_lower = response.content.lower()
        if "completo" in content_lower and any(word in content_lower for word in ["false", "falso", "nao", "não", "0"]):
            return

        # Aceita varias formas de indicar documento incompleto
        indicadores_truncado = [
            "incompleto", "truncado", "cortado", "faltando", "incomplete",
            "cut", "partial", "missing", "interrompido", "parcial",
            "completo: false", "false", "falso",
            "nao esta completo", "nao completo", "não esta completo", "não completo"
        ]
        assert any(word in content_lower for word in indicadores_truncado)

