"""
Tests for CommandReceiver - file-based command ingestion for IPC.

The CommandReceiver polls commands.jsonl for new commands from
Claude Code, enabling mid-journey interaction (stop, guidance).
"""

import json
import pytest
from pathlib import Path

from tests.ui.investor_journey_agent.command_receiver import CommandReceiver, Command


def _write_command(output_dir: Path, command_type: str, data: dict = None):
    """Helper to write a command to commands.jsonl."""
    from datetime import datetime, timezone

    cmd = {
        "command_type": command_type,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(output_dir / "commands.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(cmd) + "\n")


class TestCommandReceiverCreation:
    """Tests for CommandReceiver initialization."""

    def test_receiver_initializes_with_output_dir(self, tmp_path):
        """CommandReceiver accepts output_dir."""
        receiver = CommandReceiver(output_dir=tmp_path)
        assert receiver is not None

    def test_poll_returns_none_when_no_file(self, tmp_path):
        """poll() returns None when commands.jsonl doesn't exist."""
        receiver = CommandReceiver(output_dir=tmp_path)
        assert receiver.poll() is None

    def test_poll_returns_none_when_file_empty(self, tmp_path):
        """poll() returns None when commands.jsonl exists but is empty."""
        (tmp_path / "commands.jsonl").write_text("")
        receiver = CommandReceiver(output_dir=tmp_path)
        assert receiver.poll() is None


class TestPollCommand:
    """Tests for polling individual commands."""

    def test_poll_returns_command_after_write(self, tmp_path):
        """After writing a command, poll() returns it."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "stop", {"reason": "User wants report"})

        cmd = receiver.poll()

        assert cmd is not None
        assert cmd.command_type == "stop"
        assert cmd.data["reason"] == "User wants report"

    def test_poll_tracks_position(self, tmp_path):
        """poll() only returns NEW commands, not previously read ones."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "stop", {"reason": "first"})

        cmd1 = receiver.poll()
        assert cmd1 is not None
        assert cmd1.data["reason"] == "first"

        # Second poll with no new commands
        cmd2 = receiver.poll()
        assert cmd2 is None

    def test_poll_returns_new_command_after_previous(self, tmp_path):
        """poll() returns new commands written after the last read."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "stop", {"reason": "first"})
        receiver.poll()  # Consume first

        _write_command(tmp_path, "guidance", {"instruction": "click settings"})
        cmd = receiver.poll()
        assert cmd is not None
        assert cmd.command_type == "guidance"

    def test_command_has_timestamp(self, tmp_path):
        """Command object includes the timestamp from the JSON."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "stop")

        cmd = receiver.poll()
        assert cmd.timestamp is not None


class TestPollAll:
    """Tests for poll_all() returning multiple commands."""

    def test_poll_all_returns_empty_list_when_no_commands(self, tmp_path):
        """poll_all() returns empty list when no commands exist."""
        receiver = CommandReceiver(output_dir=tmp_path)
        assert receiver.poll_all() == []

    def test_poll_all_returns_multiple_commands(self, tmp_path):
        """poll_all() returns all unread commands as a list."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "guidance", {"instruction": "click A"})
        _write_command(tmp_path, "guidance", {"instruction": "click B"})
        _write_command(tmp_path, "stop", {"reason": "done"})

        cmds = receiver.poll_all()

        assert len(cmds) == 3
        assert cmds[0].command_type == "guidance"
        assert cmds[1].command_type == "guidance"
        assert cmds[2].command_type == "stop"

    def test_poll_all_tracks_position(self, tmp_path):
        """poll_all() doesn't return previously consumed commands."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "stop")
        receiver.poll_all()  # Consume

        _write_command(tmp_path, "guidance", {"instruction": "new"})
        cmds = receiver.poll_all()
        assert len(cmds) == 1
        assert cmds[0].command_type == "guidance"


class TestCommandTypes:
    """Tests for parsing different command types."""

    def test_stop_command_parsed(self, tmp_path):
        """'stop' command is recognized with optional reason."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "stop", {"reason": "User wants report"})

        cmd = receiver.poll()
        assert cmd.command_type == "stop"
        assert cmd.data["reason"] == "User wants report"

    def test_guidance_command_parsed(self, tmp_path):
        """'guidance' command includes instruction text."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "guidance", {"instruction": "Try the settings button"})

        cmd = receiver.poll()
        assert cmd.command_type == "guidance"
        assert cmd.data["instruction"] == "Try the settings button"

    def test_unknown_command_returns_with_type(self, tmp_path):
        """Unknown command types are still returned (not silently dropped)."""
        receiver = CommandReceiver(output_dir=tmp_path)
        _write_command(tmp_path, "unknown_cmd", {"foo": "bar"})

        cmd = receiver.poll()
        assert cmd is not None
        assert cmd.command_type == "unknown_cmd"

    def test_malformed_json_line_skipped(self, tmp_path):
        """Malformed JSON lines are skipped gracefully."""
        receiver = CommandReceiver(output_dir=tmp_path)
        with open(tmp_path / "commands.jsonl", "w") as f:
            f.write("this is not json\n")
        _write_command(tmp_path, "stop")

        cmds = receiver.poll_all()
        assert len(cmds) == 1
        assert cmds[0].command_type == "stop"


class TestAgentCommandReceiverIntegration:
    """Tests that InvestorJourneyAgent accepts CommandReceiver."""

    def test_agent_constructor_accepts_command_receiver(self):
        """InvestorJourneyAgent accepts optional command_receiver param."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig
        from unittest.mock import MagicMock

        receiver = MagicMock(spec=CommandReceiver)
        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
            command_receiver=receiver,
        )

        assert agent.command_receiver is receiver

    def test_agent_constructor_defaults_to_no_receiver(self):
        """InvestorJourneyAgent defaults to command_receiver=None."""
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="iphone_14",
            config=AgentConfig(ask_before_action=False),
        )

        assert agent.command_receiver is None


class TestLLMBrainGuidance:
    """Tests that LLMBrain.decide_next_action() accepts user_guidance."""

    @pytest.mark.asyncio
    async def test_guidance_text_included_in_prompt(self):
        """When user_guidance is provided, it appears in the API call."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona
        from unittest.mock import patch, AsyncMock

        config = AgentConfig()
        brain = LLMBrain(config)

        with patch.object(brain, '_call_claude', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"action_type": "click", "target": "#settings", "thought": "Following guidance", "frustration_level": 0.2, "confidence": 0.9}'

            persona = get_persona("investor")
            await brain.decide_next_action(
                screenshot_base64="dGVzdA==",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="test",
                user_guidance="Try clicking the settings button",
            )

            # Check the messages sent to Claude contain the guidance
            call_args = mock_call.call_args
            messages = call_args.kwargs.get("messages") or call_args[0][0]
            # The user content should contain the guidance text
            user_message = messages[0]["content"]
            text_parts = [p["text"] for p in user_message if p.get("type") == "text"]
            full_text = " ".join(text_parts)
            assert "Try clicking the settings button" in full_text

    @pytest.mark.asyncio
    async def test_no_guidance_works_normally(self):
        """When user_guidance is None, prompt works unchanged."""
        from tests.ui.investor_journey_agent.llm_brain import LLMBrain
        from tests.ui.investor_journey_agent.config import AgentConfig
        from tests.ui.investor_journey_agent.personas import get_persona
        from unittest.mock import patch, AsyncMock

        config = AgentConfig()
        brain = LLMBrain(config)

        with patch.object(brain, '_call_claude', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = '{"action_type": "wait", "target": "", "thought": "test", "frustration_level": 0.1, "confidence": 0.9}'

            persona = get_persona("investor")
            action = await brain.decide_next_action(
                screenshot_base64="dGVzdA==",
                dom_snapshot="<html></html>",
                persona=persona,
                goal="test",
            )

            # Should work without user_guidance parameter
            assert action.action_type.value == "wait"
