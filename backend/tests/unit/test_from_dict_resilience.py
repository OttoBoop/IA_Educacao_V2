"""Tests for from_dict() resilience against bad database data.

These tests verify that model from_dict() methods handle corrupted or
unexpected database values gracefully — returning a usable object with
sensible fallbacks instead of raising ValueError or TypeError.

RED phase: all tests in this file should FAIL until the safety wrappers
are implemented in models.py.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models import (
    Materia,
    Turma,
    Aluno,
    Atividade,
    Documento,
    NivelEnsino,
    StatusProcessamento,
    TipoDocumento,
)


class TestMateriaFromDictResilience:
    """Materia.from_dict() must not crash on bad enum values or datetime strings."""

    def test_invalid_nivel_enum_uses_fallback(self):
        """nivel with a value not in NivelEnsino should fall back to OUTRO, not raise."""
        data = {"id": "m1", "nome": "Math", "nivel": "NONEXISTENT_NIVEL"}
        mat = Materia.from_dict(data)
        assert mat.id == "m1"
        assert mat.nivel == NivelEnsino.OUTRO

    def test_malformed_criado_em(self):
        """A non-ISO criado_em string should not raise — object is still created."""
        data = {"id": "m1", "nome": "Math", "criado_em": "not-a-date"}
        mat = Materia.from_dict(data)
        assert mat.id == "m1"

    def test_none_criado_em_value(self):
        """criado_em key present with value None should not raise."""
        data = {"id": "m1", "nome": "Math", "criado_em": None}
        mat = Materia.from_dict(data)
        assert mat.id == "m1"


class TestTurmaFromDictResilience:
    """Turma.from_dict() must not crash on bad datetime strings."""

    def test_malformed_criado_em(self):
        """A non-ISO criado_em string should not raise — object is still created."""
        data = {
            "id": "t1",
            "materia_id": "m1",
            "nome": "9A",
            "criado_em": "broken-date",
        }
        turma = Turma.from_dict(data)
        assert turma.id == "t1"

    def test_none_criado_em_value(self):
        """criado_em key present with value None should not raise."""
        data = {
            "id": "t1",
            "materia_id": "m1",
            "nome": "9A",
            "criado_em": None,
        }
        turma = Turma.from_dict(data)
        assert turma.id == "t1"


class TestAlunoFromDictResilience:
    """Aluno.from_dict() must not crash on bad datetime strings."""

    def test_malformed_criado_em(self):
        """A non-ISO criado_em string should not raise — object is still created."""
        data = {"id": "a1", "nome": "Joao", "criado_em": "invalid"}
        aluno = Aluno.from_dict(data)
        assert aluno.id == "a1"

    def test_none_atualizado_em_value(self):
        """atualizado_em key present with value None should not raise."""
        data = {"id": "a1", "nome": "Joao", "atualizado_em": None}
        aluno = Aluno.from_dict(data)
        assert aluno.id == "a1"


class TestAtividadeFromDictResilience:
    """Atividade.from_dict() must not crash on bad datetime strings."""

    def test_malformed_criado_em(self):
        """A non-ISO criado_em string should not raise — object is still created."""
        data = {
            "id": "at1",
            "turma_id": "t1",
            "nome": "Prova",
            "criado_em": "bad",
        }
        ativ = Atividade.from_dict(data)
        assert ativ.id == "at1"

    def test_malformed_data_aplicacao(self):
        """A non-ISO data_aplicacao string should not raise — field treated as no date."""
        data = {
            "id": "at1",
            "turma_id": "t1",
            "nome": "Prova",
            "data_aplicacao": "not-a-date",
        }
        ativ = Atividade.from_dict(data)
        assert ativ.id == "at1"

    def test_none_data_aplicacao_value(self):
        """data_aplicacao key present with value None should produce None field — regression guard."""
        data = {
            "id": "at1",
            "turma_id": "t1",
            "nome": "Prova",
            "data_aplicacao": None,
        }
        ativ = Atividade.from_dict(data)
        assert ativ.id == "at1"
        assert ativ.data_aplicacao is None


class TestDocumentoFromDictResilience:
    """Documento.from_dict() must not crash on bad enum values or datetime strings."""

    def test_invalid_status_enum_uses_fallback(self):
        """status with a value not in StatusProcessamento should fall back to CONCLUIDO."""
        data = {
            "id": "d1",
            "tipo": "enunciado",
            "atividade_id": "a1",
            "status": "NONEXISTENT_STATUS",
        }
        doc = Documento.from_dict(data)
        assert doc.id == "d1"
        assert doc.status == StatusProcessamento.CONCLUIDO

    def test_malformed_criado_em(self):
        """A non-ISO criado_em string should not raise — object is still created."""
        data = {
            "id": "d1",
            "tipo": "enunciado",
            "atividade_id": "a1",
            "criado_em": "not-a-date",
        }
        doc = Documento.from_dict(data)
        assert doc.id == "d1"

    def test_none_criado_em_value(self):
        """criado_em key present with value None should not raise."""
        data = {
            "id": "d1",
            "tipo": "enunciado",
            "atividade_id": "a1",
            "criado_em": None,
        }
        doc = Documento.from_dict(data)
        assert doc.id == "d1"
