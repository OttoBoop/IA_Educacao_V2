"""
Tests for F6-T1: Python Pre-test Setup (--setup CLI flag).

- F6-T1: build_parser() must include --setup argument
  - Argument exists in the parser's action list
  - Defaults to None when not provided
  - Accepts a file path value (e.g., path/to/setup.py)
"""

import unittest

from tests.ui.investor_journey_agent.__main__ import build_parser


# ============================================================
# F6-T1: --setup CLI argument
# ============================================================


class TestSetupCLIFlag(unittest.TestCase):
    """F6-T1: build_parser() must include --setup argument."""

    def test_cli_has_setup_argument(self):
        """--setup must be registered in the argument parser."""
        parser = build_parser()
        action_dests = {a.dest for a in parser._actions}
        self.assertIn(
            "setup",
            action_dests,
            "build_parser() must include `--setup` argument. "
            "Add `parser.add_argument('--setup', ...)` to build_parser() in __main__.py.",
        )

    def test_setup_defaults_to_none(self):
        """--setup must default to None when not provided on the CLI."""
        parser = build_parser()
        args = parser.parse_args(["--url", "http://localhost:8000"])
        self.assertIsNone(
            getattr(args, "setup", None),
            "--setup should default to None when not provided.",
        )

    def test_setup_accepts_path_value(self):
        """--setup must accept a file path like 'path/to/setup.py'."""
        parser = build_parser()
        # This parse_args call raises SystemExit(2) if --setup is not defined.
        args = parser.parse_args(
            ["--url", "http://localhost:8000", "--setup", "path/to/setup.py"]
        )
        self.assertEqual(
            args.setup,
            "path/to/setup.py",
            "--setup path/to/setup.py should be stored as 'path/to/setup.py'.",
        )

    def test_setup_accepts_absolute_path(self):
        """--setup must accept an absolute file path."""
        parser = build_parser()
        args = parser.parse_args(
            ["--url", "http://localhost:8000", "--setup", "/home/user/setup.py"]
        )
        self.assertEqual(
            args.setup,
            "/home/user/setup.py",
            "--setup /home/user/setup.py should be stored as-is.",
        )


if __name__ == "__main__":
    unittest.main()
