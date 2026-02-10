"""
Tests for context persistence (F2: Save/Load per URL).

Verifies that website context can be saved and loaded from a JSON store keyed by URL.
Also tests the wiring of context_store into __main__.py (F2-T2).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock


# ── F2-T1: context_store.py CRUD operations ─────────────────────────


class TestSaveContext:
    """Tests for save_context function."""

    def test_save_context_creates_file(self, tmp_path):
        """save_context should create context_store.json if it doesn't exist."""
        from tests.ui.investor_journey_agent.context_store import save_context

        store_path = tmp_path / "context_store.json"
        save_context("https://example.com", "An example website", store_path=store_path)

        assert store_path.exists()

    def test_save_context_stores_url_key(self, tmp_path):
        """save_context should store context keyed by URL."""
        from tests.ui.investor_journey_agent.context_store import save_context

        store_path = tmp_path / "context_store.json"
        save_context("https://example.com", "An example website", store_path=store_path)

        data = json.loads(store_path.read_text())
        assert "https://example.com" in data
        assert data["https://example.com"] == "An example website"

    def test_save_context_updates_existing(self, tmp_path):
        """save_context should update an existing entry for the same URL."""
        from tests.ui.investor_journey_agent.context_store import save_context

        store_path = tmp_path / "context_store.json"
        save_context("https://example.com", "Old description", store_path=store_path)
        save_context("https://example.com", "New description", store_path=store_path)

        data = json.loads(store_path.read_text())
        assert data["https://example.com"] == "New description"

    def test_save_context_preserves_other_entries(self, tmp_path):
        """save_context should not clobber other URL entries."""
        from tests.ui.investor_journey_agent.context_store import save_context

        store_path = tmp_path / "context_store.json"
        save_context("https://a.com", "Site A", store_path=store_path)
        save_context("https://b.com", "Site B", store_path=store_path)

        data = json.loads(store_path.read_text())
        assert data["https://a.com"] == "Site A"
        assert data["https://b.com"] == "Site B"


class TestLoadContext:
    """Tests for load_context function."""

    def test_load_context_returns_saved_text(self, tmp_path):
        """load_context should return the saved description for a known URL."""
        from tests.ui.investor_journey_agent.context_store import save_context, load_context

        store_path = tmp_path / "context_store.json"
        save_context("https://example.com", "An example website", store_path=store_path)

        result = load_context("https://example.com", store_path=store_path)
        assert result == "An example website"

    def test_load_context_returns_none_for_unknown_url(self, tmp_path):
        """load_context should return None for a URL not in the store."""
        from tests.ui.investor_journey_agent.context_store import load_context

        store_path = tmp_path / "context_store.json"
        # Empty store or no file
        result = load_context("https://unknown.com", store_path=store_path)
        assert result is None

    def test_load_context_returns_none_when_no_file(self, tmp_path):
        """load_context should return None when the store file doesn't exist."""
        from tests.ui.investor_journey_agent.context_store import load_context

        store_path = tmp_path / "nonexistent" / "context_store.json"
        result = load_context("https://example.com", store_path=store_path)
        assert result is None


class TestStoreFileFormat:
    """Tests for store file format (human-readable JSON)."""

    def test_store_file_is_valid_json(self, tmp_path):
        """The store file should be valid, parseable JSON."""
        from tests.ui.investor_journey_agent.context_store import save_context

        store_path = tmp_path / "context_store.json"
        save_context("https://example.com", "Test", store_path=store_path)

        # Should not raise
        data = json.loads(store_path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)

    def test_store_file_is_indented(self, tmp_path):
        """The store file should be indented for human readability."""
        from tests.ui.investor_journey_agent.context_store import save_context

        store_path = tmp_path / "context_store.json"
        save_context("https://example.com", "Test", store_path=store_path)

        content = store_path.read_text(encoding="utf-8")
        # Indented JSON has newlines and spaces
        assert "\n" in content
        assert "  " in content


# ── F2-T2: Integration — context_store wired into __main__.py ────────


class TestMainContextStoreIntegration:
    """Integration tests: __main__.py uses context_store for auto-load and save."""

    def test_main_imports_context_store(self):
        """__main__.py should import from context_store."""
        import tests.ui.investor_journey_agent.__main__ as main_mod
        source = Path(main_mod.__file__).read_text(encoding="utf-8")
        assert "context_store" in source

    def test_main_auto_loads_saved_context_when_no_cli_flag(self):
        """When --context is not provided, main should auto-load saved context for the URL."""
        from tests.ui.investor_journey_agent.__main__ import resolve_context

        # Pre-save a context
        from tests.ui.investor_journey_agent.context_store import save_context
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "context_store.json"
            save_context("https://example.com", "Saved description", store_path=store_path)

            result = resolve_context(
                cli_context=None,
                url="https://example.com",
                store_path=store_path,
            )
            assert result == "Saved description"

    def test_main_cli_context_overrides_saved(self):
        """When --context is provided, it should override saved context."""
        from tests.ui.investor_journey_agent.__main__ import resolve_context

        from tests.ui.investor_journey_agent.context_store import save_context
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "context_store.json"
            save_context("https://example.com", "Old saved", store_path=store_path)

            result = resolve_context(
                cli_context="CLI override",
                url="https://example.com",
                store_path=store_path,
            )
            assert result == "CLI override"

    def test_main_saves_new_context_to_store(self):
        """When --context is provided, it should be saved to the store."""
        from tests.ui.investor_journey_agent.__main__ import resolve_context
        from tests.ui.investor_journey_agent.context_store import load_context

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "context_store.json"

            resolve_context(
                cli_context="New description",
                url="https://example.com",
                store_path=store_path,
            )

            saved = load_context("https://example.com", store_path=store_path)
            assert saved == "New description"

    def test_main_returns_none_when_no_context_anywhere(self):
        """When no CLI context and no saved context, should return None."""
        from tests.ui.investor_journey_agent.__main__ import resolve_context

        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            store_path = Path(tmp) / "context_store.json"

            result = resolve_context(
                cli_context=None,
                url="https://unknown.com",
                store_path=store_path,
            )
            assert result is None
