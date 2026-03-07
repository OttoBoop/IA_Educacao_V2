"""
Tests for cascade_steps.py — F6-T3: Desempenho Cascade Verification Steps.

Verifies that the module defines the structural constants needed to drive
desempenho cascade verification: when materia-level desempenho is triggered,
it should auto-create tarefa and turma reports.
"""

import unittest


class TestCascadeStepsImport(unittest.TestCase):
    """The cascade_steps module must be importable."""

    def test_module_can_be_imported(self):
        """cascade_steps can be imported from the investor_journey_agent package."""
        from tests.ui.investor_journey_agent import cascade_steps  # noqa: F401


class TestCascadeLevels(unittest.TestCase):
    """CASCADE_LEVELS must be an ordered list of the three report levels."""

    def setUp(self):
        from tests.ui.investor_journey_agent.cascade_steps import CASCADE_LEVELS
        self.levels = CASCADE_LEVELS

    def test_cascade_levels_is_list(self):
        """CASCADE_LEVELS must be a list."""
        self.assertIsInstance(self.levels, list)

    def test_cascade_levels_has_exactly_three_items(self):
        """CASCADE_LEVELS must contain exactly 3 items."""
        self.assertEqual(
            len(self.levels),
            3,
            f"Expected 3 levels, got {len(self.levels)}: {self.levels}",
        )

    def test_cascade_levels_contains_tarefa(self):
        """CASCADE_LEVELS must include 'tarefa'."""
        self.assertIn("tarefa", self.levels)

    def test_cascade_levels_contains_turma(self):
        """CASCADE_LEVELS must include 'turma'."""
        self.assertIn("turma", self.levels)

    def test_cascade_levels_contains_materia(self):
        """CASCADE_LEVELS must include 'materia'."""
        self.assertIn("materia", self.levels)

    def test_cascade_levels_correct_order(self):
        """CASCADE_LEVELS must be ordered: ['tarefa', 'turma', 'materia']."""
        self.assertEqual(
            self.levels,
            ["tarefa", "turma", "materia"],
            "Order must be tarefa → turma → materia (ascending aggregation level).",
        )


class TestCascadeStepsList(unittest.TestCase):
    """CASCADE_STEPS must be a non-trivial list of step dicts."""

    def setUp(self):
        from tests.ui.investor_journey_agent.cascade_steps import CASCADE_STEPS
        self.steps = CASCADE_STEPS

    def test_cascade_steps_is_list(self):
        """CASCADE_STEPS must be a list."""
        self.assertIsInstance(self.steps, list)

    def test_cascade_steps_has_at_least_four_items(self):
        """CASCADE_STEPS must contain at least 4 step definitions."""
        self.assertGreaterEqual(
            len(self.steps),
            4,
            f"Expected at least 4 steps, got {len(self.steps)}.",
        )


class TestCascadeStepStructure(unittest.TestCase):
    """Each step in CASCADE_STEPS must have the required keys."""

    REQUIRED_KEYS = {"step_id", "action", "level", "verify", "expected_outputs"}

    def setUp(self):
        from tests.ui.investor_journey_agent.cascade_steps import CASCADE_STEPS
        self.steps = CASCADE_STEPS

    def test_every_step_has_step_id(self):
        """Every step must have a 'step_id' key."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                self.assertIn("step_id", step, f"Step {i} missing 'step_id'.")

    def test_every_step_has_action(self):
        """Every step must have an 'action' key."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                self.assertIn("action", step, f"Step {i} missing 'action'.")

    def test_every_step_has_level(self):
        """Every step must have a 'level' key."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                self.assertIn("level", step, f"Step {i} missing 'level'.")

    def test_every_step_has_verify(self):
        """Every step must have a 'verify' key."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                self.assertIn("verify", step, f"Step {i} missing 'verify'.")

    def test_every_step_has_expected_outputs(self):
        """Every step must have an 'expected_outputs' key."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                self.assertIn(
                    "expected_outputs", step, f"Step {i} missing 'expected_outputs'."
                )

    def test_all_required_keys_present_in_every_step(self):
        """Every step must have ALL required keys at once."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                missing = self.REQUIRED_KEYS - set(step.keys())
                self.assertEqual(
                    missing,
                    set(),
                    f"Step {i} (id={step.get('step_id', '?')}) missing keys: {missing}",
                )


class TestCascadeStepValues(unittest.TestCase):
    """Step field values must be semantically valid."""

    def setUp(self):
        from tests.ui.investor_journey_agent.cascade_steps import (
            CASCADE_LEVELS,
            CASCADE_STEPS,
        )
        self.steps = CASCADE_STEPS
        self.levels = CASCADE_LEVELS

    def test_every_step_level_is_in_cascade_levels(self):
        """Every step's 'level' value must be one of CASCADE_LEVELS."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i, step_id=step.get("step_id")):
                self.assertIn(
                    step["level"],
                    self.levels,
                    f"Step '{step.get('step_id')}' has level '{step['level']}' "
                    f"which is not in CASCADE_LEVELS {self.levels}.",
                )

    def test_every_step_expected_outputs_contains_json_or_pdf(self):
        """Every step's 'expected_outputs' must contain at least 'json' or 'pdf'."""
        valid_outputs = {"json", "pdf"}
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i, step_id=step.get("step_id")):
                outputs = step.get("expected_outputs", [])
                self.assertIsInstance(
                    outputs,
                    list,
                    f"Step '{step.get('step_id')}' expected_outputs must be a list.",
                )
                overlap = valid_outputs & set(outputs)
                self.assertGreater(
                    len(overlap),
                    0,
                    f"Step '{step.get('step_id')}' expected_outputs {outputs} "
                    "must contain at least one of ['json', 'pdf'].",
                )

    def test_step_ids_are_unique(self):
        """Every step must have a unique step_id."""
        ids = [step.get("step_id") for step in self.steps]
        self.assertEqual(
            len(ids),
            len(set(ids)),
            f"Duplicate step_ids found: {[x for x in ids if ids.count(x) > 1]}",
        )

    def test_step_ids_are_strings(self):
        """Every step_id must be a non-empty string."""
        for i, step in enumerate(self.steps):
            with self.subTest(step_index=i):
                self.assertIsInstance(step.get("step_id"), str)
                self.assertGreater(len(step["step_id"]), 0)


class TestExpectedReportsPerLevel(unittest.TestCase):
    """EXPECTED_REPORTS_PER_LEVEL must map each level to a config dict."""

    def setUp(self):
        from tests.ui.investor_journey_agent.cascade_steps import (
            CASCADE_LEVELS,
            EXPECTED_REPORTS_PER_LEVEL,
        )
        self.reports = EXPECTED_REPORTS_PER_LEVEL
        self.levels = CASCADE_LEVELS

    def test_expected_reports_per_level_is_dict(self):
        """EXPECTED_REPORTS_PER_LEVEL must be a dict."""
        self.assertIsInstance(self.reports, dict)

    def test_all_three_levels_present(self):
        """EXPECTED_REPORTS_PER_LEVEL must have entries for all 3 levels."""
        for level in self.levels:
            with self.subTest(level=level):
                self.assertIn(
                    level,
                    self.reports,
                    f"EXPECTED_REPORTS_PER_LEVEL missing entry for level '{level}'.",
                )

    def test_materia_auto_creates_includes_tarefa(self):
        """'materia' level must auto-create 'tarefa' reports."""
        auto_creates = self.reports.get("materia", {}).get("auto_creates", [])
        self.assertIn(
            "tarefa",
            auto_creates,
            f"'materia' auto_creates {auto_creates} must include 'tarefa'.",
        )

    def test_materia_auto_creates_includes_turma(self):
        """'materia' level must auto-create 'turma' reports."""
        auto_creates = self.reports.get("materia", {}).get("auto_creates", [])
        self.assertIn(
            "turma",
            auto_creates,
            f"'materia' auto_creates {auto_creates} must include 'turma'.",
        )

    def test_all_levels_have_must_have_pdf_true(self):
        """All levels must have 'must_have_pdf' = True."""
        for level in self.levels:
            with self.subTest(level=level):
                config = self.reports.get(level, {})
                self.assertIn(
                    "must_have_pdf",
                    config,
                    f"Level '{level}' missing 'must_have_pdf' key.",
                )
                self.assertTrue(
                    config["must_have_pdf"],
                    f"Level '{level}' must_have_pdf must be True, got {config['must_have_pdf']}.",
                )

    def test_all_levels_have_expected_count_at_least_one(self):
        """All levels must have 'expected_count' >= 1."""
        for level in self.levels:
            with self.subTest(level=level):
                config = self.reports.get(level, {})
                self.assertIn(
                    "expected_count",
                    config,
                    f"Level '{level}' missing 'expected_count' key.",
                )
                self.assertGreaterEqual(
                    config["expected_count"],
                    1,
                    f"Level '{level}' expected_count must be >= 1, got {config['expected_count']}.",
                )

    def test_all_levels_have_auto_creates_key(self):
        """All levels must have an 'auto_creates' key (list, may be empty for leaf levels)."""
        for level in self.levels:
            with self.subTest(level=level):
                config = self.reports.get(level, {})
                self.assertIn(
                    "auto_creates",
                    config,
                    f"Level '{level}' missing 'auto_creates' key.",
                )
                self.assertIsInstance(
                    config["auto_creates"],
                    list,
                    f"Level '{level}' auto_creates must be a list.",
                )


if __name__ == "__main__":
    unittest.main()
