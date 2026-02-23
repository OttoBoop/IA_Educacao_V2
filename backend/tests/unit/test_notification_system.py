"""
Unit tests for the notification system (sound + toast).

Tests verify:
- Web Audio API sound generator exists in frontend JS
- Toast notification element supports pipeline events
- Sound functions (success chime, error alert) are defined

F5-T1 from PLAN_Task_Panel_Sidebar_UI.md

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_notification_system.py -v
"""

import pytest
from pathlib import Path


@pytest.fixture
def html_content():
    """Read the index_v2.html file content."""
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


class TestNotificationSoundSystem:
    """Tests for the Web Audio API notification sounds."""

    def test_audio_context_initialization(self, html_content):
        """Frontend must create/use an AudioContext for sound generation."""
        assert "AudioContext" in html_content, (
            "Missing AudioContext usage — Web Audio API not initialized"
        )

    def test_success_sound_function_exists(self, html_content):
        """A function to play success sound must exist."""
        assert "playSuccessSound" in html_content or "playNotificationSound" in html_content, (
            "Missing success sound function (playSuccessSound or playNotificationSound)"
        )

    def test_error_sound_function_exists(self, html_content):
        """A function to play error sound must exist."""
        assert "playErrorSound" in html_content or "playNotificationSound" in html_content, (
            "Missing error sound function (playErrorSound or playNotificationSound)"
        )

    def test_oscillator_used_for_sound(self, html_content):
        """Sounds should use oscillator (Web Audio API) for generation."""
        assert "createOscillator" in html_content or "oscillator" in html_content.lower(), (
            "Missing oscillator usage — sounds should be generated via Web Audio API"
        )


class TestNotificationToast:
    """Tests for the pipeline-specific toast notifications."""

    def test_pipeline_toast_function_exists(self, html_content):
        """A dedicated function for pipeline toast notifications must exist."""
        # The existing showToast() is generic. We need a pipeline-specific wrapper
        # that includes the task context (matéria, turma, etc.)
        assert "showPipelineToast" in html_content, (
            "Missing showPipelineToast function for pipeline-specific notifications"
        )

    def test_toast_auto_dismiss(self, html_content):
        """Toast must auto-dismiss (setTimeout pattern)."""
        # Check for auto-dismiss pattern in toast-related code
        assert "setTimeout" in html_content, (
            "Missing setTimeout for toast auto-dismiss"
        )
        # More specifically, look for a 5-second dismiss for pipeline toasts
        # (existing toast uses 3000ms, pipeline should use 5000ms per plan)
        assert "5000" in html_content, (
            "Missing 5000ms (5s) auto-dismiss timeout for pipeline toast"
        )
