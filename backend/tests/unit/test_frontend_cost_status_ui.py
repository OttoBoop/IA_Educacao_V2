"""Structural checks for the dashboard cost status alert."""

from pathlib import Path

import pytest


FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture()
def html_content():
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


def test_dashboard_fetches_cost_status(html_content):
    assert "api('/custos/status?limit=80')" in html_content
    assert "costStatusPromise" in html_content
    assert "Promise.allSettled([statsPromise, materiasPromise, costStatusPromise])" in html_content


def test_dashboard_has_dedicated_cost_alert_container(html_content):
    assert 'id="dashboard-cost-alerts"' in html_content
    assert "renderDashboardCostStatus(costStatus)" in html_content
    assert "renderDashboardCostStatusError()" in html_content


def test_dashboard_surfaces_non_durable_token_usage(html_content):
    assert "token_usage_not_durable" in html_content
    assert "custos_persistencia_status" in html_content
    assert "parcial_sem_token_usage_duravel" in html_content
    assert "tokenUsageBackend.durable === false" in html_content
    assert "Custos não duráveis" in html_content
    assert "Aplique a migration token_usage" in html_content


def test_dashboard_does_not_hide_cost_status_request_failure(html_content):
    assert "Custos sem verificação" in html_content
    assert "Não foi possível verificar custos agora" in html_content
