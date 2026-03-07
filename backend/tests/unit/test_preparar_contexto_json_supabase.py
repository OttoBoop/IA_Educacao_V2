"""
Test that _preparar_contexto_json uses storage.resolver_caminho_documento()
instead of direct Path access, so JSON context loads correctly on Render
where files are stored in Supabase (not local filesystem).

Bug: executor.py:978-1002 uses Path(doc.caminho_arquivo) directly,
which fails on Render because files are in Supabase. Should use
storage.resolver_caminho_documento(doc) like _preparar_variaveis_texto does.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from prompts import EtapaProcessamento
from models import TipoDocumento


class TestPrepararContextoJsonUsesResolver(unittest.TestCase):
    """_preparar_contexto_json must use storage.resolver_caminho_documento()."""

    def _make_doc(self, tipo, extensao=".json", caminho="nonexistent/path.json", aluno_id=None):
        """Create a mock document object."""
        doc = MagicMock()
        doc.tipo = tipo
        doc.extensao = extensao
        doc.caminho_arquivo = caminho
        doc.aluno_id = aluno_id
        doc.id = "test_doc_id"
        doc.nome_arquivo = "test.json"
        return doc

    def _make_executor(self, storage_mock):
        """Create a PipelineExecutor with mocked storage."""
        from executor import PipelineExecutor
        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = storage_mock
        # Mock prompt_manager (not needed for this test)
        executor.prompt_manager = MagicMock()
        return executor

    def test_carregar_json_calls_resolver_caminho_documento(self):
        """
        When loading JSON docs, _preparar_contexto_json must call
        storage.resolver_caminho_documento(doc) — NOT use Path(doc.caminho_arquivo).

        This is critical for Render where files are in Supabase.
        """
        # Create a real temp JSON file to be "resolved" by the mock
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"questoes": [{"numero": 1, "texto": "Q1"}]}, f, ensure_ascii=False)
            resolved_path = Path(f.name)

        try:
            # Create mock document with a path that does NOT exist locally
            # (simulating Render where files are in Supabase)
            doc_questoes = self._make_doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                caminho="supabase://bucket/nonexistent.json",
            )

            storage_mock = MagicMock()
            storage_mock.listar_documentos = MagicMock(return_value=[doc_questoes])
            # resolver_caminho_documento should be called and return the real temp path
            storage_mock.resolver_caminho_documento = MagicMock(return_value=resolved_path)
            storage_mock.base_path = Path("/nonexistent/base")

            executor = self._make_executor(storage_mock)

            result = executor._preparar_contexto_json(
                atividade_id="test_ativ",
                aluno_id=None,
                etapa=EtapaProcessamento.CORRIGIR,
            )

            # The resolver MUST have been called for the questoes doc
            storage_mock.resolver_caminho_documento.assert_called()
            called_docs = [
                call.args[0] for call in storage_mock.resolver_caminho_documento.call_args_list
            ]
            self.assertIn(
                doc_questoes,
                called_docs,
                "resolver_caminho_documento must be called with the questoes doc. "
                "Currently _preparar_contexto_json uses Path(doc.caminho_arquivo) directly, "
                "which fails on Render where files are in Supabase.",
            )

            # And the JSON data must have been loaded
            self.assertIn(
                "questoes_extraidas",
                result,
                "questoes_extraidas should be in the context after resolver resolved the path.",
            )
        finally:
            resolved_path.unlink(missing_ok=True)

    def test_nonexistent_local_path_still_loads_via_resolver(self):
        """
        Even when doc.caminho_arquivo points to a nonexistent local path,
        the JSON should load because resolver_caminho_documento downloads
        from Supabase to a temp location.
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"respostas": [{"questao": 1, "resposta": "x=5"}]}, f, ensure_ascii=False)
            resolved_path = Path(f.name)

        try:
            doc_respostas = self._make_doc(
                TipoDocumento.EXTRACAO_RESPOSTAS,
                caminho="/does/not/exist/on/render.json",
                aluno_id="aluno_test",
            )

            # Also need questoes doc for CORRIGIR context
            doc_questoes = self._make_doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                caminho="/also/nonexistent.json",
            )

            storage_mock = MagicMock()
            storage_mock.listar_documentos = MagicMock(
                side_effect=lambda ativ_id, aluno_id=None: (
                    [doc_respostas] if aluno_id else [doc_questoes]
                )
            )
            storage_mock.resolver_caminho_documento = MagicMock(return_value=resolved_path)
            storage_mock.base_path = Path("/nonexistent/base")

            executor = self._make_executor(storage_mock)

            result = executor._preparar_contexto_json(
                atividade_id="test_ativ",
                aluno_id="aluno_test",
                etapa=EtapaProcessamento.CORRIGIR,
            )

            # resolver_caminho_documento must have been called
            self.assertTrue(
                storage_mock.resolver_caminho_documento.called,
                "resolver_caminho_documento was never called. "
                "_preparar_contexto_json must use it instead of Path(doc.caminho_arquivo).",
            )
        finally:
            resolved_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
