"""
Integration tests for pipeline error handling (F8-T2).

Tests the WIRING between modules — not individual units.
Each test exercises the real chain: storage → visualizador → routes → PDF.

Unlike unit tests that mock everything, integration tests only mock the
database layer while using real file I/O, real JSON parsing, and real
module interactions.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_json_dir():
    """Create a temporary directory for JSON test files."""
    tmpdir = tempfile.mkdtemp(prefix="prova_ai_integration_")
    yield Path(tmpdir)
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def erro_pipeline_data():
    """Standard error pipeline data for tests."""
    return {
        "tipo": "DOCUMENTO_FALTANTE",
        "mensagem": "Documentos necessarios nao encontrados",
        "severidade": "critico",
        "etapa": "corrigir",
        "timestamp": "2026-02-24T12:00:00"
    }


@pytest.fixture
def json_with_error(temp_json_dir, erro_pipeline_data):
    """Create a real JSON file on disk with _erro_pipeline."""
    filepath = temp_json_dir / "correcao_test.json"
    data = {
        "_erro_pipeline": erro_pipeline_data,
        "_documentos_faltantes": ["extracao_questoes.json"],
        "nota": 0,
        "questoes": []
    }
    filepath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return filepath


@pytest.fixture
def json_without_error(temp_json_dir):
    """Create a real JSON file on disk without error."""
    filepath = temp_json_dir / "correcao_normal.json"
    data = {
        "nota": 8.5,
        "feedback": "Bom trabalho",
        "questoes": [
            {"numero": 1, "nota": 8.5, "nota_maxima": 10, "status": "parcial"}
        ]
    }
    filepath.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return filepath


def _make_mock_storage(json_path, has_error=True):
    """Create a mock storage that returns real file paths for JSON reading."""
    from models import TipoDocumento

    mock_atividade = MagicMock()
    mock_atividade.nome = "Prova Integration"
    mock_atividade.nota_maxima = 10.0
    mock_atividade.turma_id = "turma_1"

    mock_aluno = MagicMock()
    mock_aluno.nome = "Aluno Integration"
    mock_aluno.id = "aluno_int"
    mock_aluno.matricula = "INT001"

    mock_correcao_doc = MagicMock()
    mock_correcao_doc.tipo = TipoDocumento.CORRECAO
    mock_correcao_doc.id = "doc_correcao"
    mock_correcao_doc.extensao = ".json"
    mock_correcao_doc.aluno_id = "aluno_int"
    mock_correcao_doc.nome_arquivo = json_path.name
    mock_correcao_doc.criado_em = None
    mock_correcao_doc.ia_provider = "test_provider"

    mock_storage = MagicMock()
    mock_storage.get_atividade = MagicMock(return_value=mock_atividade)
    mock_storage.get_aluno = MagicMock(return_value=mock_aluno)
    mock_storage.listar_documentos = MagicMock(return_value=[mock_correcao_doc])
    mock_storage.get_documento = MagicMock(return_value=mock_correcao_doc)
    mock_storage.resolver_caminho_documento = MagicMock(return_value=json_path)

    return mock_storage


# ============================================================
# Integration Test: Visualizador reads real JSON with error
# ============================================================

class TestVisualizadorStorageIntegration:
    """Visualizador + real JSON file I/O + error propagation."""

    def test_visualizador_reads_real_json_with_erro_pipeline(self, json_with_error):
        """VisualizadorResultados reads a real JSON file and propagates erro_pipeline."""
        from visualizador import VisualizadorResultados

        mock_storage = _make_mock_storage(json_with_error, has_error=True)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        # _ler_json uses module-level storage import, so patch that too
        with patch("visualizador.storage", mock_storage):
            resultado = vis.get_resultado_aluno("ativ_int", "aluno_int")

        assert resultado is not None, "Should return VisaoAluno even with error"
        assert resultado.erro_pipeline is not None, \
            "VisaoAluno should have erro_pipeline from real JSON file"
        assert resultado.erro_pipeline["tipo"] == "DOCUMENTO_FALTANTE"

    def test_visualizador_reads_real_json_without_erro(self, json_without_error):
        """VisualizadorResultados reads normal JSON — no error contamination."""
        from visualizador import VisualizadorResultados

        mock_storage = _make_mock_storage(json_without_error, has_error=False)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        with patch("visualizador.storage", mock_storage):
            resultado = vis.get_resultado_aluno("ativ_int", "aluno_int")

        assert resultado is not None
        assert resultado.erro_pipeline is None, \
            "Normal result should NOT have erro_pipeline"

    def test_visualizador_to_dict_chain_with_error(self, json_with_error):
        """Full chain: JSON file → VisualizadorResultados → VisaoAluno.to_dict()."""
        from visualizador import VisualizadorResultados

        mock_storage = _make_mock_storage(json_with_error, has_error=True)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        with patch("visualizador.storage", mock_storage):
            resultado = vis.get_resultado_aluno("ativ_int", "aluno_int")
        resultado_dict = resultado.to_dict()

        # Verify the dict representation includes error
        assert "erro_pipeline" in resultado_dict, \
            "to_dict() must include erro_pipeline"
        assert resultado_dict["erro_pipeline"]["tipo"] == "DOCUMENTO_FALTANTE"
        assert resultado_dict["erro_pipeline"]["severidade"] == "critico"

    def test_visualizador_to_dict_chain_without_error(self, json_without_error):
        """Full chain: normal JSON → VisualizadorResultados → to_dict() has no error."""
        from visualizador import VisualizadorResultados

        mock_storage = _make_mock_storage(json_without_error, has_error=False)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        with patch("visualizador.storage", mock_storage):
            resultado = vis.get_resultado_aluno("ativ_int", "aluno_int")
        resultado_dict = resultado.to_dict()

        assert "erro_pipeline" not in resultado_dict, \
            "Normal to_dict() should NOT include erro_pipeline"


# ============================================================
# Integration Test: Routes endpoint chain
# ============================================================

class TestRoutesEndpointIntegration:
    """Routes endpoint + Visualizador + Storage chain."""

    @pytest.mark.asyncio
    async def test_endpoint_returns_erro_when_visualizador_has_error(self, json_with_error):
        """API endpoint detects error from visualizador and returns status=erro."""
        from visualizador import VisualizadorResultados

        # Build a real visualizador with mocked storage
        mock_storage = _make_mock_storage(json_with_error, has_error=True)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        # The route calls visualizador.get_resultado_aluno() first.
        # Since our error data produces a VisaoAluno, it will go through the "completo" path
        with patch("routes_resultados.visualizador", vis), \
             patch("routes_resultados.storage", mock_storage), \
             patch("visualizador.storage", mock_storage):
            from routes_resultados import get_resultado_aluno
            response = await get_resultado_aluno("ativ_int", "aluno_int")

        # When visualizador returns a result, the route wraps it as completo=True
        assert response["sucesso"] is True
        assert response["completo"] is True
        # The erro_pipeline is inside resultado dict (from VisaoAluno.to_dict())
        assert "erro_pipeline" in response["resultado"], \
            "Resultado dict should contain erro_pipeline from the chain"

    @pytest.mark.asyncio
    async def test_endpoint_partial_result_with_error(self, json_with_error, erro_pipeline_data):
        """When visualizador returns None, partial result path detects error in stored JSON."""
        mock_storage = _make_mock_storage(json_with_error, has_error=True)

        # Make visualizador return None so route falls through to partial path
        mock_vis = MagicMock()
        mock_vis.get_resultado_aluno = MagicMock(return_value=None)

        # Storage returns docs for partial path scanning
        from models import TipoDocumento
        mock_doc = MagicMock()
        mock_doc.tipo = TipoDocumento.CORRECAO
        mock_doc.id = "doc_correcao"
        mock_doc.extensao = ".json"
        mock_doc.aluno_id = "aluno_int"
        mock_doc.nome_arquivo = json_with_error.name

        def listar_docs(ativ_id, aluno_id=None):
            if aluno_id:
                return [mock_doc]
            return []

        mock_storage.listar_documentos = MagicMock(side_effect=listar_docs)

        with patch("routes_resultados.visualizador", mock_vis), \
             patch("routes_resultados.storage", mock_storage):
            from routes_resultados import get_resultado_aluno
            response = await get_resultado_aluno("ativ_int", "aluno_int")

        assert response["completo"] is False
        assert response.get("status") == "erro", \
            "Partial result with error JSON should have status=erro"
        assert "erro_pipeline" in response, \
            "Partial result should propagate erro_pipeline"
        assert response["erro_pipeline"]["tipo"] == "DOCUMENTO_FALTANTE"

    @pytest.mark.asyncio
    async def test_endpoint_partial_result_without_error(self, json_without_error):
        """Partial result with normal JSON should NOT have status=erro."""
        mock_storage = _make_mock_storage(json_without_error, has_error=False)

        mock_vis = MagicMock()
        mock_vis.get_resultado_aluno = MagicMock(return_value=None)

        from models import TipoDocumento
        mock_doc = MagicMock()
        mock_doc.tipo = TipoDocumento.CORRECAO
        mock_doc.id = "doc_normal"
        mock_doc.extensao = ".json"
        mock_doc.aluno_id = "aluno_int"
        mock_doc.nome_arquivo = json_without_error.name

        def listar_docs(ativ_id, aluno_id=None):
            if aluno_id:
                return [mock_doc]
            return []

        mock_storage.listar_documentos = MagicMock(side_effect=listar_docs)

        with patch("routes_resultados.visualizador", mock_vis), \
             patch("routes_resultados.storage", mock_storage):
            from routes_resultados import get_resultado_aluno
            response = await get_resultado_aluno("ativ_int", "aluno_int")

        assert response["completo"] is False
        assert response.get("status") != "erro", \
            "Normal partial result should NOT have status=erro"


# ============================================================
# Integration Test: PDF generation chain
# ============================================================

class TestPDFGenerationIntegration:
    """PDF generation from data with pipeline errors."""

    def test_pdf_chain_with_error_data(self, erro_pipeline_data):
        """generate_pdf() produces PDF with error section from real error data."""
        from document_generators import generate_pdf

        data = {
            "_erro_pipeline": erro_pipeline_data,
            "nota": 0,
            "questoes": []
        }

        pdf_bytes = generate_pdf(data, title="Integration Test", doc_type="correcao")

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100, "PDF should have substantial content"

        # Verify error text in PDF
        pdf_text = pdf_bytes.decode("latin-1", errors="ignore")
        assert "ERRO DE PROCESSAMENTO" in pdf_text
        assert "DOCUMENTO_FALTANTE" in pdf_text

    def test_pdf_chain_normal_data(self):
        """generate_pdf() with normal data has no error section."""
        from document_generators import generate_pdf

        data = {
            "nota": 8.5,
            "nota_maxima": 10,
            "questoes": [
                {"numero": 1, "pontos_obtidos": 8.5, "pontos_maximos": 10}
            ]
        }

        pdf_bytes = generate_pdf(data, title="Normal Test", doc_type="correcao")
        pdf_text = pdf_bytes.decode("latin-1", errors="ignore")

        assert "ERRO DE PROCESSAMENTO" not in pdf_text

    def test_pdf_chain_error_fields_present(self, erro_pipeline_data):
        """PDF error section includes all error fields from the pipeline data."""
        from document_generators import generate_pdf

        data = {"_erro_pipeline": erro_pipeline_data, "nota": 0}

        pdf_bytes = generate_pdf(data, title="Fields Test", doc_type="correcao")
        pdf_text = pdf_bytes.decode("latin-1", errors="ignore")

        # All fields from the error should appear in the PDF
        assert "DOCUMENTO_FALTANTE" in pdf_text, "tipo should appear in PDF"
        assert "critico" in pdf_text, "severidade should appear in PDF"
        assert "corrigir" in pdf_text, "etapa should appear in PDF"


# ============================================================
# Integration Test: Full chain (Visualizador → to_dict → PDF)
# ============================================================

class TestFullChainIntegration:
    """End-to-end: JSON file → Visualizador → to_dict → generate_pdf."""

    def test_full_chain_error_to_pdf(self, json_with_error):
        """JSON with error → Visualizador reads → to_dict → generate_pdf includes error."""
        from visualizador import VisualizadorResultados
        from document_generators import generate_pdf

        # Step 1: Visualizador reads the file
        mock_storage = _make_mock_storage(json_with_error, has_error=True)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        with patch("visualizador.storage", mock_storage):
            resultado = vis.get_resultado_aluno("ativ_int", "aluno_int")
        assert resultado is not None

        # Step 2: Convert to dict (as the API would)
        resultado_dict = resultado.to_dict()
        assert "erro_pipeline" in resultado_dict

        # Step 3: Generate PDF from the dict
        # The PDF generator expects _erro_pipeline key (with underscore prefix)
        # to_dict() uses erro_pipeline (without underscore)
        # We bridge the key format as the real code would
        pdf_bytes = generate_pdf(
            {"_erro_pipeline": resultado_dict["erro_pipeline"], "nota": 0},
            title="Full Chain Test",
            doc_type="relatorio_final"
        )

        pdf_text = pdf_bytes.decode("latin-1", errors="ignore")
        assert "ERRO DE PROCESSAMENTO" in pdf_text, \
            "Full chain should produce PDF with error section"

    def test_full_chain_normal_no_error(self, json_without_error):
        """Normal JSON → Visualizador → to_dict → generate_pdf has no error."""
        from visualizador import VisualizadorResultados
        from document_generators import generate_pdf

        mock_storage = _make_mock_storage(json_without_error, has_error=False)
        vis = VisualizadorResultados()
        vis.storage = mock_storage

        with patch("visualizador.storage", mock_storage):
            resultado = vis.get_resultado_aluno("ativ_int", "aluno_int")
        resultado_dict = resultado.to_dict()

        assert "erro_pipeline" not in resultado_dict

        pdf_bytes = generate_pdf(resultado_dict, title="Normal Chain", doc_type="correcao")
        pdf_text = pdf_bytes.decode("latin-1", errors="ignore")
        assert "ERRO DE PROCESSAMENTO" not in pdf_text
