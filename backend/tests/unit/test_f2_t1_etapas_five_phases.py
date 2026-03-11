"""
F2-T1: Expand renderDesempenhoEtapasRow() stages from 3 to 5+ phases.

RED phase — tests should FAIL because:
- renderDesempenhoEtapasRow has only 3 stages (corrigir, analisar, relatorio)
- prefetchDesempenhoEtapasState only maps 3 doc types (correcao, analise_habilidades, relatorio_final)
- The two missing phases are extrair_questoes and extrair_gabarito
"""

import re
from pathlib import Path

import pytest


HTML_PATH = Path(__file__).resolve().parents[3] / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    return HTML_PATH.read_text(encoding="utf-8")


class TestF2T1_EtapasFivePhases:
    """F2-T1: renderDesempenhoEtapasRow must render all pipeline phases, not just 3."""

    def test_stages_array_has_at_least_five_entries(self, html_content):
        """The stages array in renderDesempenhoEtapasRow must have >= 5 entries."""
        match = re.search(
            r'function renderDesempenhoEtapasRow.*?const stages = \[(.*?)\];',
            html_content,
            re.DOTALL,
        )
        assert match, "Could not find stages array in renderDesempenhoEtapasRow"
        stages_block = match.group(1)
        keys = re.findall(r"key:\s*'(\w+)'", stages_block)
        assert len(keys) >= 5, (
            f"renderDesempenhoEtapasRow has only {len(keys)} stages ({keys}). "
            f"Must have at least 5 to show all pipeline phases."
        )

    def test_stages_include_extrair_questoes(self, html_content):
        """The stages array must include extrair_questoes phase."""
        match = re.search(
            r'function renderDesempenhoEtapasRow.*?const stages = \[(.*?)\];',
            html_content,
            re.DOTALL,
        )
        assert match, "Could not find stages array in renderDesempenhoEtapasRow"
        stages_block = match.group(1)
        assert "'extrair_questoes'" in stages_block, (
            "renderDesempenhoEtapasRow stages array is missing 'extrair_questoes' phase"
        )

    def test_stages_include_extrair_gabarito(self, html_content):
        """The stages array must include extrair_gabarito phase."""
        match = re.search(
            r'function renderDesempenhoEtapasRow.*?const stages = \[(.*?)\];',
            html_content,
            re.DOTALL,
        )
        assert match, "Could not find stages array in renderDesempenhoEtapasRow"
        stages_block = match.group(1)
        assert "'extrair_gabarito'" in stages_block, (
            "renderDesempenhoEtapasRow stages array is missing 'extrair_gabarito' phase"
        )

    def test_prefetch_maps_at_least_five_doc_types(self, html_content):
        """prefetchDesempenhoEtapasState must map at least 5 doc types in stagesExistentes."""
        match = re.search(
            r'function prefetchDesempenhoEtapasState.*?const stagesExistentes = \{(.*?)\};',
            html_content,
            re.DOTALL,
        )
        assert match, "Could not find stagesExistentes in prefetchDesempenhoEtapasState"
        mapping_block = match.group(1)
        # Count key: value pairs
        keys = re.findall(r'(\w+):\s*existingDocs\.has', mapping_block)
        assert len(keys) >= 5, (
            f"prefetchDesempenhoEtapasState only maps {len(keys)} doc types ({keys}). "
            f"Must map at least 5 to cover all pipeline phases."
        )
