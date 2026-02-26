"""
Tests for F6-T1/F6-T2: Python Pre-test Setup (--setup).

- F6-T1: build_parser() must include --setup argument
  - Argument exists in the parser's action list
  - Defaults to None when not provided
  - Accepts a file path value (e.g., path/to/setup.py)
- F6-T2: run_journey() accepts setup parameter; agent._run_setup() execs setup file
  - run_journey() signature includes setup: Optional[str] = None
  - _run_setup(path, page, browser) execs the file with page/browser in namespace
  - _run_setup raises RuntimeError with file path on setup exception
"""

import inspect
import os
import tempfile
import unittest
from pathlib import Path

from tests.ui.investor_journey_agent.__main__ import build_parser
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


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


# ============================================================
# F6-T2: run_journey() accepts setup parameter
# ============================================================


class TestRunJourneyAcceptsSetupParam(unittest.TestCase):
    """F6-T2: run_journey() must accept a setup parameter."""

    def test_run_journey_has_setup_parameter(self):
        """run_journey() signature must include setup: Optional[str] = None."""
        sig = inspect.signature(InvestorJourneyAgent.run_journey)
        self.assertIn(
            "setup",
            sig.parameters,
            "InvestorJourneyAgent.run_journey() must accept `setup` parameter. "
            "Add `setup: Optional[str] = None` to run_journey() in agent.py.",
        )

    def test_setup_defaults_to_none_in_run_journey(self):
        """setup parameter must default to None."""
        sig = inspect.signature(InvestorJourneyAgent.run_journey)
        if "setup" not in sig.parameters:
            self.skipTest("setup param not yet added — covered by other test")
        default = sig.parameters["setup"].default
        self.assertIsNone(
            default,
            "setup must default to None in run_journey(). "
            "Use `setup: Optional[str] = None`.",
        )


# ============================================================
# F6-T2: _run_setup() helper method
# ============================================================


class TestRunSetupMethod(unittest.TestCase):
    """F6-T2: InvestorJourneyAgent._run_setup() must exec the setup file."""

    def _make_agent(self):
        return InvestorJourneyAgent.__new__(InvestorJourneyAgent)

    def test_agent_has_run_setup_method(self):
        """InvestorJourneyAgent must have a _run_setup() method."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_run_setup"),
            "InvestorJourneyAgent must have `_run_setup(path, page, browser)` method. "
            "Add it to agent.py and call it from run_journey() when setup is provided.",
        )

    def test_setup_file_executed_with_page_and_browser(self):
        """_run_setup must exec() the setup file with 'page' and 'browser' in its namespace."""
        agent = self._make_agent()

        with tempfile.TemporaryDirectory() as tmpdir:
            sentinel = Path(tmpdir) / "sentinel.txt"
            setup_file = Path(tmpdir) / "setup.py"
            # Use forward slashes so the path is valid inside the exec'd Python string
            sentinel_str = str(sentinel).replace("\\", "/")
            setup_file.write_text(
                f"open('{sentinel_str}', 'w').write(str(page) + ':' + str(browser))\n"
            )

            agent._run_setup(str(setup_file), page="PAGE_VAL", browser="BROWSER_VAL")

            self.assertTrue(
                sentinel.exists(),
                "_run_setup must exec() the setup file. The file did not run (sentinel not created). "
                "Add `_run_setup(self, path, page, browser)` that reads and exec()s the file.",
            )
            self.assertEqual(
                sentinel.read_text(),
                "PAGE_VAL:BROWSER_VAL",
                "Setup file must have 'page' and 'browser' in its exec namespace.",
            )

    def test_setup_exception_includes_file_path(self):
        """_run_setup must raise RuntimeError with the setup file path on exception."""
        agent = self._make_agent()

        with tempfile.TemporaryDirectory() as tmpdir:
            setup_file = Path(tmpdir) / "bad_setup.py"
            setup_file.write_text("raise ValueError('intentional failure')\n")
            path_str = str(setup_file)

            with self.assertRaises(Exception) as ctx:
                agent._run_setup(path_str, page=None, browser=None)

            self.assertIn(
                path_str,
                str(ctx.exception),
                "Exception from _run_setup must include the setup file path so the user "
                "knows which file failed. Use: raise RuntimeError(f'Setup file failed: {path}: {e}')",
            )


if __name__ == "__main__":
    unittest.main()
