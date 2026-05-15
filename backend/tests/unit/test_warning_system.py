"""
Warning System Tests — F1-T1 (schema) + F2-T1 (severity mapping)

Tests for the Illegible Writing Warning UI feature.
Validates that all 6 student pipeline stages include _avisos schema
and that the severity mapping table returns correct colors.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_warning_system.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# F1-T1: Schema contains _avisos_documento/_avisos_questao
# ============================================================

# Stages whose schemas live in STAGE_TOOL_INSTRUCTIONS (executor.py)
TOOL_INSTRUCTION_STAGES = [
    "CORRIGIR",
    "ANALISAR_HABILIDADES",
    "GERAR_RELATORIO",
]

# Stages whose schemas live in PROMPTS_PADRAO (prompts.py)
PROMPT_STAGES = [
    "EXTRAIR_QUESTOES",
    "EXTRAIR_GABARITO",
    "EXTRAIR_RESPOSTAS",
]

ALL_STUDENT_STAGES = TOOL_INSTRUCTION_STAGES + PROMPT_STAGES

WARNING_CODES = [
    "ILLEGIBLE_DOCUMENT",
    "ILLEGIBLE_QUESTION",
    "MISSING_CONTENT",
    "LOW_CONFIDENCE",
]

OLD_STUB_FIELDS = [
    "_documento_ilegivel",
    "_campos_faltantes",
]


class TestWarningSchemaInToolInstructions:
    """F1-T1: Verify STAGE_TOOL_INSTRUCTIONS contain _avisos schema."""

    def _get_stage_text(self, stage_name: str) -> str:
        """Get the instruction text for a STAGE_TOOL_INSTRUCTIONS stage."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        from prompts import EtapaProcessamento

        stage_enum = EtapaProcessamento[stage_name]
        return STAGE_TOOL_INSTRUCTIONS[stage_enum]

    @pytest.mark.parametrize("stage", TOOL_INSTRUCTION_STAGES)
    def test_stage_has_avisos_documento(self, stage):
        """Each tool-instruction stage must include _avisos_documento in its schema."""
        text = self._get_stage_text(stage)
        assert "_avisos_documento" in text, (
            f"{stage} STAGE_TOOL_INSTRUCTIONS missing '_avisos_documento' array"
        )

    @pytest.mark.parametrize("stage", TOOL_INSTRUCTION_STAGES)
    def test_stage_has_avisos_questao(self, stage):
        """Each tool-instruction stage must include _avisos_questao in its schema."""
        text = self._get_stage_text(stage)
        assert "_avisos_questao" in text, (
            f"{stage} STAGE_TOOL_INSTRUCTIONS missing '_avisos_questao' array"
        )

    @pytest.mark.parametrize("stage", TOOL_INSTRUCTION_STAGES)
    @pytest.mark.parametrize("code", WARNING_CODES)
    def test_stage_has_warning_code(self, stage, code):
        """Each tool-instruction stage must document all 4 warning codes."""
        text = self._get_stage_text(stage)
        assert code in text, (
            f"{stage} STAGE_TOOL_INSTRUCTIONS missing warning code '{code}'"
        )

    @pytest.mark.parametrize("stage", TOOL_INSTRUCTION_STAGES)
    @pytest.mark.parametrize("old_field", OLD_STUB_FIELDS)
    def test_old_stubs_removed(self, stage, old_field):
        """Old stub fields must be removed from STAGE_TOOL_INSTRUCTIONS."""
        text = self._get_stage_text(stage)
        assert old_field not in text, (
            f"{stage} still contains old stub field '{old_field}' — "
            "should be replaced by _avisos_documento/_avisos_questao"
        )


class TestWarningSchemaInPrompts:
    """F1-T1: Verify PROMPTS_PADRAO contain _avisos schema for EXTRAIR stages."""

    def _get_prompt_text(self, stage_name: str) -> str:
        """Get the full prompt text for an EXTRAIR stage."""
        from prompts import EtapaProcessamento, PROMPTS_PADRAO

        stage_enum = EtapaProcessamento[stage_name]
        template = PROMPTS_PADRAO[stage_enum]
        return template.texto

    @pytest.mark.parametrize("stage", PROMPT_STAGES)
    def test_prompt_has_avisos_documento(self, stage):
        """Each EXTRAIR prompt must include _avisos_documento in its JSON schema."""
        text = self._get_prompt_text(stage)
        assert "_avisos_documento" in text, (
            f"{stage} prompt missing '_avisos_documento' array in JSON schema"
        )

    @pytest.mark.parametrize("stage", PROMPT_STAGES)
    def test_prompt_has_avisos_questao(self, stage):
        """Each EXTRAIR prompt must include _avisos_questao in its JSON schema."""
        text = self._get_prompt_text(stage)
        assert "_avisos_questao" in text, (
            f"{stage} prompt missing '_avisos_questao' array in JSON schema"
        )

    @pytest.mark.parametrize("stage", PROMPT_STAGES)
    @pytest.mark.parametrize("code", WARNING_CODES)
    def test_prompt_has_warning_code(self, stage, code):
        """Each EXTRAIR prompt must document all 4 warning codes."""
        text = self._get_prompt_text(stage)
        assert code in text, (
            f"{stage} prompt missing warning code '{code}'"
        )


# ============================================================
# F2-T1: Severity mapping (stage + code → color)
# ============================================================

# Expected severity for each (stage, code) combination
# Based on discovery + user decision:
#   - ILLEGIBLE_QUESTION applies to ALL 6 stages (user updated from N/A)
#   - MISSING_CONTENT is yellow in EXTRAIR_RESPOSTAS, CORRIGIR,
#     ANALISAR_HABILIDADES, GERAR_RELATORIO (student may skip intentionally)
#   - MISSING_CONTENT is orange in EXTRAIR_QUESTOES, EXTRAIR_GABARITO
#   - All other combos are orange
SEVERITY_EXPECTATIONS = []
for stage in ALL_STUDENT_STAGES:
    for code in WARNING_CODES:
        if code == "MISSING_CONTENT" and stage in (
            "EXTRAIR_RESPOSTAS", "CORRIGIR",
            "ANALISAR_HABILIDADES", "GERAR_RELATORIO",
        ):
            SEVERITY_EXPECTATIONS.append((stage, code, "yellow"))
        else:
            SEVERITY_EXPECTATIONS.append((stage, code, "orange"))


class TestSeverityMapping:
    """F2-T1: Verify get_warning_severity() returns correct colors."""

    @pytest.mark.parametrize("stage,code,expected", SEVERITY_EXPECTATIONS,
                             ids=[f"{s}-{c}" for s, c, _ in SEVERITY_EXPECTATIONS])
    def test_severity_mapping(self, stage, code, expected):
        """Each (stage, code) combo must map to the correct severity color."""
        from visualizador import get_warning_severity

        result = get_warning_severity(stage, code)
        assert result == expected, (
            f"get_warning_severity('{stage}', '{code}') returned '{result}', "
            f"expected '{expected}'"
        )

    def test_unknown_code_returns_none(self):
        """Unknown warning codes should return None (schema violation)."""
        from visualizador import get_warning_severity

        result = get_warning_severity("CORRIGIR", "UNKNOWN_CODE")
        assert result is None, (
            "Unknown warning code should return None (indicates schema violation)"
        )

    def test_unknown_stage_returns_none(self):
        """Unknown stage should return None."""
        from visualizador import get_warning_severity

        result = get_warning_severity("NONEXISTENT_STAGE", "ILLEGIBLE_DOCUMENT")
        assert result is None, (
            "Unknown stage should return None"
        )


# ============================================================
# F4-T1 supplement: _fontes_utilizadas in GERAR_RELATORIO
# ============================================================

class TestFontesUtilizadasSchema:
    """GERAR_RELATORIO schema must include _fontes_utilizadas field."""

    def test_gerar_relatorio_has_fontes_utilizadas(self):
        """GERAR_RELATORIO STAGE_TOOL_INSTRUCTIONS must include _fontes_utilizadas."""
        from executor import STAGE_TOOL_INSTRUCTIONS
        from prompts import EtapaProcessamento

        stage_enum = EtapaProcessamento["GERAR_RELATORIO"]
        text = STAGE_TOOL_INSTRUCTIONS[stage_enum]
        assert "_fontes_utilizadas" in text, (
            "GERAR_RELATORIO STAGE_TOOL_INSTRUCTIONS missing '_fontes_utilizadas' field"
        )


# ============================================================
# P2: create_document default _avisos injection
# ============================================================

class TestCreateDocumentAvisosDefaults:
    """JSON saved through create_document must get default aviso metadata."""

    def test_inject_default_avisos_adds_missing_fields(self, tmp_path):
        """Missing _avisos_* fields are added before the JSON enters storage."""
        import json
        from models import TipoDocumento
        from tool_handlers import _inject_default_avisos

        arquivo = tmp_path / "correcao.json"
        arquivo.write_text(json.dumps({"nota_final": 8.5, "questoes": []}), encoding="utf-8")

        _inject_default_avisos(str(arquivo), TipoDocumento.CORRECAO)

        data = json.loads(arquivo.read_text(encoding="utf-8"))
        assert data["_avisos_documento"] == []
        assert data["_avisos_questao"] == []
        assert data["_avisos_stage"] == "CORRIGIR"

    def test_inject_default_avisos_preserves_existing_fields(self, tmp_path):
        """Existing aviso lists are not overwritten by the default injector."""
        import json
        from models import TipoDocumento
        from tool_handlers import _inject_default_avisos

        aviso = {"codigo": "LOW_CONFIDENCE", "explicacao": "leitura parcial"}
        arquivo = tmp_path / "relatorio.json"
        arquivo.write_text(
            json.dumps({
                "nota_final": 7.0,
                "_avisos_documento": [aviso],
                "_avisos_questao": [],
                "_avisos_stage": "GERAR_RELATORIO",
            }),
            encoding="utf-8",
        )

        _inject_default_avisos(str(arquivo), TipoDocumento.RELATORIO_FINAL)

        data = json.loads(arquivo.read_text(encoding="utf-8"))
        assert data["_avisos_documento"] == [aviso]
        assert data["_avisos_questao"] == []
        assert data["_avisos_stage"] == "GERAR_RELATORIO"

    @pytest.mark.asyncio
    async def test_create_document_rejects_invalid_json(self):
        """A .json artifact must be parseable before it can enter storage."""
        from tool_handlers import handle_create_document
        from tools import ToolExecutionContext

        result = await handle_create_document(
            {
                "documents": [
                    {
                        "filename": "correcao_invalida.json",
                        "content": '{"nota_final": 7, "feedback": "linha\nquebrada"}',
                    }
                ]
            },
            ToolExecutionContext(
                atividade_id="ativ-1",
                aluno_id="aluno-1",
                expected_document_type=None,
                etapa="correcao",
            ),
        )

        assert result.is_error is True
        assert result.files_generated == []
        assert "Invalid JSON for create_document" in result.content

    @pytest.mark.asyncio
    async def test_create_document_rejects_non_json_in_pipeline_stage(self):
        """Dual-output pipeline stages use create_document for JSON only."""
        from models import TipoDocumento
        from tool_handlers import handle_create_document
        from tools import ToolExecutionContext

        result = await handle_create_document(
            {
                "documents": [
                    {
                        "filename": "correcao_extra.pdf",
                        "content": "PDF must be produced by execute_python_code.",
                    }
                ]
            },
            ToolExecutionContext(
                atividade_id="ativ-1",
                aluno_id="aluno-1",
                expected_document_type=TipoDocumento.CORRECAO,
                etapa="correcao",
            ),
        )

        assert result.is_error is True
        assert result.files_generated == []
        assert "only accepts .json" in result.content

    @pytest.mark.asyncio
    async def test_create_document_rejects_malformed_documents_entries(self):
        """Malformed documents entries must return a tool error, not an exception."""
        from tool_handlers import handle_create_document
        from tools import ToolExecutionContext

        result = await handle_create_document(
            {"documents": ["correcao.pdf"]},
            ToolExecutionContext(
                atividade_id="ativ-1",
                aluno_id="aluno-1",
                etapa="correcao",
            ),
        )

        assert result.is_error is True
        assert result.files_generated == []
        assert "Invalid document entry" in result.content

    @pytest.mark.asyncio
    async def test_create_document_pipeline_errors_when_storage_does_not_persist(self, monkeypatch):
        """Pipeline artifacts are valid only after they are persisted in storage."""
        from models import TipoDocumento
        from tool_handlers import handle_create_document
        from tools import ToolExecutionContext
        import storage as storage_module

        class DummyStorage:
            def salvar_documento(self, **_kwargs):
                return None

        monkeypatch.setattr(storage_module, "storage", DummyStorage())

        result = await handle_create_document(
            {
                "documents": [
                    {
                        "filename": "analise_habilidades.json",
                        "content": {"habilidades": [], "indicadores": {}, "recomendacoes": []},
                    }
                ]
            },
            ToolExecutionContext(
                atividade_id="ativ-1",
                aluno_id="aluno-1",
                expected_document_type=TipoDocumento.ANALISE_HABILIDADES,
                etapa="analise_habilidades",
            ),
        )

        assert result.is_error is True
        assert result.files_generated == []
        assert "Storage persistence failed for pipeline artifact" in result.content
