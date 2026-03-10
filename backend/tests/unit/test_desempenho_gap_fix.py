"""
Tests for PLAN_Desempenho_Gap_Fix.md — Wave 1

FA-T1 RED: Whitespace resposta_raw — LLM returns " " but real content is in create_document
           tool call. The fallback logic in executar_com_tools doesn't strip whitespace.

FB-T1 RED: Missing Cache-Control header on serve_frontend() allows browsers to cache
           old index_v2.html from before the Etapas section was added.

FC-T1 RED: _cascade_prereqs() not implemented — must be added to PipelineExecutor
           and create missing upstream docs before desempenho runs.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_desempenho_gap_fix.py -v
"""

import inspect
import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# FA-T1: Turma blank doc — whitespace resposta_raw bug
# ============================================================

def _apply_executar_com_tools_extraction_logic(raw_content: str, tool_calls: list) -> str:
    """
    Replicates the extraction logic from executor.py lines 2283-2297.
    Returns what resposta_raw would be set to given a response from the LLM.
    """
    is_sentinel = raw_content == "[Maximum tool iterations reached]"

    # This is the CURRENT (potentially buggy) logic:
    if not raw_content or is_sentinel:
        for tc in tool_calls:
            if tc.get("name") == "create_document":
                doc_content = tc.get("input", {}).get("content", "")
                if doc_content:
                    raw_content = doc_content
                    break

    if raw_content == "[Maximum tool iterations reached]":
        raw_content = ""

    return raw_content


class TestFA_T1_TurmaBlankDocRootCause:
    """
    FA-T1: Characterise the whitespace bug in executar_com_tools.

    When the LLM uses create_document to produce the report content,
    it often returns " " (single space / whitespace) in the text `content` field.
    The fallback that extracts content from the tool call only runs when
    `not raw_content`, but " " is truthy — so the fallback is skipped and
    resposta_raw ends up as " ".

    Fix required (FA-T2): change `if not raw_content` → `if not raw_content.strip()`
    """

    def test_whitespace_content_is_not_replaced_by_create_document_data(self):
        """
        RED: Demonstrates the bug.
        When LLM response content is whitespace and create_document has real data,
        the extraction logic SHOULD use the tool content — but currently DOESN'T.
        This test asserts the DESIRED behavior; it will FAIL because the bug exists.
        """
        tool_calls = [
            {
                "name": "create_document",
                "input": {
                    "content": (
                        "Resumo do desempenho da turma: Os alunos demonstraram "
                        "excelente participação e evolução ao longo do semestre."
                    ),
                    "documents": [],
                }
            }
        ]

        result = _apply_executar_com_tools_extraction_logic(" ", tool_calls)

        # DESIRED: should extract content from create_document tool
        # ACTUAL (bug): returns " " because `not " "` is False
        assert result.strip(), (
            "FA-T1 BUG CONFIRMED: resposta_raw is whitespace-only when LLM returns ' ' "
            "as content but puts the actual report in create_document tool call.\n"
            "Root cause: executor.py:2286 — `if not raw_content` doesn't strip whitespace.\n"
            "Fix (FA-T2): change to `if not raw_content.strip() or is_sentinel:`"
        )

    def test_empty_content_correctly_falls_back_to_create_document(self):
        """
        Sanity: empty string ("") already works — this is the control case.
        The bug is specific to whitespace-only strings.
        """
        tool_calls = [
            {
                "name": "create_document",
                "input": {"content": "Real content here", "documents": []}
            }
        ]

        result = _apply_executar_com_tools_extraction_logic("", tool_calls)
        assert result == "Real content here", (
            "Empty string should fall back to create_document content — this should pass."
        )

    def test_real_content_is_preserved(self):
        """
        Sanity: when LLM returns actual content, it should be kept as-is.
        """
        result = _apply_executar_com_tools_extraction_logic(
            "Full report text from LLM", []
        )
        assert result == "Full report text from LLM"


# ============================================================
# FB-T1: Etapas UI — missing Cache-Control header
# ============================================================

class TestFB_T1_EtapasUIRootCause:
    """
    FB-T1: Characterise missing Cache-Control header in serve_frontend().

    Without `Cache-Control: no-cache`, browsers cache old index_v2.html from
    before the Etapas section was added. After a Render deploy that adds the
    section, users still see the cached (old) HTML — no etapas section visible.

    Fix required (FB-T2): add headers={"Cache-Control": "no-cache, must-revalidate"}
    to the FileResponse in serve_frontend().
    """

    def test_serve_frontend_has_no_cache_control_header(self):
        """
        RED: serve_frontend() should return Cache-Control: no-cache.
        Currently it doesn't — this test will fail because the header is absent.
        """
        try:
            from fastapi.testclient import TestClient
            from main_v2 import app
        except ImportError as e:
            pytest.skip(f"Cannot import FastAPI app: {e}")

        client = TestClient(app)
        response = client.get("/")

        cache_control = response.headers.get("cache-control", "")
        assert "no-cache" in cache_control.lower(), (
            "FB-T1 BUG CONFIRMED: serve_frontend() missing Cache-Control header.\n"
            f"  Got: cache-control={cache_control!r}\n"
            "Root cause: main_v2.py FileResponse has no cache headers — browsers "
            "serve stale index_v2.html after Render deploys, hiding the Etapas section.\n"
            "Fix (FB-T2): add headers={'Cache-Control': 'no-cache, must-revalidate'} "
            "to FileResponse in serve_frontend()."
        )


# ============================================================
# FC-T1: Cascade backend — _cascade_prereqs not yet implemented
# ============================================================

class TestFC_T1_CascadePrereqs:
    """
    FC-T1: _cascade_prereqs() must exist on PipelineExecutor and handle
    auto-creation of missing upstream docs before desempenho runs.

    Expected signature:
        async _cascade_prereqs(level, entity_id, provider_id=None, force_reexec=False)

    For tarefa level: if student RELATORIO_FINAL docs are missing,
        run executar_pipeline_completo() for each student without a doc.

    For turma level: if tarefa desempenho docs are missing for any atividade,
        run gerar_relatorio_desempenho_tarefa() for each missing atividade.

    For materia level: if turma desempenho docs are missing for any turma,
        run gerar_relatorio_desempenho_turma() for each missing turma.
    """

    def test_cascade_prereqs_method_exists(self):
        """RED: _cascade_prereqs() must exist on PipelineExecutor."""
        from executor import PipelineExecutor
        assert hasattr(PipelineExecutor, "_cascade_prereqs"), (
            "FC-T1: PipelineExecutor is missing _cascade_prereqs() — "
            "F2-T4 was never implemented. This is the root cause of the cascade failure."
        )

    def test_cascade_prereqs_is_async(self):
        """RED: _cascade_prereqs() must be an async method."""
        from executor import PipelineExecutor
        method = getattr(PipelineExecutor, "_cascade_prereqs", None)
        if method is None:
            pytest.skip("_cascade_prereqs not yet defined — covered by test_cascade_prereqs_method_exists")
        assert inspect.iscoroutinefunction(method), (
            "_cascade_prereqs must be async — it calls async executor methods."
        )

    @pytest.mark.asyncio
    async def test_cascade_prereqs_tarefa_calls_pipeline_for_students_without_relatorio(self):
        """
        RED: For tarefa level, when students lack RELATORIO_FINAL,
        _cascade_prereqs must call executar_pipeline_completo() for each.
        """
        from executor import PipelineExecutor

        if not hasattr(PipelineExecutor, "_cascade_prereqs"):
            pytest.skip("_cascade_prereqs not yet defined")

        # Mock storage: 2 alunos, but ZERO RELATORIO_FINAL docs for the atividade
        mock_storage = MagicMock()
        mock_storage.listar_alunos.return_value = [
            MagicMock(id="aluno_1", nome="Alice"),
            MagicMock(id="aluno_2", nome="Bob"),
        ]
        mock_storage.listar_documentos.return_value = []  # no docs
        mock_storage.get_atividade.return_value = MagicMock(id="atv_1", turma_id="turma_1")

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = mock_storage
        executor.executar_pipeline_completo = AsyncMock(
            return_value={"gerar_relatorio": MagicMock(sucesso=True)}
        )

        await executor._cascade_prereqs(
            level="tarefa",
            entity_id="atv_1",
            provider_id="gem3flash001",
        )

        # Must have called pipeline for BOTH students
        assert executor.executar_pipeline_completo.call_count == 2, (
            f"Expected executar_pipeline_completo called 2× (one per student without "
            f"RELATORIO_FINAL), but called {executor.executar_pipeline_completo.call_count}×."
        )

    @pytest.mark.asyncio
    async def test_cascade_prereqs_tarefa_skips_students_with_existing_relatorio(self):
        """
        FC-T1: Students who already have RELATORIO_FINAL must NOT be re-run
        (unless force_reexec=True).
        """
        from executor import PipelineExecutor

        if not hasattr(PipelineExecutor, "_cascade_prereqs"):
            pytest.skip("_cascade_prereqs not yet defined")

        from models import TipoDocumento
        mock_storage = MagicMock()
        mock_storage.listar_alunos.return_value = [
            MagicMock(id="aluno_1", nome="Alice"),
            MagicMock(id="aluno_2", nome="Bob"),
        ]
        # aluno_1 has RELATORIO_FINAL; aluno_2 does not
        doc_with_relatorio = MagicMock()
        doc_with_relatorio.aluno_id = "aluno_1"
        doc_with_relatorio.tipo = TipoDocumento.RELATORIO_FINAL
        mock_storage.listar_documentos.return_value = [doc_with_relatorio]
        mock_storage.get_atividade.return_value = MagicMock(id="atv_1", turma_id="turma_1")

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = mock_storage
        executor.executar_pipeline_completo = AsyncMock(
            return_value={"gerar_relatorio": MagicMock(sucesso=True)}
        )

        await executor._cascade_prereqs(
            level="tarefa",
            entity_id="atv_1",
            provider_id="gem3flash001",
        )

        # Only aluno_2 should be run (aluno_1 already has docs)
        assert executor.executar_pipeline_completo.call_count == 1, (
            f"Expected 1 pipeline call (only for aluno_2 who lacks RELATORIO_FINAL), "
            f"but got {executor.executar_pipeline_completo.call_count}."
        )
        actual_aluno = executor.executar_pipeline_completo.call_args[1].get(
            "aluno_id"
        ) or executor.executar_pipeline_completo.call_args[0][1]
        assert actual_aluno == "aluno_2", (
            f"Expected pipeline run for aluno_2 (missing doc), got: {actual_aluno}"
        )

    @pytest.mark.asyncio
    async def test_cascade_prereqs_force_reexec_reruns_all_students(self):
        """
        FC-T1: With force_reexec=True, all students must be re-run even if docs exist.
        """
        from executor import PipelineExecutor

        if not hasattr(PipelineExecutor, "_cascade_prereqs"):
            pytest.skip("_cascade_prereqs not yet defined")

        from models import TipoDocumento
        mock_storage = MagicMock()
        mock_storage.listar_alunos.return_value = [
            MagicMock(id="aluno_1", nome="Alice"),
            MagicMock(id="aluno_2", nome="Bob"),
        ]
        # Both have RELATORIO_FINAL already
        doc_a = MagicMock()
        doc_a.aluno_id = "aluno_1"
        doc_a.tipo = TipoDocumento.RELATORIO_FINAL
        doc_b = MagicMock()
        doc_b.aluno_id = "aluno_2"
        doc_b.tipo = TipoDocumento.RELATORIO_FINAL
        mock_storage.listar_documentos.return_value = [doc_a, doc_b]
        mock_storage.get_atividade.return_value = MagicMock(id="atv_1", turma_id="turma_1")

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = mock_storage
        executor.executar_pipeline_completo = AsyncMock(
            return_value={"gerar_relatorio": MagicMock(sucesso=True)}
        )

        await executor._cascade_prereqs(
            level="tarefa",
            entity_id="atv_1",
            provider_id="gem3flash001",
            force_reexec=True,
        )

        # force_reexec=True → must run for BOTH students regardless of existing docs
        assert executor.executar_pipeline_completo.call_count == 2, (
            f"With force_reexec=True, expected 2 pipeline calls (one per student), "
            f"but got {executor.executar_pipeline_completo.call_count}."
        )


# ============================================================
# FC-T3: Force re-execute — route param not yet wired
# ============================================================

class TestFC_T3_ForceReexecRouteParam:
    """
    FC-T3: All 3 desempenho routes must accept force_reexec: bool = Form(False).

    Currently the routes only accept atividade_id/turma_id/materia_id + provider_id.
    The force_reexec flag must be added so the UI can trigger a full cascade re-run.

    Fix required (FC-T3):
        - Add force_reexec: bool = Form(False) to all 3 route signatures
        - Pass it through to the background task functions
        - Background functions call _cascade_prereqs() with force_reexec before
          calling gerar_relatorio_desempenho_*()
    """

    def test_tarefa_route_accepts_force_reexec_param(self):
        """RED: executar_pipeline_desempenho_tarefa must accept force_reexec."""
        try:
            from routes_prompts import executar_pipeline_desempenho_tarefa
        except ImportError as e:
            pytest.skip(f"Cannot import routes_prompts: {e}")
        sig = inspect.signature(executar_pipeline_desempenho_tarefa)
        assert "force_reexec" in sig.parameters, (
            "FC-T3 BUG: executar_pipeline_desempenho_tarefa missing force_reexec param.\n"
            "Fix: add force_reexec: bool = Form(False) to route signature."
        )

    def test_turma_route_accepts_force_reexec_param(self):
        """RED: executar_pipeline_desempenho_turma must accept force_reexec."""
        try:
            from routes_prompts import executar_pipeline_desempenho_turma
        except ImportError as e:
            pytest.skip(f"Cannot import routes_prompts: {e}")
        sig = inspect.signature(executar_pipeline_desempenho_turma)
        assert "force_reexec" in sig.parameters, (
            "FC-T3 BUG: executar_pipeline_desempenho_turma missing force_reexec param.\n"
            "Fix: add force_reexec: bool = Form(False) to route signature."
        )

    def test_materia_route_accepts_force_reexec_param(self):
        """RED: executar_pipeline_desempenho_materia must accept force_reexec."""
        try:
            from routes_prompts import executar_pipeline_desempenho_materia
        except ImportError as e:
            pytest.skip(f"Cannot import routes_prompts: {e}")
        sig = inspect.signature(executar_pipeline_desempenho_materia)
        assert "force_reexec" in sig.parameters, (
            "FC-T3 BUG: executar_pipeline_desempenho_materia missing force_reexec param.\n"
            "Fix: add force_reexec: bool = Form(False) to route signature."
        )

    def test_tarefa_background_fn_accepts_force_reexec(self):
        """RED: _executar_desempenho_tarefa_background must accept force_reexec."""
        try:
            from routes_prompts import _executar_desempenho_tarefa_background
        except ImportError as e:
            pytest.skip(f"Cannot import routes_prompts: {e}")
        sig = inspect.signature(_executar_desempenho_tarefa_background)
        assert "force_reexec" in sig.parameters, (
            "FC-T3 BUG: _executar_desempenho_tarefa_background missing force_reexec param.\n"
            "Fix: add force_reexec param and pass to _cascade_prereqs()."
        )

    def test_turma_background_fn_accepts_force_reexec(self):
        """RED: _executar_desempenho_turma_background must accept force_reexec."""
        try:
            from routes_prompts import _executar_desempenho_turma_background
        except ImportError as e:
            pytest.skip(f"Cannot import routes_prompts: {e}")
        sig = inspect.signature(_executar_desempenho_turma_background)
        assert "force_reexec" in sig.parameters, (
            "FC-T3 BUG: _executar_desempenho_turma_background missing force_reexec param.\n"
            "Fix: add force_reexec param and pass to _cascade_prereqs()."
        )

    def test_materia_background_fn_accepts_force_reexec(self):
        """RED: _executar_desempenho_materia_background must accept force_reexec."""
        try:
            from routes_prompts import _executar_desempenho_materia_background
        except ImportError as e:
            pytest.skip(f"Cannot import routes_prompts: {e}")
        sig = inspect.signature(_executar_desempenho_materia_background)
        assert "force_reexec" in sig.parameters, (
            "FC-T3 BUG: _executar_desempenho_materia_background missing force_reexec param.\n"
            "Fix: add force_reexec param and pass to _cascade_prereqs()."
        )
