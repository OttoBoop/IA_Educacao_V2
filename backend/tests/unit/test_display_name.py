"""
Tests for display_name generation and filename sanitization.

F1-T1: build_display_name() — generates structured display names from metadata
F1-T2: sanitize_filename() + build_storage_filename() — filesystem-safe names with hash suffix
"""

import re
import pytest
from models import TipoDocumento


# ============================================================
# F1-T1: build_display_name() tests
# ============================================================

class TestBuildDisplayName:
    """Tests for the build_display_name() pure function."""

    def test_full_metadata_student_doc(self):
        """Student doc with all fields produces full structured name."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            aluno_nome="Maria Silva",
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Prova Respondida - Maria Silva - Cálculo I - Turma A"

    def test_base_doc_without_aluno(self):
        """Base doc type (enunciado) omits aluno from name."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.ENUNCIADO,
            aluno_nome=None,
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Enunciado - Cálculo I - Turma A"

    def test_gabarito_without_aluno(self):
        """Gabarito is a base doc — no aluno in name."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.GABARITO,
            aluno_nome=None,
            materia_nome="Física II",
            turma_nome="Turma B",
        )
        assert result == "Gabarito - Física II - Turma B"

    def test_ai_generated_correcao(self):
        """AI-generated correction gets structured name with aluno."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.CORRECAO,
            aluno_nome="João Santos",
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Correção - João Santos - Cálculo I - Turma A"

    def test_relatorio_final(self):
        """Relatório final gets proper label."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.RELATORIO_FINAL,
            aluno_nome="Ana Costa",
            materia_nome="Álgebra Linear",
            turma_nome="Turma C",
        )
        assert result == "Relatório Final - Ana Costa - Álgebra Linear - Turma C"

    def test_criterios_correcao_base_doc(self):
        """Critérios de correção is a base doc — no aluno."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.CRITERIOS_CORRECAO,
            aluno_nome=None,
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Critérios de Correção - Cálculo I - Turma A"

    def test_none_aluno_on_student_doc_omits_aluno(self):
        """If aluno_nome is None even for student doc type, omit it."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            aluno_nome=None,
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Prova Respondida - Cálculo I - Turma A"

    def test_empty_string_aluno_omits_aluno(self):
        """Empty string aluno_nome is treated as missing — omitted."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            aluno_nome="",
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Prova Respondida - Cálculo I - Turma A"

    def test_none_materia_omits_materia(self):
        """None matéria is omitted from name."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            aluno_nome="Maria Silva",
            materia_nome=None,
            turma_nome="Turma A",
        )
        assert result == "Prova Respondida - Maria Silva - Turma A"

    def test_none_turma_omits_turma(self):
        """None turma is omitted from name."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            aluno_nome="Maria Silva",
            materia_nome="Cálculo I",
            turma_nome=None,
        )
        assert result == "Prova Respondida - Maria Silva - Cálculo I"

    def test_all_none_except_tipo(self):
        """Only tipo provided — just the tipo label."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.ENUNCIADO,
            aluno_nome=None,
            materia_nome=None,
            turma_nome=None,
        )
        assert result == "Enunciado"

    def test_all_tipo_values_produce_nonempty(self):
        """Every TipoDocumento value produces a non-empty display name."""
        from storage import build_display_name

        for tipo in TipoDocumento:
            result = build_display_name(
                tipo=tipo,
                aluno_nome="Test Student",
                materia_nome="Test Subject",
                turma_nome="Test Class",
            )
            assert result, f"Empty display_name for {tipo}"
            assert "None" not in result, f"'None' literal in display_name for {tipo}"

    def test_no_none_literal_in_output(self):
        """The string 'None' should never appear in display_name output."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            aluno_nome=None,
            materia_nome=None,
            turma_nome=None,
        )
        assert "None" not in result

    def test_extracao_questoes_is_base_doc(self):
        """Extração de questões is activity-level (no aluno)."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.EXTRACAO_QUESTOES,
            aluno_nome=None,
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Extração de Questões - Cálculo I - Turma A"

    def test_analise_habilidades(self):
        """Análise de habilidades gets proper label with accents."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.ANALISE_HABILIDADES,
            aluno_nome="Maria Silva",
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Análise de Habilidades - Maria Silva - Cálculo I - Turma A"

    def test_relatorio_desempenho_tarefa(self):
        """Aggregate report tipo gets proper label."""
        from storage import build_display_name

        result = build_display_name(
            tipo=TipoDocumento.RELATORIO_DESEMPENHO_TAREFA,
            aluno_nome=None,
            materia_nome="Cálculo I",
            turma_nome="Turma A",
        )
        assert result == "Relatório de Desempenho (Tarefa) - Cálculo I - Turma A"


# ============================================================
# F1-T2: sanitize_filename() tests
# ============================================================

class TestSanitizeFilename:
    """Tests for the sanitize_filename() utility."""

    def test_keeps_portuguese_accents(self):
        """Portuguese accents (é, ã, ô, ç) are preserved."""
        from storage import sanitize_filename

        result = sanitize_filename("Correção - João - Cálculo")
        assert "ç" in result
        assert "ã" in result
        assert "á" in result

    def test_strips_forward_slash(self):
        """Forward slash is removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name/with/slashes")
        assert "/" not in result

    def test_strips_backslash(self):
        """Backslash is removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name\\with\\backslashes")
        assert "\\" not in result

    def test_strips_colon(self):
        """Colon is removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name:with:colons")
        assert ":" not in result

    def test_strips_asterisk(self):
        """Asterisk is removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name*with*stars")
        assert "*" not in result

    def test_strips_question_mark(self):
        """Question mark is removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name?with?questions")
        assert "?" not in result

    def test_strips_angle_brackets(self):
        """Angle brackets are removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name<with>brackets")
        assert "<" not in result
        assert ">" not in result

    def test_strips_pipe(self):
        """Pipe character is removed."""
        from storage import sanitize_filename

        result = sanitize_filename("Name|with|pipes")
        assert "|" not in result

    def test_all_unsafe_chars_at_once(self):
        """All 8 unsafe chars stripped from a single string."""
        from storage import sanitize_filename

        result = sanitize_filename('a/b\\c:d*e?f<g>h|i')
        for char in ['/', '\\', ':', '*', '?', '<', '>', '|']:
            assert char not in result

    def test_preserves_hyphens_and_spaces(self):
        """Hyphens and spaces are kept (they're valid in filenames)."""
        from storage import sanitize_filename

        result = sanitize_filename("Prova Respondida - Maria Silva")
        assert " " in result
        assert "-" in result

    def test_empty_string(self):
        """Empty input returns empty output."""
        from storage import sanitize_filename

        result = sanitize_filename("")
        assert result == ""

    def test_normal_name_unchanged(self):
        """A normal name with no unsafe chars passes through unchanged."""
        from storage import sanitize_filename

        result = sanitize_filename("Prova Respondida - Maria Silva - Cálculo I")
        assert result == "Prova Respondida - Maria Silva - Cálculo I"


# ============================================================
# F1-T2: build_storage_filename() tests (sanitize + hash suffix)
# ============================================================

class TestBuildStorageFilename:
    """Tests for building a complete storage filename with hash suffix."""

    def test_output_format_matches_pattern(self):
        """Output matches '{sanitized_name}_{hash4}.{ext}' pattern."""
        from storage import build_storage_filename

        result = build_storage_filename("Prova Respondida - Maria Silva", ".pdf")
        pattern = r'^.+_[a-f0-9]{4}\.pdf$'
        assert re.match(pattern, result), f"'{result}' doesn't match pattern '{pattern}'"

    def test_hash_suffix_is_4_hex_chars(self):
        """Hash suffix is exactly 4 hex characters."""
        from storage import build_storage_filename

        result = build_storage_filename("Test Name", ".pdf")
        # Extract hash: everything between last _ and .ext
        stem = result.rsplit(".", 1)[0]  # remove extension
        hash_part = stem.rsplit("_", 1)[1]  # get part after last _
        assert re.match(r'^[a-f0-9]{4}$', hash_part), f"Hash '{hash_part}' is not 4 hex chars"

    def test_sanitizes_unsafe_chars(self):
        """Unsafe chars in display_name are sanitized before building filename."""
        from storage import build_storage_filename

        result = build_storage_filename("Name/with:unsafe*chars", ".pdf")
        # Should not contain unsafe chars (excluding the extension dot)
        stem = result.rsplit(".", 1)[0]
        for char in ['/', '\\', ':', '*', '?', '<', '>', '|']:
            assert char not in stem

    def test_preserves_accents_in_filename(self):
        """Portuguese accents preserved in the final filename."""
        from storage import build_storage_filename

        result = build_storage_filename("Correção - João - Cálculo", ".pdf")
        assert "ç" in result
        assert "ã" in result

    def test_different_names_get_different_hashes(self):
        """Different display names produce different hash suffixes."""
        from storage import build_storage_filename

        result1 = build_storage_filename("Name A", ".pdf")
        result2 = build_storage_filename("Name B", ".pdf")
        hash1 = result1.rsplit(".", 1)[0].rsplit("_", 1)[1]
        hash2 = result2.rsplit(".", 1)[0].rsplit("_", 1)[1]
        assert hash1 != hash2

    def test_extension_without_dot(self):
        """Extension without leading dot still works."""
        from storage import build_storage_filename

        result = build_storage_filename("Test Name", "pdf")
        assert result.endswith(".pdf")

    def test_json_extension(self):
        """Works with .json extension (for AI-generated docs)."""
        from storage import build_storage_filename

        result = build_storage_filename("Correção - Maria", ".json")
        assert result.endswith(".json")
        pattern = r'^.+_[a-f0-9]{4}\.json$'
        assert re.match(pattern, result)
