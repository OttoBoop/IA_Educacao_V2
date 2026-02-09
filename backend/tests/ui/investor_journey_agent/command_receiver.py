"""
CommandReceiver - File-based command ingestion for IPC with Claude Code.

Polls commands.jsonl for new commands, enabling external processes
to send stop, guidance, and other commands to the running agent.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Command:
    """A command received from an external process."""

    command_type: str
    data: Dict
    timestamp: Optional[str] = None


class CommandReceiver:
    """Polls commands.jsonl for new commands from Claude Code."""

    def __init__(self, output_dir: Path):
        self._output_dir = Path(output_dir)
        self._commands_path = self._output_dir / "commands.jsonl"
        self._read_position = 0

    def poll(self) -> Optional[Command]:
        """Read and return the next unread command, or None."""
        cmds = self.poll_all()
        return cmds[0] if cmds else None

    def poll_all(self) -> List[Command]:
        """Read and return all unread commands."""
        if not self._commands_path.exists():
            return []

        commands = []
        try:
            with open(self._commands_path, "r", encoding="utf-8") as f:
                f.seek(self._read_position)
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        commands.append(Command(
                            command_type=data.get("command_type", "unknown"),
                            data=data.get("data", {}),
                            timestamp=data.get("timestamp"),
                        ))
                    except json.JSONDecodeError:
                        continue  # Skip malformed lines
                self._read_position = f.tell()
        except OSError:
            return []

        return commands
