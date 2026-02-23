"""
Unit tests for GET /api/health endpoint.

Tests verify the health endpoint returns correct status based on
Supabase connectivity. All DB calls are mocked — no real connections.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_health_endpoint.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a TestClient for the FastAPI app."""
    from main_v2 import app
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    """Tests for GET /api/health."""

    def test_returns_healthy_when_supabase_connected(self, client):
        """When supabase_db.test_connection() succeeds, return healthy status."""
        mock_db = MagicMock()
        mock_db.test_connection.return_value = (True, "Connected! 5 materias in database")

        with patch("main_v2.supabase_db", mock_db):
            response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["supabase"] is True

    def test_returns_degraded_when_supabase_unreachable(self, client):
        """When supabase_db.test_connection() fails, return degraded status."""
        mock_db = MagicMock()
        mock_db.test_connection.return_value = (False, "Connection failed: timeout")

        with patch("main_v2.supabase_db", mock_db):
            response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["supabase"] is False
        assert "message" in data

    def test_returns_degraded_on_unexpected_exception(self, client):
        """If test_connection() raises, endpoint catches it and returns degraded."""
        mock_db = MagicMock()
        mock_db.test_connection.side_effect = Exception("Unexpected error")

        with patch("main_v2.supabase_db", mock_db):
            response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["supabase"] is False
