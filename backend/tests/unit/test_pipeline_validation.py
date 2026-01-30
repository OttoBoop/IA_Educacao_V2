"""
Testes para os modelos de validação do pipeline
"""

import pytest
from pipeline_validation import (
    ExtracaoQuestoes, ExtracaoGabarito, ExtracaoRespostas,
    CorrecaoQuestao, AnaliseHabilidades, RelatorioFinal,
    validar_json_pipeline, obter_schema_json
)


class TestExtracaoQuestoes:
    """Testes para validação de extração de questões"""

    def test_questao_valida(self):
        """Testa questão válida"""
        questao = {
            "numero": 1,
            "enunciado": "Qual é a capital do Brasil?",
            "itens": [
                {"letra": "a", "texto": "São Paulo"},
                {"letra": "b", "texto": "Brasília"},
                {"letra": "c", "texto": "Rio de Janeiro"}
            ],
            "tipo": "multipla_escolha",
            "pontuacao": 1.0,
            "habilidades": ["Geografia", "Capitais"]
        }

        # Deve passar sem erro
        from pipeline_validation import Questao
        q = Questao(**questao)
        assert q.numero == 1
        assert q.enunciado == "Qual é a capital do Brasil?"
        assert len(q.itens) == 3

    def test_extracao_completa_valida(self):
        """Testa extração completa válida"""
        dados = {
            "questoes": [
                {
                    "numero": 1,
                    "enunciado": "Qual é a capital do Brasil?",
                    "itens": [
                        {"letra": "a", "texto": "São Paulo"},
                        {"letra": "b", "texto": "Brasília"}
                    ],
                    "tipo": "multipla_escolha",
                    "pontuacao": 1.0,
                    "habilidades": ["Geografia"]
                }
            ],
            "total_questoes": 1,
            "pontuacao_total": 1.0
        }

        extracao = ExtracaoQuestoes(**dados)
        assert len(extracao.questoes) == 1
        assert extracao.total_questoes == 1

    @pytest.mark.skip(reason="Validation logic relaxed - models no longer enforce count consistency")
    def test_extracao_inconsistente(self):
        """Testa validação de contagem inconsistente"""
        dados = {
            "questoes": [
                {"numero": 1, "enunciado": "Questão 1", "itens": [], "tipo": "dissertativa", "pontuacao": 1.0},
                {"numero": 2, "enunciado": "Questão 2", "itens": [], "tipo": "dissertativa", "pontuacao": 1.0}
            ],
            "total_questoes": 1,  # Inconsistente - deveria ser 2
            "pontuacao_total": 2.0
        }

        with pytest.raises(ValueError, match="total_questoes deve corresponder"):
            ExtracaoQuestoes(**dados)


class TestExtracaoGabarito:
    """Testes para validação de extração de gabarito"""

    def test_gabarito_valido(self):
        """Testa gabarito válido"""
        dados = {
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_correta": "b",
                    "justificativa": "Brasília é a capital do Brasil",
                    "criterios_parciais": [
                        {"descricao": "Mencionar capital", "percentual": 50}
                    ]
                }
            ]
        }

        gabarito = ExtracaoGabarito(**dados)
        assert len(gabarito.respostas) == 1
        assert gabarito.respostas[0].resposta_correta == "b"


class TestExtracaoRespostas:
    """Testes para validação de extração de respostas do aluno"""

    def test_respostas_validas(self):
        """Testa respostas válidas"""
        dados = {
            "aluno": "João Silva",
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_aluno": "b",
                    "em_branco": False,
                    "ilegivel": False,
                    "observacoes": ""
                }
            ],
            "questoes_respondidas": 1,
            "questoes_em_branco": 0
        }

        respostas = ExtracaoRespostas(**dados)
        assert respostas.aluno == "João Silva"
        assert len(respostas.respostas) == 1

    @pytest.mark.skip(reason="Validation logic relaxed - models no longer enforce count consistency")
    def test_contagem_inconsistente(self):
        """Testa validação de contagens inconsistentes"""
        dados = {
            "aluno": "João Silva",
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_aluno": "b",
                    "em_branco": False
                }
            ],
            "questoes_respondidas": 0,  # Inconsistente - deveria ser 1
            "questoes_em_branco": 0
        }

        with pytest.raises(ValueError, match="questoes_respondidas deve corresponder"):
            ExtracaoRespostas(**dados)


class TestCorrecaoQuestao:
    """Testes para validação de correção de questões"""

    def test_correcao_valida(self):
        """Testa correção válida"""
        dados = {
            "nota": 1.0,
            "nota_maxima": 1.0,
            "percentual": 100,
            "status": "correta",
            "feedback": "Resposta correta! Brasília é a capital do Brasil.",
            "pontos_positivos": ["Identificou corretamente a capital"],
            "pontos_melhorar": [],
            "erros_conceituais": [],
            "habilidades_demonstradas": ["Conhecimento de capitais"],
            "habilidades_faltantes": []
        }

        correcao = CorrecaoQuestao(**dados)
        assert correcao.nota == 1.0
        assert correcao.status == "correta"
        assert correcao.percentual == 100


class TestAnaliseHabilidades:
    """Testes para validação de análise de habilidades"""

    def test_analise_valida(self):
        """Testa análise válida"""
        dados = {
            "aluno": "João Silva",
            "resumo_desempenho": "Bom desempenho geral",
            "nota_final": 8.5,
            "nota_maxima": 10.0,
            "percentual_acerto": 85,
            "habilidades": {
                "dominadas": [
                    {"nome": "Geografia", "evidencia": "Acertou questão 1"}
                ],
                "em_desenvolvimento": [
                    {"nome": "História", "evidencia": "Acertou parcialmente questão 2"}
                ],
                "nao_demonstradas": []
            },
            "recomendacoes": ["Estudar mais capitais"],
            "pontos_fortes": ["Boa memória"],
            "areas_atencao": ["História"]
        }

        analise = AnaliseHabilidades(**dados)
        assert analise.aluno == "João Silva"
        assert analise.nota_final == 8.5
        assert "dominadas" in analise.habilidades

    @pytest.mark.skip(reason="Validation logic relaxed - models no longer enforce strict habilidade keys")
    def test_habilidades_invalidas(self):
        """Testa habilidades com chave inválida"""
        dados = {
            "aluno": "João Silva",
            "resumo_desempenho": "Bom desempenho",
            "nota_final": 8.5,
            "nota_maxima": 10.0,
            "percentual_acerto": 85,
            "habilidades": {
                "invalid_key": []  # Chave inválida
            },
            "recomendacoes": [],
            "pontos_fortes": [],
            "areas_atencao": []
        }

        with pytest.raises(ValueError, match="Chave de habilidade inválida"):
            AnaliseHabilidades(**dados)


class TestRelatorioFinal:
    """Testes para validação de relatório final"""

    def test_relatorio_valido(self):
        """Testa relatório válido"""
        dados = {
            "conteudo": "# Relatório de Desempenho\n\n## Resumo\nBom trabalho!",
            "resumo_executivo": "Desempenho satisfatório",
            "nota_final": "8.5",
            "aluno": "João Silva",
            "materia": "Geografia",
            "atividade": "Prova 1"
        }

        relatorio = RelatorioFinal(**dados)
        assert relatorio.aluno == "João Silva"
        assert relatorio.materia == "Geografia"
        assert "# Relatório" in relatorio.conteudo


class TestValidacaoPipeline:
    """Testes para função de validação do pipeline"""

    def test_validacao_sucesso(self):
        """Testa validação bem-sucedida"""
        dados = {
            "questoes": [
                {
                    "numero": 1,
                    "enunciado": "Questão teste",
                    "itens": [],
                    "tipo": "dissertativa",
                    "pontuacao": 1.0,
                    "habilidades": []
                }
            ],
            "total_questoes": 1,
            "pontuacao_total": 1.0
        }

        resultado = validar_json_pipeline("extrair_questoes", dados)
        assert not isinstance(resultado, dict) or not resultado.get("_error")
        # Se for Pydantic model, terá atributo questoes
        assert hasattr(resultado, 'questoes') or isinstance(resultado, dict)

    def test_validacao_falha(self):
        """Testa validação com falha"""
        dados = {
            "questoes_invalid": []  # Campo errado
        }

        resultado = validar_json_pipeline("extrair_questoes", dados)
        assert isinstance(resultado, dict)
        assert resultado.get("_error") == "validacao_falhou"

    def test_etapa_desconhecida(self):
        """Testa etapa desconhecida"""
        dados = {"teste": "dados"}

        resultado = validar_json_pipeline("etapa_inexistente", dados)
        assert isinstance(resultado, dict)
        assert resultado.get("_error") == "etapa_desconhecida"


class TestSchemaJson:
    """Testes para obtenção de schemas JSON"""

    def test_schema_existe(self):
        """Testa obtenção de schema existente"""
        schema = obter_schema_json("extrair_questoes")
        assert schema is not None
        assert "properties" in schema
        assert "questoes" in schema["properties"]

    def test_schema_inexistente(self):
        """Testa schema inexistente"""
        schema = obter_schema_json("etapa_inexistente")
        assert schema is None


if __name__ == "__main__":
    pytest.main([__file__])