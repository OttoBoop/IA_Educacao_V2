"""
F2-T4: Per-phase prompt/model customization in the desempenho settings modal.

RED phase — tests MUST FAIL because:
- The modal currently has ONE global model selector (input-desempenho-provider)
- There is no "Advanced Options" collapsible section
- There are no per-phase model selector dropdowns
- executarDesempenhoFromModal() does not collect per-phase model selections

The 6 pipeline phases are:
  extrair_questoes, extrair_gabarito, extrair_respostas,
  corrigir, analisar_habilidades, gerar_relatorio
"""

import re
from pathlib import Path

import pytest


HTML_PATH = Path(__file__).resolve().parents[3] / "frontend" / "index_v2.html"

PIPELINE_PHASES = [
    "extrair_questoes",
    "extrair_gabarito",
    "extrair_respostas",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]


@pytest.fixture
def html_content():
    return HTML_PATH.read_text(encoding="utf-8")


class TestF2T4_AdvancedOptionsSection:
    """F2-T4: The desempenho settings modal must have an 'Advanced Options' collapsible section."""

    def test_advanced_options_section_exists(self, html_content):
        """modal-desempenho-settings must contain an advanced options collapsible section."""
        # Look for a section ID or label that signals "advanced options"
        pattern = re.compile(
            r'id=["\']desempenho-advanced|'
            r'[Oo]p[çc][õo]es\s+[Aa]van[çc]adas|'
            r'[Aa]dvanced\s+[Oo]ptions',
            re.IGNORECASE,
        )
        assert pattern.search(html_content), (
            "The desempenho settings modal has no 'Advanced Options' section. "
            "Expected an element with id='desempenho-advanced' or a label containing "
            "'Opções Avançadas' / 'Advanced Options'."
        )

    def test_advanced_options_section_is_inside_desempenho_modal(self, html_content):
        """The advanced options section must be inside modal-desempenho-settings, not elsewhere."""
        # Capture the modal block
        modal_match = re.search(
            r'<div[^>]+id=["\']modal-desempenho-settings["\'].*?</div>\s*</div>\s*</div>',
            html_content,
            re.DOTALL,
        )
        assert modal_match, "Could not find modal-desempenho-settings in the HTML."
        modal_block = modal_match.group(0)

        pattern = re.compile(
            r'id=["\']desempenho-advanced|'
            r'[Oo]p[çc][õo]es\s+[Aa]van[çc]adas|'
            r'[Aa]dvanced\s+[Oo]ptions',
            re.IGNORECASE,
        )
        assert pattern.search(modal_block), (
            "The advanced options section was not found inside modal-desempenho-settings. "
            "It must live within that modal's body."
        )


class TestF2T4_PerPhaseModelSelectors:
    """F2-T4: Each pipeline phase must have its own model selector dropdown."""

    def test_per_phase_selectors_exist(self, html_content):
        """There must be select elements with data-phase attributes for per-phase model selection."""
        # Accept either data-phase="<phase>" or id="desempenho-model-<phase>"
        phase_selector_pattern = re.compile(
            r'data-phase=["\'](\w+)["\']|id=["\']desempenho-model-(\w+)["\']'
        )
        found_phases = set()
        for m in phase_selector_pattern.finditer(html_content):
            phase = m.group(1) or m.group(2)
            if phase in PIPELINE_PHASES:
                found_phases.add(phase)

        assert found_phases, (
            "No per-phase model selectors found. Expected select elements with "
            "data-phase='<phase>' or id='desempenho-model-<phase>' for each pipeline phase."
        )

    @pytest.mark.parametrize("phase", PIPELINE_PHASES)
    def test_each_phase_has_a_selector(self, html_content, phase):
        """Every pipeline phase must have a dedicated model selector element."""
        # Match either data-phase="<phase>" or id="desempenho-model-<phase>"
        pattern = re.compile(
            rf'data-phase=["\']{re.escape(phase)}["\']|'
            rf'id=["\']desempenho-model-{re.escape(phase)}["\']'
        )
        assert pattern.search(html_content), (
            f"No per-phase model selector found for phase '{phase}'. "
            f"Expected a select with data-phase='{phase}' or id='desempenho-model-{phase}'."
        )

    def test_all_six_phases_have_selectors(self, html_content):
        """All 6 pipeline phases must have dedicated model selector elements."""
        phase_selector_pattern = re.compile(
            r'data-phase=["\'](\w+)["\']|id=["\']desempenho-model-(\w+)["\']'
        )
        found_phases = set()
        for m in phase_selector_pattern.finditer(html_content):
            phase = m.group(1) or m.group(2)
            if phase in PIPELINE_PHASES:
                found_phases.add(phase)

        missing = set(PIPELINE_PHASES) - found_phases
        assert not missing, (
            f"Per-phase model selectors are missing for: {sorted(missing)}. "
            f"All 6 phases must have a selector: {PIPELINE_PHASES}"
        )


class TestF2T4_ExecutarCollectsPerPhaseModels:
    """F2-T4: executarDesempenhoFromModal() must collect per-phase model selections."""

    def test_executa_reads_per_phase_model_data(self, html_content):
        """executarDesempenhoFromModal must query per-phase model selectors."""
        # Capture the function body
        func_match = re.search(
            r'function executarDesempenhoFromModal\s*\(\)(.*?)(?=\n\s{0,8}function |\n\s{0,8}async function |\Z)',
            html_content,
            re.DOTALL,
        )
        assert func_match, "Could not find executarDesempenhoFromModal function."
        func_body = func_match.group(1)

        # Expect it to query per-phase selectors — data-phase or desempenho-model-
        per_phase_read_pattern = re.compile(
            r'data-phase|desempenho-model-|phaseModels|phase_models|perPhase',
            re.IGNORECASE,
        )
        assert per_phase_read_pattern.search(func_body), (
            "executarDesempenhoFromModal() does not collect per-phase model selections. "
            "It must query elements by data-phase or id='desempenho-model-<phase>' and "
            "pass per-phase model IDs to the backend."
        )

    def test_executa_passes_per_phase_models_to_backend_call(self, html_content):
        """executarDesempenhoFromModal must forward per-phase models to executarDesempenho()."""
        func_match = re.search(
            r'function executarDesempenhoFromModal\s*\(\)(.*?)(?=\n\s{0,8}function |\n\s{0,8}async function |\Z)',
            html_content,
            re.DOTALL,
        )
        assert func_match, "Could not find executarDesempenhoFromModal function."
        func_body = func_match.group(1)

        # Find the call to executarDesempenho(...)
        call_match = re.search(
            r'executarDesempenho\s*\(([^)]+)\)',
            func_body,
        )
        assert call_match, (
            "executarDesempenhoFromModal() does not call executarDesempenho(). "
            "Cannot verify that per-phase models are forwarded."
        )
        call_args = call_match.group(1)

        # The per-phase models variable must appear in the call arguments
        per_phase_arg_pattern = re.compile(
            r'phaseModels|phase_models|perPhase|modelosPorEtapa',
            re.IGNORECASE,
        )
        assert per_phase_arg_pattern.search(call_args), (
            f"executarDesempenho() is called without a per-phase models argument. "
            f"Current args: {call_args.strip()!r}. "
            f"Expected a variable like 'phaseModels' or 'modelosPorEtapa' in the call."
        )
