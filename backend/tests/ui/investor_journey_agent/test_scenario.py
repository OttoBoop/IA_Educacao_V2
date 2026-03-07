"""
Tests for F6-T1: Journey Scenario Script.

Verifies that scenario.py exists in the investor_journey_agent package and
exports the correct constants the journey agent needs to run the full pipeline
verification scenario across 4 AI models.

Required exports:
- MODELS: list[str]               — exactly 4 model IDs
- PIPELINE_STAGES: list[str]      — ordered pipeline stage names
- VERIFICATION_GOAL: str          — goal text for --goal flag
- CHECKLIST: list[dict]           — verification steps with id/description/category
"""

import unittest


# ============================================================
# Import check — must fail with ImportError until scenario.py exists
# ============================================================


class TestScenarioModuleImport(unittest.TestCase):
    """scenario.py must be importable from the investor_journey_agent package."""

    def test_scenario_module_can_be_imported(self):
        """Module must be importable as tests.ui.investor_journey_agent.scenario."""
        try:
            import tests.ui.investor_journey_agent.scenario as scenario  # noqa: F401
        except ImportError as e:
            self.fail(
                f"Could not import tests.ui.investor_journey_agent.scenario: {e}\n"
                "Create scenario.py in tests/ui/investor_journey_agent/ with the "
                "required MODELS, PIPELINE_STAGES, VERIFICATION_GOAL, and CHECKLIST exports."
            )


# ============================================================
# MODELS export
# ============================================================


class TestScenarioModels(unittest.TestCase):
    """MODELS must be a list of exactly 4 model IDs."""

    @classmethod
    def setUpClass(cls):
        try:
            import tests.ui.investor_journey_agent.scenario as scenario
            cls.scenario = scenario
        except ImportError:
            cls.scenario = None

    def _require_scenario(self):
        if self.scenario is None:
            self.skipTest("scenario module not importable — covered by TestScenarioModuleImport")

    def test_models_is_a_list(self):
        """MODELS must be a list."""
        self._require_scenario()
        self.assertIsInstance(
            self.scenario.MODELS,
            list,
            "MODELS must be a list. Define MODELS: list[str] = [...] in scenario.py.",
        )

    def test_models_has_exactly_four_items(self):
        """MODELS must contain exactly 4 model IDs."""
        self._require_scenario()
        self.assertEqual(
            len(self.scenario.MODELS),
            4,
            f"MODELS must have exactly 4 items (one per supported AI provider). "
            f"Currently has {len(self.scenario.MODELS)}: {self.scenario.MODELS}.",
        )

    def test_models_contains_gpt4o(self):
        """MODELS must include 'gpt-4o'."""
        self._require_scenario()
        self.assertIn(
            "gpt-4o",
            self.scenario.MODELS,
            "MODELS must include 'gpt-4o'. Add it to the MODELS list in scenario.py.",
        )

    def test_models_contains_gpt5_nano(self):
        """MODELS must include 'gpt-5-nano'."""
        self._require_scenario()
        self.assertIn(
            "gpt-5-nano",
            self.scenario.MODELS,
            "MODELS must include 'gpt-5-nano'. Add it to the MODELS list in scenario.py.",
        )

    def test_models_contains_claude_haiku(self):
        """MODELS must include 'claude-haiku-4-5-20251001'."""
        self._require_scenario()
        self.assertIn(
            "claude-haiku-4-5-20251001",
            self.scenario.MODELS,
            "MODELS must include 'claude-haiku-4-5-20251001'. Add it to MODELS in scenario.py.",
        )

    def test_models_contains_gemini_flash(self):
        """MODELS must include 'gemini-3-flash-preview'."""
        self._require_scenario()
        self.assertIn(
            "gemini-3-flash-preview",
            self.scenario.MODELS,
            "MODELS must include 'gemini-3-flash-preview'. Add it to MODELS in scenario.py.",
        )


# ============================================================
# PIPELINE_STAGES export
# ============================================================


class TestScenarioPipelineStages(unittest.TestCase):
    """PIPELINE_STAGES must list all 4 pipeline stage names in order."""

    @classmethod
    def setUpClass(cls):
        try:
            import tests.ui.investor_journey_agent.scenario as scenario
            cls.scenario = scenario
        except ImportError:
            cls.scenario = None

    def _require_scenario(self):
        if self.scenario is None:
            self.skipTest("scenario module not importable — covered by TestScenarioModuleImport")

    def test_pipeline_stages_is_a_list(self):
        """PIPELINE_STAGES must be a list."""
        self._require_scenario()
        self.assertIsInstance(
            self.scenario.PIPELINE_STAGES,
            list,
            "PIPELINE_STAGES must be a list. Define PIPELINE_STAGES: list[str] = [...] in scenario.py.",
        )

    def test_pipeline_stages_has_exactly_four_items(self):
        """PIPELINE_STAGES must contain exactly 4 stage names."""
        self._require_scenario()
        self.assertEqual(
            len(self.scenario.PIPELINE_STAGES),
            4,
            f"PIPELINE_STAGES must have exactly 4 items (one per pipeline stage). "
            f"Currently has {len(self.scenario.PIPELINE_STAGES)}: {self.scenario.PIPELINE_STAGES}.",
        )

    def test_pipeline_stages_contains_extrair_questoes(self):
        """PIPELINE_STAGES must include 'extrair_questoes'."""
        self._require_scenario()
        self.assertIn(
            "extrair_questoes",
            self.scenario.PIPELINE_STAGES,
            "PIPELINE_STAGES must include 'extrair_questoes'. Add it to PIPELINE_STAGES in scenario.py.",
        )

    def test_pipeline_stages_contains_corrigir(self):
        """PIPELINE_STAGES must include 'corrigir'."""
        self._require_scenario()
        self.assertIn(
            "corrigir",
            self.scenario.PIPELINE_STAGES,
            "PIPELINE_STAGES must include 'corrigir'. Add it to PIPELINE_STAGES in scenario.py.",
        )

    def test_pipeline_stages_contains_analisar_habilidades(self):
        """PIPELINE_STAGES must include 'analisar_habilidades'."""
        self._require_scenario()
        self.assertIn(
            "analisar_habilidades",
            self.scenario.PIPELINE_STAGES,
            "PIPELINE_STAGES must include 'analisar_habilidades'. Add it to PIPELINE_STAGES in scenario.py.",
        )

    def test_pipeline_stages_contains_gerar_relatorio(self):
        """PIPELINE_STAGES must include 'gerar_relatorio'."""
        self._require_scenario()
        self.assertIn(
            "gerar_relatorio",
            self.scenario.PIPELINE_STAGES,
            "PIPELINE_STAGES must include 'gerar_relatorio'. Add it to PIPELINE_STAGES in scenario.py.",
        )


# ============================================================
# VERIFICATION_GOAL export
# ============================================================


class TestScenarioVerificationGoal(unittest.TestCase):
    """VERIFICATION_GOAL must be a non-empty string referencing pipeline and 4 models."""

    @classmethod
    def setUpClass(cls):
        try:
            import tests.ui.investor_journey_agent.scenario as scenario
            cls.scenario = scenario
        except ImportError:
            cls.scenario = None

    def _require_scenario(self):
        if self.scenario is None:
            self.skipTest("scenario module not importable — covered by TestScenarioModuleImport")

    def test_verification_goal_is_a_string(self):
        """VERIFICATION_GOAL must be a string."""
        self._require_scenario()
        self.assertIsInstance(
            self.scenario.VERIFICATION_GOAL,
            str,
            "VERIFICATION_GOAL must be a str. Define VERIFICATION_GOAL: str = '...' in scenario.py.",
        )

    def test_verification_goal_is_non_empty(self):
        """VERIFICATION_GOAL must not be an empty string."""
        self._require_scenario()
        self.assertGreater(
            len(self.scenario.VERIFICATION_GOAL.strip()),
            0,
            "VERIFICATION_GOAL must not be empty. Provide the --goal text for the tester persona.",
        )

    def test_verification_goal_mentions_pipeline(self):
        """VERIFICATION_GOAL must contain the word 'pipeline' (case-insensitive)."""
        self._require_scenario()
        self.assertIn(
            "pipeline",
            self.scenario.VERIFICATION_GOAL.lower(),
            "VERIFICATION_GOAL must mention 'pipeline' so the tester persona knows "
            "this is a pipeline verification run. Add 'pipeline' to VERIFICATION_GOAL.",
        )

    def test_verification_goal_mentions_four_models(self):
        """VERIFICATION_GOAL must contain '4' to indicate the number of models to test."""
        self._require_scenario()
        self.assertIn(
            "4",
            self.scenario.VERIFICATION_GOAL,
            "VERIFICATION_GOAL must mention '4' (the number of models to verify). "
            "Include '4 models' or '4 AI models' in VERIFICATION_GOAL.",
        )


# ============================================================
# CHECKLIST export
# ============================================================


class TestScenarioChecklist(unittest.TestCase):
    """CHECKLIST must be a list of dicts covering all verification dimensions."""

    @classmethod
    def setUpClass(cls):
        try:
            import tests.ui.investor_journey_agent.scenario as scenario
            cls.scenario = scenario
        except ImportError:
            cls.scenario = None

    def _require_scenario(self):
        if self.scenario is None:
            self.skipTest("scenario module not importable — covered by TestScenarioModuleImport")

    def test_checklist_is_a_list(self):
        """CHECKLIST must be a list."""
        self._require_scenario()
        self.assertIsInstance(
            self.scenario.CHECKLIST,
            list,
            "CHECKLIST must be a list of dicts. Define CHECKLIST: list[dict] = [...] in scenario.py.",
        )

    def test_checklist_has_at_least_eight_items(self):
        """CHECKLIST must have at least 8 items to cover all stages + download + desempenho."""
        self._require_scenario()
        self.assertGreaterEqual(
            len(self.scenario.CHECKLIST),
            8,
            f"CHECKLIST must have at least 8 items (covering all 4 pipeline stages, "
            f"download, desempenho cascade, and validation steps). "
            f"Currently has {len(self.scenario.CHECKLIST)} items.",
        )

    def test_each_checklist_item_has_id_key(self):
        """Every CHECKLIST dict must have an 'id' key."""
        self._require_scenario()
        for i, item in enumerate(self.scenario.CHECKLIST):
            self.assertIn(
                "id",
                item,
                f"CHECKLIST[{i}] is missing the 'id' key. "
                f"Each checklist item must be a dict with keys: 'id', 'description', 'category'. "
                f"Item content: {item}",
            )

    def test_each_checklist_item_has_description_key(self):
        """Every CHECKLIST dict must have a 'description' key."""
        self._require_scenario()
        for i, item in enumerate(self.scenario.CHECKLIST):
            self.assertIn(
                "description",
                item,
                f"CHECKLIST[{i}] is missing the 'description' key. "
                f"Each checklist item must be a dict with keys: 'id', 'description', 'category'. "
                f"Item content: {item}",
            )

    def test_each_checklist_item_has_category_key(self):
        """Every CHECKLIST dict must have a 'category' key."""
        self._require_scenario()
        for i, item in enumerate(self.scenario.CHECKLIST):
            self.assertIn(
                "category",
                item,
                f"CHECKLIST[{i}] is missing the 'category' key. "
                f"Each checklist item must be a dict with keys: 'id', 'description', 'category'. "
                f"Item content: {item}",
            )

    def test_checklist_covers_pipeline_category(self):
        """At least one CHECKLIST item must have category 'pipeline'."""
        self._require_scenario()
        categories = [item.get("category") for item in self.scenario.CHECKLIST]
        self.assertIn(
            "pipeline",
            categories,
            "CHECKLIST must contain at least one item with category='pipeline'. "
            "Add pipeline stage verification steps to CHECKLIST.",
        )

    def test_checklist_covers_download_category(self):
        """At least one CHECKLIST item must have category 'download'."""
        self._require_scenario()
        categories = [item.get("category") for item in self.scenario.CHECKLIST]
        self.assertIn(
            "download",
            categories,
            "CHECKLIST must contain at least one item with category='download'. "
            "Add file download verification steps to CHECKLIST.",
        )

    def test_checklist_covers_validation_category(self):
        """At least one CHECKLIST item must have category 'validation'."""
        self._require_scenario()
        categories = [item.get("category") for item in self.scenario.CHECKLIST]
        self.assertIn(
            "validation",
            categories,
            "CHECKLIST must contain at least one item with category='validation'. "
            "Add content validation steps (origem_id chain, student name, question count) to CHECKLIST.",
        )

    def test_checklist_covers_desempenho_category(self):
        """At least one CHECKLIST item must have category 'desempenho'."""
        self._require_scenario()
        categories = [item.get("category") for item in self.scenario.CHECKLIST]
        self.assertIn(
            "desempenho",
            categories,
            "CHECKLIST must contain at least one item with category='desempenho'. "
            "Add desempenho cascade verification steps to CHECKLIST.",
        )

    def test_checklist_item_ids_are_unique(self):
        """Every CHECKLIST item 'id' must be unique."""
        self._require_scenario()
        ids = [item.get("id") for item in self.scenario.CHECKLIST if "id" in item]
        unique_ids = set(ids)
        self.assertEqual(
            len(ids),
            len(unique_ids),
            f"CHECKLIST item 'id' values must be unique. "
            f"Duplicate IDs found: {[x for x in ids if ids.count(x) > 1]}",
        )

    def test_checklist_item_ids_are_strings(self):
        """Every CHECKLIST item 'id' must be a non-empty string."""
        self._require_scenario()
        for i, item in enumerate(self.scenario.CHECKLIST):
            if "id" not in item:
                continue  # covered by test_each_checklist_item_has_id_key
            self.assertIsInstance(
                item["id"],
                str,
                f"CHECKLIST[{i}]['id'] must be a string. Got: {type(item['id']).__name__}",
            )
            self.assertGreater(
                len(item["id"].strip()),
                0,
                f"CHECKLIST[{i}]['id'] must not be empty.",
            )

    def test_checklist_item_categories_are_valid(self):
        """Every CHECKLIST item 'category' must be one of the 4 allowed values."""
        self._require_scenario()
        valid_categories = {"pipeline", "download", "validation", "desempenho"}
        for i, item in enumerate(self.scenario.CHECKLIST):
            if "category" not in item:
                continue  # covered by test_each_checklist_item_has_category_key
            self.assertIn(
                item["category"],
                valid_categories,
                f"CHECKLIST[{i}]['category'] must be one of {sorted(valid_categories)}. "
                f"Got: '{item['category']}'",
            )


if __name__ == "__main__":
    unittest.main()
