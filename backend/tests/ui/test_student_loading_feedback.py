"""UI tests for the student loading shells and request guards."""

import asyncio
import json
import os

import pytest

pytest_plugins = ["pytest_asyncio"]

try:
    from playwright.async_api import Browser, Page, Route, async_playwright, expect

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


LOCAL_URL = "http://localhost:8000/index_v2.html"

FAKE_ALUNO_RESPONSE = {
    "aluno": {
        "id": "aluno-1",
        "nome": "Maria Silva",
        "matricula": "2024001",
        "email": "maria@example.com",
    },
    "turmas": [
        {
            "id": "turma-1",
            "nome": "9A",
            "ano_letivo": 2026,
            "periodo": None,
            "descricao": None,
            "materia_id": "mat-1",
            "materia_nome": "Matematica",
            "observacoes": None,
            "data_entrada": "2026-02-01T00:00:00",
        }
    ],
    "total_turmas": 1,
}

FAKE_DASHBOARD_RESPONSE = {
    "aluno": {"id": "aluno-1", "nome": "Maria Silva", "matricula": "2024001"},
    "resumo": {
        "total_turmas": 1,
        "total_atividades": 2,
        "atividades_corrigidas": 1,
        "media_geral": 8.5,
    },
    "por_materia": [
        {
            "materia": "Matematica",
            "total_atividades": 2,
            "corrigidas": 1,
            "media": 8.5,
        }
    ],
    "historico_recente": [
        {
            "materia": "Matematica",
            "turma": "9A",
            "atividade_id": "ativ-1",
            "atividade": "Prova 1",
            "tipo": "prova",
            "data": "2026-03-10T09:00:00",
            "nota": 8.5,
            "nota_maxima": 10.0,
            "percentual": 85.0,
            "corrigido": True,
        }
    ],
}

FAKE_RESULTADO_RESPONSE = {
    "sucesso": True,
    "completo": False,
    "progresso": 50,
    "etapas": {
        "prova_respondida": {"nome": "Prova do Aluno", "completa": True, "doc_id": "doc-1"},
        "correcao": {"nome": "Correcao", "completa": False, "doc_id": None},
    },
    "dados_parciais": {},
    "documentos_disponiveis": [],
    "mensagem": "Pipeline em progresso",
}

FAKE_DOCUMENTOS_RESPONSE = {"documentos": []}
FAKE_ATIVIDADE_RESPONSE = {
    "atividade": {
        "id": "ativ-1",
        "nome": "Prova 1",
        "turma_id": "turma-1",
        "tipo": "prova",
        "data_aplicacao": "2026-03-10T09:00:00",
        "nota_maxima": 10.0,
    },
    "turma": {"id": "turma-1", "nome": "9A", "materia_id": "mat-1"},
    "materia": {"id": "mat-1", "nome": "Matematica"},
}


@pytest.fixture(scope="session", autouse=True)
async def check_server():
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not installed. Run: pip install playwright && playwright install chromium")

    if not os.getenv("RUN_UI_TESTS"):
        pytest.skip("UI tests disabled. Set RUN_UI_TESTS=1 to enable")

    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(LOCAL_URL, timeout=5.0)
            if response.status_code != 200:
                pytest.exit(
                    f"Server at {LOCAL_URL} returned {response.status_code}. "
                    "Start with: cd backend && python -m uvicorn main_v2:app --port 8000"
                )
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.exit(
            "Cannot connect to local UI server. "
            "Start with: cd backend && python -m uvicorn main_v2:app --port 8000 "
            f"(error: {exc})"
        )


@pytest.fixture(scope="function")
async def browser():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def page(browser: Browser):
    page = await browser.new_page(viewport={"width": 1440, "height": 960})
    yield page
    await page.close()


async def prepare_page(page: Page):
    await page.goto(LOCAL_URL, wait_until="domcontentloaded")
    await page.wait_for_function("() => typeof showAluno === 'function' && typeof showDashboardAluno === 'function'")
    await page.evaluate(
        """
        () => {
            document.querySelectorAll('.modal-overlay.active').forEach(el => el.classList.remove('active'));
        }
        """
    )


async def fulfill_json(route: Route, payload, delay_ms: int = 0):
    if delay_ms:
        await asyncio.sleep(delay_ms / 1000)
    await route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps(payload),
    )


def json_handler(payload, delay_ms: int = 0):
    async def handler(route: Route):
        await fulfill_json(route, payload, delay_ms=delay_ms)

    return handler


@pytest.mark.asyncio
@pytest.mark.ui
async def test_show_aluno_loading_shell_progresses_to_reassurance_and_retry(page: Page):
    await page.route("**/api/alunos/aluno-1", json_handler(FAKE_ALUNO_RESPONSE, delay_ms=7200))
    await prepare_page(page)

    await page.evaluate("() => { void showAluno('aluno-1', 'Maria Silva', '2024001'); }")

    await expect(page.locator("#content .page-title")).to_have_text("Maria Silva", timeout=700)
    await expect(page.locator("#content")).to_contain_text("Buscando turmas e dados do aluno...", timeout=700)
    await expect(page.locator("#content")).to_contain_text(
        "A página está funcionando. Isso pode levar alguns segundos.",
        timeout=700,
    )

    await page.wait_for_timeout(1700)
    await expect(page.locator("#content")).to_contain_text(
        "Os dados estão demorando mais que o normal, mas o carregamento continua.",
        timeout=700,
    )

    await page.wait_for_timeout(4600)
    await expect(page.get_by_role("button", name="Tentar novamente")).to_be_visible(timeout=700)


@pytest.mark.asyncio
@pytest.mark.ui
async def test_show_dashboard_aluno_shell_appears_immediately(page: Page):
    await page.route("**/api/dashboard/aluno/aluno-1", json_handler(FAKE_DASHBOARD_RESPONSE, delay_ms=2000))
    await prepare_page(page)

    await page.evaluate("() => { void showDashboardAluno('aluno-1', 'Maria Silva', '2024001'); }")

    await expect(page.locator("#content .page-title")).to_have_text("Dashboard do Aluno", timeout=700)
    await expect(page.locator("#content")).to_contain_text("Calculando histórico e estatísticas...", timeout=700)
    await expect(page.locator("#content")).to_contain_text("Turmas", timeout=700)


@pytest.mark.asyncio
@pytest.mark.ui
async def test_show_resultado_aluno_shell_appears_immediately(page: Page):
    await page.route("**/api/resultados/ativ-1/aluno-1", json_handler(FAKE_RESULTADO_RESPONSE, delay_ms=2200))
    await page.route("**/api/documentos?atividade_id=ativ-1&aluno_id=aluno-1", json_handler(FAKE_DOCUMENTOS_RESPONSE))
    await page.route("**/api/atividades/ativ-1", json_handler(FAKE_ATIVIDADE_RESPONSE))
    await page.route("**/api/alunos/aluno-1", json_handler(FAKE_ALUNO_RESPONSE))
    await prepare_page(page)

    await page.evaluate("() => { void showResultadoAluno('ativ-1', 'aluno-1', 'Maria Silva', 'Prova 1'); }")

    await expect(page.locator("#content .page-title")).to_have_text("Resultado de Maria Silva", timeout=700)
    await expect(page.locator("#content")).to_contain_text("Buscando correção, documentos e progresso...", timeout=700)
    await expect(page.locator("#content")).to_contain_text("Carregando correção e etapas do pipeline...", timeout=700)


@pytest.mark.asyncio
@pytest.mark.ui
async def test_student_request_guard_prevents_old_detail_response_from_overwriting_new_view(page: Page):
    await page.route("**/api/alunos/aluno-1", json_handler(FAKE_ALUNO_RESPONSE, delay_ms=1800))
    await page.route("**/api/dashboard/aluno/aluno-1", json_handler(FAKE_DASHBOARD_RESPONSE, delay_ms=150))
    await prepare_page(page)

    await page.evaluate("() => { void showAluno('aluno-1', 'Maria Silva', '2024001'); }")
    await page.wait_for_timeout(120)
    await page.evaluate("() => { void showDashboardAluno('aluno-1', 'Maria Silva', '2024001'); }")

    await expect(page.locator("#content .page-title")).to_have_text("Dashboard do Aluno", timeout=1000)
    await page.wait_for_timeout(2200)
    await expect(page.locator("#content .page-title")).to_have_text("Dashboard do Aluno", timeout=700)
    await expect(page.locator("#content")).not_to_contain_text("Turmas do Aluno", timeout=700)
