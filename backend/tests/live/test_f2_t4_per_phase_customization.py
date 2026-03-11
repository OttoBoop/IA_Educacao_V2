"""
F2-T4: Per-phase prompt/model customization in the desempenho settings modal.

The advanced options section must:
1. Populate per-phase model dropdowns with available models (not just "Padrão")
2. Send per-phase model selections to the backend via FormData
3. Backend pipeline endpoints must accept `phase_models` parameter

Existing state:
  - 6 per-phase <select> elements exist with data-phase attributes ✓
  - executarDesempenhoFromModal() collects phaseModels from selectors ✓
  - BUT: dropdowns only have <option value="">Padrão</option> — NOT populated
  - BUT: phaseModels collected but NOT sent to backend in FormData
  - BUT: backend does NOT accept phase_models parameter

Run: cd IA_Educacao_V2/backend && pytest tests/live/test_f2_t4_per_phase_customization.py -v -m live
"""

import re
from pathlib import Path

import pytest
import requests

from .conftest import LIVE_URL

pytestmark = [pytest.mark.live]

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"

PIPELINE_PHASES = [
    "extrair_questoes",
    "extrair_gabarito",
    "extrair_respostas",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]


# ============================================================
# Shared fixtures
# ============================================================

@pytest.fixture(scope="module")
def html_content():
    """Read the frontend HTML file once for all tests in this module."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


# ============================================================
# Test 1: Per-phase dropdowns populated with model options
# ============================================================


class TestPerPhaseDropdownsPopulated:
    """F2-T4: carregarDesempenhoProviders() must populate the per-phase
    model dropdowns with available models, not just the main provider
    dropdown.

    Current state: only `input-desempenho-provider` is populated.
    Per-phase selects only have <option value="">Padrão</option>.
    """

    def test_populate_function_fills_phase_selectors(self, html_content):
        """carregarDesempenhoProviders() must populate per-phase model
        selectors by iterating desempenho-model-<phase> elements and
        inserting model <option> elements.

        Acceptable patterns:
          - querySelectorAll('[data-phase]').forEach(...innerHTML)
          - getElementById('desempenho-model-' + phase).innerHTML
          - A loop that sets options on all 6 phase selects

        The key requirement: each per-phase dropdown must show the
        available models so users can override the default per-phase.
        """
        # Find carregarDesempenhoProviders function and extract ONLY its body
        match = re.search(
            r"async\s+function\s+carregarDesempenhoProviders\s*\(",
            html_content,
        )
        assert match, "carregarDesempenhoProviders function not found"

        # Find the next function declaration to limit scope
        next_func = re.search(
            r"\n\s{8}(?:async\s+)?function\s+\w+\s*\(",
            html_content[match.end():match.end() + 3000],
        )
        end_offset = next_func.start() if next_func else 2000
        func_body = html_content[match.start():match.end() + end_offset]

        # Check that it populates per-phase selectors (not just the main one)
        # Must reference desempenho-model- IDs or data-phase attributes
        populates_phase_selectors = bool(re.search(
            r"""(?:desempenho-model-\w|querySelectorAll\s*\(\s*['"][^'"]*data-phase)""",
            func_body,
        ))
        assert populates_phase_selectors, (
            "F2-T4: carregarDesempenhoProviders() must populate per-phase model "
            "selectors (desempenho-model-<phase>). "
            "\nCurrently: only populates the main 'input-desempenho-provider' dropdown. "
            "\nExpected: iterate per-phase selects and insert model <option> elements."
        )


# ============================================================
# Test 2: phaseModels sent to backend in FormData
# ============================================================


class TestPhaseModelsSentToBackend:
    """F2-T4: executarDesempenho() must serialize phaseModels and
    append it to the FormData sent to the backend API.

    Current state: phaseModels parameter is accepted but never
    appended to FormData (lines 10148-10157).
    """

    def test_phase_models_appended_to_form_data(self, html_content):
        """executarDesempenho() must include phaseModels in the FormData.

        Acceptable patterns:
          - formData.append('phase_models', JSON.stringify(phaseModels))
          - formData.append('phase_models', ...)
          - formData.set('phase_models', ...)

        The key requirement: per-phase model selections must reach the
        backend so it can use different models for different phases.
        """
        match = re.search(
            r"async\s+function\s+executarDesempenho\s*\(",
            html_content,
        )
        assert match, "executarDesempenho function not found"
        func_body = html_content[match.start():match.start() + 3000]

        sends_phase_models = bool(re.search(
            r"""formData\.(?:append|set)\s*\(\s*['"]phase_models['"]""",
            func_body,
        ))
        assert sends_phase_models, (
            "F2-T4: executarDesempenho() must append 'phase_models' to FormData. "
            "\nCurrently: phaseModels parameter is accepted but NEVER sent to backend. "
            "\nExpected: `formData.append('phase_models', JSON.stringify(phaseModels))` "
            "so the backend knows which model to use for each pipeline phase."
        )


# ============================================================
# Test 3: Per-phase selectors have "Padrão" default + model list
# ============================================================


class TestPerPhaseSelectorsHaveDefaultOption:
    """F2-T4: Each per-phase selector must have a "Padrão" (default)
    option that means 'use the global model selection'.
    """

    def test_phase_selectors_have_padrao_default(self, html_content):
        """Each per-phase <select> must have an option with value=""
        labeled "Padrão" as the first/default option.
        """
        for phase in PIPELINE_PHASES:
            pattern = re.compile(
                rf'id=["\']desempenho-model-{re.escape(phase)}["\']'
            )
            assert pattern.search(html_content), (
                f"F2-T4: Missing per-phase selector for '{phase}'"
            )

        # Check that each has a "Padrão" option
        has_padrao = bool(re.search(
            r"""<option\s+value=['"]['"]>Padr[aã]o</option>""",
            html_content,
        ))
        assert has_padrao, (
            "F2-T4: Per-phase selectors must have a 'Padrão' default option "
            "with empty value, meaning 'use global model selection'."
        )


# ============================================================
# Test 4 (LIVE): Backend pipeline endpoint accepts phase_models
# ============================================================


class TestBackendAcceptsPhaseModels:
    """F2-T4 (LIVE): The desempenho pipeline endpoints must accept
    a `phase_models` parameter in the form data.
    """

    def test_pipeline_tarefa_accepts_phase_models(self):
        """POST /api/executar/pipeline-desempenho-tarefa must not
        reject phase_models as an unknown parameter.

        We send an invalid atividade_id to avoid triggering a real
        pipeline, but include phase_models to verify it's accepted.
        """
        url = f"{LIVE_URL}/api/executar/pipeline-desempenho-tarefa"
        resp = requests.post(
            url,
            data={
                "atividade_id": "nonexistent-f2t4-test",
                "phase_models": '{"extrair_questoes": "gpt5nano001"}',
            },
            timeout=30,
        )
        # Should return 200 (task queued) or 400/404 (invalid entity)
        # NOT 422 (validation error — unknown field) or 500
        assert resp.status_code not in (422, 500), (
            f"POST pipeline-desempenho-tarefa rejected phase_models. "
            f"Status: {resp.status_code}. Response: {resp.text[:300]}"
        )


# ============================================================
# Test 5: Phase labels displayed next to each selector
# ============================================================


class TestPhaseLabelsDisplayed:
    """F2-T4: Each per-phase model selector must have a visible label
    showing the phase name so users know which phase they're customizing.
    """

    def test_phase_selectors_have_labels(self, html_content):
        """The advanced options section must contain human-readable phase
        labels near each per-phase model selector.

        Acceptable patterns:
          - <label>Extrair Questões</label> before the select
          - A <small> or <span> with the phase name
          - The select itself has a label attribute
          - Phase names appear in the advanced section HTML

        The key requirement: the user must see "Extrair Questões",
        "Corrigir", etc. next to each dropdown.
        """
        # Find the advanced section content
        match = re.search(
            r'id=["\']desempenho-advanced["\']',
            html_content,
        )
        assert match, "desempenho-advanced section not found"

        # Get the advanced section content (up to ~5000 chars)
        section = html_content[match.start():match.start() + 5000]

        # Check that at least some phase labels are visible
        phase_labels = [
            "Extrair Quest",  # Extrair Questões
            "Extrair Gab",    # Extrair Gabarito
            "Extrair Resp",   # Extrair Respostas
            "Corrigir",
            "Analisar",       # Analisar Habilidades
            "Relat",          # Relatório / Gerar Relatório
        ]
        found_labels = sum(
            1 for label in phase_labels
            if re.search(re.escape(label), section, re.IGNORECASE)
        )
        assert found_labels >= 4, (
            f"F2-T4: Per-phase model selectors must have visible labels. "
            f"Found {found_labels}/6 phase labels in the advanced section. "
            f"Expected at least 4 (e.g., 'Extrair Questões', 'Corrigir', etc.)."
        )
