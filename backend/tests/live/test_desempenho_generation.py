"""
C-T1: Generate Desempenho reports at all 3 levels and verify content.

Live Playwright tests against the deployed application.
Triggers report generation via the UI, waits for the background task
to complete by polling the GET API, and verifies report content has
expected sections (narrative structure, student data, keywords).

Run:
    cd IA_Educacao_V2/backend
    pytest tests/live/test_desempenho_generation.py -v -m live
"""
import asyncio
import sys

import pytest
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from .conftest import LIVE_URL, MATERIA_ID, TURMA_ID, ATIVIDADE_ID

GENERATION_TIMEOUT = 180  # seconds to wait for background report generation
POLL_INTERVAL = 5         # seconds between API polls

pytestmark = [pytest.mark.live, pytest.mark.asyncio]


# ============================================================
# Helpers
# ============================================================

async def _launch_and_navigate():
    """Launch headless browser and navigate to the live app."""
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1280, "height": 800})
    page = await context.new_page()

    await page.goto(LIVE_URL, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass

    await page.evaluate("typeof closeWelcome === 'function' && closeWelcome()")
    await asyncio.sleep(0.5)

    return pw, browser, page


async def _go_to_desempenho_tab(page, level, entity_id):
    """Navigate to an entity view and switch to its Desempenho tab."""
    show_map = {
        "tarefa": f"showAtividade('{entity_id}')",
        "turma": f"showTurma('{entity_id}')",
        "materia": f"showMateria('{entity_id}')",
    }
    tab_func_map = {
        "tarefa": "showAtividadeTab",
        "turma": "showTurmaTab",
        "materia": "showMateriaTab",
    }

    await page.evaluate(show_map[level])
    await asyncio.sleep(2)

    tab_func = tab_func_map[level]
    clicked = await page.evaluate(f"""
        (() => {{
            const tabs = document.querySelectorAll('[onclick]');
            for (const tab of tabs) {{
                const oc = tab.getAttribute('onclick') || '';
                if (oc.includes("{tab_func}") && oc.includes("desempenho")) {{
                    tab.click();
                    return true;
                }}
            }}
            return false;
        }})()
    """)
    await asyncio.sleep(2)
    return clicked


async def _click_generate(page, level):
    """Click the Gerar Relatório button.  Returns 'clicked' | 'disabled' | 'not_found'."""
    return await page.evaluate(f"""
        (() => {{
            const area = document.getElementById('desempenho-generate-area-{level}');
            if (!area) return 'area_not_found';
            const btn = area.querySelector('button:not([disabled])');
            if (btn && btn.textContent.includes('Gerar')) {{
                btn.click();
                return 'clicked';
            }}
            if (area.querySelector('button[disabled]')) return 'disabled';
            return 'not_found';
        }})()
    """)


async def _poll_reports(page, level, entity_id, timeout=GENERATION_TIMEOUT):
    """Poll GET /api/desempenho/{level}/{entity_id} until runs appear."""
    for _ in range(timeout // POLL_INTERVAL):
        await asyncio.sleep(POLL_INTERVAL)
        data = await page.evaluate(f"""
            (async () => {{
                try {{
                    const r = await fetch('/api/desempenho/{level}/{entity_id}');
                    if (!r.ok) return {{ error: 'HTTP ' + r.status }};
                    return await r.json();
                }} catch (e) {{
                    return {{ error: e.message }};
                }}
            }})()
        """)
        if data and not data.get("error"):
            if data.get("runs"):
                return data
    return None


async def _fetch_doc_content(page, doc_id):
    """Fetch a single document's content via the API."""
    return await page.evaluate(f"""
        (async () => {{
            try {{
                const r = await fetch('/api/documentos/{doc_id}/conteudo');
                if (!r.ok) return {{ error: 'HTTP ' + r.status }};
                return await r.json();
            }} catch (e) {{
                return {{ error: e.message }};
            }}
        }})()
    """)


# Keywords that should appear in a desempenho report
_EXPECTED_KEYWORDS = [
    "aluno", "desempenho", "questão", "nota", "avaliação",
    "turma", "atividade", "relatório", "recomend",
]


def _assert_report_quality(content_data, level):
    """Verify the report content has expected structure and sections."""
    assert content_data is not None, f"No content data for {level} report"
    assert not content_data.get("error"), (
        f"Error fetching {level} report: {content_data.get('error')}"
    )
    assert content_data.get("pode_visualizar"), (
        f"{level} report not viewable (tipo_conteudo={content_data.get('tipo_conteudo')})"
    )

    conteudo = content_data.get("conteudo")
    assert conteudo is not None, f"{level} report conteudo is None"

    # Normalise to string for keyword search
    text = str(conteudo) if not isinstance(conteudo, str) else conteudo

    assert len(text) > 200, (
        f"{level} report too short ({len(text)} chars) — likely empty or error"
    )

    found = [kw for kw in _EXPECTED_KEYWORDS if kw.lower() in text.lower()]
    assert len(found) >= 2, (
        f"{level} report missing expected keywords. "
        f"Found {found}, expected ≥2 of {_EXPECTED_KEYWORDS}"
    )


# ============================================================
# Tests — one per Desempenho level
# ============================================================

class TestDesempenhoReportGeneration:
    """C-T1: Generate desempenho reports at all 3 levels and verify content."""

    async def test_generate_tarefa_report(self):
        """Atividade level: generate report via UI → poll API → verify content."""
        pw, browser, page = await _launch_and_navigate()
        try:
            ok = await _go_to_desempenho_tab(page, "tarefa", ATIVIDADE_ID)
            assert ok, "Could not find atividade Desempenho tab"

            gen = await _click_generate(page, "tarefa")
            assert gen == "clicked", f"Generate button not clickable (tarefa): {gen}"

            data = await _poll_reports(page, "tarefa", ATIVIDADE_ID)
            assert data is not None, (
                f"No tarefa reports within {GENERATION_TIMEOUT}s"
            )

            doc_id = data["runs"][0]["docs"][0]["id"]
            content = await _fetch_doc_content(page, doc_id)
            _assert_report_quality(content, "tarefa")
        finally:
            await browser.close()
            await pw.stop()

    async def test_generate_turma_report(self):
        """Turma level: generate report via UI → poll API → verify content."""
        pw, browser, page = await _launch_and_navigate()
        try:
            ok = await _go_to_desempenho_tab(page, "turma", TURMA_ID)
            assert ok, "Could not find turma Desempenho tab"

            gen = await _click_generate(page, "turma")
            assert gen == "clicked", f"Generate button not clickable (turma): {gen}"

            data = await _poll_reports(page, "turma", TURMA_ID)
            assert data is not None, (
                f"No turma reports within {GENERATION_TIMEOUT}s"
            )

            doc_id = data["runs"][0]["docs"][0]["id"]
            content = await _fetch_doc_content(page, doc_id)
            _assert_report_quality(content, "turma")
        finally:
            await browser.close()
            await pw.stop()

    async def test_generate_materia_report(self):
        """Matéria level: generate report via UI → poll API → verify content."""
        pw, browser, page = await _launch_and_navigate()
        try:
            ok = await _go_to_desempenho_tab(page, "materia", MATERIA_ID)
            assert ok, "Could not find matéria Desempenho tab"

            gen = await _click_generate(page, "materia")
            assert gen == "clicked", f"Generate button not clickable (matéria): {gen}"

            data = await _poll_reports(page, "materia", MATERIA_ID)
            assert data is not None, (
                f"No matéria reports within {GENERATION_TIMEOUT}s"
            )

            doc_id = data["runs"][0]["docs"][0]["id"]
            content = await _fetch_doc_content(page, doc_id)
            _assert_report_quality(content, "materia")
        finally:
            await browser.close()
            await pw.stop()
