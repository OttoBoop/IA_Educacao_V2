"""
Integration tests for F3-T3: /api/documentos/upload-lote accepting display_names.

Tests the WIRING between the batch-upload endpoint (routes_extras.py) and
storage.salvar_documento(display_name=...) introduced in F3-T1.

The endpoint currently has no display_names parameter, so:
  - test_lote_with_display_names_array     -> RED (MUST FAIL)
  - test_lote_without_display_names_compat -> GREEN (should already pass)
  - test_lote_partial_display_names        -> RED (MUST FAIL)

Plan: docs/PLAN_File_Naming_Document_Tracking.md  (F3-T3)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient


# ============================================================
# F3-T3 Tests
# ============================================================

class TestUploadLoteDisplayNames:
    """
    /api/documentos/upload-lote endpoint must accept an optional
    display_names JSON array and apply each name to the corresponding file.
    """

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, temp_data_dir):
        """Set up isolated SQLite-backed storage and TestClient for each test.

        Patches both Supabase flags to False BEFORE constructing StorageManager
        so the instance uses SQLite rather than the live Supabase instance.
        """
        monkeypatch.setattr("storage.SUPABASE_DB_AVAILABLE", False)
        monkeypatch.setattr("storage.SUPABASE_STORAGE_AVAILABLE", False)

        from storage import StorageManager
        self.storage = StorageManager(base_path=str(temp_data_dir))

        # Build the full educational hierarchy
        self.materia = self.storage.criar_materia(nome="Fisica")
        self.turma = self.storage.criar_turma(
            materia_id=self.materia.id, nome="Turma B"
        )
        # tipo=enunciado does not require aluno_id, so no aluno needed
        self.atividade = self.storage.criar_atividade(
            turma_id=self.turma.id, nome="Prova 2"
        )

        # Patch the storage singleton used by the endpoints
        monkeypatch.setattr("main_v2.storage", self.storage)
        monkeypatch.setattr("routes_extras.storage", self.storage)

        from main_v2 import app
        self.client = TestClient(app)

    def test_lote_with_display_names_array(self):
        """
        POST /api/documentos/upload-lote with display_names='["Nome A","Nome B"]'
        (JSON-encoded string) for 2 files must return documents where:
          - documentos[0]["display_name"] == "Nome A"
          - documentos[1]["display_name"] == "Nome B"

        RED: FAILS because the endpoint does not accept a display_names Form field.
        FastAPI ignores it and salvar_documento() auto-generates names for both files.
        Implement display_names in upload_documentos_lote() in routes_extras.py (F3-T3).
        """
        display_names = json.dumps(["Nome A", "Nome B"])

        response = self.client.post(
            "/api/documentos/upload-lote",
            data={
                "tipo": "enunciado",
                "atividade_id": self.atividade.id,
                "display_names": display_names,
            },
            files=[
                ("files", ("doc1.pdf", b"%PDF-1.4 content one", "application/pdf")),
                ("files", ("doc2.pdf", b"%PDF-1.4 content two", "application/pdf")),
            ],
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()

        assert data["salvos"] == 2, (
            f"Expected 2 saved documents, got {data['salvos']}. "
            f"Errors: {data.get('detalhes_erros', [])}"
        )

        docs = data["documentos"]
        assert docs[0]["display_name"] == "Nome A", (
            f"Expected docs[0].display_name='Nome A', got '{docs[0]['display_name']}'. "
            "The endpoint must parse display_names JSON and pass each entry to "
            "storage.salvar_documento(display_name=...) per file."
        )
        assert docs[1]["display_name"] == "Nome B", (
            f"Expected docs[1].display_name='Nome B', got '{docs[1]['display_name']}'."
        )

    def test_lote_without_display_names_backward_compat(self):
        """
        POST /api/documentos/upload-lote without display_names must still succeed
        and save all documents with non-empty auto-generated display_names.

        This should PASS already — salvar_documento() auto-generates
        display_name when none is provided (F3-T1 is already implemented).
        """
        response = self.client.post(
            "/api/documentos/upload-lote",
            data={
                "tipo": "enunciado",
                "atividade_id": self.atividade.id,
            },
            files=[
                ("files", ("file1.pdf", b"%PDF-1.4 alpha", "application/pdf")),
                ("files", ("file2.pdf", b"%PDF-1.4 beta", "application/pdf")),
            ],
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()

        assert data["success"] is True, "Response success flag must be True"
        assert data["salvos"] == 2, (
            f"Expected 2 saved documents without display_names, got {data['salvos']}. "
            f"Errors: {data.get('detalhes_erros', [])}"
        )
        for i, doc in enumerate(data["documentos"]):
            assert doc.get("display_name"), (
                f"documentos[{i}].display_name must be auto-generated (non-empty) "
                "when display_names param is omitted."
            )

    def test_lote_partial_display_names(self):
        """
        POST /api/documentos/upload-lote with display_names='["Nome A"]' for 2 files:
          - The first document must use "Nome A" as display_name.
          - The second document must have a non-empty auto-generated display_name.

        RED: FAILS because the endpoint does not accept display_names at all.
        After implementation the endpoint must handle partial arrays gracefully:
        use explicit names where provided, fall back to auto-generation for the rest.
        """
        display_names = json.dumps(["Nome A"])

        response = self.client.post(
            "/api/documentos/upload-lote",
            data={
                "tipo": "enunciado",
                "atividade_id": self.atividade.id,
                "display_names": display_names,
            },
            files=[
                ("files", ("first.pdf", b"%PDF-1.4 first", "application/pdf")),
                ("files", ("second.pdf", b"%PDF-1.4 second", "application/pdf")),
            ],
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text}"
        )
        data = response.json()

        assert data["salvos"] == 2, (
            f"Expected 2 saved documents for partial display_names test, "
            f"got {data['salvos']}. Errors: {data.get('detalhes_erros', [])}"
        )

        docs = data["documentos"]
        assert docs[0]["display_name"] == "Nome A", (
            f"First document must use the explicit display_name 'Nome A', "
            f"got '{docs[0]['display_name']}'."
        )
        assert docs[1]["display_name"], (
            "Second document must have a non-empty auto-generated display_name "
            "when no explicit name was provided for that index."
        )
        assert docs[1]["display_name"] != "Nome A", (
            "Second document must NOT reuse the first document's display_name."
        )
