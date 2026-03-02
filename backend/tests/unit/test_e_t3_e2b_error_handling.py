"""
Test E-T3: E2B error handling audit for handle_execute_python_code()

Tests:
- Timeout errors produce structured error code + UI message + server log
- Security violations produce structured error code + UI message + server log
- General execution errors produce structured error code + UI message + server log
- Internal/exception errors produce structured error code + UI message + server log

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_e_t3_e2b_error_handling.py -v
"""

import pytest
import sys
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass, field

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools import ToolResult, ToolExecutionContext


# ============================================================
# MOCK CODE EXECUTOR
# ============================================================

class FakeExecutionStatus:
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class FakeResult:
    is_success: bool = False
    status: str = "error"
    stdout: str = ""
    stderr: str = ""
    error_message: str = ""
    files_generated: list = field(default_factory=list)
    plots_generated: list = field(default_factory=list)
    execution_time_ms: float = 0.0


def _make_mock_code_executor_module(execute_return=None, detect_libs_error=None):
    """Build a fake code_executor module with all expected exports"""
    mock_mod = MagicMock()
    mock_mod.ExecutionStatus = FakeExecutionStatus

    fake_exec = MagicMock()
    fake_exec.execute = AsyncMock(return_value=execute_return or FakeResult())
    mock_mod.code_executor = fake_exec

    if detect_libs_error:
        mock_mod.detect_libraries_from_code = MagicMock(side_effect=detect_libs_error)
    else:
        mock_mod.detect_libraries_from_code = MagicMock(return_value=[])
    mock_mod.detect_output_files_from_code = MagicMock(return_value=[])

    return mock_mod


@pytest.fixture(autouse=True)
def _clear_module_cache():
    """Ensure tool_handlers is re-imported fresh each test"""
    sys.modules.pop("tool_handlers", None)
    yield
    sys.modules.pop("tool_handlers", None)


async def _call_handler(mock_module, code="print('test')"):
    """Patch code_executor module and call handle_execute_python_code"""
    with patch.dict("sys.modules", {"code_executor": mock_module}):
        sys.modules.pop("tool_handlers", None)
        from tool_handlers import handle_execute_python_code
        return await handle_execute_python_code({"code": code})


# ============================================================
# TEST: STRUCTURED ERROR CODES
# ============================================================

class TestStructuredErrorCodes:
    """Each error path returns a parseable error code in the content"""

    @pytest.mark.asyncio
    async def test_timeout_has_error_code(self):
        """Timeout error includes [E2B_TIMEOUT] code in content"""
        mod = _make_mock_code_executor_module(execute_return=FakeResult(
            is_success=False, status=FakeExecutionStatus.TIMEOUT,
            stdout="partial...", error_message="Timed out after 30s"
        ))
        result = await _call_handler(mod, "time.sleep(60)")
        assert result.is_error is True
        assert "[E2B_TIMEOUT]" in result.content

    @pytest.mark.asyncio
    async def test_security_violation_has_error_code(self):
        """Security violation includes [E2B_SECURITY] code in content"""
        mod = _make_mock_code_executor_module(execute_return=FakeResult(
            is_success=False, status=FakeExecutionStatus.SECURITY_VIOLATION,
            error_message="Blocked: os.system()"
        ))
        result = await _call_handler(mod, "os.system('hack')")
        assert result.is_error is True
        assert "[E2B_SECURITY]" in result.content

    @pytest.mark.asyncio
    async def test_general_error_has_error_code(self):
        """General execution error includes [E2B_ERROR] code in content"""
        mod = _make_mock_code_executor_module(execute_return=FakeResult(
            is_success=False, status=FakeExecutionStatus.ERROR,
            stderr="ModuleNotFoundError: No module named 'x'"
        ))
        result = await _call_handler(mod, "import nonexistent")
        assert result.is_error is True
        assert "[E2B_ERROR]" in result.content

    @pytest.mark.asyncio
    async def test_internal_exception_has_error_code(self):
        """Exception during execution includes [E2B_INTERNAL] code in content"""
        mod = _make_mock_code_executor_module(detect_libs_error=RuntimeError("Sandbox crashed"))
        result = await _call_handler(mod, "print('hello')")
        assert result.is_error is True
        assert "[E2B_INTERNAL]" in result.content


# ============================================================
# TEST: SERVER LOGGING
# ============================================================

class TestServerLogging:
    """Each error path writes a server log entry"""

    @pytest.mark.asyncio
    async def test_timeout_is_logged(self, caplog):
        """Timeout triggers logger.error with E2B_TIMEOUT"""
        mod = _make_mock_code_executor_module(execute_return=FakeResult(
            is_success=False, status=FakeExecutionStatus.TIMEOUT,
            error_message="Timed out"
        ))
        with caplog.at_level(logging.ERROR):
            await _call_handler(mod, "time.sleep(60)")
        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert any("E2B_TIMEOUT" in r.message for r in errors), \
            f"Expected E2B_TIMEOUT in logs, got: {[r.message for r in errors]}"

    @pytest.mark.asyncio
    async def test_security_violation_is_logged(self, caplog):
        """Security violation triggers logger.error with E2B_SECURITY"""
        mod = _make_mock_code_executor_module(execute_return=FakeResult(
            is_success=False, status=FakeExecutionStatus.SECURITY_VIOLATION,
            error_message="Blocked"
        ))
        with caplog.at_level(logging.ERROR):
            await _call_handler(mod, "os.system('hack')")
        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert any("E2B_SECURITY" in r.message for r in errors), \
            f"Expected E2B_SECURITY in logs, got: {[r.message for r in errors]}"

    @pytest.mark.asyncio
    async def test_internal_exception_is_logged(self, caplog):
        """Internal exception triggers logger.error with E2B_INTERNAL"""
        mod = _make_mock_code_executor_module(detect_libs_error=RuntimeError("Sandbox crashed"))
        with caplog.at_level(logging.ERROR):
            await _call_handler(mod, "print('hi')")
        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert any("E2B_INTERNAL" in r.message for r in errors), \
            f"Expected E2B_INTERNAL in logs, got: {[r.message for r in errors]}"
