"""
Warning Visualizador Tests — F3-T1 (avisos in VisaoAluno) + F4-T1 (lineage)

Tests that visualizador reads _avisos fields from JSON documents
and includes them in VisaoAluno.to_dict() with computed severity.
Also tests _fontes_utilizadas lineage for GERAR_RELATORIO.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_warning_visualizador.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# F3-T1: VisaoAluno includes avisos with severity
# ============================================================

class TestVisaoAlunoAvisosFields:
    """F3-T1: VisaoAluno dataclass has avisos fields and to_dict includes them."""

    def _make_visao(self, **overrides):
        """Create a minimal VisaoAluno with defaults."""
        from visualizador import VisaoAluno

        defaults = dict(
            aluno_id="a1", aluno_nome="Test",
            atividade_id="at1", atividade_nome="Prova",
            nota_final=8.0, nota_maxima=10.0, percentual=80.0,
            total_questoes=4, questoes_corretas=3,
            questoes_parciais=0, questoes_incorretas=1, questoes_branco=0,
        )
        defaults.update(overrides)
        return VisaoAluno(**defaults)

    def test_avisos_documento_field_exists(self):
        """VisaoAluno must have avisos_documento list field."""
        visao = self._make_visao()
        assert hasattr(visao, "avisos_documento"), (
            "VisaoAluno missing 'avisos_documento' field"
        )
        assert isinstance(visao.avisos_documento, list)

    def test_avisos_questao_field_exists(self):
        """VisaoAluno must have avisos_questao list field."""
        visao = self._make_visao()
        assert hasattr(visao, "avisos_questao"), (
            "VisaoAluno missing 'avisos_questao' field"
        )
        assert isinstance(visao.avisos_questao, list)

    def test_to_dict_includes_avisos_documento(self):
        """to_dict() must include avisos_documento with severity."""
        warnings = [
            {"codigo": "ILLEGIBLE_DOCUMENT", "explicacao": "PDF too blurry"}
        ]
        visao = self._make_visao(avisos_documento=warnings)
        d = visao.to_dict()
        assert "avisos_documento" in d, "to_dict() missing 'avisos_documento'"
        assert len(d["avisos_documento"]) == 1
        w = d["avisos_documento"][0]
        assert w["codigo"] == "ILLEGIBLE_DOCUMENT"
        assert w["explicacao"] == "PDF too blurry"
        assert "severidade" in w, "Warning must have computed 'severidade'"

    def test_to_dict_includes_avisos_questao(self):
        """to_dict() must include avisos_questao with severity and questao number."""
        warnings = [
            {"codigo": "ILLEGIBLE_QUESTION", "questao": 3, "explicacao": "Handwriting unreadable"}
        ]
        visao = self._make_visao(avisos_questao=warnings)
        d = visao.to_dict()
        assert "avisos_questao" in d, "to_dict() missing 'avisos_questao'"
        assert len(d["avisos_questao"]) == 1
        w = d["avisos_questao"][0]
        assert w["codigo"] == "ILLEGIBLE_QUESTION"
        assert w["questao"] == 3
        assert "severidade" in w

    def test_severity_computed_from_stage(self):
        """Severity must be computed using get_warning_severity with the stage context."""
        # MISSING_CONTENT in CORRIGIR should be yellow
        warnings = [
            {"codigo": "MISSING_CONTENT", "explicacao": "Aluno pulou questao"}
        ]
        visao = self._make_visao(
            avisos_documento=warnings,
            _avisos_stage="CORRIGIR",
        )
        d = visao.to_dict()
        w = d["avisos_documento"][0]
        assert w["severidade"] == "yellow", (
            f"MISSING_CONTENT in CORRIGIR should be yellow, got {w['severidade']}"
        )

    def test_severity_orange_in_extraction_stage(self):
        """MISSING_CONTENT in EXTRAIR_QUESTOES should be orange."""
        warnings = [
            {"codigo": "MISSING_CONTENT", "explicacao": "Content missing"}
        ]
        visao = self._make_visao(
            avisos_documento=warnings,
            _avisos_stage="EXTRAIR_QUESTOES",
        )
        d = visao.to_dict()
        w = d["avisos_documento"][0]
        assert w["severidade"] == "orange", (
            f"MISSING_CONTENT in EXTRAIR_QUESTOES should be orange, got {w['severidade']}"
        )

    def test_empty_avisos_when_none_present(self):
        """When no warnings exist, to_dict() should have empty lists."""
        visao = self._make_visao()
        d = visao.to_dict()
        assert d.get("avisos_documento") == [], "Should be empty list, not missing"
        assert d.get("avisos_questao") == [], "Should be empty list, not missing"

    def test_multiple_warnings_each_gets_severity(self):
        """Multiple warnings should each have their own severity computed."""
        warnings = [
            {"codigo": "ILLEGIBLE_DOCUMENT", "explicacao": "Blurry"},
            {"codigo": "MISSING_CONTENT", "explicacao": "Missing"},
        ]
        visao = self._make_visao(
            avisos_documento=warnings,
            _avisos_stage="CORRIGIR",
        )
        d = visao.to_dict()
        assert len(d["avisos_documento"]) == 2
        assert d["avisos_documento"][0]["severidade"] == "orange"  # ILLEGIBLE_DOCUMENT
        assert d["avisos_documento"][1]["severidade"] == "yellow"  # MISSING_CONTENT in CORRIGIR


class TestVisaoAlunoReadsAvisosFromJson:
    """F3-T1: _processar_correcao reads _avisos from JSON into VisaoAluno."""

    def test_processar_correcao_reads_avisos_documento(self):
        """_processar_correcao must populate avisos_documento from JSON."""
        from visualizador import VisualizadorResultados, VisaoAluno

        viz = VisualizadorResultados()
        visao = VisaoAluno(
            aluno_id="a1", aluno_nome="Test",
            atividade_id="at1", atividade_nome="Prova",
            nota_final=0, nota_maxima=10, percentual=0,
            total_questoes=0, questoes_corretas=0,
            questoes_parciais=0, questoes_incorretas=0, questoes_branco=0,
        )

        data = {
            "nota_final": 7.5,
            "questoes": [
                {"numero": 1, "nota": 7.5, "nota_maxima": 10, "acerto": True, "feedback": "ok"}
            ],
            "total_acertos": 1,
            "total_erros": 0,
            "feedback_geral": "Good",
            "_avisos_documento": [
                {"codigo": "LOW_CONFIDENCE", "explicacao": "Scan quality poor"}
            ],
            "_avisos_questao": [
                {"codigo": "ILLEGIBLE_QUESTION", "questao": 1, "explicacao": "Handwriting messy"}
            ],
        }

        viz._processar_correcao(visao, data)

        assert len(visao.avisos_documento) == 1, "Should have 1 document-level warning"
        assert visao.avisos_documento[0]["codigo"] == "LOW_CONFIDENCE"
        assert len(visao.avisos_questao) == 1, "Should have 1 question-level warning"
        assert visao.avisos_questao[0]["questao"] == 1

    def test_processar_correcao_no_avisos_returns_empty(self):
        """Old JSON without _avisos should leave empty lists (no crash)."""
        from visualizador import VisualizadorResultados, VisaoAluno

        viz = VisualizadorResultados()
        visao = VisaoAluno(
            aluno_id="a1", aluno_nome="Test",
            atividade_id="at1", atividade_nome="Prova",
            nota_final=0, nota_maxima=10, percentual=0,
            total_questoes=0, questoes_corretas=0,
            questoes_parciais=0, questoes_incorretas=0, questoes_branco=0,
        )

        data = {
            "nota_final": 7.5,
            "questoes": [],
            "total_acertos": 0,
            "total_erros": 0,
            "feedback_geral": "ok",
        }

        viz._processar_correcao(visao, data)

        assert visao.avisos_documento == [], "Should be empty list for old JSON"
        assert visao.avisos_questao == [], "Should be empty list for old JSON"


# ============================================================
# F4-T1: GERAR_RELATORIO lineage (_fontes_utilizadas)
# ============================================================

class TestFontesUtilizadas:
    """F4-T1: VisaoAluno.to_dict() includes fontes_utilizadas from relatorio JSON."""

    def _make_visao(self, **overrides):
        from visualizador import VisaoAluno
        defaults = dict(
            aluno_id="a1", aluno_nome="Test",
            atividade_id="at1", atividade_nome="Prova",
            nota_final=8.0, nota_maxima=10.0, percentual=80.0,
            total_questoes=4, questoes_corretas=3,
            questoes_parciais=0, questoes_incorretas=1, questoes_branco=0,
        )
        defaults.update(overrides)
        return VisaoAluno(**defaults)

    def test_fontes_utilizadas_field_exists(self):
        """VisaoAluno must have fontes_utilizadas field."""
        visao = self._make_visao()
        assert hasattr(visao, "fontes_utilizadas"), (
            "VisaoAluno missing 'fontes_utilizadas' field"
        )

    def test_to_dict_includes_fontes_when_present(self):
        """to_dict() must include fontes_utilizadas when set."""
        fontes = ["EXTRAIR_QUESTOES", "CORRIGIR", "ANALISAR_HABILIDADES"]
        visao = self._make_visao(fontes_utilizadas=fontes)
        d = visao.to_dict()
        assert "fontes_utilizadas" in d
        assert d["fontes_utilizadas"] == fontes

    def test_to_dict_fontes_null_when_absent(self):
        """to_dict() must include fontes_utilizadas as None when not set."""
        visao = self._make_visao()
        d = visao.to_dict()
        assert "fontes_utilizadas" in d
        assert d["fontes_utilizadas"] is None
