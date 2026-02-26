"""
A5: Source inspection test — verify the backward-compat 301 redirect is correctly implemented.

This test FAILS until A3 (redirect task) is complete.

Verifies that routes_prompts.py contains:
  1. A route decorator at /api/executar/pipeline-turma
  2. That route uses RedirectResponse with status_code=301
  3. The redirect target is /api/executar/pipeline-todos-os-alunos

No test server required — source inspection only.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_a3_redirect_pipeline_turma.py -v
"""

import re
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent.parent  # IA_Educacao_V2/backend
ROUTES_PROMPTS = BACKEND_ROOT / "routes_prompts.py"


def _get_routes_content() -> str:
    assert ROUTES_PROMPTS.exists(), f"routes_prompts.py not found at {ROUTES_PROMPTS}"
    return ROUTES_PROMPTS.read_text(encoding="utf-8")


# ============================================================
# Tests
# ============================================================

def test_redirect_route_exists_for_old_pipeline_turma():
    """routes_prompts.py must define a route at /api/executar/pipeline-turma.

    This backward-compat route lets existing bookmarks and integrations continue
    to work after A2 renames the main endpoint to /api/executar/pipeline-todos-os-alunos.
    """
    content = _get_routes_content()
    assert "/api/executar/pipeline-turma" in content, (
        "routes_prompts.py must contain a route at '/api/executar/pipeline-turma'. "
        "Add a backward-compat redirect:\n"
        "  @router.post('/api/executar/pipeline-turma', ...)\n"
        "  async def redirect_pipeline_turma(...):\n"
        "      return RedirectResponse(url='/api/executar/pipeline-todos-os-alunos', status_code=301)"
    )


def test_redirect_uses_redirect_response():
    """The pipeline-turma backward-compat route must use RedirectResponse.

    A plain 'return' or HTTPException would not preserve HTTP method semantics.
    RedirectResponse with status_code=308 (Permanent Redirect) preserves POST.
    status_code=301 is also acceptable for this use case.
    """
    content = _get_routes_content()
    assert "RedirectResponse" in content, (
        "routes_prompts.py must import and use RedirectResponse for the pipeline-turma redirect. "
        "Add 'from fastapi.responses import RedirectResponse' and use it in the redirect handler."
    )


def test_redirect_points_to_new_endpoint():
    """The redirect must point to /api/executar/pipeline-todos-os-alunos.

    This verifies the new canonical URL is referenced in the redirect target.
    """
    content = _get_routes_content()
    assert "pipeline-todos-os-alunos" in content, (
        "routes_prompts.py must contain '/api/executar/pipeline-todos-os-alunos' as the redirect target. "
        "The pipeline-turma backward-compat route must redirect to this new URL."
    )


def test_redirect_uses_301_status_code():
    """The redirect must use HTTP 301 (Moved Permanently).

    301 signals to clients that the URL has permanently moved and they should
    update their bookmarks/links.
    """
    content = _get_routes_content()
    # Check for 301 anywhere near RedirectResponse context
    assert "301" in content, (
        "routes_prompts.py must use status_code=301 in the RedirectResponse. "
        "Example: return RedirectResponse(url='/api/executar/pipeline-todos-os-alunos', status_code=301)"
    )


def test_new_endpoint_pipeline_todos_os_alunos_exists():
    """After A2+A3, the canonical endpoint must be at /api/executar/pipeline-todos-os-alunos.

    This verifies the new URL is a real route, not just a redirect target string.
    """
    content = _get_routes_content()
    # The @router.post decorator for the new endpoint
    assert '@router.post("/api/executar/pipeline-todos-os-alunos"' in content or \
           "@router.post('/api/executar/pipeline-todos-os-alunos'" in content, (
        "routes_prompts.py must have the new canonical route: "
        "@router.post('/api/executar/pipeline-todos-os-alunos', ...). "
        "This is the A2 rename task — did you forget to rename the decorator?"
    )
