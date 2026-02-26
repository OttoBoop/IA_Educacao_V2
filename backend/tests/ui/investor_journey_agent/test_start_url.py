"""
Tests for F5-T1/F5-T2: Deep-link Navigation (--start-url).

- F5-T1: build_parser() must include --start-url argument
  - Argument exists in the parser's action list
  - Accepts a URL fragment (e.g., /#turmas)
  - Defaults to None when not provided
- F5-T2: resolve_start_url() utility + run_journey() accepts start_url parameter
  - Fragment (#turmas) is appended to the full base URL
  - Path (/dashboard) replaces the base URL path (uses origin)
  - run_journey() signature includes start_url: Optional[str] = None
"""

import inspect
import unittest

from tests.ui.investor_journey_agent.__main__ import build_parser
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


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


# ============================================================
# F5-T2: resolve_start_url() utility function
# ============================================================


class TestResolveStartURL(unittest.TestCase):
    """F5-T2: resolve_start_url() must compute the correct full URL."""

    def _import_fn(self):
        """Import resolve_start_url lazily so import errors produce helpful test failures."""
        try:
            from tests.ui.investor_journey_agent.url_utils import resolve_start_url
            return resolve_start_url
        except ImportError as e:
            self.fail(
                f"Could not import resolve_start_url from url_utils: {e}. "
                "Add `resolve_start_url(base_url, start_url)` to url_utils.py."
            )

    def test_fragment_appended_to_base_url(self):
        """Fragment (#turmas) must be appended to the full base URL (including path)."""
        resolve_start_url = self._import_fn()
        result = resolve_start_url("https://example.com", "#turmas")
        self.assertEqual(
            result,
            "https://example.com#turmas",
            "resolve_start_url('https://example.com', '#turmas') must return "
            "'https://example.com#turmas'. A fragment is appended to the full base URL.",
        )

    def test_fragment_appended_to_base_url_with_path(self):
        """Fragment (#turmas) must be appended to the base URL even if it has a path."""
        resolve_start_url = self._import_fn()
        result = resolve_start_url("https://example.com/home", "#turmas")
        self.assertEqual(
            result,
            "https://example.com/home#turmas",
            "resolve_start_url('https://example.com/home', '#turmas') must return "
            "'https://example.com/home#turmas'.",
        )

    def test_path_replaces_base_url_path(self):
        """Path (/dashboard) must replace the base URL path, keeping the origin."""
        resolve_start_url = self._import_fn()
        result = resolve_start_url("https://example.com/home", "/dashboard")
        self.assertEqual(
            result,
            "https://example.com/dashboard",
            "resolve_start_url('https://example.com/home', '/dashboard') must return "
            "'https://example.com/dashboard'. A path replaces the base URL path.",
        )

    def test_path_on_base_url_without_path(self):
        """Path (/dashboard) on a root base URL must return origin + path."""
        resolve_start_url = self._import_fn()
        result = resolve_start_url("https://example.com", "/dashboard")
        self.assertEqual(
            result,
            "https://example.com/dashboard",
            "resolve_start_url('https://example.com', '/dashboard') must return "
            "'https://example.com/dashboard'.",
        )


# ============================================================
# F5-T2: run_journey() accepts start_url parameter
# ============================================================


class TestRunJourneyAcceptsStartURL(unittest.TestCase):
    """F5-T2: run_journey() must accept a start_url parameter."""

    def test_run_journey_has_start_url_parameter(self):
        """run_journey() signature must include start_url: Optional[str] = None."""
        sig = inspect.signature(InvestorJourneyAgent.run_journey)
        self.assertIn(
            "start_url",
            sig.parameters,
            "InvestorJourneyAgent.run_journey() must accept `start_url` parameter. "
            "Add `start_url: Optional[str] = None` to run_journey() in agent.py.",
        )

    def test_start_url_defaults_to_none_in_run_journey(self):
        """start_url parameter must default to None."""
        sig = inspect.signature(InvestorJourneyAgent.run_journey)
        if "start_url" not in sig.parameters:
            self.skipTest("start_url param not yet added — covered by other test")
        default = sig.parameters["start_url"].default
        self.assertIsNone(
            default,
            "start_url must default to None in run_journey(). "
            "Use `start_url: Optional[str] = None`.",
        )


if __name__ == "__main__":
    unittest.main()
