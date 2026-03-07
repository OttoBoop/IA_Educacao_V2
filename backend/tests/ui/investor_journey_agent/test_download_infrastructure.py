"""
Tests for F5-T3: File Download Capability.

- AgentConfig must have a `downloads_dir` field (Optional[Path], default None,
  which resolves to output_dir / "downloads")
- InvestorJourneyAgent must have a `_download_file()` async method
- `_download_file()` must accept: url (str), model (str), stage (str), student (str)
- InvestorJourneyAgent must have a `_ensure_download_dir()` method that creates
  the model/stage/student folder hierarchy under downloads_dir
"""

import inspect
import unittest
from pathlib import Path

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# AgentConfig.downloads_dir field
# ============================================================


class TestAgentConfigDownloadsDir(unittest.TestCase):
    """AgentConfig must expose a downloads_dir Optional[Path] field."""

    def test_agent_config_has_downloads_dir_field(self):
        """AgentConfig dataclass must have a `downloads_dir` attribute."""
        config = AgentConfig.__new__(AgentConfig)
        self.assertTrue(
            hasattr(AgentConfig, "__dataclass_fields__")
            and "downloads_dir" in AgentConfig.__dataclass_fields__,
            "AgentConfig is missing `downloads_dir` field. "
            "Add `downloads_dir: Optional[Path] = None` to AgentConfig in config.py.",
        )

    def test_downloads_dir_defaults_to_none_before_post_init(self):
        """The declared default for downloads_dir must be None (post_init may resolve it)."""
        field_meta = AgentConfig.__dataclass_fields__.get("downloads_dir")
        self.assertIsNotNone(
            field_meta,
            "AgentConfig is missing `downloads_dir` field entirely.",
        )
        # The raw default (before __post_init__) should be None
        import dataclasses
        default = field_meta.default
        self.assertIs(
            default,
            None,
            "downloads_dir field must declare `= None` as its default value. "
            f"Got: {default!r}",
        )

    def test_downloads_dir_resolves_to_output_dir_downloads_when_none(self):
        """When downloads_dir is None, __post_init__ must resolve it to output_dir / 'downloads'."""
        config = AgentConfig(output_dir=Path("/tmp/test_journey_output"))
        self.assertEqual(
            config.downloads_dir,
            Path("/tmp/test_journey_output") / "downloads",
            "When downloads_dir is None, AgentConfig.__post_init__ must set it to "
            "`output_dir / 'downloads'`. "
            "Add this logic to __post_init__() in config.py.",
        )

    def test_downloads_dir_can_be_set_explicitly(self):
        """When downloads_dir is explicitly provided, it must be kept as-is."""
        custom = Path("/tmp/my_custom_downloads")
        config = AgentConfig(downloads_dir=custom)
        self.assertEqual(
            config.downloads_dir,
            custom,
            "When downloads_dir is explicitly set, AgentConfig must not overwrite it. "
            f"Expected {custom}, got {config.downloads_dir!r}.",
        )

    def test_downloads_dir_is_path_instance(self):
        """downloads_dir must be a Path instance after construction (not a str)."""
        config = AgentConfig(output_dir=Path("/tmp/test_journey_output"))
        self.assertIsInstance(
            config.downloads_dir,
            Path,
            "downloads_dir must be a Path instance after __post_init__ runs. "
            f"Got type: {type(config.downloads_dir).__name__}",
        )


# ============================================================
# InvestorJourneyAgent._download_file() method
# ============================================================


class TestAgentHasDownloadFileMethod(unittest.TestCase):
    """InvestorJourneyAgent must expose a `_download_file()` async method."""

    def test_agent_has_download_file_method(self):
        """InvestorJourneyAgent must have a `_download_file` attribute."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_download_file"),
            "InvestorJourneyAgent is missing `_download_file` method. "
            "Add `async def _download_file(self, url, model, stage, student)` to agent.py.",
        )

    def test_download_file_is_coroutine(self):
        """_download_file must be an async (coroutine) method."""
        method = getattr(InvestorJourneyAgent, "_download_file", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent is missing `_download_file`.")
        self.assertTrue(
            inspect.iscoroutinefunction(method),
            "_download_file must be declared with `async def`, not plain `def`. "
            "File downloads may involve async I/O.",
        )

    def test_download_file_accepts_url_model_stage_student(self):
        """_download_file must accept positional args: url, model, stage, student."""
        method = getattr(InvestorJourneyAgent, "_download_file", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent is missing `_download_file`.")
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        # 'self' is first; the remaining four must exist
        for expected_param in ("url", "model", "stage", "student"):
            self.assertIn(
                expected_param,
                params,
                f"_download_file must accept a `{expected_param}` parameter. "
                f"Current signature: {sig}. "
                "Expected: `async def _download_file(self, url: str, model: str, stage: str, student: str)`",
            )

    def test_download_file_has_exactly_four_required_params_plus_self(self):
        """_download_file must have exactly self + 4 required params (url, model, stage, student)."""
        method = getattr(InvestorJourneyAgent, "_download_file", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent is missing `_download_file`.")
        sig = inspect.signature(method)
        params = [
            name for name, p in sig.parameters.items()
            if p.default is inspect.Parameter.empty
        ]
        # self + url + model + stage + student = 5 required params total
        self.assertEqual(
            len(params),
            5,
            f"_download_file must have exactly 5 parameters (self, url, model, stage, student), "
            f"no more, no less. Current required params: {params}",
        )


# ============================================================
# InvestorJourneyAgent._ensure_download_dir() method
# ============================================================


class TestAgentHasEnsureDownloadDirMethod(unittest.TestCase):
    """InvestorJourneyAgent must have a `_ensure_download_dir()` method."""

    def test_agent_has_ensure_download_dir_method(self):
        """InvestorJourneyAgent must have a `_ensure_download_dir` attribute."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_ensure_download_dir"),
            "InvestorJourneyAgent is missing `_ensure_download_dir` method. "
            "Add `def _ensure_download_dir(self, model, stage, student) -> Path` to agent.py.",
        )

    def test_ensure_download_dir_accepts_model_stage_student(self):
        """_ensure_download_dir must accept model, stage, student parameters."""
        method = getattr(InvestorJourneyAgent, "_ensure_download_dir", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent is missing `_ensure_download_dir`.")
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        for expected_param in ("model", "stage", "student"):
            self.assertIn(
                expected_param,
                params,
                f"_ensure_download_dir must accept a `{expected_param}` parameter. "
                f"Current signature: {sig}. "
                "Expected: `def _ensure_download_dir(self, model: str, stage: str, student: str) -> Path`",
            )

    def test_ensure_download_dir_creates_hierarchy(self):
        """_ensure_download_dir must create output_dir/downloads/model/stage/student/ hierarchy."""
        import tempfile
        import os

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            result_path = agent._ensure_download_dir(
                model="modelo_A",
                stage="etapa_1",
                student="joao_silva",
            )

            expected = Path(tmp) / "downloads" / "modelo_A" / "etapa_1" / "joao_silva"
            self.assertEqual(
                result_path,
                expected,
                f"_ensure_download_dir must return the path "
                f"`output_dir/downloads/model/stage/student/`. "
                f"Expected {expected}, got {result_path!r}.",
            )
            self.assertTrue(
                expected.exists(),
                f"_ensure_download_dir must CREATE the directory hierarchy on disk. "
                f"The path {expected} does not exist after calling _ensure_download_dir().",
            )
            self.assertTrue(
                expected.is_dir(),
                f"The path created by _ensure_download_dir must be a directory, not a file.",
            )

    def test_ensure_download_dir_returns_path_instance(self):
        """_ensure_download_dir must return a Path object."""
        import tempfile

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            result = agent._ensure_download_dir(
                model="modelo_X",
                stage="etapa_2",
                student="maria",
            )
            self.assertIsInstance(
                result,
                Path,
                "_ensure_download_dir must return a Path instance. "
                f"Got type: {type(result).__name__}",
            )

    def test_ensure_download_dir_is_idempotent(self):
        """Calling _ensure_download_dir twice must not raise an error (mkdir exist_ok)."""
        import tempfile

        agent = InvestorJourneyAgent.__new__(InvestorJourneyAgent)

        with tempfile.TemporaryDirectory() as tmp:
            config = AgentConfig(output_dir=Path(tmp))
            agent.config = config

            # Call twice — must not raise FileExistsError
            try:
                agent._ensure_download_dir(model="m", stage="s", student="st")
                agent._ensure_download_dir(model="m", stage="s", student="st")
            except Exception as e:
                self.fail(
                    f"_ensure_download_dir raised {type(e).__name__} on second call: {e}. "
                    "Use `mkdir(parents=True, exist_ok=True)` to make it idempotent.",
                )


if __name__ == "__main__":
    unittest.main()
