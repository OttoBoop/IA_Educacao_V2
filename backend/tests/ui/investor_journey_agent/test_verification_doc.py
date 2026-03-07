"""
Tests for F5-T4: Verification Document Generation.

- InvestorJourneyAgent must have a `_write_verification_entry()` sync method
- Accepts keyword args: model (str), stage (str), status (str), details (str)
- Appends (not overwrites) a formatted entry to config.output_dir / "verification_report.md"
- Creates the file if it doesn't exist
- Each entry must contain model, stage, status, and details values
- Returns the Path to the verification report file
- The file must be valid markdown
"""

import inspect
import tempfile
import unittest
from pathlib import Path

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# F5-T4: _write_verification_entry() method exists
# ============================================================


class TestAgentHasWriteVerificationEntryMethod(unittest.TestCase):
    """F5-T4: InvestorJourneyAgent must have a _write_verification_entry() method."""

    def test_agent_has_write_verification_entry_method(self):
        """_write_verification_entry() method must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_write_verification_entry"),
            "InvestorJourneyAgent is missing `_write_verification_entry` method. "
            "Add `def _write_verification_entry(self, *, model, stage, status, details) -> Path` "
            "to agent.py.",
        )

    def test_write_verification_entry_is_callable(self):
        """_write_verification_entry must be callable (not a property or plain attribute)."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )
        self.assertTrue(
            callable(method),
            "_write_verification_entry must be a callable method on InvestorJourneyAgent, "
            "not a plain attribute or property.",
        )

    def test_write_verification_entry_is_not_async(self):
        """_write_verification_entry must be a regular (sync) method, not a coroutine."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )
        self.assertFalse(
            inspect.iscoroutinefunction(method),
            "_write_verification_entry must be a plain `def` method (not `async def`). "
            "File I/O for a small markdown append does not require async.",
        )


# ============================================================
# F5-T4: _write_verification_entry() accepts required params
# ============================================================


class TestWriteVerificationEntrySignature(unittest.TestCase):
    """F5-T4: _write_verification_entry must accept model, stage, status, details."""

    def test_write_verification_entry_accepts_required_params(self):
        """_write_verification_entry must accept model, stage, status, and details params."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )
        sig = inspect.signature(method)
        params = sig.parameters

        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )

        for expected_param in ("model", "stage", "status", "details"):
            has_explicit = expected_param in params
            self.assertTrue(
                has_var_keyword or has_explicit,
                f"_write_verification_entry must accept a `{expected_param}` parameter "
                f"(either explicitly or via **kwargs). "
                f"Current signature: {sig}. "
                "Expected: `def _write_verification_entry(self, *, model, stage, status, details)`",
            )


# ============================================================
# F5-T4: _write_verification_entry() creates the file
# ============================================================


class TestWriteVerificationEntryCreatesFile(unittest.TestCase):
    """F5-T4: _write_verification_entry must create verification_report.md if absent."""

    def test_write_verification_entry_creates_file(self):
        """Calling _write_verification_entry must create verification_report.md in output_dir."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            expected_file = Path(tmp) / "verification_report.md"
            self.assertFalse(
                expected_file.exists(),
                "verification_report.md should NOT exist before calling the method.",
            )

            agent._write_verification_entry(
                model="modelo_A",
                stage="corrigir",
                status="ok",
                details="Pipeline completed successfully.",
            )

            self.assertTrue(
                expected_file.exists(),
                f"_write_verification_entry must create `verification_report.md` inside "
                f"config.output_dir ({tmp}). The file does not exist after calling the method.",
            )


# ============================================================
# F5-T4: _write_verification_entry() appends, not overwrites
# ============================================================


class TestWriteVerificationEntryAppends(unittest.TestCase):
    """F5-T4: Calling _write_verification_entry twice must append both entries."""

    def test_write_verification_entry_appends_not_overwrites(self):
        """Two calls must result in both entries present in the file (append mode)."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            agent._write_verification_entry(
                model="modelo_A",
                stage="corrigir",
                status="ok",
                details="First entry detail.",
            )
            agent._write_verification_entry(
                model="modelo_B",
                stage="analisar",
                status="fail",
                details="Second entry detail.",
            )

            report_file = Path(tmp) / "verification_report.md"
            self.assertTrue(
                report_file.exists(),
                "verification_report.md must exist after two calls to _write_verification_entry.",
            )
            content = report_file.read_text(encoding="utf-8")

            self.assertIn(
                "First entry detail.",
                content,
                "_write_verification_entry must APPEND — first entry must still be present "
                "after a second call. Got content:\n" + content,
            )
            self.assertIn(
                "Second entry detail.",
                content,
                "_write_verification_entry must APPEND — second entry must also be present. "
                "Got content:\n" + content,
            )


# ============================================================
# F5-T4: _write_verification_entry() content contains all values
# ============================================================


class TestWriteVerificationEntryContent(unittest.TestCase):
    """F5-T4: Written entry must include model, stage, status, and details values."""

    def test_write_verification_entry_contains_all_values(self):
        """File content must include model, stage, status, and details values."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            agent._write_verification_entry(
                model="modelo_especial",
                stage="etapa_verificacao",
                status="passou",
                details="Todos os alunos foram corrigidos com sucesso.",
            )

            report_file = Path(tmp) / "verification_report.md"
            content = report_file.read_text(encoding="utf-8")

            for value, label in [
                ("modelo_especial", "model"),
                ("etapa_verificacao", "stage"),
                ("passou", "status"),
                ("Todos os alunos foram corrigidos com sucesso.", "details"),
            ]:
                self.assertIn(
                    value,
                    content,
                    f"_write_verification_entry must include the `{label}` value '{value}' "
                    f"in the written content. Got content:\n{content}",
                )

    def test_written_content_is_valid_markdown(self):
        """The entry must contain at least one markdown structural element (heading or list item)."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            agent._write_verification_entry(
                model="modelo_md",
                stage="etapa_md",
                status="ok",
                details="Markdown check.",
            )

            report_file = Path(tmp) / "verification_report.md"
            content = report_file.read_text(encoding="utf-8")

            has_heading = any(line.startswith("#") for line in content.splitlines())
            has_list_item = any(
                line.lstrip().startswith("-") or line.lstrip().startswith("*")
                for line in content.splitlines()
            )
            has_bold = "**" in content
            has_separator = "---" in content

            is_valid_markdown = has_heading or has_list_item or has_bold or has_separator
            self.assertTrue(
                is_valid_markdown,
                "The content written by _write_verification_entry must be valid markdown. "
                "It must contain at least one markdown element: heading (#), list item (- or *), "
                "bold (**text**), or horizontal rule (---). "
                f"Got content:\n{content}",
            )


# ============================================================
# F5-T4: _write_verification_entry() returns Path to report file
# ============================================================


class TestWriteVerificationEntryReturnsPath(unittest.TestCase):
    """F5-T4: _write_verification_entry must return a Path pointing to the report file."""

    def test_write_verification_entry_returns_path(self):
        """_write_verification_entry must return a Path instance."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            result = agent._write_verification_entry(
                model="modelo_retorno",
                stage="etapa_retorno",
                status="ok",
                details="Checking return value.",
            )

            self.assertIsInstance(
                result,
                Path,
                "_write_verification_entry must return a Path instance. "
                f"Got type: {type(result).__name__!r}. "
                "Return the Path to the verification_report.md file.",
            )

    def test_returned_path_points_to_verification_report(self):
        """The returned Path must point to verification_report.md inside output_dir."""
        method = getattr(InvestorJourneyAgent, "_write_verification_entry", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have `_write_verification_entry` before this test can run.",
        )

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            result = agent._write_verification_entry(
                model="modelo_path",
                stage="etapa_path",
                status="ok",
                details="Checking returned path location.",
            )

            expected = Path(tmp) / "verification_report.md"
            self.assertEqual(
                result,
                expected,
                "_write_verification_entry must return the Path to "
                "`config.output_dir / 'verification_report.md'`. "
                f"Expected {expected}, got {result!r}.",
            )
            self.assertTrue(
                result.exists(),
                "The Path returned by _write_verification_entry must point to a file that "
                f"actually exists on disk. Path: {result}",
            )


if __name__ == "__main__":
    unittest.main()
