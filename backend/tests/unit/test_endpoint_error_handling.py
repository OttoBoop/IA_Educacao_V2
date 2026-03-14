"""Tests for endpoint error handling — 3 endpoints must not return 500."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import logging
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main_v2 import app

client = TestClient(app)


class TestEstatisticasErrorHandling:
    """GET /api/estatisticas must not return 500 when storage throws."""

    def test_returns_200_when_fast_helper_throws(self):
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.get_estatisticas_gerais_fast.side_effect = ValueError("bad enum in DB")
            response = client.get("/api/estatisticas")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "total_materias" in data or "_error" in data

    def test_returns_200_when_fast_helper_raises_generic_exception(self):
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.get_estatisticas_gerais_fast.side_effect = Exception("db error")
            response = client.get("/api/estatisticas")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestArvoreNavegacaoErrorHandling:
    """GET /api/navegacao/arvore must not return 500 when storage throws."""

    def test_returns_200_when_get_arvore_throws(self):
        with patch("main_v2.storage") as mock_storage:
            mock_storage.get_arvore_navegacao.side_effect = ValueError("from_dict failed")
            response = client.get("/api/navegacao/arvore")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "materias" in data or "_error" in data


class TestDocumentosTodosErrorHandling:
    """GET /api/documentos/todos must not return 500 when storage throws."""

    def test_returns_200_when_fast_helper_throws(self):
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos_com_contexto_fast.side_effect = Exception("crash")
            response = client.get("/api/documentos/todos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "documentos" in data or "_error" in data

    def test_returns_empty_payload_when_fast_helper_raises_generic_exception(self):
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos_com_contexto_fast.side_effect = Exception("db error")
            response = client.get("/api/documentos/todos")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["documentos"] == []


class TestErrorLogging:
    """Verify that endpoint errors are logged server-side via logging.exception()."""

    def test_estatisticas_logs_exception(self, caplog):
        with caplog.at_level(logging.ERROR):
            with patch("routes_extras.storage") as mock_storage:
                mock_storage.get_estatisticas_gerais_fast.side_effect = ValueError("test log")
                client.get("/api/estatisticas")
        assert "Error in /api/estatisticas" in caplog.text

    def test_arvore_logs_exception(self, caplog):
        with caplog.at_level(logging.ERROR):
            with patch("main_v2.storage") as mock_storage:
                mock_storage.get_arvore_navegacao.side_effect = ValueError("test log")
                client.get("/api/navegacao/arvore")
        assert "Error in /api/navegacao/arvore" in caplog.text

    def test_documentos_todos_logs_exception(self, caplog):
        with caplog.at_level(logging.ERROR):
            with patch("routes_extras.storage") as mock_storage:
                mock_storage.listar_documentos_com_contexto_fast.side_effect = ValueError("test log")
                client.get("/api/documentos/todos")
        assert "Error in /api/documentos/todos" in caplog.text


class TestErrorFieldContainsMessage:
    """Verify that _error field contains the exception message."""

    def test_estatisticas_error_field(self):
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.get_estatisticas_gerais_fast.side_effect = ValueError("specific error msg")
            response = client.get("/api/estatisticas")
        data = response.json()
        assert "_error" in data
        assert "specific error msg" in data["_error"]

    def test_arvore_error_field(self):
        with patch("main_v2.storage") as mock_storage:
            mock_storage.get_arvore_navegacao.side_effect = ValueError("arvore crash")
            response = client.get("/api/navegacao/arvore")
        data = response.json()
        assert "_error" in data
        assert "arvore crash" in data["_error"]

    def test_documentos_error_field(self):
        with patch("routes_extras.storage") as mock_storage:
            mock_storage.listar_documentos_com_contexto_fast.side_effect = ValueError("docs crash")
            response = client.get("/api/documentos/todos")
        data = response.json()
        assert "_error" in data
        assert "docs crash" in data["_error"]
