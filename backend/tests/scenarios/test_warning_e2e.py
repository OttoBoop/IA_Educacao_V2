"""
Warning System E2E Tests — Inject pre-built warning data, verify full read path.

Tests that warnings flow correctly from pipeline JSON → visualizador → API response.
Uses DocumentFactory.criar_correcao_com_avisos() to create realistic warning data
without needing a real AI pipeline run.

Run: cd IA_Educacao_V2/backend && pytest tests/scenarios/test_warning_e2e.py -v
"""

import importlib
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def app_with_storage(monkeypatch, temp_data_dir: Path):
    """Create a fresh FastAPI app with isolated storage."""
    import storage as storage_module
    from storage import StorageManager

    storage_instance = StorageManager(base_path=temp_data_dir)
    monkeypatch.setattr(storage_module, "storage", storage_instance)

    # Also patch visualizador's storage reference
    import visualizador as viz_module
    monkeypatch.setattr(viz_module, "storage", storage_instance)

    modules_to_reload = [
        "executor",
        "routes_prompts",
        "routes_pipeline",
        "routes_extras",
        "routes_resultados",
        "routes_chat",
        "main_v2",
    ]

    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)

    # Re-patch after reload (reload resets module-level globals)
    import visualizador as viz_mod_reloaded
    monkeypatch.setattr(viz_mod_reloaded, "storage", storage_instance)

    # Patch the visualizador singleton used by routes_resultados
    import routes_resultados
    if hasattr(routes_resultados, "visualizador"):
        routes_resultados.visualizador.storage = storage_instance

    import main_v2

    return main_v2.app, storage_instance


@pytest.fixture
def seeded_context_with_warnings(app_with_storage, temp_data_dir: Path):
    """
    Seed DB with a student whose CORRECAO document contains warnings.

    Creates:
    - Materia, Turma, Atividade, Aluno (DB entities)
    - Enunciado, Gabarito, Prova respondida (documents)
    - CORRECAO JSON with _avisos_documento and _avisos_questao pre-populated
    """
    app, storage_instance = app_with_storage
    from models import NivelEnsino, TipoDocumento
    from tests.fixtures.document_factory import DocumentFactory

    # Create DB entities
    materia = storage_instance.criar_materia(
        "Matemática",
        "Matemática básica",
        NivelEnsino.FUNDAMENTAL_2,
    )
    turma = storage_instance.criar_turma(
        materia.id, "9º Ano A", ano_letivo=2024, periodo="Manhã",
    )
    atividade = storage_instance.criar_atividade(
        turma.id, "Prova Warning Test", tipo="prova", nota_maxima=10.0,
    )
    aluno = storage_instance.criar_aluno(
        "Maria Avisos", "maria@test.com", "2024-W01",
    )
    storage_instance.vincular_aluno_turma(aluno.id, turma.id)

    factory = DocumentFactory(temp_data_dir / "docs")

    # Base documents
    enunciado = factory.criar_prova_teste("Matemática", num_questoes=4)
    gabarito = factory.criar_gabarito_teste("Matemática", num_questoes=4)
    prova_aluno = factory.criar_prova_aluno("Maria Avisos", "Matemática", num_questoes=4)

    storage_instance.salvar_documento(
        str(enunciado.path), TipoDocumento.ENUNCIADO, atividade.id,
    )
    storage_instance.salvar_documento(
        str(gabarito.path), TipoDocumento.GABARITO, atividade.id,
    )
    storage_instance.salvar_documento(
        str(prova_aluno.path), TipoDocumento.PROVA_RESPONDIDA,
        atividade.id, aluno_id=aluno.id,
    )

    # CORRECAO with warnings
    avisos_doc = [
        {"codigo": "ILLEGIBLE_DOCUMENT", "explicacao": "Digitalização muito borrada"},
        {"codigo": "LOW_CONFIDENCE", "explicacao": "Confiança geral baixa na leitura"},
    ]
    avisos_q = [
        {"codigo": "ILLEGIBLE_QUESTION", "questao": 2, "explicacao": "Resposta da questão 2 ilegível"},
        {"codigo": "MISSING_CONTENT", "questao": 4, "explicacao": "Questão 4 em branco"},
    ]
    correcao = factory.criar_correcao_com_avisos(
        aluno_nome="Maria Avisos",
        materia="Matemática",
        num_questoes=4,
        avisos_documento=avisos_doc,
        avisos_questao=avisos_q,
        nota_final=5.0,
    )
    storage_instance.salvar_documento(
        str(correcao.path), TipoDocumento.CORRECAO,
        atividade.id, aluno_id=aluno.id,
    )

    return {
        "app": app,
        "storage": storage_instance,
        "atividade": atividade,
        "aluno": aluno,
        "avisos_documento": avisos_doc,
        "avisos_questao": avisos_q,
        "correcao_path": correcao.path,
    }


@pytest.fixture
def seeded_context_clean(app_with_storage, temp_data_dir: Path):
    """Seed DB with a student whose CORRECAO has NO warnings (clean doc)."""
    app, storage_instance = app_with_storage
    from models import NivelEnsino, TipoDocumento
    from tests.fixtures.document_factory import DocumentFactory

    materia = storage_instance.criar_materia(
        "Matemática", "Matemática", NivelEnsino.FUNDAMENTAL_2,
    )
    turma = storage_instance.criar_turma(
        materia.id, "9º Ano B", ano_letivo=2024, periodo="Tarde",
    )
    atividade = storage_instance.criar_atividade(
        turma.id, "Prova Clean", tipo="prova", nota_maxima=10.0,
    )
    aluno = storage_instance.criar_aluno(
        "João Limpo", "joao@test.com", "2024-C01",
    )
    storage_instance.vincular_aluno_turma(aluno.id, turma.id)

    factory = DocumentFactory(temp_data_dir / "docs")

    enunciado = factory.criar_prova_teste("Matemática", num_questoes=4)
    gabarito = factory.criar_gabarito_teste("Matemática", num_questoes=4)
    prova_aluno = factory.criar_prova_aluno("João Limpo", "Matemática", num_questoes=4)

    storage_instance.salvar_documento(
        str(enunciado.path), TipoDocumento.ENUNCIADO, atividade.id,
    )
    storage_instance.salvar_documento(
        str(gabarito.path), TipoDocumento.GABARITO, atividade.id,
    )
    storage_instance.salvar_documento(
        str(prova_aluno.path), TipoDocumento.PROVA_RESPONDIDA,
        atividade.id, aluno_id=aluno.id,
    )

    # Clean CORRECAO — no warnings
    correcao = factory.criar_correcao_com_avisos(
        aluno_nome="João Limpo",
        materia="Matemática",
        num_questoes=4,
        avisos_documento=[],
        avisos_questao=[],
        nota_final=9.0,
    )
    storage_instance.salvar_documento(
        str(correcao.path), TipoDocumento.CORRECAO,
        atividade.id, aluno_id=aluno.id,
    )

    return {
        "app": app,
        "storage": storage_instance,
        "atividade": atividade,
        "aluno": aluno,
    }


# ============================================================
# Tests: Visualizador reads warnings from pipeline JSON
# ============================================================

class TestVisualizadorReadsWarnings:
    """E2E: visualizador reads _avisos from CORRECAO JSON and includes severity."""

    def test_visualizador_reads_avisos_documento(self, seeded_context_with_warnings, monkeypatch):
        """Visualizador must read _avisos_documento from CORRECAO JSON."""
        import visualizador as viz_mod
        from visualizador import VisualizadorResultados

        ctx = seeded_context_with_warnings
        monkeypatch.setattr(viz_mod, "storage", ctx["storage"])
        viz = VisualizadorResultados()
        resultado = viz.get_resultado_aluno(ctx["atividade"].id, ctx["aluno"].id)

        assert resultado is not None, "get_resultado_aluno returned None"
        result_dict = resultado.to_dict()

        assert "avisos_documento" in result_dict, "to_dict() missing avisos_documento"
        avisos = result_dict["avisos_documento"]
        assert len(avisos) == 2, f"Expected 2 avisos_documento, got {len(avisos)}"

        # Check codes match what we injected
        codes = [w["codigo"] for w in avisos]
        assert "ILLEGIBLE_DOCUMENT" in codes
        assert "LOW_CONFIDENCE" in codes

        # Check severity was added
        for w in avisos:
            assert "severidade" in w, f"Warning {w['codigo']} missing 'severidade'"

    def test_visualizador_reads_avisos_questao(self, seeded_context_with_warnings, monkeypatch):
        """Visualizador must read _avisos_questao from CORRECAO JSON."""
        import visualizador as viz_mod
        from visualizador import VisualizadorResultados

        ctx = seeded_context_with_warnings
        monkeypatch.setattr(viz_mod, "storage", ctx["storage"])
        viz = VisualizadorResultados()
        resultado = viz.get_resultado_aluno(ctx["atividade"].id, ctx["aluno"].id)

        result_dict = resultado.to_dict()
        avisos = result_dict["avisos_questao"]
        assert len(avisos) == 2, f"Expected 2 avisos_questao, got {len(avisos)}"

        # Check question numbers
        q_nums = [w["questao"] for w in avisos]
        assert 2 in q_nums
        assert 4 in q_nums

    def test_clean_document_has_empty_avisos(self, seeded_context_clean, monkeypatch):
        """Clean CORRECAO (no warnings) must return empty arrays."""
        import visualizador as viz_mod
        from visualizador import VisualizadorResultados

        ctx = seeded_context_clean
        monkeypatch.setattr(viz_mod, "storage", ctx["storage"])
        viz = VisualizadorResultados()
        resultado = viz.get_resultado_aluno(ctx["atividade"].id, ctx["aluno"].id)

        result_dict = resultado.to_dict()
        assert result_dict["avisos_documento"] == [], "Expected empty avisos_documento"
        assert result_dict["avisos_questao"] == [], "Expected empty avisos_questao"


# ============================================================
# Tests: API returns warnings in response
# ============================================================

class TestAPIReturnsWarnings:
    """E2E: GET /api/resultados/ returns warnings with severity."""

    def test_api_resultado_includes_avisos(self, seeded_context_with_warnings):
        """API response must include avisos_documento and avisos_questao."""
        ctx = seeded_context_with_warnings
        client = TestClient(ctx["app"])

        resp = client.get(
            f"/api/resultados/{ctx['atividade'].id}/{ctx['aluno'].id}"
        )
        assert resp.status_code == 200, f"API returned {resp.status_code}: {resp.text}"

        data = resp.json()
        resultado = data.get("resultado", data)

        assert "avisos_documento" in resultado, "API response missing avisos_documento"
        assert "avisos_questao" in resultado, "API response missing avisos_questao"
        assert len(resultado["avisos_documento"]) == 2
        assert len(resultado["avisos_questao"]) == 2

        # Verify severity is present
        for w in resultado["avisos_documento"]:
            assert "severidade" in w, f"API warning {w['codigo']} missing severidade"

    def test_api_clean_resultado_has_empty_avisos(self, seeded_context_clean):
        """API response for clean doc must have empty avisos arrays."""
        ctx = seeded_context_clean
        client = TestClient(ctx["app"])

        resp = client.get(
            f"/api/resultados/{ctx['atividade'].id}/{ctx['aluno'].id}"
        )
        assert resp.status_code == 200

        data = resp.json()
        resultado = data.get("resultado", data)

        assert resultado["avisos_documento"] == []
        assert resultado["avisos_questao"] == []
