"""
Shared fixtures for live browser tests.

Live tests run against the deployed application at the LIVE_URL.
They require: playwright, pytest-asyncio.

Run: cd IA_Educacao_V2/backend && pytest tests/live/ -v -m live
"""
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "live: marks tests that hit the live deployment (deselect with '-m \"not live\"')")


LIVE_URL = "https://ia-educacao-v2.onrender.com"

# Entity IDs from live API (/api/navegacao/arvore)
MATERIA_ID = "f95445ace30e7dc5"       # Cálculo 1
TURMA_ID = "6b5dc44c08aaf375"         # EPGE 2021
ATIVIDADE_ID = "effad48d128c7083"     # A1 - Cálculo 1
