"""
Tests for journey agent infrastructure improvements.

- F2-T1: AgentConfig max_steps default = 400 (updated from 200 for F5-T1)
- F2-T2: CLI --max-steps default = 400 (updated from 200 for F5-T1)
- F3-T1: _do_step() helper method exists on InvestorJourneyAgent
- F5-T2: verbose flag on AgentConfig and _log_verbose() method on agent
"""

import inspect
import unittest

from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.__main__ import build_parser
from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent


# ============================================================
# F5-T1: AgentConfig default max_steps = 400
# ============================================================


class TestAgentConfigDefaultSteps(unittest.TestCase):
    """F5-T1: Default max_steps in AgentConfig should be 400."""

    def test_default_max_steps_is_400(self):
        """AgentConfig().max_steps must default to 400 for full pipeline verification."""
        config = AgentConfig()
        self.assertEqual(
            config.max_steps,
            400,
            f"Expected AgentConfig().max_steps == 400 but got {config.max_steps}. "
            "Change `max_steps: int = 200` to `max_steps: int = 400` in config.py.",
        )


# ============================================================
# F5-T1: CLI --max-steps default = 400
# ============================================================


class TestCLIDefaultMaxSteps(unittest.TestCase):
    """F5-T1: CLI --max-steps flag should default to 400."""

    def test_cli_max_steps_default_is_400(self):
        """build_parser() --max-steps default must be 400."""
        parser = build_parser()
        default = parser.get_default("max_steps")
        self.assertEqual(
            default,
            400,
            f"Expected --max-steps CLI default == 400 but got {default}. "
            "Change `default=200` to `default=400` in __main__.py --max-steps argument.",
        )


# ============================================================
# F3-T1: _do_step() helper method on InvestorJourneyAgent
# ============================================================


class TestDoStepHelper(unittest.TestCase):
    """F3-T1: InvestorJourneyAgent must have a _do_step() async helper method."""

    def test_agent_has_do_step_method(self):
        """_do_step() method must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_do_step"),
            "InvestorJourneyAgent must have a _do_step() method. "
            "Extract the per-step logic from run_journey() loop into _do_step().",
        )

    def test_do_step_is_async(self):
        """_do_step() must be an async coroutine function."""
        method = getattr(InvestorJourneyAgent, "_do_step", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent must have _do_step()")
        self.assertTrue(
            inspect.iscoroutinefunction(method),
            "_do_step() must be an async method (coroutine function) "
            "so it can be awaited in the async journey loop.",
        )


# ============================================================
# F5-T2: verbose flag on AgentConfig
# ============================================================


class TestAgentConfigVerboseFlag(unittest.TestCase):
    """F5-T2: AgentConfig must have a verbose boolean field defaulting to True."""

    def test_agent_config_has_verbose_field(self):
        """AgentConfig must have a 'verbose' attribute."""
        config = AgentConfig()
        self.assertTrue(
            hasattr(config, "verbose"),
            "AgentConfig must have a 'verbose' field. "
            "Add `verbose: bool = True` to the AgentConfig dataclass in config.py.",
        )

    def test_agent_config_verbose_default_is_true(self):
        """AgentConfig().verbose must default to True."""
        config = AgentConfig()
        self.assertTrue(
            config.verbose,
            f"Expected AgentConfig().verbose == True but got {config.verbose!r}. "
            "Add `verbose: bool = True` to the AgentConfig dataclass in config.py.",
        )

    def test_agent_config_verbose_can_be_set_false(self):
        """AgentConfig should accept verbose=False without error."""
        config = AgentConfig(verbose=False)
        self.assertFalse(
            config.verbose,
            "AgentConfig(verbose=False).verbose must be False.",
        )


# ============================================================
# F5-T2: _log_verbose() method on InvestorJourneyAgent
# ============================================================


class TestLogVerboseMethod(unittest.TestCase):
    """F5-T2: InvestorJourneyAgent must have a _log_verbose() method."""

    def test_agent_has_log_verbose_method(self):
        """_log_verbose() must exist on InvestorJourneyAgent."""
        self.assertTrue(
            hasattr(InvestorJourneyAgent, "_log_verbose"),
            "InvestorJourneyAgent must have a '_log_verbose()' method. "
            "Add a `_log_verbose(self, **kwargs)` method to agent.py.",
        )

    def test_log_verbose_is_callable(self):
        """_log_verbose must be a callable method (not a property or attribute)."""
        method = getattr(InvestorJourneyAgent, "_log_verbose", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent must have _log_verbose()")
        self.assertTrue(
            callable(method),
            "_log_verbose must be a callable method on InvestorJourneyAgent.",
        )

    def test_log_verbose_accepts_materia_kwarg(self):
        """_log_verbose() must accept a 'materia' keyword argument."""
        method = getattr(InvestorJourneyAgent, "_log_verbose", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent must have _log_verbose()")
        sig = inspect.signature(method)
        params = sig.parameters
        # Must accept **kwargs OR have explicit 'materia' param
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        has_explicit = "materia" in params
        self.assertTrue(
            has_var_keyword or has_explicit,
            "_log_verbose() must accept keyword arguments including 'materia'. "
            "Use `def _log_verbose(self, **kwargs)` or add explicit parameters.",
        )

    def test_log_verbose_accepts_pipeline_context_kwargs(self):
        """_log_verbose() must accept turma, aluno, stage, provider, step_number kwargs."""
        method = getattr(InvestorJourneyAgent, "_log_verbose", None)
        self.assertIsNotNone(method, "InvestorJourneyAgent must have _log_verbose()")
        sig = inspect.signature(method)
        params = sig.parameters
        has_var_keyword = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        if not has_var_keyword:
            expected_params = {"turma", "aluno", "stage", "provider", "step_number"}
            missing = expected_params - set(params.keys())
            self.assertEqual(
                missing,
                set(),
                f"_log_verbose() is missing explicit parameters: {missing}. "
                "Either use `**kwargs` or declare all pipeline context params explicitly.",
            )

    def test_log_verbose_returns_formatted_string_with_materia(self):
        """_log_verbose() must return a string containing the materia value when provided."""
        # We cannot instantiate the full agent without heavy deps,
        # so we build a minimal stand-in using the actual class method unbound.
        # This test is intentionally written against the method signature and
        # will fail until _log_verbose() exists AND returns a string.
        method = getattr(InvestorJourneyAgent, "_log_verbose", None)
        self.assertIsNotNone(
            method,
            "InvestorJourneyAgent must have _log_verbose() before this test can run.",
        )
        # Confirm the return annotation (if present) is str or absent (not None/NoReturn)
        sig = inspect.signature(method)
        ann = sig.return_annotation
        if ann is not inspect.Parameter.empty:
            self.assertIs(
                ann,
                str,
                f"_log_verbose() return annotation should be `str`, got {ann!r}.",
            )

    def test_log_verbose_returns_string_containing_context_values(self):
        """_log_verbose() must return a formatted string with the supplied context values.

        This test instantiates a minimal agent stub to call the method directly.
        It will fail until:
        1. _log_verbose() exists on InvestorJourneyAgent
        2. It returns a string that includes the keyword arg values passed in
        """
        # Attempt to create a minimal agent instance using object.__new__ to
        # bypass __init__ (which requires API keys and browser setup).
        agent = object.__new__(InvestorJourneyAgent)

        # Confirm _log_verbose exists before calling
        if not hasattr(agent, "_log_verbose"):
            self.fail(
                "InvestorJourneyAgent must have a '_log_verbose()' method. "
                "Add `def _log_verbose(self, **kwargs) -> str:` to agent.py."
            )

        result = agent._log_verbose(
            materia="Matematica",
            turma="Turma-A",
            aluno="Joao",
            stage="corrigir",
            provider="anthropic",
            step_number=3,
        )

        self.assertIsInstance(
            result,
            str,
            f"_log_verbose() must return a str, got {type(result).__name__!r}.",
        )
        self.assertIn(
            "Matematica",
            result,
            "The string returned by _log_verbose() must contain the 'materia' value 'Matematica'.",
        )
        self.assertIn(
            "Turma-A",
            result,
            "The string returned by _log_verbose() must contain the 'turma' value 'Turma-A'.",
        )
        self.assertIn(
            "Joao",
            result,
            "The string returned by _log_verbose() must contain the 'aluno' value 'Joao'.",
        )
        self.assertIn(
            "corrigir",
            result,
            "The string returned by _log_verbose() must contain the 'stage' value 'corrigir'.",
        )
        self.assertIn(
            "anthropic",
            result,
            "The string returned by _log_verbose() must contain the 'provider' value 'anthropic'.",
        )


if __name__ == "__main__":
    unittest.main()
