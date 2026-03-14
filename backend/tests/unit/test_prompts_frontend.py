"""
Tests for frontend-facing prompt API behaviors (F11-T1).

Verifies backend behaviors that the new prompts.js module depends on:
- All 11 stages returned from /api/prompts/etapas (10 EtapaProcessamento + display names)
- Default prompts are is_padrao=True and can't be deleted
- Version history is saved on update
- Prompt duplication works

Related plan: docs/PLAN_Prompts_Page_Rewrite.md
Task: F11-T1
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from main_v2 import app
    return TestClient(app)


class TestEtapasEndpoint:
    """All pipeline stages must be returned for tab rendering."""

    def test_etapas_returns_all_stages(self, client):
        """GET /api/prompts/etapas returns all 10 EtapaProcessamento values."""
        resp = client.get("/api/prompts/etapas")
        assert resp.status_code == 200
        data = resp.json()
        etapas = data["etapas"]
        assert len(etapas) == 10

        etapa_ids = [e["id"] for e in etapas]
        expected = [
            "extrair_questoes", "extrair_gabarito", "extrair_respostas",
            "corrigir", "analisar_habilidades", "gerar_relatorio",
            "chat_geral",
            "relatorio_desempenho_tarefa", "relatorio_desempenho_turma",
            "relatorio_desempenho_materia"
        ]
        for exp in expected:
            assert exp in etapa_ids, f"Missing etapa: {exp}"

    def test_etapas_have_nome_and_descricao(self, client):
        """Each etapa entry has id, nome, and descricao fields."""
        resp = client.get("/api/prompts/etapas")
        data = resp.json()
        for e in data["etapas"]:
            assert "id" in e
            assert "nome" in e
            assert "descricao" in e
            assert len(e["nome"]) > 0


class TestDefaultPrompts:
    """Default prompts must be marked is_padrao and protected from deletion."""

    def test_default_prompts_are_padrao(self):
        """PROMPTS_PADRAO entries all have is_padrao=True."""
        from prompts import PROMPTS_PADRAO
        for etapa, prompt in PROMPTS_PADRAO.items():
            assert prompt.is_padrao is True, f"Prompt for {etapa} should be is_padrao=True"

    def test_default_prompts_cover_key_stages(self):
        """At least the 7 core execution stages have default prompts."""
        from prompts import PROMPTS_PADRAO, EtapaProcessamento
        core_stages = [
            EtapaProcessamento.EXTRAIR_QUESTOES,
            EtapaProcessamento.EXTRAIR_GABARITO,
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
            EtapaProcessamento.CORRIGIR,
            EtapaProcessamento.ANALISAR_HABILIDADES,
            EtapaProcessamento.GERAR_RELATORIO,
            EtapaProcessamento.CHAT_GERAL,
        ]
        for stage in core_stages:
            assert stage in PROMPTS_PADRAO, f"Missing default prompt for {stage.value}"

    def test_cannot_delete_padrao_prompt(self):
        """PromptManager.deletar_prompt refuses to delete is_padrao prompts."""
        from prompts import prompt_manager
        # Get a known default prompt
        from prompts import EtapaProcessamento
        padrao = prompt_manager.get_prompt_padrao(EtapaProcessamento.CORRIGIR)
        if padrao:
            result = prompt_manager.deletar_prompt(padrao.id)
            assert result is False, "Should not be able to delete a default prompt"


class TestVersionHistory:
    """Updates must save old version to prompts_historico."""

    def test_update_saves_history(self):
        """Updating a prompt's text creates a history entry."""
        from prompts import prompt_manager, EtapaProcessamento

        # Create a test prompt
        test_prompt = prompt_manager.criar_prompt(
            nome="Test History Prompt",
            etapa=EtapaProcessamento.CORRIGIR,
            texto="Versao 1 do texto"
        )
        assert test_prompt is not None

        # Update it
        updated = prompt_manager.atualizar_prompt(
            test_prompt.id,
            texto="Versao 2 do texto"
        )
        assert updated is not None
        assert updated.versao == 2

        # Check history
        historico = prompt_manager.get_historico(test_prompt.id)
        assert len(historico) >= 1
        assert historico[0]["versao"] == 1
        assert "Versao 1" in historico[0]["texto"]

        # Cleanup
        prompt_manager.deletar_prompt(test_prompt.id)


class TestPromptDuplication:
    """Duplicating a prompt creates a new prompt with different ID."""

    def test_duplicar_creates_copy(self):
        """duplicar_prompt creates a new prompt with the given name."""
        from prompts import prompt_manager, EtapaProcessamento

        # Create original
        original = prompt_manager.criar_prompt(
            nome="Original para duplicar",
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
            texto="Texto original"
        )
        assert original is not None

        # Duplicate
        copia = prompt_manager.duplicar_prompt(original.id, "Copia do original")
        assert copia is not None
        assert copia.id != original.id
        assert copia.nome == "Copia do original"
        assert copia.texto == original.texto
        assert copia.etapa == original.etapa
        assert copia.is_padrao is False

        # Cleanup
        prompt_manager.deletar_prompt(original.id)
        prompt_manager.deletar_prompt(copia.id)
