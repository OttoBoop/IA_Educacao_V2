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


class TestDeployInfoEndpoint:
    """Tests for GET /api/deploy-info."""

    def test_reads_commit_written_during_build(self, client, tmp_path):
        deploy_file = tmp_path / "deploy_sha.txt"
        deploy_file.write_text(
            "be19b7eae80f111ed589f902dfb293b7230312e0\n",
            encoding="utf-8",
        )

        with patch("main_v2.DEPLOY_SHA_PATH", deploy_file), patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/deploy-info")

        assert response.status_code == 200
        data = response.json()
        assert data["commit"] == "be19b7e"
        assert data["full_commit"] == "be19b7eae80f111ed589f902dfb293b7230312e0"
        assert data["source"] == "deploy_sha_file"

    def test_env_commit_takes_precedence(self, client, tmp_path):
        deploy_file = tmp_path / "deploy_sha.txt"
        deploy_file.write_text("1111111\n", encoding="utf-8")

        with patch("main_v2.DEPLOY_SHA_PATH", deploy_file), patch.dict(
            "os.environ",
            {"NOVOCR_DEPLOY_SHA": "abcdef1234567890"},
            clear=True,
        ):
            response = client.get("/api/deploy-info")

        assert response.status_code == 200
        data = response.json()
        assert data["commit"] == "abcdef1"
        assert data["full_commit"] == "abcdef1234567890"
        assert data["source"] == "NOVOCR_DEPLOY_SHA"

    def test_returns_unknown_when_commit_unavailable(self, client, tmp_path):
        missing_file = tmp_path / "missing-deploy-sha.txt"

        with patch("main_v2.DEPLOY_SHA_PATH", missing_file), patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/deploy-info")

        assert response.status_code == 200
        data = response.json()
        assert data["commit"] == "unknown"
        assert data["full_commit"] is None
        assert data["source"] == "unavailable"
