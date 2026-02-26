"""
Tests for F5-T1: Deep-link Navigation (--start-url CLI flag).

- F5-T1: build_parser() must include --start-url argument
  - Argument exists in the parser's action list
  - Accepts a URL fragment (e.g., /#turmas)
  - Defaults to None when not provided
"""

import unittest

from tests.ui.investor_journey_agent.__main__ import build_parser


# ============================================================
# F5-T1: --start-url CLI argument
# ============================================================


class TestStartURLCLIFlag(unittest.TestCase):
    """F5-T1: build_parser() must include --start-url argument."""

    def test_cli_has_start_url_argument(self):
        """--start-url must be registered in the argument parser."""
        parser = build_parser()
        action_dests = {a.dest for a in parser._actions}
        self.assertIn(
            "start_url",
            action_dests,
            "build_parser() must include `--start-url` argument. "
            "Add `parser.add_argument('--start-url', ...)` to build_parser() in __main__.py.",
        )

    def test_start_url_defaults_to_none(self):
        """--start-url must default to None when not provided on the CLI."""
        parser = build_parser()
        # If --start-url doesn't exist yet, get_default returns None anyway (same as expected),
        # so we verify via action_dests first and trust test_cli_has_start_url_argument catches absence.
        args = parser.parse_args(["--url", "http://localhost:8000"])
        self.assertIsNone(
            getattr(args, "start_url", None),
            "--start-url should default to None when not provided.",
        )

    def test_start_url_accepts_fragment_value(self):
        """--start-url must accept a hash fragment like '/#turmas'."""
        parser = build_parser()
        # This parse_args call raises SystemExit(2) if --start-url is not defined.
        args = parser.parse_args(
            ["--url", "http://localhost:8000", "--start-url", "/#turmas"]
        )
        self.assertEqual(
            args.start_url,
            "/#turmas",
            "--start-url /#turmas should be stored as '/#turmas'.",
        )

    def test_start_url_accepts_path_value(self):
        """--start-url must accept a path like '/dashboard'."""
        parser = build_parser()
        args = parser.parse_args(
            ["--url", "http://localhost:8000", "--start-url", "/dashboard"]
        )
        self.assertEqual(
            args.start_url,
            "/dashboard",
            "--start-url /dashboard should be stored as '/dashboard'.",
        )


if __name__ == "__main__":
    unittest.main()
