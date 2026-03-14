"""Unit tests for the student loading shells in the frontend."""

from pathlib import Path


FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


def _read_html() -> str:
    assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
    return FRONTEND_HTML.read_text(encoding="utf-8")


def _extract_function_body(html: str, marker: str) -> str:
    start = html.find(marker)
    if start == -1:
        return ""
    brace_start = html.find("{", start)
    if brace_start == -1:
        return ""

    depth = 0
    for idx in range(brace_start, len(html)):
        if html[idx] == "{":
            depth += 1
        elif html[idx] == "}":
            depth -= 1
            if depth == 0:
                return html[brace_start + 1 : idx]
    return ""


def _body_before_first_await(body: str) -> str:
    await_index = body.find("await ")
    if await_index == -1:
        return body
    return body[:await_index]


def test_reassuring_loading_shell_has_progressive_messages_and_retry():
    html = _read_html()
    body = _extract_function_body(html, "function renderReassuringLoadingShell(")

    assert body
    assert "A página está funcionando. Isso pode levar alguns segundos." in body
    assert "Os dados estão demorando mais que o normal, mas o carregamento continua." in body
    assert "Tentar novamente" in html
    assert "CONTENT_REASSURANCE_DELAY_MS" in html
    assert "CONTENT_RETRY_SUGGESTION_DELAY_MS" in html


def test_show_aluno_renders_loading_shell_before_first_await():
    html = _read_html()
    body = _extract_function_body(html, "async function showAluno(")
    sync_prefix = _body_before_first_await(body)

    assert "renderReassuringLoadingShell({" in sync_prefix
    assert "Buscando turmas e dados do aluno..." in sync_prefix
    assert "renderStudentErrorShell(" in body


def test_show_resultado_aluno_renders_loading_shell_before_first_await():
    html = _read_html()
    body = _extract_function_body(html, "async function showResultadoAluno(")
    sync_prefix = _body_before_first_await(body)

    assert "renderReassuringLoadingShell({" in sync_prefix
    assert "Buscando correção, documentos e progresso..." in sync_prefix
    assert "hydrateResultadoAlunoBreadcrumb(" in body
    assert "renderStudentErrorShell(" in body


def test_show_dashboard_aluno_renders_loading_shell_before_first_await():
    html = _read_html()
    body = _extract_function_body(html, "async function showDashboardAluno(")
    sync_prefix = _body_before_first_await(body)

    assert "renderReassuringLoadingShell({" in sync_prefix
    assert "Calculando histórico e estatísticas..." in sync_prefix
    assert "renderPlaceholderStats" in body
    assert "renderStudentErrorShell(" in body
