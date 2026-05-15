"""
Testes para os modelos de validação do pipeline
"""

import pytest
from pipeline_validation import (
    ExtracaoQuestoes, ExtracaoGabarito, ExtracaoRespostas,
    CorrecaoQuestao, CorrecaoPipeline, AnaliseHabilidades, RelatorioFinal,
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

    def test_gabarito_todo_missing_content_falha_alto(self):
        """Gabarito com todas as respostas MISSING_CONTENT não pode ser sucesso."""
        dados = {
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_correta": "MISSING_CONTENT",
                    "justificativa": "nao encontrado",
                    "criterios_parciais": []
                },
                {
                    "questao_numero": 2,
                    "resposta_correta": "MISSING_CONTENT",
                    "justificativa": "nao encontrado",
                    "criterios_parciais": []
                },
            ]
        }

        with pytest.raises(ValueError, match="todas as respostas como MISSING_CONTENT"):
            ExtracaoGabarito(**dados)

    def test_validar_json_pipeline_rejeita_gabarito_todo_missing_content(self):
        """A função pública de validação deve retornar erro estruturado."""
        dados = {
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_correta": "MISSING_CONTENT",
                    "justificativa": "nao encontrado",
                    "criterios_parciais": []
                }
            ]
        }

        resultado = validar_json_pipeline("extrair_gabarito", dados)
        assert isinstance(resultado, dict)
        assert resultado.get("_error") == "validacao_falhou"


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


class TestCorrecaoPipeline:
    """Testes para o schema de correção usado pela pipeline."""

    def test_correcao_agregada_tool_use_valida(self):
        """CORRIGIR aceita o formato agregado descrito em STAGE_TOOL_INSTRUCTIONS."""
        dados = {
            "nota_final": 8.0,
            "questoes": [
                {"numero": 1, "nota": 4.0, "nota_maxima": 5.0, "acerto": True, "feedback": "ok"},
                {"numero": 2, "nota": 4.0, "nota_maxima": 5.0, "acerto": False, "feedback": "parcial"},
            ],
            "total_acertos": 1,
            "total_erros": 1,
            "feedback_geral": "Bom desempenho",
            "_avisos_documento": [
                {"codigo": "LOW_CONFIDENCE", "explicacao": "Leitura parcial"}
            ],
            "_avisos_questao": [],
        }

        resultado = validar_json_pipeline("corrigir", dados)
        assert isinstance(resultado, CorrecaoPipeline)
        assert resultado.nota_final == 8.0
        assert len(resultado.questoes) == 2
        assert resultado.avisos_documento[0]["codigo"] == "LOW_CONFIDENCE"

    def test_correcao_sem_nota_ou_questoes_falha(self):
        """CORRIGIR não deve aceitar JSON vazio como correção válida."""
        resultado = validar_json_pipeline("corrigir", {"feedback_geral": "sem dados"})
        assert isinstance(resultado, dict)
        assert resultado.get("_error") == "validacao_falhou"


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

    def test_analise_tool_use_valida(self):
        """ANALISAR_HABILIDADES aceita o formato de lista plana do tool-use."""
        dados = {
            "habilidades": [
                {"nome": "Interpretação", "nivel": "em_desenvolvimento", "nota": 6.0}
            ],
            "indicadores": {
                "proficiencia_geral": 6.0,
                "areas_destaque": [],
                "areas_atencao": ["Interpretação"],
            },
            "recomendacoes": [
                {"tipo": "estudo", "descricao": "Revisar gráficos", "prioridade": "alta"}
            ],
            "_avisos_documento": [],
            "_avisos_questao": [],
        }

        resultado = validar_json_pipeline("analisar_habilidades", dados)
        assert isinstance(resultado, AnaliseHabilidades)
        assert isinstance(resultado.habilidades, list)
        assert resultado.indicadores["proficiencia_geral"] == 6.0

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

    def test_relatorio_tool_use_valido(self):
        """GERAR_RELATORIO aceita o formato de tool-use sem perder linhagem."""
        dados = {
            "resumo_geral": "Aluno com bom raciocínio e lacunas pontuais.",
            "pontos_fortes": ["Organização"],
            "areas_melhoria": ["Justificativas"],
            "recomendacoes": [
                {"tipo": "pratica", "descricao": "Refazer Q2", "prioridade": "media"}
            ],
            "nota_final": 7.5,
            "detalhamento": "Detalhes por questão.",
            "_fontes_utilizadas": ["EXTRAIR_QUESTOES", "CORRIGIR", "ANALISAR_HABILIDADES"],
            "_avisos_documento": [],
            "_avisos_questao": [],
        }

        resultado = validar_json_pipeline("gerar_relatorio", dados)
        assert isinstance(resultado, RelatorioFinal)
        assert resultado.resumo_geral.startswith("Aluno")
        assert resultado.fontes_utilizadas == [
            "EXTRAIR_QUESTOES", "CORRIGIR", "ANALISAR_HABILIDADES"
        ]


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

    @pytest.mark.parametrize("etapa", [
        "extrair_questoes",
        "extrair_gabarito",
        "extrair_respostas",
        "corrigir",
        "analisar_habilidades",
        "gerar_relatorio",
    ])
    def test_schema_inclui_avisos_aliases(self, etapa):
        """Schemas oficiais expõem os aliases JSON _avisos_* usados na pipeline."""
        schema = obter_schema_json(etapa)
        assert "_avisos_documento" in schema["properties"]
        assert "_avisos_questao" in schema["properties"]

    def test_schema_relatorio_inclui_fontes_utilizadas_alias(self):
        """Schema oficial do relatório expõe a linhagem usada pelo visualizador."""
        schema = obter_schema_json("gerar_relatorio")
        assert "_fontes_utilizadas" in schema["properties"]


if __name__ == "__main__":
    pytest.main([__file__])
