"""
Testes unitários para modelos do executor.

Verifica que ResultadoExecucao e outras classes têm os atributos corretos.
"""

import pytest
from dataclasses import fields


class TestResultadoExecucao:
    """Testes para a classe ResultadoExecucao"""

    def test_required_attributes_exist(self):
        """Verifica que ResultadoExecucao tem todos os atributos esperados"""
        from executor import ResultadoExecucao, EtapaProcessamento

        # Criar instância mínima
        resultado = ResultadoExecucao(
            sucesso=True,
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES
        )

        # Atributos que DEVEM existir
        required_attrs = [
            'sucesso',
            'etapa',
            'prompt_usado',
            'prompt_id',
            'provider',
            'modelo',
            'resposta_raw',
            'resposta_parsed',
            'tokens_entrada',
            'tokens_saida',
            'tempo_ms',
            'documento_id',  # NÃO documento_gerado
            'anexos_enviados',
            'anexos_confirmados',
            'alertas',
            'erro',  # NÃO mensagem
        ]

        for attr in required_attrs:
            assert hasattr(resultado, attr), f"ResultadoExecucao missing attribute: {attr}"

    def test_no_invalid_attributes(self):
        """Verifica que atributos inválidos NÃO existem"""
        from executor import ResultadoExecucao, EtapaProcessamento

        resultado = ResultadoExecucao(
            sucesso=False,
            etapa=EtapaProcessamento.CORRIGIR,
            erro="Test error"
        )

        # Atributos que NÃO devem existir (erros comuns)
        invalid_attrs = [
            'mensagem',  # Correto é 'erro'
            'documento_gerado',  # Correto é 'documento_id'
            'message',  # English variant
        ]

        for attr in invalid_attrs:
            assert not hasattr(resultado, attr), f"ResultadoExecucao should NOT have attribute: {attr}"

    def test_to_dict_returns_correct_keys(self):
        """Verifica que to_dict retorna todas as chaves esperadas"""
        from executor import ResultadoExecucao, EtapaProcessamento

        resultado = ResultadoExecucao(
            sucesso=True,
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
            erro="Test error"
        )

        result_dict = resultado.to_dict()

        expected_keys = {
            'sucesso', 'etapa', 'prompt_id', 'provider', 'modelo',
            'resposta_raw', 'resposta_parsed', 'tokens_entrada',
            'tokens_saida', 'tempo_ms', 'documento_id',
            'anexos_enviados', 'anexos_confirmados', 'alertas', 'erro',
            'erro_codigo', 'retryable', 'retry_after', 'tentativas'
        }

        assert set(result_dict.keys()) == expected_keys

    def test_erro_field_works(self):
        """Verifica que o campo 'erro' funciona corretamente"""
        from executor import ResultadoExecucao, EtapaProcessamento

        error_msg = "Atividade não encontrada"
        resultado = ResultadoExecucao(
            sucesso=False,
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
            erro=error_msg
        )

        assert resultado.erro == error_msg
        assert resultado.to_dict()['erro'] == error_msg


class TestExecutorMethods:
    """Testes para métodos do PipelineExecutor"""

    def test_erro_method_returns_correct_structure(self):
        """Verifica que _erro() retorna ResultadoExecucao com atributos corretos"""
        from executor import PipelineExecutor, EtapaProcessamento

        executor = PipelineExecutor()
        result = executor._erro(
            EtapaProcessamento.EXTRAIR_QUESTOES,
            "Test error message"
        )

        assert result.sucesso == False
        assert result.erro == "Test error message"
        assert hasattr(result, 'documento_id')
        assert not hasattr(result, 'documento_gerado')
        assert not hasattr(result, 'mensagem')


class TestParsearResposta:
    """Testes para o método _parsear_resposta"""

    def test_empty_response(self):
        """Verifica tratamento de resposta vazia"""
        from executor import PipelineExecutor

        executor = PipelineExecutor()
        result = executor._parsear_resposta("")

        assert result is not None
        assert result.get("_error") == "empty_response"

    def test_whitespace_only(self):
        """Verifica tratamento de resposta só com espaços"""
        from executor import PipelineExecutor

        executor = PipelineExecutor()
        result = executor._parsear_resposta("   \n\t  ")

        assert result is not None
        assert result.get("_error") == "whitespace_only"

    def test_empty_json(self):
        """Verifica tratamento de JSON vazio"""
        from executor import PipelineExecutor

        executor = PipelineExecutor()

        # JSON vazio {}
        result = executor._parsear_resposta("{}")
        assert result is not None
        assert result.get("_error") == "empty_json"

        # Array vazio []
        result = executor._parsear_resposta("[]")
        assert result is not None
        assert result.get("_error") == "empty_json"

    def test_valid_json(self):
        """Verifica que JSON válido é parseado corretamente"""
        from executor import PipelineExecutor

        executor = PipelineExecutor()
        result = executor._parsear_resposta('{"questoes": [1, 2, 3]}')

        assert result is not None
        assert "_error" not in result
        assert result.get("questoes") == [1, 2, 3]

    def test_json_in_code_block(self):
        """Verifica extração de JSON de bloco de código"""
        from executor import PipelineExecutor

        executor = PipelineExecutor()
        result = executor._parsear_resposta('```json\n{"ok": true}\n```')

        assert result is not None
        assert result.get("ok") == True
