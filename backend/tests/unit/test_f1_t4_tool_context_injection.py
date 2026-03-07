import pytest
import base64
from unittest.mock import patch, AsyncMock, MagicMock
from tool_handlers import handle_execute_python_code
from tools import ToolExecutionContext
from models import TipoDocumento

@pytest.mark.asyncio
async def test_handle_execute_python_code_uses_injected_type():
    with patch("tool_handlers.sandbox_manager") as mock_sandbox, \
         patch("tool_handlers.storage") as mock_storage:
        
        # Mocks
        mock_sandbox.execute_python = AsyncMock()
        mock_sandbox.execute_python.return_value = MagicMock(
            is_error=False,
            files_generated=[
                MagicMock(filename="report.pdf", content_base64=base64.b64encode(b"fake_pdf").decode("utf-8"))
            ]
        )
        mock_storage.salvar_documento = MagicMock(return_value=MagicMock(id="doc-123", caminho_storage="path/report.pdf"))
        
        # Context with expected document type
        context = ToolExecutionContext(
            atividade_id="ativ-1",
            aluno_id="aluno-1",
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TAREFA
        )
        
        # Execute
        result = await handle_execute_python_code({"code": "print('ok')"}, context)
        
        # Verify
        assert not result.is_error
        mock_storage.salvar_documento.assert_called_once()
        call_args = mock_storage.salvar_documento.call_args[1]
        assert call_args["tipo"] == TipoDocumento.RELATORIO_DESEMPENHO_TAREFA
        
@pytest.mark.asyncio
async def test_handle_execute_python_code_fallback_to_mapping():
    with patch("tool_handlers.sandbox_manager") as mock_sandbox, \
         patch("tool_handlers.storage") as mock_storage:
        
        # Mocks
        mock_sandbox.execute_python = AsyncMock()
        mock_sandbox.execute_python.return_value = MagicMock(
            is_error=False,
            files_generated=[
                MagicMock(filename="report.pdf", content_base64=base64.b64encode(b"fake_pdf").decode("utf-8"))
            ]
        )
        mock_storage.salvar_documento = MagicMock(return_value=MagicMock(id="doc-123", caminho_storage="path/report.pdf"))
        
        # Context WITHOUT expected document type
        context = ToolExecutionContext(
            atividade_id="ativ-1",
            aluno_id="aluno-1"
        )
        
        # Execute
        result = await handle_execute_python_code({"code": "print('ok')"}, context)
        
        # Verify
        assert not result.is_error
        mock_storage.salvar_documento.assert_called_once()
        call_args = mock_storage.salvar_documento.call_args[1]
        assert call_args["tipo"] == TipoDocumento.RELATORIO_FINAL
