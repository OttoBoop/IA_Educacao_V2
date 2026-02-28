"""
test_sidebar_dedup.py — RED Tests: Sidebar Duplicate Materia Fix

F2-T2: Tests for the duplicate sidebar matéria bug.

Root cause (found in F2-T1):
  - listar_materias() in storage.py (line 351) does SELECT * FROM materias
    with no DISTINCT / dedup — returns all rows including duplicates.
  - get_arvore_navegacao() (line 1455) iterates all matérias with no dedup.
  - renderNavTree() in index_v2.html (line ~6161) renders everything it receives
    faithfully — no dedup logic. It clears the container with innerHTML= before
    rendering, so the bug is NOT append-without-clear. The API sends duplicates,
    renderNavTree renders them as-is.

What these tests verify:
  Test 1 (Integration): Intercept /api/navegacao/arvore via page.route() to return
    a response with two "Matemática" entries (different IDs, same name). After the
    page calls loadNavTree(), the sidebar DOM must contain each matéria name exactly
    once. FAILS because renderNavTree() renders all items it receives.

  Test 2 (Unit via page.evaluate): Call renderNavTree() directly with duplicate
    input [{id:"m1", nome:"Matemática", turmas:[]}, {id:"m2", nome:"Matemática",
    turmas:[]}]. Assert the sidebar container has exactly 1 matéria entry.
    FAILS because renderNavTree() does no dedup.

These tests MUST FAIL in RED phase because renderNavTree() renders whatever
array it receives without any deduplication.

They will PASS after F2-T3 implements dedup in renderNavTree().

Run:
    cd IA_Educacao_V2/backend
    RUN_UI_TESTS=1 pytest tests/ui/test_sidebar_dedup.py -v

Requires: local server at http://localhost:8000
    python -m uvicorn main_v2:app --port 8000 --reload
"""

import os
import json
import pytest
from typing import List

pytest_plugins = ['pytest_asyncio']

try:
    from playwright.async_api import async_playwright, Page, Browser, Route
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

LOCAL_URL = "http://localhost:8000"

# API response with two matérias that have the SAME name but different IDs.
# This simulates the database-level duplicates that listar_materias() returns.
# renderNavTree() will receive this and render 2 nodes — demonstrating the bug.
DUPLICATE_ARVORE_RESPONSE = {
    "materias": [
        {
            "id": "mat-dup-1",
            "nome": "Matematica",
            "turmas": []
        },
        {
            "id": "mat-dup-2",
            "nome": "Matematica",
            "turmas": []
        }
    ]
}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
async def check_server():
    """Verify local server is running before tests."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip(
            "Playwright not installed. Run: pip install playwright && playwright install chromium"
        )

    if not os.getenv("RUN_UI_TESTS"):
        pytest.skip("UI tests disabled. Set RUN_UI_TESTS=1 to enable")

    import httpx
    try:
        # Use a longer timeout (30s) to accommodate Supabase initialization
        # on the first request after server startup.
        async with httpx.AsyncClient() as client:
            response = await client.get(LOCAL_URL, timeout=30.0)
            if response.status_code != 200:
                pytest.exit(
                    f"Server at {LOCAL_URL} returned {response.status_code}.\n"
                    f"Start with: cd IA_Educacao_V2/backend && python -m uvicorn main_v2:app --port 8000"
                )
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.exit(
            f"Cannot connect to {LOCAL_URL}. Start server first.\n"
            f"  cd IA_Educacao_V2/backend && python -m uvicorn main_v2:app --port 8000\n"
            f"Error: {e}"
        )


@pytest.fixture(scope="function")
async def browser():
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed")
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        yield b
        await b.close()


@pytest.fixture(scope="function")
async def page(browser: Browser):
    """Desktop page (1400x900)."""
    p = await browser.new_page(viewport={"width": 1400, "height": 900})
    yield p
    await p.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

async def dismiss_all_modals(page: Page):
    """
    Force-close all active modal overlays so they do not block the sidebar.
    Uses evaluate() to directly remove .active — same as closeModal().
    """
    await page.evaluate("""
        () => {
            document.querySelectorAll('.modal-overlay.active').forEach(el => {
                el.classList.remove('active');
            });
        }
    """)
    await page.wait_for_timeout(150)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestSidebarDedup:
    """
    RED-phase tests for sidebar matéria deduplication (F2-T2).

    Both tests MUST FAIL until renderNavTree() (index_v2.html ~line 6161)
    is updated to deduplicate its input before rendering.
    """

    # ──────────────────────────────────────────────────────────────────────────
    # Test 1 — Integration: intercept /api/navegacao/arvore → inject duplicates
    # ──────────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_sidebar_renders_each_materia_name_exactly_once(self, page: Page):
        """
        Integration test: when the API returns two matérias with the same name,
        the sidebar must render that name exactly once (not twice).

        Strategy:
          1. Intercept /api/navegacao/arvore to return DUPLICATE_ARVORE_RESPONSE
             (two "Matematica" entries with different IDs).
          2. Load the page — loadNavTree() fetches the intercepted response and
             calls renderNavTree(data.materias).
          3. Count how many .tree-item elements exist inside #nav-tree.
          4. Assert count == 1 (not 2).

        Currently FAILS because renderNavTree() renders all items it receives
        without any deduplication — so 2 API entries produce 2 DOM nodes.

        Fix: renderNavTree() should deduplicate by matéria name (or ID) before
        rendering so each name appears at most once.
        """
        # Intercept the navigation tree API before the page loads
        async def serve_duplicate_materias(route: Route):
            await route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(DUPLICATE_ARVORE_RESPONSE)
            )

        await page.route("**/api/navegacao/arvore", serve_duplicate_materias)

        # Load the page — this triggers loadNavTree() on DOMContentLoaded
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_all_modals(page)

        # Give loadNavTree() time to fetch and render
        await page.wait_for_timeout(500)

        # Count .tree-item elements inside #tree-materias.
        # renderNavTree() renders into #tree-materias (not #nav-tree directly).
        # Each matéria in the input produces one top-level .tree-item div.
        # We count only direct .tree-item children of #tree-materias (not nested
        # turma/atividade items) to isolate the matéria count.
        materia_nodes = await page.evaluate("""
            () => {
                const container = document.getElementById('tree-materias');
                if (!container) return -1;
                // Direct children that are .tree-item (matéria-level items only)
                // renderNavTree() produces: .tree-item + .tree-children per matéria.
                // Count only .tree-item elements that are direct children.
                return Array.from(container.children)
                    .filter(el => el.classList.contains('tree-item')).length;
            }
        """)

        # Collect the actual rendered labels for a helpful error message
        rendered_labels: List[str] = await page.evaluate("""
            () => {
                const container = document.getElementById('tree-materias');
                if (!container) return [];
                // .tree-item-name holds the matéria name in renderNavTree() output
                return Array.from(container.querySelectorAll(':scope > .tree-item .tree-item-name'))
                    .map(el => el.textContent.trim());
            }
        """)

        assert materia_nodes == 1, (
            f"Sidebar rendered {materia_nodes} materia-level .tree-item node(s) inside "
            f"#tree-materias when the API returned 2 entries with the same nome 'Matematica'. "
            f"Expected exactly 1 node after deduplication. "
            f"Rendered labels: {rendered_labels}. "
            f"Currently renderNavTree() (index_v2.html line 6161) maps over all input items "
            f"without checking for duplicate nomes — 2 API entries produce 2 DOM nodes. "
            f"Fix: deduplicate by nome before the .map() call in renderNavTree()."
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Test 2 — Unit: call renderNavTree() directly with duplicate input
    # ──────────────────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    @pytest.mark.ui
    async def test_render_nav_tree_deduplicates_duplicate_input(self, page: Page):
        """
        Unit test via page.evaluate: call renderNavTree() directly with an array
        containing two matérias that share the same name. Assert the sidebar
        container renders exactly 1 .tree-item, not 2.

        Input to renderNavTree():
            [
                {id: "m1", nome: "Matematica", turmas: []},
                {id: "m2", nome: "Matematica", turmas: []}
            ]

        Expected result: #nav-tree has 1 .tree-item (deduplicated by nome).
        Actual result:   #nav-tree has 2 .tree-item (no dedup → FAILS in RED phase).

        This test does NOT depend on the API — it exercises renderNavTree() in
        isolation to prove the dedup must happen inside that function.
        """
        await page.goto(LOCAL_URL)
        await page.wait_for_load_state("networkidle")
        await dismiss_all_modals(page)

        # Call renderNavTree() directly with duplicate matéria data.
        # renderNavTree() writes into #tree-materias (not #nav-tree directly).
        # We count direct .tree-item children of #tree-materias (matéria-level nodes).
        result = await page.evaluate("""
            () => {
                const duplicateInput = [
                    { id: "m1", nome: "Matematica", turmas: [] },
                    { id: "m2", nome: "Matematica", turmas: [] }
                ];

                // renderNavTree is defined globally in index_v2.html
                if (typeof renderNavTree !== 'function') {
                    return { error: 'renderNavTree is not defined as a global function' };
                }

                renderNavTree(duplicateInput);

                // renderNavTree() renders into #tree-materias
                const container = document.getElementById('tree-materias');
                if (!container) {
                    return { error: '#tree-materias container not found in DOM' };
                }

                // Count direct .tree-item children (matéria-level, not nested turmas)
                const items = Array.from(container.children)
                    .filter(el => el.classList.contains('tree-item'));

                // .tree-item-name holds the matéria nome in renderNavTree() output
                const labels = items.map(item => {
                    const label = item.querySelector('.tree-item-name');
                    return label ? label.textContent.trim() : '';
                });

                return {
                    count: items.length,
                    labels: labels,
                    error: null
                };
            }
        """)

        # Guard: renderNavTree must be accessible
        if result.get('error'):
            pytest.fail(
                f"Cannot test renderNavTree(): {result['error']}. "
                f"Ensure renderNavTree() is a globally accessible function in index_v2.html."
            )

        count = result['count']
        labels: List[str] = result['labels']

        assert count == 1, (
            f"renderNavTree() rendered {count} matéria-level .tree-item node(s) inside "
            f"#tree-materias when given 2 matérias with the same nome 'Matematica'. "
            f"Expected exactly 1 node after deduplication by nome. "
            f"Rendered labels: {labels}. "
            f"Currently renderNavTree() (index_v2.html line 6161) maps over all input "
            f"items without checking for duplicate nomes — 2 items produce 2 DOM nodes. "
            f"Fix: before the .map() call, filter the input array to unique nomes:\n"
            f"  const seen = new Set();\n"
            f"  const unique = materias.filter(m => !seen.has(m.nome) && seen.add(m.nome));\n"
            f"  container.innerHTML = unique.map(m => ...).join('');"
        )


# ── pytest configuration ──────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "ui: UI tests using Playwright (requires local server)"
    )
