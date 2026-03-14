"""
RED tests for Resultado Final Wiring (F2-T1 / F4-T1).

Tests that _processar_correcao() handles the STAGE_TOOL_INSTRUCTIONS format
(with questoes[], nota_final, total_acertos) that the AI is instructed to produce.

Also tests that existing formats (correcoes[], nota, resposta_raw) still work.
"""
import pytest
from visualizador import VisualizadorResultados, VisaoAluno, VisaoQuestao


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_visao(**overrides) -> VisaoAluno:
    """Create a blank VisaoAluno for testing _processar_correcao()."""
    defaults = dict(
        aluno_id="a1",
        aluno_nome="Test Student",
        atividade_id="at1",
        atividade_nome="Test Activity",
        nota_final=0,
        nota_maxima=10,
        percentual=0,
        total_questoes=0,
        questoes_corretas=0,
        questoes_parciais=0,
        questoes_incorretas=0,
        questoes_branco=0,
    )
    defaults.update(overrides)
    return VisaoAluno(**defaults)


VIS = VisualizadorResultados()


# ===================================================================
# Feature 2/4: STAGE_TOOL_INSTRUCTIONS format ("questoes" + "nota_final")
# ===================================================================

class TestProcessarCorrecaoStageToolFormat:
    """Tests for the JSON format defined in STAGE_TOOL_INSTRUCTIONS for CORRIGIR."""

    def test_nota_final_extracted(self):
        """nota_final field at top level should set visao.nota_final."""
        data = {
            "nota_final": 7.5,
            "questoes": [
                {"numero": 1, "nota": 5.0, "nota_maxima": 5.0, "acerto": True, "feedback": "Correto"},
                {"numero": 2, "nota": 2.5, "nota_maxima": 5.0, "acerto": False, "feedback": "Parcial"},
            ],
            "total_acertos": 1,
            "total_erros": 1,
            "feedback_geral": "Bom desempenho",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.nota_final == 7.5, f"Expected nota_final=7.5, got {visao.nota_final}"

    def test_questoes_array_creates_visao_questoes(self):
        """questoes[] array should create VisaoQuestao objects."""
        data = {
            "nota_final": 8.0,
            "questoes": [
                {"numero": 1, "nota": 5.0, "nota_maxima": 5.0, "acerto": True, "feedback": "Perfeito"},
                {"numero": 2, "nota": 3.0, "nota_maxima": 5.0, "acerto": False, "feedback": "Incompleto"},
            ],
            "total_acertos": 1,
            "total_erros": 1,
            "feedback_geral": "Bom trabalho",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert len(visao.questoes) == 2, f"Expected 2 questions, got {len(visao.questoes)}"
        assert visao.questoes[0].numero == 1
        assert visao.questoes[1].numero == 2

    def test_total_questoes_set_from_questoes_length(self):
        """total_questoes should equal the length of questoes[] array."""
        data = {
            "nota_final": 6.0,
            "questoes": [
                {"numero": 1, "nota": 3.0, "nota_maxima": 5.0, "acerto": False, "feedback": ""},
                {"numero": 2, "nota": 3.0, "nota_maxima": 5.0, "acerto": False, "feedback": ""},
            ],
            "total_acertos": 0,
            "total_erros": 2,
            "feedback_geral": "",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.total_questoes == 2

    def test_acertos_counted_from_acerto_bool(self):
        """acerto=True in questoes[] should increment questoes_corretas."""
        data = {
            "nota_final": 10.0,
            "questoes": [
                {"numero": 1, "nota": 5.0, "nota_maxima": 5.0, "acerto": True, "feedback": "OK"},
                {"numero": 2, "nota": 5.0, "nota_maxima": 5.0, "acerto": True, "feedback": "OK"},
                {"numero": 3, "nota": 0.0, "nota_maxima": 5.0, "acerto": False, "feedback": "Errado"},
            ],
            "total_acertos": 2,
            "total_erros": 1,
            "feedback_geral": "",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.questoes_corretas == 2, f"Expected 2 correct, got {visao.questoes_corretas}"
        assert visao.questoes_incorretas == 1, f"Expected 1 incorrect, got {visao.questoes_incorretas}"

    def test_feedback_geral_set(self):
        """feedback_geral should be set from top-level field."""
        data = {
            "nota_final": 5.0,
            "questoes": [],
            "total_acertos": 0,
            "total_erros": 0,
            "feedback_geral": "Precisa melhorar na interpretação de texto",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.feedback_geral == "Precisa melhorar na interpretação de texto"

    def test_percentual_calculated(self):
        """percentual should be calculated from nota_final and nota_maxima."""
        data = {
            "nota_final": 7.0,
            "questoes": [
                {"numero": 1, "nota": 7.0, "nota_maxima": 10.0, "acerto": True, "feedback": ""},
            ],
            "total_acertos": 1,
            "total_erros": 0,
            "feedback_geral": "",
        }
        visao = _make_visao(nota_maxima=10.0)
        VIS._processar_correcao(visao, data)

        assert visao.percentual == pytest.approx(70.0, abs=0.1)

    def test_questao_nota_and_feedback_mapped(self):
        """Individual question nota, nota_maxima, and feedback should be mapped to VisaoQuestao."""
        data = {
            "nota_final": 3.5,
            "questoes": [
                {"numero": 1, "nota": 3.5, "nota_maxima": 5.0, "acerto": False, "feedback": "Faltou detalhe"},
            ],
            "total_acertos": 0,
            "total_erros": 1,
            "feedback_geral": "",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        q = visao.questoes[0]
        assert q.nota == 3.5
        assert q.nota_maxima == 5.0
        assert q.feedback == "Faltou detalhe"


# ===================================================================
# Existing Format 2: "correcoes" array (should still work)
# ===================================================================

class TestProcessarCorrecaoExistingFormats:
    """Confirm existing formats are not broken by the new format handler."""

    def test_correcoes_format_still_works(self):
        """Format 2 with correcoes[] should still extract data correctly."""
        data = {
            "correcoes": [
                {
                    "questao_numero": 1,
                    "nota": 10.0,
                    "nota_maxima": 10.0,
                    "status": "correta",
                    "feedback": "Perfeito",
                },
                {
                    "questao_numero": 2,
                    "nota": 5.0,
                    "nota_maxima": 10.0,
                    "status": "parcial",
                    "feedback": "Faltou conclusão",
                },
            ]
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.nota_final == 15.0
        assert visao.total_questoes == 2
        assert visao.questoes_corretas == 1
        assert visao.questoes_parciais == 1

    def test_single_nota_format_still_works(self):
        """Format 1 with top-level 'nota' should still work."""
        data = {
            "nota": 8.0,
            "status": "correta",
            "feedback": "Excelente resposta",
        }
        visao = _make_visao(nota_maxima=10.0)
        VIS._processar_correcao(visao, data)

        assert visao.nota_final == 8.0
        assert visao.questoes_corretas == 1

    def test_resposta_raw_fallback_sets_feedback(self):
        """Format 3 with resposta_raw should set feedback_geral."""
        data = {
            "resposta_raw": "O aluno demonstrou bom conhecimento..."
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.feedback_geral == "O aluno demonstrou bom conhecimento..."
        assert visao.nota_final == 0  # No structured data


# ===================================================================
# N/A / incomplete data flag
# ===================================================================

class TestIncompleteDataFlag:
    """When structured data is missing, visao should indicate incomplete state."""

    def test_resposta_raw_only_leaves_zero_nota_and_flags_incomplete(self):
        """When only resposta_raw is present, nota_final stays 0 and dados_incompletos=True."""
        data = {"resposta_raw": "Texto narrativo..."}
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.nota_final == 0
        assert visao.total_questoes == 0
        assert visao.dados_incompletos is True

    def test_empty_data_leaves_zero_nota_and_flags_incomplete(self):
        """When data is empty dict, nota_final stays 0 and dados_incompletos=True."""
        visao = _make_visao()
        VIS._processar_correcao(visao, {})

        assert visao.nota_final == 0
        assert visao.total_questoes == 0
        assert visao.dados_incompletos is True

    def test_structured_data_not_flagged_incomplete(self):
        """Structured data should NOT set dados_incompletos."""
        data = {
            "nota_final": 8.0,
            "questoes": [
                {"numero": 1, "nota": 8.0, "nota_maxima": 10.0, "acerto": True, "feedback": "OK"},
            ],
            "total_acertos": 1,
            "total_erros": 0,
            "feedback_geral": "Bom",
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.dados_incompletos is False

    def test_dados_incompletos_in_to_dict(self):
        """dados_incompletos should appear in to_dict() output."""
        visao = _make_visao()
        visao.dados_incompletos = True
        d = visao.to_dict()
        assert d["dados_incompletos"] is True


# ===================================================================
# Warning fields (F6-T1): _documento_ilegivel, _campos_faltantes
# ===================================================================

class TestWarningFieldsAccepted:
    """Warning fields should not break parsing and should be preserved."""

    def test_warning_fields_dont_break_correcao_parsing(self):
        """JSON with _documento_ilegivel should still parse correctly."""
        data = {
            "nota_final": 5.0,
            "questoes": [
                {"numero": 1, "nota": 5.0, "nota_maxima": 10.0, "acerto": False, "feedback": "OK"},
            ],
            "total_acertos": 0,
            "total_erros": 1,
            "feedback_geral": "Parcial",
            "_documento_ilegivel": False,
            "_campos_faltantes": [],
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.nota_final == 5.0
        assert visao.total_questoes == 1

    def test_warning_fields_with_illegible_document(self):
        """When _documento_ilegivel is True, structured data may be partial but should still parse."""
        data = {
            "nota_final": 0.0,
            "questoes": [],
            "total_acertos": 0,
            "total_erros": 0,
            "feedback_geral": "Documento não pôde ser lido adequadamente",
            "_documento_ilegivel": True,
            "_campos_faltantes": ["questoes", "nota_final"],
        }
        visao = _make_visao()
        VIS._processar_correcao(visao, data)

        assert visao.feedback_geral == "Documento não pôde ser lido adequadamente"
        assert visao.nota_final == 0.0


# ===================================================================
# _processar_analise with STAGE_TOOL_INSTRUCTIONS format
# ===================================================================

class TestProcessarAnaliseStageToolFormat:
    """Tests for the ANALISAR_HABILIDADES format from STAGE_TOOL_INSTRUCTIONS."""

    def test_habilidades_list_format(self):
        """STAGE_TOOL_INSTRUCTIONS format has habilidades as list of dicts with nome/nivel."""
        data = {
            "habilidades": [
                {"nome": "Pensamento Crítico", "nivel": "avançado", "evidencias": ["arg1"], "nota": 9.0},
                {"nome": "Resolução de Problemas", "nivel": "intermediário", "evidencias": [], "nota": 7.0},
            ],
            "indicadores": {
                "proficiencia_geral": 8.0,
                "areas_destaque": ["Pensamento Crítico"],
                "areas_atencao": ["Escrita"],
            },
            "recomendacoes": [
                {"tipo": "estudo", "descricao": "Pratique redação", "prioridade": "alta"},
            ],
        }
        visao = _make_visao()
        VIS._processar_analise(visao, data)

        # Current _processar_analise expects habilidades as a dict with
        # "dominadas", "em_desenvolvimento", "nao_demonstradas" keys.
        # The STAGE_TOOL_INSTRUCTIONS format is a flat list.
        # The visualizador needs to handle this format too.
        assert len(visao.habilidades_demonstradas) > 0 or len(visao.habilidades_faltantes) > 0, \
            "Expected at least some habilidades extracted from list format"

    def test_existing_dict_format_still_works(self):
        """Existing dict format with dominadas/em_desenvolvimento should still work."""
        data = {
            "habilidades": {
                "dominadas": [{"nome": "Leitura"}, "Escrita"],
                "em_desenvolvimento": [],
                "nao_demonstradas": [{"nome": "Cálculo"}],
            },
            "recomendacoes": ["Estudar mais matemática"],
        }
        visao = _make_visao()
        VIS._processar_analise(visao, data)

        assert "Leitura" in visao.habilidades_demonstradas
        assert "Escrita" in visao.habilidades_demonstradas
        assert "Cálculo" in visao.habilidades_faltantes
        assert "Estudar mais matemática" in visao.recomendacoes
