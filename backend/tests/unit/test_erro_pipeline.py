"""
Tests for pipeline error framework (F2-T1, F3-T1, F4-T1).

F2-T1: Error constants, SeveridadeErro enum, criar_erro_pipeline() helper.
"""
import pytest
from datetime import datetime


class TestF2T1_ErrorFramework:
    """F2-T1: Framework de erros estruturados."""

    def test_erro_documento_faltante_constant_exists(self):
        """ERRO_DOCUMENTO_FALTANTE constant exists and is correct string."""
        from models import ERRO_DOCUMENTO_FALTANTE
        assert ERRO_DOCUMENTO_FALTANTE == "DOCUMENTO_FALTANTE"

    def test_erro_questoes_faltantes_constant_exists(self):
        """ERRO_QUESTOES_FALTANTES constant exists and is correct string."""
        from models import ERRO_QUESTOES_FALTANTES
        assert ERRO_QUESTOES_FALTANTES == "QUESTOES_FALTANTES"

    def test_severidade_erro_enum_has_critico(self):
        """SeveridadeErro enum has CRITICO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "CRITICO")
        assert SeveridadeErro.CRITICO.value == "critico"

    def test_severidade_erro_enum_has_alto(self):
        """SeveridadeErro enum has ALTO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "ALTO")
        assert SeveridadeErro.ALTO.value == "alto"

    def test_severidade_erro_enum_has_medio(self):
        """SeveridadeErro enum has MEDIO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "MEDIO")
        assert SeveridadeErro.MEDIO.value == "medio"

    def test_criar_erro_pipeline_returns_dict_with_all_fields(self):
        """criar_erro_pipeline() returns dict with tipo, mensagem, severidade, etapa, timestamp."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="Arquivo não encontrado",
            severidade=SeveridadeErro.CRITICO,
            etapa="extrair_questoes"
        )
        assert isinstance(result, dict)
        assert result["tipo"] == "DOCUMENTO_FALTANTE"
        assert result["mensagem"] == "Arquivo não encontrado"
        assert result["severidade"] == "critico"
        assert result["etapa"] == "extrair_questoes"
        assert "timestamp" in result

    def test_criar_erro_pipeline_timestamp_is_iso_format(self):
        """Timestamp field is a valid ISO format string."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="test",
            severidade=SeveridadeErro.CRITICO,
            etapa="corrigir"
        )
        # Should not raise
        datetime.fromisoformat(result["timestamp"])

    def test_criar_erro_pipeline_severidade_accepts_string(self):
        """criar_erro_pipeline() works when severidade is passed as string too."""
        from models import criar_erro_pipeline
        result = criar_erro_pipeline(
            tipo="QUESTOES_FALTANTES",
            mensagem="Nenhuma questão extraída",
            severidade="alto",
            etapa="extrair_questoes"
        )
        assert result["severidade"] == "alto"

    def test_criar_erro_pipeline_no_extra_fields(self):
        """Result dict has exactly the expected fields."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="test",
            severidade=SeveridadeErro.CRITICO,
            etapa="test_etapa"
        )
        expected_keys = {"tipo", "mensagem", "severidade", "etapa", "timestamp"}
        assert set(result.keys()) == expected_keys
