"""
Code Executor API Routes

Provides endpoints for executing Python code in sandboxed environments.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import base64
import logging

from code_executor import (
    code_executor,
    get_executor,
    ExecutionStatus,
    detect_libraries_from_code,
    detect_output_files_from_code,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class CodeExecutionRequest(BaseModel):
    """Request to execute Python code"""
    code: str = Field(..., description="Python code to execute")
    libraries: Optional[List[str]] = Field(None, description="Additional pip packages to install")
    output_files: Optional[List[str]] = Field(None, description="Expected output filenames to retrieve")
    context_data: Optional[Dict[str, str]] = Field(None, description="Files to upload: {filename: base64_content}")
    auto_detect: bool = Field(True, description="Auto-detect libraries and output files from code")


class FileInfo(BaseModel):
    """Information about a generated file"""
    filename: str
    extension: str
    content_base64: str
    mime_type: str
    size_bytes: int


class CodeExecutionResponse(BaseModel):
    """Response from code execution"""
    status: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: float
    files_generated: List[FileInfo]
    plots_generated: List[str]
    error_message: Optional[str]
    executor_mode: str


class CodeValidationRequest(BaseModel):
    """Request to validate code security"""
    code: str


class CodeValidationResponse(BaseModel):
    """Response from code validation"""
    is_safe: bool
    violations: List[str]


class ExecutorStatusResponse(BaseModel):
    """Status of the code executor"""
    mode: str
    available: bool
    message: str
    config: Dict[str, Any]


# ============================================================
# API ENDPOINTS
# ============================================================

@router.post("/api/code/execute", response_model=CodeExecutionResponse, tags=["Code Executor"])
async def execute_code(request: CodeExecutionRequest):
    """
    Execute Python code in a sandboxed environment.

    The code runs in an isolated Docker container (local mode) or
    E2B cloud sandbox (production mode).

    Supported libraries: pandas, numpy, matplotlib, openpyxl, python-docx,
    reportlab, python-pptx, pillow, seaborn, xlsxwriter

    Example:
    ```python
    import pandas as pd
    df = pd.DataFrame({'name': ['Alice', 'Bob'], 'score': [95, 87]})
    df.to_excel('scores.xlsx', index=False)
    print('FILE_GENERATED:/sandbox/scores.xlsx')
    ```
    """
    try:
        # Auto-detect libraries and output files if enabled
        libraries = request.libraries or []
        output_files = request.output_files or []

        if request.auto_detect:
            detected_libs = detect_libraries_from_code(request.code)
            detected_files = detect_output_files_from_code(request.code)

            libraries = list(set(libraries + detected_libs))
            output_files = list(set(output_files + detected_files))

            logger.info(f"Auto-detected libraries: {detected_libs}")
            logger.info(f"Auto-detected output files: {detected_files}")

        # Convert context data from base64
        context_files = None
        if request.context_data:
            context_files = {
                name: base64.b64decode(content)
                for name, content in request.context_data.items()
            }

        # Execute the code
        result = await code_executor.execute(
            code=request.code,
            libraries=libraries,
            output_files=output_files,
            context_files=context_files
        )

        return CodeExecutionResponse(
            status=result.status.value,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            execution_time_ms=result.execution_time_ms,
            files_generated=[
                FileInfo(
                    filename=f.filename,
                    extension=f.extension,
                    content_base64=f.content_base64,
                    mime_type=f.mime_type,
                    size_bytes=f.size_bytes
                )
                for f in result.files_generated
            ],
            plots_generated=result.plots_generated,
            error_message=result.error_message,
            executor_mode=result.executor_mode
        )

    except Exception as e:
        logger.exception("Error in code execution endpoint")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/code/validate", response_model=CodeValidationResponse, tags=["Code Executor"])
async def validate_code(request: CodeValidationRequest):
    """
    Validate Python code for security issues without executing it.

    Returns a list of security violations if any are found.
    """
    from code_executor import SecurityValidator

    validator = SecurityValidator()
    is_safe, violations = validator.validate(request.code)

    return CodeValidationResponse(
        is_safe=is_safe,
        violations=violations
    )


@router.get("/api/code/status", response_model=ExecutorStatusResponse, tags=["Code Executor"])
async def get_executor_status():
    """
    Check if the code executor is available and get its configuration.

    Returns the current execution mode (local/e2b) and availability status.
    """
    import os
    from code_executor import CodeExecutorConfig

    mode = os.getenv("EXECUTOR_MODE", "e2b")
    config = CodeExecutorConfig()

    available, message = await code_executor.check_availability()

    return ExecutorStatusResponse(
        mode=mode,
        available=available,
        message=message,
        config={
            "timeout_seconds": config.timeout_seconds,
            "max_memory_mb": config.max_memory_mb,
            "docker_image": config.docker_image,
            "allowed_libraries": config.allowed_libraries,
        }
    )


@router.get("/api/code/libraries", tags=["Code Executor"])
async def get_allowed_libraries():
    """
    Get the list of allowed libraries for code execution.
    """
    from code_executor import CodeExecutorConfig

    config = CodeExecutorConfig()

    return {
        "allowed_libraries": config.allowed_libraries,
        "description": "These are the only libraries that can be installed during code execution."
    }


@router.post("/api/code/detect", tags=["Code Executor"])
async def detect_code_requirements(request: CodeValidationRequest):
    """
    Analyze Python code and detect required libraries and expected output files.

    Useful for understanding what a piece of code needs before execution.
    """
    libraries = detect_libraries_from_code(request.code)
    output_files = detect_output_files_from_code(request.code)

    return {
        "detected_libraries": libraries,
        "detected_output_files": output_files
    }


# ============================================================
# FILE DOWNLOAD ENDPOINT (ALTERNATIVE TO BASE64)
# ============================================================

# Note: The primary method returns files as base64 in the response.
# This endpoint is an alternative for downloading files by ID if you
# implement server-side file storage.

# @router.get("/api/code/files/{execution_id}/{filename}", tags=["Code Executor"])
# async def download_file(execution_id: str, filename: str):
#     """Download a generated file by execution ID and filename."""
#     from pathlib import Path
#     from fastapi.responses import FileResponse
#
#     file_path = Path(f"./data/code_outputs/{execution_id}/{filename}")
#
#     if not file_path.exists():
#         raise HTTPException(status_code=404, detail="File not found")
#
#     return FileResponse(
#         path=file_path,
#         filename=filename,
#         media_type="application/octet-stream"
#     )


# ============================================================
# SYNC ENDPOINTS
# ============================================================

class SyncRequest(BaseModel):
    """Request to sync files from local storage to E2B"""
    documento_ids: List[str] = Field(..., description="List of documento IDs to sync")
    target_path: Optional[str] = Field("/home/user", description="Target path in E2B sandbox")


@router.post("/api/code/sync-to-e2b", tags=["Code Executor"])
async def sync_files_to_e2b(request: SyncRequest):
    """
    Sync files from local storage to E2B sandbox.
    Useful for preparing context files before code execution.
    """
    from storage import storage
    from e2b_code_interpreter import Sandbox
    import os

    if not os.getenv("E2B_API_KEY"):
        raise HTTPException(400, "E2B not configured (missing E2B_API_KEY)")

    synced_files = []
    errors = []

    try:
        with Sandbox.create() as sandbox:
            for doc_id in request.documento_ids:
                try:
                    # Get document from storage
                    documento = storage.get_documento(doc_id)
                    if not documento:
                        errors.append(f"Documento {doc_id} not found")
                        continue

                    # Read file content
                    file_path = documento.caminho_arquivo
                    if not Path(file_path).exists():
                        errors.append(f"File {file_path} not found for documento {doc_id}")
                        continue

                    with open(file_path, 'rb') as f:
                        content = f.read()

                    # Upload to E2B
                    target_path = f"{request.target_path}/{documento.nome_arquivo}"
                    sandbox.files.write(target_path, content)

                    synced_files.append({
                        "documento_id": doc_id,
                        "filename": documento.nome_arquivo,
                        "target_path": target_path,
                        "size_bytes": len(content)
                    })

                except Exception as e:
                    errors.append(f"Error syncing {doc_id}: {str(e)}")

    except Exception as e:
        raise HTTPException(500, f"E2B sync failed: {str(e)}")

    return {
        "success": True,
        "synced_files": synced_files,
        "errors": errors,
        "total_synced": len(synced_files),
        "total_errors": len(errors)
    }


@router.post("/api/code/sync-from-e2b", tags=["Code Executor"])
async def sync_files_from_e2b(files: List[str], target_dir: str = "./data/e2b_downloads"):
    """
    Sync files from E2B sandbox to local storage.
    Useful for retrieving generated files after code execution.
    """
    from e2b_code_interpreter import Sandbox
    import os
    from pathlib import Path

    if not os.getenv("E2B_API_KEY"):
        raise HTTPException(400, "E2B not configured (missing E2B_API_KEY)")

    # Create target directory
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    downloaded_files = []
    errors = []

    try:
        with Sandbox.create() as sandbox:
            for filename in files:
                try:
                    # Download from E2B
                    content = sandbox.files.read(f"/home/user/{filename}", format="bytes")

                    # Save locally
                    local_path = target_path / filename
                    with open(local_path, 'wb') as f:
                        f.write(content)

                    downloaded_files.append({
                        "filename": filename,
                        "local_path": str(local_path),
                        "size_bytes": len(content)
                    })

                except Exception as e:
                    errors.append(f"Error downloading {filename}: {str(e)}")

    except Exception as e:
        raise HTTPException(500, f"E2B download failed: {str(e)}")

    return {
        "success": True,
        "downloaded_files": downloaded_files,
        "errors": errors,
        "total_downloaded": len(downloaded_files),
        "total_errors": len(errors)
    }
