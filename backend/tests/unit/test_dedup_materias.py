"""F3-T1: Verify get_arvore_navegacao() deduplicates matérias by nome.

RED phase — these tests MUST fail until dedup logic is added to
StorageManager.get_arvore_navegacao().

Current behaviour: listar_materias() returns ALL rows, so when two rows
share the same nome the tree will contain two entries.
Expected behaviour: the tree must contain exactly ONE entry per unique nome,
and that entry must carry all turmas attached to any of the duplicate IDs.
"""

import sys
import os
import sqlite3
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Ensure the backend directory is on sys.path so imports resolve.
BACKEND_DIR = Path(__file__).parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Force SQLite mode by ensuring supabase_db is NOT available before import.
os.environ.setdefault("PROVA_AI_TESTING", "1")
# Disable local LLM to avoid hanging during import side-effects.
os.environ.setdefault("PROVA_AI_DISABLE_LOCAL_LLM", "1")


import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_storage(base_path: str):
    """Return a StorageManager wired to SQLite at *base_path*."""
    # Patch SUPABASE_DB_AVAILABLE to False so the manager stays in SQLite mode
    # regardless of the real environment.
    with patch("storage.SUPABASE_DB_AVAILABLE", False):
        from storage import StorageManager
        mgr = StorageManager(base_path=base_path)
    return mgr


def _insert_raw_materia(db_path: Path, materia_id: str, nome: str):
    """Insert a matéria row directly via SQLite, bypassing StorageManager logic.

    This lets us create intentional duplicates (same nome, different id) that
    the normal criar_materia() API would not produce.
    """
    conn = sqlite3.connect(str(db_path))
    now = datetime.now().isoformat()
    conn.execute(
        """
        INSERT INTO materias (id, nome, descricao, nivel, criado_em, atualizado_em, metadata)
        VALUES (?, ?, NULL, 'outro', ?, ?, '{}')
        """,
        (materia_id, nome, now, now),
    )
    conn.commit()
    conn.close()


def _insert_raw_turma(db_path: Path, turma_id: str, materia_id: str, nome: str):
    """Insert a turma row directly, linked to *materia_id*."""
    conn = sqlite3.connect(str(db_path))
    now = datetime.now().isoformat()
    conn.execute(
        """
        INSERT INTO turmas (id, materia_id, nome, ano_letivo, periodo, descricao,
                            criado_em, atualizado_em, metadata)
        VALUES (?, ?, ?, NULL, NULL, NULL, ?, ?, '{}')
        """,
        (turma_id, materia_id, nome, now, now),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def storage_with_duplicate_materias(tmp_path):
    """
    Provide a StorageManager whose SQLite DB contains two matérias
    with the same nome ('Matemática') but different IDs.

    The first matéria ('mat-001') has one turma linked to it.
    The second matéria ('mat-002') is a duplicate with no turmas.

    Returns a tuple: (storage_manager, base_path)
    """
    # Build the storage (this creates the schema)
    with patch("storage.SUPABASE_DB_AVAILABLE", False):
        from storage import StorageManager
        mgr = StorageManager(base_path=str(tmp_path))

    db_path = tmp_path / "database.db"

    # Insert two matérias with identical nomes
    _insert_raw_materia(db_path, "mat-001", "Matemática")
    _insert_raw_materia(db_path, "mat-002", "Matemática")  # intentional duplicate

    # Attach a turma to the first matéria
    _insert_raw_turma(db_path, "turma-001", "mat-001", "9º Ano A")

    return mgr, tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetArvoreNavegacaoDeduplicatesMaterias:
    """get_arvore_navegacao() must return unique matérias even when the DB has duplicates."""

    def test_returns_one_materia_when_db_has_two_with_same_nome(
        self, storage_with_duplicate_materias
    ):
        """
        GIVEN a DB with 2 matérias sharing nome 'Matemática'
        WHEN  get_arvore_navegacao() is called
        THEN  the result contains exactly 1 matéria entry (not 2)
        """
        mgr, _ = storage_with_duplicate_materias

        arvore = mgr.get_arvore_navegacao()
        materias = arvore["materias"]

        assert len(materias) == 1, (
            f"Expected 1 unique matéria in the tree, got {len(materias)}. "
            f"Duplicate nomes found: {[m['nome'] for m in materias]}"
        )

    def test_unique_materia_retains_turmas(
        self, storage_with_duplicate_materias
    ):
        """
        GIVEN a DB with 2 matérias sharing nome 'Matemática', the first
              having 1 turma linked
        WHEN  get_arvore_navegacao() is called
        THEN  the single deduplicated matéria entry has 1 turma (not 0 and not 2)

        This test ALSO requires dedup to have happened first: if there are still
        2 matéria entries in the tree the assertion on count==1 will fail, which
        means this test must fail in the RED phase just like the first test.
        """
        mgr, _ = storage_with_duplicate_materias

        arvore = mgr.get_arvore_navegacao()
        materias = arvore["materias"]

        # Dedup must have reduced the list to exactly 1 entry.
        # If dedup has NOT been implemented there will be 2 entries and this
        # assertion fires, making the test fail for the right reason.
        assert len(materias) == 1, (
            f"Dedup not implemented: expected 1 matéria, got {len(materias)}. "
            f"The deduplicated entry should carry the turma from mat-001."
        )

        retained = materias[0]
        assert len(retained["turmas"]) == 1, (
            f"Expected the deduplicated matéria to have 1 turma, "
            f"got {len(retained['turmas'])}"
        )
        assert retained["turmas"][0]["nome"] == "9º Ano A"

    def test_deduplicated_nome_is_correct(
        self, storage_with_duplicate_materias
    ):
        """
        GIVEN a DB with duplicate matérias named 'Matemática'
        WHEN  get_arvore_navegacao() is called
        THEN  the tree has exactly 1 entry and its nome is 'Matemática'
        """
        mgr, _ = storage_with_duplicate_materias

        arvore = mgr.get_arvore_navegacao()
        materias = arvore["materias"]

        # Must be exactly 1 entry after dedup.
        assert len(materias) == 1, (
            f"Expected 1 matéria after dedup, got {len(materias)}: "
            f"{[m['nome'] for m in materias]}"
        )
        assert materias[0]["nome"] == "Matemática"


# ---------------------------------------------------------------------------
# F3-T2: criar_materia() must reject creation when nome already exists
# ---------------------------------------------------------------------------

class TestCriarMateriaRejectsDuplicate:
    """criar_materia() must reject creation when nome already exists.

    RED phase — these tests MUST fail until a uniqueness check is added to
    StorageManager.criar_materia().

    Current behaviour: criar_materia() blindly inserts the row; calling it
    twice with the same nome succeeds and produces two DB rows.
    Expected behaviour: the second call raises ValueError when a matéria
    with the same nome is already present.
    """

    def test_second_creation_with_same_nome_raises_value_error(self, tmp_path):
        """
        GIVEN a StorageManager with one matéria 'Matemática' already created
        WHEN  criar_materia('Matemática') is called a second time
        THEN  a ValueError is raised (duplicate name rejected)
        """
        mgr = _make_storage(str(tmp_path))

        # First creation must succeed without error.
        mgr.criar_materia("Matemática")

        # Second creation with the identical nome must raise ValueError.
        with pytest.raises(ValueError, match="Matemática"):
            mgr.criar_materia("Matemática")

    def test_error_message_identifies_duplicate_name(self, tmp_path):
        """
        GIVEN a matéria 'Física' already exists
        WHEN  criar_materia('Física') is called again
        THEN  the ValueError message contains the duplicate name
        """
        mgr = _make_storage(str(tmp_path))
        mgr.criar_materia("Física")

        with pytest.raises(ValueError) as exc_info:
            mgr.criar_materia("Física")

        assert "Física" in str(exc_info.value), (
            f"Expected the error message to mention the duplicate name 'Física', "
            f"got: {exc_info.value}"
        )

    def test_different_name_after_first_creation_succeeds(self, tmp_path):
        """
        GIVEN a matéria 'Matemática' already exists
        WHEN  criar_materia('Português') is called
        THEN  it succeeds (only exact-name duplicates are rejected)
        """
        mgr = _make_storage(str(tmp_path))
        mgr.criar_materia("Matemática")

        # A different name must not raise.
        result = mgr.criar_materia("Português")

        assert result is not None
        assert result.nome == "Português"

    def test_case_sensitive_same_name_is_rejected(self, tmp_path):
        """
        GIVEN a matéria 'História' already exists
        WHEN  criar_materia('História') is called again (identical casing)
        THEN  ValueError is raised

        This test reinforces that the check is for exact nome equality.
        """
        mgr = _make_storage(str(tmp_path))
        mgr.criar_materia("História")

        with pytest.raises(ValueError):
            mgr.criar_materia("História")


# ---------------------------------------------------------------------------
# F3-T3: cleanup_duplicate_materias() must remove pre-existing duplicates
# ---------------------------------------------------------------------------


@pytest.fixture
def storage_with_duplicates_and_unique(tmp_path):
    """
    Provide a StorageManager whose SQLite DB contains:
      - 'Matemática' (mat-001) with turma '9º Ano A' (turma-001)
      - 'Matemática' (mat-002) — duplicate — with turma '9º Ano B' (turma-002)
      - 'Física'     (mat-003) — unique   — with no turmas

    Returns a tuple: (storage_manager, db_path)
    """
    with patch("storage.SUPABASE_DB_AVAILABLE", False):
        from storage import StorageManager
        mgr = StorageManager(base_path=str(tmp_path))

    db_path = tmp_path / "database.db"

    _insert_raw_materia(db_path, "mat-001", "Matemática")
    _insert_raw_materia(db_path, "mat-002", "Matemática")   # intentional duplicate
    _insert_raw_materia(db_path, "mat-003", "Física")        # unique — must survive untouched

    _insert_raw_turma(db_path, "turma-001", "mat-001", "9º Ano A")
    _insert_raw_turma(db_path, "turma-002", "mat-002", "9º Ano B")  # turma on the duplicate

    return mgr, db_path


class TestCleanupDuplicateMaterias:
    """F3-T3: cleanup_duplicate_materias() must remove duplicate matérias and merge turmas."""

    def test_method_exists_on_storage_manager(self, storage_with_duplicates_and_unique):
        """
        GIVEN a StorageManager instance
        WHEN  we check for the cleanup_duplicate_materias attribute
        THEN  it exists and is callable

        This test fails in the RED phase because the method does not exist yet.
        """
        mgr, _ = storage_with_duplicates_and_unique

        assert hasattr(mgr, "cleanup_duplicate_materias"), (
            "StorageManager must have a cleanup_duplicate_materias() method — "
            "it does not exist yet (RED phase)."
        )
        assert callable(mgr.cleanup_duplicate_materias), (
            "cleanup_duplicate_materias must be callable."
        )

    def test_cleanup_leaves_exactly_one_materia_per_unique_nome(
        self, storage_with_duplicates_and_unique
    ):
        """
        GIVEN a DB with two 'Matemática' rows and one 'Física' row
        WHEN  cleanup_duplicate_materias() is called
        THEN  listar_materias() returns exactly 2 matérias (one per unique nome)
        """
        mgr, _ = storage_with_duplicates_and_unique

        mgr.cleanup_duplicate_materias()

        materias = mgr.listar_materias()
        nomes = [m.nome for m in materias]

        assert len(materias) == 2, (
            f"Expected 2 unique matérias after cleanup (Matemática + Física), "
            f"got {len(materias)}: {nomes}"
        )

    def test_cleanup_surviving_materia_has_both_turmas_merged(
        self, storage_with_duplicates_and_unique
    ):
        """
        GIVEN 'Matemática' mat-001 has '9º Ano A' and mat-002 (duplicate) has '9º Ano B'
        WHEN  cleanup_duplicate_materias() is called
        THEN  the surviving 'Matemática' matéria has BOTH turmas (2 total, none discarded)
        """
        mgr, _ = storage_with_duplicates_and_unique

        mgr.cleanup_duplicate_materias()

        materias = mgr.listar_materias()
        matematica = next((m for m in materias if m.nome == "Matemática"), None)

        assert matematica is not None, (
            "After cleanup 'Matemática' must still exist as a surviving matéria."
        )

        turmas = mgr.listar_turmas(materia_id=matematica.id)
        turma_nomes = [t.nome for t in turmas]

        assert len(turmas) == 2, (
            f"Expected 2 turmas on the surviving 'Matemática' (merged from both duplicates), "
            f"got {len(turmas)}: {turma_nomes}"
        )
        assert "9º Ano A" in turma_nomes, (
            f"Turma '9º Ano A' (from mat-001) must be preserved. Got: {turma_nomes}"
        )
        assert "9º Ano B" in turma_nomes, (
            f"Turma '9º Ano B' (from mat-002, the duplicate) must be reassigned. Got: {turma_nomes}"
        )

    def test_cleanup_does_not_delete_unique_materia(
        self, storage_with_duplicates_and_unique
    ):
        """
        GIVEN 'Física' (mat-003) is a unique matéria with no duplicates
        WHEN  cleanup_duplicate_materias() is called
        THEN  'Física' still exists with 0 turmas (untouched)
        """
        mgr, _ = storage_with_duplicates_and_unique

        mgr.cleanup_duplicate_materias()

        materias = mgr.listar_materias()
        fisica = next((m for m in materias if m.nome == "Física"), None)

        assert fisica is not None, (
            "After cleanup 'Física' must still exist — unique matérias must NOT be deleted."
        )

        turmas = mgr.listar_turmas(materia_id=fisica.id)
        assert len(turmas) == 0, (
            f"'Física' had no turmas originally and must still have 0 after cleanup, "
            f"got {len(turmas)}."
        )

    def test_cleanup_returns_report_dict_with_counts(
        self, storage_with_duplicates_and_unique
    ):
        """
        GIVEN a DB with 1 duplicate 'Matemática' row (mat-002) and 1 reassignable turma (turma-002)
        WHEN  cleanup_duplicate_materias() is called
        THEN  it returns {'duplicates_removed': 1, 'turmas_reassigned': 1}
        """
        mgr, _ = storage_with_duplicates_and_unique

        report = mgr.cleanup_duplicate_materias()

        assert isinstance(report, dict), (
            f"cleanup_duplicate_materias() must return a dict, got {type(report)}."
        )
        assert report.get("duplicates_removed") == 1, (
            f"Expected duplicates_removed=1 (mat-002 removed), got {report.get('duplicates_removed')}. "
            f"Full report: {report}"
        )
        assert report.get("turmas_reassigned") == 1, (
            f"Expected turmas_reassigned=1 (turma-002 moved to surviving matéria), "
            f"got {report.get('turmas_reassigned')}. Full report: {report}"
        )
