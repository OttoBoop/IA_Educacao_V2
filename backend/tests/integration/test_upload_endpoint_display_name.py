"""
Integration tests for F3-T2: /api/documentos/upload accepting display_name.

Tests the WIRING between the upload endpoint (main_v2.py) and
storage.salvar_documento(display_name=...) introduced in F3-T1.

RED phase: test_upload_with_explicit_display_name MUST FAIL because
the endpoint signature does not yet accept display_name as a Form field,
so the value is silently dropped and salvar_documento() auto-generates instead.

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F3-T2)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


# ============================================================
# F3-T2 Tests
# ============================================================

class TestUploadEndpointDisplayName:
    """
    /api/documentos/upload endpoint must forward display_name to
    storage.salvar_documento() when the caller provides it.
    """

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, temp_data_dir):
        """Set up isolated SQLite-backed storage and TestClient for each test.

        Patches storage.SUPABASE_DB_AVAILABLE and storage.SUPABASE_STORAGE_AVAILABLE
        to False BEFORE constructing StorageManager so the instance uses SQLite
        (the local temp database) rather than the live Supabase instance.
        """
        # Patch both Supabase flags to False so StorageManager uses SQLite
        monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
        monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

        from storage import StorageManager
        self.storage = StorageManager(base_path=str(temp_data_dir))

        # Build the full educational hierarchy
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

        # Patch the storage singleton used by the endpoints
        monkeypatch.setattr("main_v2.storage", self.storage)
        monkeypatch.setattr("routes_extras.storage", self.storage)

        from main_v2 import app
        self.client = TestClient(app)

    def test_upload_with_explicit_display_name(self):
        """
        POST /api/documentos/upload with display_name='Minha Prova Custom'
        must return a documento whose display_name equals the provided value.

        RED: FAILS because the endpoint signature does not include display_name
        as a Form field — FastAPI ignores the field and salvar_documento()
        auto-generates a display_name instead of using the caller-supplied one.
        Implement display_name=Form(None) in upload_documento() in main_v2.py (F3-T2).
        """
        response = self.client.post(
            "/api/documentos/upload",
            data={
                "tipo": "prova_respondida",
                "atividade_id": self.atividade.id,
                "aluno_id": self.aluno.id,
                "display_name": "Minha Prova Custom",
            },
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        doc = data["documento"]

        assert doc["display_name"] == "Minha Prova Custom", (
            f"Expected display_name='Minha Prova Custom', got '{doc['display_name']}'. "
            "The endpoint must accept display_name as a Form field and pass it to "
            "storage.salvar_documento(display_name=...). "
            "Implement this in the upload_documento() function in main_v2.py (F3-T2)."
        )

    def test_upload_without_display_name_backward_compat(self):
        """
        POST /api/documentos/upload without display_name must still succeed
        and return a non-empty auto-generated display_name.

        This should PASS already because salvar_documento() auto-generates
        display_name when none is provided (F3-T1 already implemented).
        """
        response = self.client.post(
            "/api/documentos/upload",
            data={
                "tipo": "prova_respondida",
                "atividade_id": self.atividade.id,
                "aluno_id": self.aluno.id,
            },
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()
        doc = data["documento"]

        assert doc.get("display_name"), (
            "display_name should be auto-generated (non-empty) when not provided. "
            "Verify salvar_documento() auto-generation from F3-T1 is intact."
        )

    def test_upload_display_name_key_exists_in_response_dict(self):
        """
        The response dict for /api/documentos/upload must always include
        the 'display_name' key inside the 'documento' object.

        Validates that Documento.to_dict() exposes the field regardless of
        whether it was caller-supplied or auto-generated.
        """
        response = self.client.post(
            "/api/documentos/upload",
            data={
                "tipo": "prova_respondida",
                "atividade_id": self.atividade.id,
                "aluno_id": self.aluno.id,
            },
            files={"file": ("test.pdf", b"%PDF-1.4 test content", "application/pdf")},
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()

        assert "documento" in data, "Response must have 'documento' key"
        assert "display_name" in data["documento"], (
            "Documento.to_dict() must include 'display_name' key. "
            "Check models.py Documento.to_dict() implementation."
        )
