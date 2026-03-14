"""
Tests for prompts API pagination (F1-T1).

Verifies that GET /api/prompts supports page/per_page params
while remaining backwards compatible when no pagination params are sent.

Related plan: docs/PLAN_Prompts_Page_Rewrite.md
Task: F1-T1
"""

import math
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from main_v2 import app
    return TestClient(app)


@pytest.fixture
def mock_prompts():
    """Create a list of mock PromptTemplate objects."""
    from prompts import PromptTemplate, EtapaProcessamento
    from datetime import datetime

    prompts = []
    for i in range(25):
        etapa = EtapaProcessamento.CORRIGIR if i < 15 else EtapaProcessamento.EXTRAIR_QUESTOES
        p = PromptTemplate(
            id=f"test_{i}",
            nome=f"Prompt {i}",
            etapa=etapa,
            texto=f"Texto do prompt {i}",
            is_padrao=(i == 0),
            is_ativo=True,
            versao=1,
            criado_em=datetime.now(),
            atualizado_em=datetime.now(),
        )
        prompts.append(p)
    return prompts


class TestPaginationBackwardsCompat:
    """Default calls (no pagination params) must work exactly as before."""

    def test_no_params_returns_all(self, client, mock_prompts):
        """GET /api/prompts with no page/per_page returns all prompts."""
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = mock_prompts
            resp = client.get("/api/prompts")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 25
            assert len(data["prompts"]) == 25
            assert "page" not in data
            assert "per_page" not in data
            assert "total_pages" not in data


class TestPaginatedResponse:
    """When per_page > 0, response includes pagination metadata."""

    def test_paginated_response_shape(self, client, mock_prompts):
        """Paginated response has total, page, per_page, total_pages fields."""
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = mock_prompts
            resp = client.get("/api/prompts?page=1&per_page=10")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 25
            assert data["page"] == 1
            assert data["per_page"] == 10
            assert data["total_pages"] == 3
            assert len(data["prompts"]) == 10

    def test_second_page(self, client, mock_prompts):
        """Page 2 returns the next slice of prompts."""
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = mock_prompts
            resp = client.get("/api/prompts?page=2&per_page=10")
            data = resp.json()
            assert data["page"] == 2
            assert len(data["prompts"]) == 10

    def test_last_page_partial(self, client, mock_prompts):
        """Last page may have fewer items than per_page."""
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = mock_prompts
            resp = client.get("/api/prompts?page=3&per_page=10")
            data = resp.json()
            assert data["page"] == 3
            assert len(data["prompts"]) == 5

    def test_page_beyond_total(self, client, mock_prompts):
        """Page beyond total returns empty prompts list."""
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = mock_prompts
            resp = client.get("/api/prompts?page=10&per_page=10")
            data = resp.json()
            assert data["page"] == 10
            assert len(data["prompts"]) == 0
            assert data["total"] == 25

    def test_pagination_with_etapa_filter(self, client, mock_prompts):
        """Pagination works correctly with etapa filter."""
        corrigir_prompts = [p for p in mock_prompts if p.etapa.value == "corrigir"]
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = corrigir_prompts
            resp = client.get("/api/prompts?etapa=corrigir&page=1&per_page=5")
            data = resp.json()
            assert data["total"] == 15
            assert data["per_page"] == 5
            assert data["total_pages"] == 3
            assert len(data["prompts"]) == 5

    def test_empty_results_paginated(self, client):
        """Empty results with pagination returns total_pages=1."""
        with patch('routes_prompts.prompt_manager') as mock_pm:
            mock_pm.listar_prompts.return_value = []
            resp = client.get("/api/prompts?page=1&per_page=10")
            data = resp.json()
            assert data["total"] == 0
            assert data["total_pages"] == 1
            assert len(data["prompts"]) == 0
