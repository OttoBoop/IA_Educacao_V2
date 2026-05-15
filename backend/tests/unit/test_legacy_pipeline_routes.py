"""
Regression tests for legacy synchronous pipeline routes.

These endpoints can run provider calls inside the request lifecycle. In production
that caused client timeouts, a temporarily unresponsive Render worker, and duplicate
documents after a retry. They must fail high and point callers to the task_id-based
pipeline flow.
"""

import pytest
from fastapi import HTTPException

from routes_pipeline import (
    ExecutarComToolsRequest,
    ExecutarEtapaRequest,
    executar_com_tools,
    executar_etapa,
)


@pytest.mark.asyncio
async def test_legacy_pipeline_executar_is_gone():
    with pytest.raises(HTTPException) as exc_info:
        await executar_etapa(
            ExecutarEtapaRequest(
                atividade_id="atividade-1",
                provider_id="gem3flash001",
                etapa="extrair_questoes",
            )
        )

    assert exc_info.value.status_code == 410
    assert "pipeline-completo" in str(exc_info.value.detail)
    assert "task-progress" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_legacy_pipeline_executar_com_tools_is_gone():
    with pytest.raises(HTTPException) as exc_info:
        await executar_com_tools(
            ExecutarComToolsRequest(
                mensagem="crie um documento",
                atividade_id="atividade-1",
                provider_id="gem3flash001",
                tools=["create_document"],
            )
        )

    assert exc_info.value.status_code == 410
    assert "tool-use sincrono" in str(exc_info.value.detail)
    assert "task_id" in str(exc_info.value.detail)
