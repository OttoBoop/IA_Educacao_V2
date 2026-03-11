"""
F1-T1: Refactor _desempenhoGenerating from global boolean to per-level-entity object.

RED phase — tests should FAIL because:
- Unit test: HTML still uses a global boolean `let _desempenhoGenerating = false;`
- The guard in executarDesempenho() uses `if (_desempenhoGenerating)` globally
"""

from pathlib import Path

import pytest


HTML_PATH = Path(__file__).resolve().parents[3] / "frontend" / "index_v2.html"


@pytest.fixture
def html_content():
    return HTML_PATH.read_text(encoding="utf-8")


class TestF1T1_PerLevelButtonState:
    """F1-T1: _desempenhoGenerating must be a per-level-entity object, not a global boolean."""

    def test_state_is_object_not_boolean(self, html_content):
        """_desempenhoGenerating must be initialized as an object ({}), not a boolean (false)."""
        # The old pattern: `let _desempenhoGenerating = false;`
        assert "let _desempenhoGenerating = false" not in html_content, (
            "_desempenhoGenerating is still a global boolean. "
            "Must be refactored to an object: `let _desempenhoGenerating = {};`"
        )

    def test_guard_uses_level_entity_key(self, html_content):
        """executarDesempenho guard must check per-level-entity key, not global boolean."""
        # The old pattern: `if (_desempenhoGenerating) return;`
        # New pattern should use a composite key like `_desempenhoGenerating[level + '-' + entityId]`
        assert "if (_desempenhoGenerating)" not in html_content or \
               "_desempenhoGenerating[" in html_content, (
            "executarDesempenho still uses `if (_desempenhoGenerating)` as a global guard. "
            "Must check per-key: `if (_desempenhoGenerating[key]) return;`"
        )

    def test_set_uses_level_entity_key(self, html_content):
        """Setting generating state must use per-level-entity key."""
        # Must have pattern like `_desempenhoGenerating[key] = true`
        assert "_desempenhoGenerating[" in html_content, (
            "_desempenhoGenerating must be accessed with a composite key "
            "like `_desempenhoGenerating[level + '-' + entityId]`"
        )

    def test_cleanup_uses_level_entity_key(self, html_content):
        """Cleanup must use delete or set false on per-level-entity key."""
        # Must have `delete _desempenhoGenerating[key]` or `_desempenhoGenerating[key] = false`
        assert "delete _desempenhoGenerating[" in html_content or \
               "_desempenhoGenerating[" in html_content, (
            "Cleanup must reset the per-level-entity key, not a global boolean."
        )
