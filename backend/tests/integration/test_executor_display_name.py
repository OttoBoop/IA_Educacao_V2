"""
Integration tests for F6-T1 and F6-T2: executor.py pipeline methods must produce
documents with auto-generated display_names.

F6-T1: _salvar_resultado() saves JSON documents whose display_name includes the
       tipo label (e.g. "Correção"), aluno name, materia, and turma.

F6-T2: _gerar_formatos_extras() saves format-converted documents (PDF, CSV) that
       also carry proper display_names.

Since F3-T1 already wired salvar_documento() to auto-generate display_name from
atividade_id/aluno_id metadata, these tests pin the contract: when executor calls
salvar_documento() with the correct IDs, the returned Documento MUST have a
meaningful display_name — not blank, not a hash.

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F6-T1, F6-T2)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from models import TipoDocumento
from prompts import EtapaProcessamento


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def pipeline_env(monkeypatch, temp_data_dir):
    """Set up isolated SQLite-backed StorageManager + PipelineExecutor.

    Patches Supabase flags to False, creates the educational hierarchy,
    and builds a PipelineExecutor with real storage but no AI providers.
    """
    monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
    monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

    from storage import StorageManager
    sm = StorageManager(base_path=str(temp_data_dir))

    materia = sm.criar_materia(nome="Cálculo I")
    turma = sm.criar_turma(materia_id=materia.id, nome="Turma A")
    atividade = sm.criar_atividade(turma_id=turma.id, nome="Prova 1")
    aluno = sm.criar_aluno(nome="Maria Silva", matricula="2024001")
    sm.vincular_aluno_turma(aluno_id=aluno.id, turma_id=turma.id)

    # Build PipelineExecutor bypassing __init__ (no AI providers needed)
    from executor import PipelineExecutor
    executor = PipelineExecutor.__new__(PipelineExecutor)
    executor.storage = sm
    executor.prompt_manager = MagicMock()
    executor.preparador = None

    return {
        "storage": sm,
        "executor": executor,
        "materia": materia,
        "turma": turma,
        "atividade": atividade,
        "aluno": aluno,
    }


# ============================================================
# F6-T1: _salvar_resultado() display_name tests
# ============================================================

class TestSalvarResultadoDisplayName:
    """
    When _salvar_resultado() saves a JSON document via salvar_documento(),
    the resulting Documento.display_name must be auto-generated with the
    tipo label, aluno name, materia, and turma.
    """

    def test_correcao_json_has_display_name_with_tipo_label(self, pipeline_env):
        """
        _salvar_resultado() for CORRIGIR stage must produce a Documento whose
        display_name contains 'Correção' (the _TIPO_LABELS entry for 'correcao').
        """
        env = pipeline_env
        loop = asyncio.new_event_loop()
        try:
            doc_id = loop.run_until_complete(
                env["executor"]._salvar_resultado(
                    etapa=EtapaProcessamento.CORRIGIR,
                    atividade_id=env["atividade"].id,
                    aluno_id=env["aluno"].id,
                    resposta_raw='{"nota": 8.5}',
                    resposta_parsed={"nota": 8.5, "feedback": "Bom trabalho"},
                    provider="openai",
                    modelo="gpt-5-mini",
                    prompt_id="prompt-correcao-v1",
                    tokens=100,
                    tempo_ms=500.0,
                    gerar_formatos_extras=False,  # skip extras for this test
                )
            )
        finally:
            loop.close()

        assert doc_id is not None, "_salvar_resultado() must return a document ID"

        # Fetch the saved document
        docs = env["storage"].listar_documentos(env["atividade"].id, env["aluno"].id)
        doc = next((d for d in docs if d.id == doc_id), None)
        assert doc is not None, f"Document {doc_id} not found in storage"

        assert "Correção" in doc.display_name or "Correcao" in doc.display_name, (
            f"display_name '{doc.display_name}' must contain the tipo label 'Correção'. "
            "salvar_documento() auto-generates display_name from _TIPO_LABELS when "
            "display_name is None."
        )

    def test_correcao_json_display_name_includes_aluno(self, pipeline_env):
        """
        The auto-generated display_name for a CORRIGIR document must include
        the student name 'Maria Silva'.
        """
        env = pipeline_env
        loop = asyncio.new_event_loop()
        try:
            doc_id = loop.run_until_complete(
                env["executor"]._salvar_resultado(
                    etapa=EtapaProcessamento.CORRIGIR,
                    atividade_id=env["atividade"].id,
                    aluno_id=env["aluno"].id,
                    resposta_raw='{"nota": 7.0}',
                    resposta_parsed={"nota": 7.0},
                    provider="openai",
                    modelo="gpt-5-mini",
                    prompt_id="prompt-correcao-v1",
                    tokens=80,
                    tempo_ms=400.0,
                    gerar_formatos_extras=False,
                )
            )
        finally:
            loop.close()

        docs = env["storage"].listar_documentos(env["atividade"].id, env["aluno"].id)
        doc = next((d for d in docs if d.id == doc_id), None)
        assert doc is not None

        assert "Maria Silva" in doc.display_name, (
            f"display_name '{doc.display_name}' must contain the aluno name 'Maria Silva'. "
            "salvar_documento() must resolve aluno_id to get the name."
        )

    def test_correcao_json_display_name_includes_materia_turma(self, pipeline_env):
        """
        The auto-generated display_name must include the materia name and turma name.
        """
        env = pipeline_env
        loop = asyncio.new_event_loop()
        try:
            doc_id = loop.run_until_complete(
                env["executor"]._salvar_resultado(
                    etapa=EtapaProcessamento.CORRIGIR,
                    atividade_id=env["atividade"].id,
                    aluno_id=env["aluno"].id,
                    resposta_raw='{}',
                    resposta_parsed={"nota": 9.0},
                    provider="openai",
                    modelo="gpt-5-mini",
                    prompt_id="prompt-v1",
                    tokens=50,
                    tempo_ms=300.0,
                    gerar_formatos_extras=False,
                )
            )
        finally:
            loop.close()

        docs = env["storage"].listar_documentos(env["atividade"].id, env["aluno"].id)
        doc = next((d for d in docs if d.id == doc_id), None)
        assert doc is not None

        display = doc.display_name
        assert "Cálculo I" in display or "Calculo I" in display, (
            f"display_name '{display}' must contain the materia name 'Cálculo I'."
        )
        assert "Turma A" in display, (
            f"display_name '{display}' must contain the turma name 'Turma A'."
        )

    def test_relatorio_final_display_name_no_aluno(self, pipeline_env):
        """
        RELATORIO_DESEMPENHO_TURMA is a turma-level report (no specific aluno).
        display_name should include the tipo label and materia/turma but not a
        specific student name.
        """
        env = pipeline_env
        loop = asyncio.new_event_loop()
        try:
            doc_id = loop.run_until_complete(
                env["executor"]._salvar_resultado(
                    etapa=EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA,
                    atividade_id=env["atividade"].id,
                    aluno_id=None,  # turma-level report
                    resposta_raw='{}',
                    resposta_parsed={"resumo": "Turma OK"},
                    provider="openai",
                    modelo="gpt-5-mini",
                    prompt_id="prompt-relatorio",
                    tokens=60,
                    tempo_ms=350.0,
                    gerar_formatos_extras=False,
                )
            )
        finally:
            loop.close()

        docs = env["storage"].listar_documentos(env["atividade"].id, None)
        doc = next((d for d in docs if d.id == doc_id), None)
        assert doc is not None

        display = doc.display_name
        # Must NOT be empty
        assert display, "display_name must not be empty for turma-level report"
        # Must NOT contain specific aluno
        assert "Maria Silva" not in display, (
            f"Turma-level report display_name should not contain a specific aluno name."
        )


# ============================================================
# F6-T2: _gerar_formatos_extras() display_name tests
# ============================================================

class TestGerarFormatosExtrasDisplayName:
    """
    When _gerar_formatos_extras() saves format-converted documents,
    each must also get an auto-generated display_name.
    """

    def test_extras_docs_have_nonempty_display_name(self, pipeline_env):
        """
        Documents saved by _gerar_formatos_extras() must have non-empty
        auto-generated display_names.
        """
        env = pipeline_env

        # First save a base JSON document
        loop = asyncio.new_event_loop()
        try:
            doc_id = loop.run_until_complete(
                env["executor"]._salvar_resultado(
                    etapa=EtapaProcessamento.CORRIGIR,
                    atividade_id=env["atividade"].id,
                    aluno_id=env["aluno"].id,
                    resposta_raw='{}',
                    resposta_parsed={
                        "nota": 8.0,
                        "questoes": [{"numero": 1, "nota": 8.0}],
                    },
                    provider="openai",
                    modelo="gpt-5-mini",
                    prompt_id="prompt-v1",
                    tokens=50,
                    tempo_ms=300.0,
                    gerar_formatos_extras=False,  # we'll call it manually
                )
            )

            # Now call _gerar_formatos_extras manually
            extra_ids = loop.run_until_complete(
                env["executor"]._gerar_formatos_extras(
                    documento_id=doc_id,
                    tipo=TipoDocumento.CORRECAO,
                    conteudo={"nota": 8.0, "questoes": [{"numero": 1, "nota": 8.0}]},
                    atividade_id=env["atividade"].id,
                    aluno_id=env["aluno"].id,
                )
            )
        finally:
            loop.close()

        # Check that at least one extra doc was generated
        if not extra_ids:
            pytest.skip(
                "No extra formats generated for CORRECAO — "
                "document_generators may not support this type. "
                "Test is still valid as a contract pin."
            )

        for extra_id in extra_ids:
            docs = env["storage"].listar_documentos(env["atividade"].id, env["aluno"].id)
            extra_doc = next((d for d in docs if d.id == extra_id), None)
            assert extra_doc is not None, f"Extra doc {extra_id} not found"
            assert extra_doc.display_name, (
                f"Extra format doc {extra_id} (ext={extra_doc.extensao}) "
                f"must have a non-empty display_name, got '{extra_doc.display_name}'"
            )
