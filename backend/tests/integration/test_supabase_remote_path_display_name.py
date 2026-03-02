"""
Integration tests for F3-T5: Supabase Storage remote_path uses the
display_name-based filename rather than a raw tempfile path.

When SUPABASE_STORAGE_AVAILABLE is True, storage.salvar_documento() calls
supabase_storage.upload(local_path, remote_path).  The remote_path is
derived from caminho_relativo, which in turn is built from nome_arquivo.

After F3-T1:
  nome_arquivo = build_storage_filename(display_name, ext)
                 e.g. "Prova Respondida - Maria - Calculo I_a3f1.pdf"

So the remote_path MUST contain the display_name-based filename and MUST NOT
contain raw tempfile patterns (e.g. "tmp", "var/folders", "AppData/Local/Temp").

Both tests use monkeypatch to inject a mock supabase_storage and to set
SUPABASE_STORAGE_AVAILABLE=True inside storage.py while keeping
SUPABASE_DB_AVAILABLE=False so StorageManager uses SQLite for the hierarchy.

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F3-T5)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import re
import pytest
from pathlib import Path
from unittest.mock import MagicMock


# ============================================================
# Helper
# ============================================================

def _make_mock_supabase_storage():
    """Return a mock supabase_storage that records upload() calls."""
    mock = MagicMock()
    mock.enabled = True
    mock.upload.return_value = (True, "Upload OK")
    return mock


# ============================================================
# F3-T5 Tests
# ============================================================

class TestSupabaseRemotePathDisplayName:
    """
    When Supabase Storage is available, the remote_path passed to
    supabase_storage.upload() must be derived from the display_name-based
    filename — not from a raw tempfile path.
    """

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, temp_data_dir):
        """Set up isolated SQLite-backed StorageManager with the full hierarchy.

        SUPABASE_DB_AVAILABLE=False so StorageManager uses SQLite.
        SUPABASE_STORAGE_AVAILABLE will be set per-test using monkeypatch.
        """
        monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
        # Keep SUPABASE_STORAGE_AVAILABLE False here; individual tests set it True
        monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

        from storage import StorageManager
        self.storage = StorageManager(base_path=str(temp_data_dir))

        self.materia = self.storage.criar_materia(nome="Calculo I")
        self.turma = self.storage.criar_turma(
            materia_id=self.materia.id, nome="Turma A"
        )
        self.atividade = self.storage.criar_atividade(
            turma_id=self.turma.id, nome="Prova 1"
        )
        self.aluno = self.storage.criar_aluno(nome="Maria Silva", matricula="2024001")
        self.storage.vincular_aluno_turma(
            aluno_id=self.aluno.id, turma_id=self.turma.id
        )

        self.mock_supa = _make_mock_supabase_storage()

    def test_supabase_remote_path_contains_meaningful_filename(self, monkeypatch, tmp_path):
        """
        When supabase_storage is available, supabase_storage.upload() must be
        called with a remote_path whose final path component contains the
        display_name-based filename.

        The display_name for a prova_respondida by "Maria Silva" in "Calculo I",
        "Turma A" is built by build_display_name() as:
            "Prova Respondida - Maria Silva - Calculo I - Turma A"

        build_storage_filename() then produces:
            "Prova Respondida - Maria Silva - Calculo I - Turma A_<hash4>.pdf"

        The remote_path passed to supabase_storage.upload() must end with that
        filename (or a sanitized version of it), NOT with a raw tempfile path.
        """
        from models import TipoDocumento

        # Enable Supabase Storage with the mock for this test
        monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", True)
        monkeypatch.setattr("storage.supabase_storage", self.mock_supa)

        # Create a real temporary PDF to upload
        source_pdf = tmp_path / "source.pdf"
        source_pdf.write_bytes(b"%PDF-1.4 test content for supabase path test")

        documento = self.storage.salvar_documento(
            arquivo_origem=str(source_pdf),
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=self.atividade.id,
            aluno_id=self.aluno.id,
            criado_por="usuario",
        )

        assert self.mock_supa.upload.called, (
            "supabase_storage.upload() was not called. "
            "Verify SUPABASE_STORAGE_AVAILABLE patch and supabase_storage import "
            "in storage.py."
        )

        # Extract the remote_path argument (second positional arg to upload())
        call_args = self.mock_supa.upload.call_args
        remote_path = (
            call_args[0][1]
            if call_args[0]
            else call_args.kwargs.get("remote_path", "")
        )

        # The nome_arquivo stored in the documento must match the remote_path tail
        assert documento is not None, "salvar_documento() must return a Documento object."
        nome_arquivo = documento.nome_arquivo

        assert nome_arquivo in remote_path, (
            f"remote_path='{remote_path}' must contain the display_name-based "
            f"filename '{nome_arquivo}'. "
            "storage.salvar_documento() must use caminho_relativo (which includes "
            "nome_arquivo) as the remote_path, not the temp file path."
        )

        # The display_name human-readable label must appear in nome_arquivo.
        # build_display_name() produces "Prova Respondida - ..." for PROVA_RESPONDIDA.
        assert any(
            fragment in nome_arquivo
            for fragment in ["Prova Respondida", "Prova_Respondida", "prova_respondida"]
        ), (
            f"nome_arquivo '{nome_arquivo}' must contain a human-readable label "
            "derived from the display_name (e.g. 'Prova Respondida'). "
            "build_storage_filename() should produce a meaningful filename, not a "
            "random hash."
        )

    def test_supabase_remote_path_no_temp_hash(self, monkeypatch, tmp_path):
        """
        The remote_path passed to supabase_storage.upload() must NOT resemble
        a raw system tempfile path.

        Tempfile patterns that should NOT appear in remote_path:
          - "/tmp/"          (Linux/macOS temp dirs)
          - "\\Temp\\"       (Windows temp dirs)
          - "\\AppData\\"    (Windows AppData)
          - "/var/folders/"  (macOS temp dirs)
          - "tmpXXXXXX"      (Python tempfile.NamedTemporaryFile prefix pattern)

        These patterns indicate that the endpoint is accidentally uploading the
        temporary file path instead of the computed destination path.
        """
        from models import TipoDocumento

        monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", True)
        monkeypatch.setattr("storage.supabase_storage", self.mock_supa)

        source_pdf = tmp_path / "upload_source.pdf"
        source_pdf.write_bytes(b"%PDF-1.4 content for temp hash test")

        self.storage.salvar_documento(
            arquivo_origem=str(source_pdf),
            tipo=TipoDocumento.PROVA_RESPONDIDA,
            atividade_id=self.atividade.id,
            aluno_id=self.aluno.id,
            criado_por="usuario",
        )

        assert self.mock_supa.upload.called, (
            "supabase_storage.upload() was not called."
        )

        call_args = self.mock_supa.upload.call_args
        remote_path = (
            call_args[0][1]
            if call_args[0]
            else call_args.kwargs.get("remote_path", "")
        )

        # Patterns that indicate a raw tempfile path leaked into remote_path
        TEMP_PATTERNS = [
            r"/tmp/",
            r"\\Temp\\",
            r"\\AppData\\",
            r"/var/folders/",
            r"tmp[a-zA-Z0-9_]{6,}",   # Python NamedTemporaryFile prefix pattern
        ]

        for pattern in TEMP_PATTERNS:
            assert not re.search(pattern, remote_path, re.IGNORECASE), (
                f"remote_path='{remote_path}' matches tempfile pattern '{pattern}'. "
                "The Supabase upload remote_path must be built from the computed "
                "destination path (caminho_relativo), not from the source temp file. "
                "Check storage.salvar_documento() lines that construct remote_path."
            )
