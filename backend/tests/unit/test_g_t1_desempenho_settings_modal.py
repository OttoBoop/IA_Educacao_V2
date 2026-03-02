"""
Test G-T1: Desempenho Settings Modal HTML

G-T1: Create desempenho settings modal HTML in index_v2.html — clone
modal-pipeline-completo pattern (lines 3884-3959): model dropdown (from
/settings/models), prompt dropdown (from /prompts filtered for desempenho
etapas), force-rerun checkbox. Add carregarDesempenhoProviders() to populate
dropdowns.

Tests:
- Modal with desempenho settings ID exists
- Modal has model/provider dropdown
- Modal has prompt dropdown
- Modal has force-rerun checkbox
- carregarDesempenhoProviders() JS function exists
- Modal follows standard structure (modal-header, modal-body, modal-footer)

Run: cd IA_Educacao_V2/backend && python -m pytest tests/unit/test_g_t1_desempenho_settings_modal.py -v
"""

from pathlib import Path
import re

import pytest

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    """Read the frontend HTML file."""
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


@pytest.fixture
def modal_block(html_content):
    """Extract the desempenho settings modal HTML block.

    Searches for a modal-overlay div whose id contains both 'desempenho' and
    'settings' (or 'configuracoes'). Returns the slice of HTML starting at
    that div up to (but not including) the next top-level modal-overlay, so
    all assertions operate on the correct modal only.
    """
    # Match the opening tag of a modal-overlay whose id references desempenho settings
    pattern = re.compile(
        r'<div[^>]+class=["\'][^"\']*modal-overlay[^"\']*["\'][^>]+'
        r'id=["\'][^"\']*desempenho[^"\']*(?:settings|configurac)[^"\']*["\'][^>]*>',
        re.IGNORECASE,
    )
    match = pattern.search(html_content)
    if match is None:
        # Also try id before class order
        pattern2 = re.compile(
            r'<div[^>]+id=["\'][^"\']*desempenho[^"\']*(?:settings|configurac)[^"\']*["\'][^>]+'
            r'class=["\'][^"\']*modal-overlay[^"\']*["\'][^>]*>',
            re.IGNORECASE,
        )
        match = pattern2.search(html_content)
    return match


# ============================================================
# TEST 1: Desempenho settings modal exists
# ============================================================

class TestDesempenhoSettingsModalExists:
    """G-T1: A modal element referencing desempenho settings must be present."""

    def test_desempenho_settings_modal_exists(self, html_content):
        """HTML must contain a modal-overlay with an id referencing desempenho
        and settings (or configuracoes/configurações)."""
        has_modal = (
            'id="modal-desempenho-settings"' in html_content
            or "id='modal-desempenho-settings'" in html_content
            or 'id="modal-desempenho-configuracoes"' in html_content
            or "id='modal-desempenho-configuracoes'" in html_content
        )
        # Also allow any id that contains 'desempenho' AND ('settings' OR 'config')
        if not has_modal:
            has_modal = bool(re.search(
                r'id=["\'][^"\']*desempenho[^"\']*(?:settings|config)[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            ))
        assert has_modal, (
            "index_v2.html must contain a modal-overlay element whose id "
            "references both 'desempenho' and 'settings' (or 'configuracoes'). "
            "Expected something like id=\"modal-desempenho-settings\". "
            "G-T1 clones modal-pipeline-completo to create this modal."
        )


# ============================================================
# TEST 2: Model/provider dropdown inside the modal
# ============================================================

class TestModalHasModelDropdown:
    """G-T1: Settings modal must include a <select> for model/provider selection."""

    def test_modal_has_model_dropdown(self, html_content):
        """Modal must contain a <select> element for choosing the AI model/provider.

        Expected id candidates: input-desempenho-provider, input-desempenho-model,
        or similar pattern following the modal-pipeline-completo naming convention
        (which uses input-pipeline-provider-default).
        """
        # Check for the expected select id variants
        has_provider_select = (
            'id="input-desempenho-provider"' in html_content
            or "id='input-desempenho-provider'" in html_content
            or 'id="input-desempenho-model"' in html_content
            or "id='input-desempenho-model'" in html_content
        )
        # Broader pattern: any select whose id contains 'desempenho' and 'provider' or 'model'
        if not has_provider_select:
            has_provider_select = bool(re.search(
                r'<select[^>]+id=["\'][^"\']*desempenho[^"\']*(?:provider|model)[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            ))
        assert has_provider_select, (
            "index_v2.html must have a <select> element inside the desempenho settings modal "
            "for AI model/provider selection. "
            "Expected id like 'input-desempenho-provider' or 'input-desempenho-model', "
            "mirroring 'input-pipeline-provider-default' in modal-pipeline-completo. "
            "G-T1 requires this dropdown to be populated from /settings/models."
        )


# ============================================================
# TEST 3: Prompt dropdown inside the modal
# ============================================================

class TestModalHasPromptDropdown:
    """G-T1: Settings modal must include a <select> for prompt selection."""

    def test_modal_has_prompt_dropdown(self, html_content):
        """Modal must contain a <select> element for choosing the desempenho prompt.

        Expected id candidates: input-desempenho-prompt or similar, mirroring
        input-pipeline-prompt-default from modal-pipeline-completo.
        """
        has_prompt_select = (
            'id="input-desempenho-prompt"' in html_content
            or "id='input-desempenho-prompt'" in html_content
        )
        # Broader pattern: any select whose id contains 'desempenho' and 'prompt'
        if not has_prompt_select:
            has_prompt_select = bool(re.search(
                r'<select[^>]+id=["\'][^"\']*desempenho[^"\']*prompt[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            ))
        assert has_prompt_select, (
            "index_v2.html must have a <select> element inside the desempenho settings modal "
            "for prompt selection. "
            "Expected id like 'input-desempenho-prompt', mirroring "
            "'input-pipeline-prompt-default' in modal-pipeline-completo. "
            "G-T1 requires this dropdown to be populated from /prompts filtered for "
            "desempenho etapas."
        )


# ============================================================
# TEST 4: Force-rerun checkbox inside the modal
# ============================================================

class TestModalHasForceRerunCheckbox:
    """G-T1: Settings modal must include a checkbox for force-rerun."""

    def test_modal_has_force_rerun_checkbox(self, html_content):
        """Modal must contain an <input type='checkbox'> for forcing re-execution.

        Expected id candidates: input-desempenho-force-rerun or similar,
        mirroring input-pipeline-force-rerun from modal-pipeline-completo.
        """
        has_checkbox = (
            'id="input-desempenho-force-rerun"' in html_content
            or "id='input-desempenho-force-rerun'" in html_content
        )
        # Broader pattern: any checkbox whose id contains 'desempenho' and 'force' or 'rerun'
        if not has_checkbox:
            has_checkbox = bool(re.search(
                r'<input[^>]+type=["\']checkbox["\'][^>]+id=["\'][^"\']*desempenho[^"\']*(?:force|rerun)[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            ))
            if not has_checkbox:
                has_checkbox = bool(re.search(
                    r'<input[^>]+id=["\'][^"\']*desempenho[^"\']*(?:force|rerun)[^"\']*["\'][^>]+type=["\']checkbox["\']',
                    html_content,
                    re.IGNORECASE,
                ))
        assert has_checkbox, (
            "index_v2.html must have an <input type='checkbox'> inside the desempenho settings modal "
            "for the force-rerun option. "
            "Expected id like 'input-desempenho-force-rerun', mirroring "
            "'input-pipeline-force-rerun' in modal-pipeline-completo."
        )


# ============================================================
# TEST 5: carregarDesempenhoProviders() JS function exists
# ============================================================

class TestCarregarDesempenhoProvidersFunction:
    """G-T1: A JavaScript function to populate the dropdowns must be defined."""

    def test_carregar_desempenho_providers_function_exists(self, html_content):
        """index_v2.html must define a carregarDesempenhoProviders() function
        (or equivalent name) that fetches models + prompts and populates the
        settings modal dropdowns.

        Mirrors the carregarProviders() / carregarPipelineProviders() pattern
        used by modal-pipeline-completo to populate its dropdowns.
        """
        has_function = (
            "function carregarDesempenhoProviders(" in html_content
            or "async function carregarDesempenhoProviders(" in html_content
        )
        # Also allow arrow-function or slightly different naming
        if not has_function:
            has_function = bool(re.search(
                r'(?:async\s+)?function\s+carregar(?:Desempenho)?(?:Settings)?Providers?\s*\(',
                html_content,
                re.IGNORECASE,
            ))
        assert has_function, (
            "index_v2.html must define a 'carregarDesempenhoProviders()' function "
            "(sync or async) that populates the model and prompt dropdowns in the "
            "desempenho settings modal. "
            "This mirrors the provider-loading pattern used by modal-pipeline-completo."
        )


# ============================================================
# TEST 6: Modal uses the standard modal structure
# ============================================================

class TestModalHasStandardStructure:
    """G-T1: The desempenho settings modal must follow the standard
    modal-overlay > modal > modal-header + modal-body + modal-footer pattern
    used throughout index_v2.html."""

    def test_modal_has_modal_header(self, html_content):
        """The desempenho settings modal block must contain a modal-header element."""
        # Locate the modal-desempenho-settings block
        modal_start = html_content.find('modal-desempenho-settings')
        if modal_start == -1:
            # Fallback: any id containing desempenho + settings/config
            match = re.search(
                r'id=["\'][^"\']*desempenho[^"\']*(?:settings|config)[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            )
            modal_start = match.start() if match else -1

        assert modal_start != -1, (
            "Desempenho settings modal must exist before testing its structure. "
            "Add the modal-overlay element with a desempenho-settings id first."
        )
        # Look within the next 4000 chars (enough for a complete modal)
        modal_slice = html_content[modal_start: modal_start + 4000]
        assert "modal-header" in modal_slice, (
            "The desempenho settings modal must contain a 'modal-header' div, "
            "following the standard modal-overlay > modal > modal-header pattern."
        )

    def test_modal_has_modal_body(self, html_content):
        """The desempenho settings modal block must contain a modal-body element."""
        modal_start = html_content.find('modal-desempenho-settings')
        if modal_start == -1:
            match = re.search(
                r'id=["\'][^"\']*desempenho[^"\']*(?:settings|config)[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            )
            modal_start = match.start() if match else -1

        assert modal_start != -1, (
            "Desempenho settings modal must exist before testing its structure."
        )
        modal_slice = html_content[modal_start: modal_start + 4000]
        assert "modal-body" in modal_slice, (
            "The desempenho settings modal must contain a 'modal-body' div "
            "holding the form elements (model select, prompt select, checkbox)."
        )

    def test_modal_has_modal_footer(self, html_content):
        """The desempenho settings modal block must contain a modal-footer element."""
        modal_start = html_content.find('modal-desempenho-settings')
        if modal_start == -1:
            match = re.search(
                r'id=["\'][^"\']*desempenho[^"\']*(?:settings|config)[^"\']*["\']',
                html_content,
                re.IGNORECASE,
            )
            modal_start = match.start() if match else -1

        assert modal_start != -1, (
            "Desempenho settings modal must exist before testing its structure."
        )
        modal_slice = html_content[modal_start: modal_start + 4000]
        assert "modal-footer" in modal_slice, (
            "The desempenho settings modal must contain a 'modal-footer' div "
            "with Cancel + Execute buttons, following the standard pattern."
        )
