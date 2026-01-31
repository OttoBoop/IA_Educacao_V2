"""
Test Pipeline Prompts UI - Verifica que o modal Pipeline tem selecao de prompts.

Bug Fix: 2026-01-30 - Pipeline Prompts Selection Missing
Commit: f5884f0

Requires: Playwright, local server OR production access
Markers: @pytest.mark.ui, @pytest.mark.regression

Run standalone: python tests/ui/test_pipeline_prompts.py
Run with pytest: pytest tests/ui/test_pipeline_prompts.py -v
"""

import sys
import time

# Verificar se playwright esta instalado
try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[WARN] Playwright nao instalado. Rode: pip install playwright && playwright install chromium")

# Importar pytest apenas se disponivel
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

# URLs para teste
LOCAL_URL = "file:///c:/Users/otavi/Documents/prova-ai/IA_Educacao_V2/frontend/index_v2.html"
PROD_URL = "https://ia-educacao-v2.onrender.com/"


def populate_pipeline_modal(page: Page):
    """Abre e popula o modal Pipeline Completo com dados simulados."""
    page.evaluate("""
        // Fechar modal welcome
        const welcome = document.getElementById('modal-welcome');
        if (welcome) welcome.style.display = 'none';

        // Abrir modal pipeline
        const modal = document.getElementById('modal-pipeline-completo');
        if (modal) {
            modal.classList.add('active');
            modal.style.display = 'flex';
        }

        // Popular container unificado se vazio
        const unified = document.getElementById('pipeline-steps-unified');
        if (unified && unified.children.length === 0) {
            const etapas = [
                {id: 'extrair_questoes', nome: 'Extrair Questoes'},
                {id: 'extrair_gabarito', nome: 'Extrair Gabarito'},
                {id: 'extrair_respostas', nome: 'Extrair Respostas'},
                {id: 'corrigir', nome: 'Corrigir'},
                {id: 'analisar_habilidades', nome: 'Analisar Habilidades'},
                {id: 'gerar_relatorio', nome: 'Gerar Relatorio'}
            ];
            unified.innerHTML = etapas.map(e => `
                <div style="display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 8px; align-items: center;">
                    <label style="display: flex; align-items: center; gap: 6px;">
                        <input type="checkbox" checked>
                        <span>${e.nome}</span>
                    </label>
                    <select class="form-select" data-prompt-etapa="${e.id}">
                        <option value="">Padrao</option>
                    </select>
                    <select class="form-select" data-etapa="${e.id}">
                        <option value="">Padrao</option>
                    </select>
                </div>
            `).join('');
        }

        // Abrir accordion
        const accordion = document.getElementById('pipeline-advanced-models');
        if (accordion) accordion.setAttribute('open', '');
    """)


# Skip se playwright nao disponivel
requires_playwright = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright nao instalado"
) if PYTEST_AVAILABLE else lambda f: f


class TestPipelinePromptsRegression:
    """
    Testes de regressao para a funcionalidade de selecao de prompts no Pipeline.

    Bug: Modal Pipeline nao tinha opcao de selecionar prompts por etapa.
    Fix: Adicionado select de prompt padrao + 3 colunas no accordion.
    """

    @requires_playwright
    @pytest.mark.ui
    @pytest.mark.regression
    def test_prompt_select_exists_local(self):
        """Verifica que o select de prompt padrao existe (teste local)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 800, 'height': 900})

            page.goto(LOCAL_URL, timeout=30000)
            time.sleep(1)
            populate_pipeline_modal(page)
            time.sleep(0.5)

            # Verificar que o select de prompt padrao existe
            count = page.locator('#input-pipeline-prompt-default').count()
            browser.close()

            assert count > 0, "Select de prompt padrao nao encontrado no HTML local"

    @requires_playwright
    @pytest.mark.ui
    @pytest.mark.regression
    @pytest.mark.slow
    def test_prompt_select_exists_production(self):
        """Verifica que o select de prompt padrao existe em producao."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 800, 'height': 900})

            page.goto(PROD_URL, timeout=90000)
            page.wait_for_load_state('networkidle', timeout=90000)
            time.sleep(2)
            populate_pipeline_modal(page)
            time.sleep(0.5)

            # Verificar que o select de prompt padrao existe
            count = page.locator('#input-pipeline-prompt-default').count()
            browser.close()

            assert count > 0, "Select de prompt padrao nao encontrado em producao"

    @requires_playwright
    @pytest.mark.ui
    @pytest.mark.regression
    def test_accordion_has_three_columns(self):
        """Verifica que o accordion tem 3 colunas (ETAPA | PROMPT | MODELO)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 800, 'height': 900})

            page.goto(LOCAL_URL, timeout=30000)
            time.sleep(1)

            # Verificar CSS de 3 colunas no HTML
            html = page.content()
            browser.close()

            assert "grid-template-columns: 1.2fr 1fr 1fr" in html, \
                "Accordion nao tem layout de 3 colunas"

    @requires_playwright
    @pytest.mark.ui
    @pytest.mark.regression
    def test_accordion_header_has_prompt_column(self):
        """Verifica que o header do accordion inclui coluna PROMPT."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 800, 'height': 900})

            page.goto(LOCAL_URL, timeout=30000)
            time.sleep(1)

            html = page.content()
            browser.close()

            # O header deve ter Etapa, Prompt e Modelo
            assert "<span>Etapa</span>" in html, "Header nao tem coluna ETAPA"
            assert "<span>Prompt</span>" in html, "Header nao tem coluna PROMPT"
            assert "<span>Modelo</span>" in html, "Header nao tem coluna MODELO"


class TestPipelinePromptsSync:
    """Testes de sincronizacao entre local e producao."""

    @requires_playwright
    @pytest.mark.ui
    @pytest.mark.slow
    def test_local_and_production_are_synced(self):
        """Verifica que local e producao tem os mesmos elementos."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            # Testar local
            page_local = browser.new_page(viewport={'width': 800, 'height': 900})
            page_local.goto(LOCAL_URL, timeout=30000)
            time.sleep(1)
            local_has_prompt = page_local.locator('#input-pipeline-prompt-default').count() > 0
            page_local.close()

            # Testar producao
            page_prod = browser.new_page(viewport={'width': 800, 'height': 900})
            page_prod.goto(PROD_URL, timeout=90000)
            page_prod.wait_for_load_state('networkidle', timeout=90000)
            time.sleep(2)
            prod_has_prompt = page_prod.locator('#input-pipeline-prompt-default').count() > 0
            page_prod.close()

            browser.close()

            assert local_has_prompt == prod_has_prompt, \
                f"Dessincronizacao: local={local_has_prompt}, prod={prod_has_prompt}"


def run_standalone():
    """Roda testes sem pytest."""
    if not PLAYWRIGHT_AVAILABLE:
        print("[ERRO] Playwright nao instalado!")
        print("Rode: pip install playwright && playwright install chromium")
        return False

    print("=" * 60)
    print("TESTES STANDALONE - Pipeline Prompts UI")
    print("=" * 60)

    tests = TestPipelinePromptsRegression()
    results = []

    # Teste 1: Local prompt select
    print("\n[TEST] test_prompt_select_exists_local...")
    try:
        tests.test_prompt_select_exists_local()
        print("[PASS]")
        results.append(True)
    except Exception as e:
        print(f"[FAIL] {e}")
        results.append(False)

    # Teste 2: 3 colunas
    print("\n[TEST] test_accordion_has_three_columns...")
    try:
        tests.test_accordion_has_three_columns()
        print("[PASS]")
        results.append(True)
    except Exception as e:
        print(f"[FAIL] {e}")
        results.append(False)

    # Teste 3: Header com PROMPT
    print("\n[TEST] test_accordion_header_has_prompt_column...")
    try:
        tests.test_accordion_header_has_prompt_column()
        print("[PASS]")
        results.append(True)
    except Exception as e:
        print(f"[FAIL] {e}")
        results.append(False)

    # Resumo
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"RESULTADO: {passed}/{total} testes passaram")
    print("=" * 60)

    return all(results)


if __name__ == "__main__":
    if PYTEST_AVAILABLE and len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        pytest.main([__file__, "-v"])
    else:
        success = run_standalone()
        sys.exit(0 if success else 1)
