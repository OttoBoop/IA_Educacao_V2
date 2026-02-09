"""
Tests for the occlusion test fixture HTML file.

F1-T3: The fixture must provide a controlled HTML page with elements in
various occlusion states for testing the agent's elementFromPoint logic.
"""

from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_PATH = FIXTURE_DIR / "occlusion_test.html"


# ============================================================
# F1-T3: Mock HTML fixture for occlusion testing
# ============================================================


class TestOcclusionFixtureExists:
    """The fixture file must exist and be valid HTML."""

    def test_fixture_file_exists(self):
        """occlusion_test.html must exist in the fixtures directory."""
        assert FIXTURE_PATH.exists(), f"Fixture not found at {FIXTURE_PATH}"

    def test_fixture_is_valid_html(self):
        """Fixture must start with <!DOCTYPE html>."""
        content = FIXTURE_PATH.read_text(encoding="utf-8")
        assert content.strip().startswith("<!DOCTYPE html>")


class TestOcclusionFixtureElements:
    """The fixture must contain specific elements for each occlusion scenario."""

    @pytest.fixture(autouse=True)
    def load_fixture(self):
        self.html = FIXTURE_PATH.read_text(encoding="utf-8")

    def test_has_visible_button(self):
        """Fixture must have a fully visible button with id='btn-visible'."""
        assert 'id="btn-visible"' in self.html

    def test_has_occluded_button(self):
        """Fixture must have a button behind a full-screen overlay with id='btn-occluded'."""
        assert 'id="btn-occluded"' in self.html

    def test_has_partial_button(self):
        """Fixture must have a partially occluded button with id='btn-partial'."""
        assert 'id="btn-partial"' in self.html

    def test_has_offscreen_button(self):
        """Fixture must have an off-screen button with id='btn-offscreen'."""
        assert 'id="btn-offscreen"' in self.html

    def test_has_overlay_element(self):
        """Fixture must have an overlay div with id='overlay'."""
        assert 'id="overlay"' in self.html

    def test_has_partial_overlay(self):
        """Fixture must have a partial overlay div with id='partial-overlay'."""
        assert 'id="partial-overlay"' in self.html

    def test_overlay_has_high_z_index(self):
        """Overlay must use z-index to sit above buttons (simulating a modal)."""
        assert "z-index" in self.html

    def test_offscreen_button_has_negative_position(self):
        """Off-screen button must be positioned outside the viewport."""
        # The button should have a negative top or left value
        assert "btn-offscreen" in self.html
        # Verify it's positioned off-screen via CSS
        assert "-9999" in self.html or "-1000" in self.html
