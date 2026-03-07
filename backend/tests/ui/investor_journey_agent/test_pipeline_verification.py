"""
Tests for F6-T4: Integration module — pipeline_verification.py.

Verifies that pipeline_verification.py integrates the three source modules:
- scenario.py        (MODELS, PIPELINE_STAGES, VERIFICATION_GOAL, CHECKLIST)
- validation_rules.py (STAGE_RULES, validate_stage_output)
- cascade_steps.py   (CASCADE_LEVELS, CASCADE_STEPS, EXPECTED_REPORTS_PER_LEVEL)

Required exports from pipeline_verification.py:
- build_verification_goal()         -> str
- build_full_checklist()            -> list[dict]
- validate_pipeline_outputs(outputs) -> dict
- generate_verification_report(results) -> str
"""

import unittest


# ============================================================
# Import check — must fail with ImportError until pipeline_verification.py exists
# ============================================================


class TestPipelineVerificationModuleImport(unittest.TestCase):
    """pipeline_verification.py must be importable from the investor_journey_agent package."""

    def test_pipeline_verification_module_can_be_imported(self):
        """Module must be importable as tests.ui.investor_journey_agent.pipeline_verification."""
        try:
            import tests.ui.investor_journey_agent.pipeline_verification as pv  # noqa: F401
        except ImportError as e:
            self.fail(
                f"Could not import tests.ui.investor_journey_agent.pipeline_verification: {e}\n"
                "Create pipeline_verification.py in tests/ui/investor_journey_agent/ with the "
                "required build_verification_goal, build_full_checklist, "
                "validate_pipeline_outputs, and generate_verification_report exports."
            )


# ============================================================
# Shared setup mixin
# ============================================================


class _PipelineVerificationBase(unittest.TestCase):
    """Base class that imports the module once and skips tests if unavailable."""

    @classmethod
    def setUpClass(cls):
        try:
            import tests.ui.investor_journey_agent.pipeline_verification as pv
            cls.pv = pv
        except ImportError:
            cls.pv = None

    def _require_module(self):
        if self.pv is None:
            self.skipTest(
                "pipeline_verification module not importable — covered by "
                "TestPipelineVerificationModuleImport"
            )


# ============================================================
# build_verification_goal()
# ============================================================


class TestBuildVerificationGoal(_PipelineVerificationBase):
    """build_verification_goal() must return a comprehensive goal string."""

    def test_function_exists(self):
        """build_verification_goal must be a callable on the module."""
        self._require_module()
        self.assertTrue(
            callable(getattr(self.pv, "build_verification_goal", None)),
            "pipeline_verification must expose a callable 'build_verification_goal'. "
            "Define: def build_verification_goal() -> str: ...",
        )

    def test_returns_a_string(self):
        """build_verification_goal() must return a str."""
        self._require_module()
        result = self.pv.build_verification_goal()
        self.assertIsInstance(
            result,
            str,
            f"build_verification_goal() must return a str. Got: {type(result).__name__}",
        )

    def test_returns_non_empty_string(self):
        """build_verification_goal() must not return an empty string."""
        self._require_module()
        result = self.pv.build_verification_goal()
        self.assertGreater(
            len(result.strip()),
            0,
            "build_verification_goal() returned an empty string. "
            "It must combine VERIFICATION_GOAL with CHECKLIST summary.",
        )

    def test_includes_all_four_model_names(self):
        """build_verification_goal() must reference all 4 model names from scenario.MODELS."""
        self._require_module()
        result = self.pv.build_verification_goal()
        expected_models = [
            "gpt-4o",
            "gpt-5-nano",
            "claude-haiku-4-5-20251001",
            "gemini-3-flash-preview",
        ]
        for model in expected_models:
            self.assertIn(
                model,
                result,
                f"build_verification_goal() result must include the model name '{model}'. "
                f"It should pull model names from scenario.MODELS.",
            )

    def test_includes_all_four_pipeline_stages(self):
        """build_verification_goal() must reference all 4 pipeline stage names."""
        self._require_module()
        result = self.pv.build_verification_goal()
        expected_stages = [
            "extrair_questoes",
            "corrigir",
            "analisar_habilidades",
            "gerar_relatorio",
        ]
        for stage in expected_stages:
            self.assertIn(
                stage,
                result,
                f"build_verification_goal() result must include the pipeline stage '{stage}'. "
                f"It should pull stage names from scenario.PIPELINE_STAGES.",
            )

    def test_references_desempenho_cascade(self):
        """build_verification_goal() must mention 'desempenho' or 'cascade'."""
        self._require_module()
        result = self.pv.build_verification_goal().lower()
        self.assertTrue(
            "desempenho" in result or "cascade" in result,
            "build_verification_goal() must reference desempenho cascade. "
            "Include content about cascade_steps.py in the goal string.",
        )

    def test_longer_than_verification_goal_alone(self):
        """build_verification_goal() must return more than just VERIFICATION_GOAL verbatim."""
        self._require_module()
        import tests.ui.investor_journey_agent.scenario as scenario

        result = self.pv.build_verification_goal()
        # The integration function should add checklist summary, making it longer
        self.assertGreater(
            len(result),
            len(scenario.VERIFICATION_GOAL),
            "build_verification_goal() must combine VERIFICATION_GOAL with additional content "
            "(e.g., a CHECKLIST summary). The result is identical to VERIFICATION_GOAL — "
            "it must be enriched with extra information.",
        )


# ============================================================
# build_full_checklist()
# ============================================================


class TestBuildFullChecklist(_PipelineVerificationBase):
    """build_full_checklist() must merge CHECKLIST from scenario.py with CASCADE_STEPS."""

    def test_function_exists(self):
        """build_full_checklist must be a callable on the module."""
        self._require_module()
        self.assertTrue(
            callable(getattr(self.pv, "build_full_checklist", None)),
            "pipeline_verification must expose a callable 'build_full_checklist'. "
            "Define: def build_full_checklist() -> list[dict]: ...",
        )

    def test_returns_a_list(self):
        """build_full_checklist() must return a list."""
        self._require_module()
        result = self.pv.build_full_checklist()
        self.assertIsInstance(
            result,
            list,
            f"build_full_checklist() must return a list. Got: {type(result).__name__}",
        )

    def test_total_count_equals_checklist_plus_cascade_steps(self):
        """Result length must equal len(CHECKLIST) + len(CASCADE_STEPS)."""
        self._require_module()
        import tests.ui.investor_journey_agent.scenario as scenario
        import tests.ui.investor_journey_agent.cascade_steps as cascade_steps

        result = self.pv.build_full_checklist()
        expected_count = len(scenario.CHECKLIST) + len(cascade_steps.CASCADE_STEPS)
        self.assertEqual(
            len(result),
            expected_count,
            f"build_full_checklist() returned {len(result)} items but expected {expected_count} "
            f"(scenario.CHECKLIST={len(scenario.CHECKLIST)} + "
            f"cascade_steps.CASCADE_STEPS={len(cascade_steps.CASCADE_STEPS)}). "
            "Merge both lists into the result.",
        )

    def test_every_item_has_id_key(self):
        """Every item in the result must have an 'id' key."""
        self._require_module()
        result = self.pv.build_full_checklist()
        for i, item in enumerate(result):
            self.assertIn(
                "id",
                item,
                f"build_full_checklist() result[{i}] is missing the 'id' key. "
                f"Every item must have 'id', 'description', 'category'. Item: {item}",
            )

    def test_every_item_has_description_key(self):
        """Every item in the result must have a 'description' key."""
        self._require_module()
        result = self.pv.build_full_checklist()
        for i, item in enumerate(result):
            self.assertIn(
                "description",
                item,
                f"build_full_checklist() result[{i}] is missing the 'description' key. "
                f"Every item must have 'id', 'description', 'category'. Item: {item}",
            )

    def test_every_item_has_category_key(self):
        """Every item in the result must have a 'category' key."""
        self._require_module()
        result = self.pv.build_full_checklist()
        for i, item in enumerate(result):
            self.assertIn(
                "category",
                item,
                f"build_full_checklist() result[{i}] is missing the 'category' key. "
                f"Every item must have 'id', 'description', 'category'. Item: {item}",
            )

    def test_cascade_steps_mapped_to_desempenho_cascade_category(self):
        """Items derived from CASCADE_STEPS must have category='desempenho_cascade'."""
        self._require_module()
        import tests.ui.investor_journey_agent.cascade_steps as cascade_steps

        result = self.pv.build_full_checklist()
        cascade_ids = {step["step_id"] for step in cascade_steps.CASCADE_STEPS}
        cascade_items = [
            item for item in result if item.get("id") in cascade_ids
        ]
        self.assertEqual(
            len(cascade_items),
            len(cascade_steps.CASCADE_STEPS),
            f"Expected {len(cascade_steps.CASCADE_STEPS)} items with IDs from CASCADE_STEPS "
            f"({sorted(cascade_ids)}) in the full checklist. "
            f"Found {len(cascade_items)}. Map each CASCADE_STEPS entry to a checklist dict "
            "keeping the step_id as 'id'.",
        )
        for item in cascade_items:
            self.assertEqual(
                item.get("category"),
                "desempenho_cascade",
                f"Item with id='{item.get('id')}' derived from CASCADE_STEPS must have "
                f"category='desempenho_cascade'. Got: '{item.get('category')}'",
            )

    def test_all_ids_are_unique(self):
        """All item 'id' values across the combined list must be unique."""
        self._require_module()
        result = self.pv.build_full_checklist()
        ids = [item.get("id") for item in result if "id" in item]
        unique_ids = set(ids)
        self.assertEqual(
            len(ids),
            len(unique_ids),
            f"build_full_checklist() has duplicate 'id' values. "
            f"Duplicates: {[x for x in ids if ids.count(x) > 1]}. "
            "All IDs across CHECKLIST and CASCADE_STEPS must be unique.",
        )

    def test_scenario_checklist_items_preserved(self):
        """All original CHECKLIST items from scenario.py must appear in the result."""
        self._require_module()
        import tests.ui.investor_journey_agent.scenario as scenario

        result = self.pv.build_full_checklist()
        result_ids = {item.get("id") for item in result}
        for item in scenario.CHECKLIST:
            self.assertIn(
                item["id"],
                result_ids,
                f"build_full_checklist() is missing scenario CHECKLIST item id='{item['id']}'. "
                "All original CHECKLIST items must be included in the merged result.",
            )


# ============================================================
# validate_pipeline_outputs()
# ============================================================


class TestValidatePipelineOutputs(_PipelineVerificationBase):
    """validate_pipeline_outputs() must delegate to validate_stage_output per stage."""

    def test_function_exists(self):
        """validate_pipeline_outputs must be a callable on the module."""
        self._require_module()
        self.assertTrue(
            callable(getattr(self.pv, "validate_pipeline_outputs", None)),
            "pipeline_verification must expose a callable 'validate_pipeline_outputs'. "
            "Define: def validate_pipeline_outputs(outputs: dict) -> dict: ...",
        )

    def test_returns_a_dict(self):
        """validate_pipeline_outputs() must return a dict."""
        self._require_module()
        result = self.pv.validate_pipeline_outputs({})
        self.assertIsInstance(
            result,
            dict,
            f"validate_pipeline_outputs() must return a dict. Got: {type(result).__name__}",
        )

    def test_result_has_valid_key(self):
        """Result dict must have a top-level 'valid' key."""
        self._require_module()
        result = self.pv.validate_pipeline_outputs({})
        self.assertIn(
            "valid",
            result,
            "validate_pipeline_outputs() result must have a 'valid' key (bool). "
            "Return: {'valid': bool, 'results': {...}}",
        )

    def test_result_has_results_key(self):
        """Result dict must have a top-level 'results' key."""
        self._require_module()
        result = self.pv.validate_pipeline_outputs({})
        self.assertIn(
            "results",
            result,
            "validate_pipeline_outputs() result must have a 'results' key (dict). "
            "Return: {'valid': bool, 'results': {...}}",
        )

    def test_empty_outputs_returns_valid_true(self):
        """An empty outputs dict means no stages to validate — overall valid should be True."""
        self._require_module()
        result = self.pv.validate_pipeline_outputs({})
        self.assertTrue(
            result["valid"],
            "validate_pipeline_outputs({}) must return valid=True when there are no stages. "
            "No failing stages means overall result is valid.",
        )

    def test_valid_stage_output_passes(self):
        """A stage with all required fields and adequate PDF size must pass."""
        self._require_module()
        outputs = {
            "extrair_questoes": {
                "json": {"questoes": ["q1", "q2"], "total_questoes": 2},
                "pdf_size": 5000,
            }
        }
        result = self.pv.validate_pipeline_outputs(outputs)
        self.assertIn(
            "extrair_questoes",
            result["results"],
            "validate_pipeline_outputs() result['results'] must include 'extrair_questoes' "
            "when it is present in the inputs.",
        )
        stage_result = result["results"]["extrair_questoes"]
        self.assertTrue(
            stage_result.get("valid"),
            f"extrair_questoes with valid JSON fields and adequate PDF size must pass validation. "
            f"Got: {stage_result}",
        )

    def test_missing_json_field_makes_stage_fail(self):
        """A stage missing a required JSON field must fail."""
        self._require_module()
        outputs = {
            "extrair_questoes": {
                "json": {"questoes": ["q1"]},  # missing 'total_questoes'
                "pdf_size": 5000,
            }
        }
        result = self.pv.validate_pipeline_outputs(outputs)
        stage_result = result["results"]["extrair_questoes"]
        self.assertFalse(
            stage_result.get("valid"),
            "extrair_questoes missing required field 'total_questoes' must fail validation. "
            f"Got: {stage_result}",
        )
        self.assertIsInstance(
            stage_result.get("errors"),
            list,
            "Failed stage result must include an 'errors' list.",
        )
        self.assertGreater(
            len(stage_result["errors"]),
            0,
            "Failed stage result 'errors' list must not be empty.",
        )

    def test_pdf_too_small_makes_stage_fail(self):
        """A stage with a PDF below the minimum size must fail."""
        self._require_module()
        outputs = {
            "extrair_questoes": {
                "json": {"questoes": ["q1"], "total_questoes": 1},
                "pdf_size": 10,  # below 1000 byte minimum
            }
        }
        result = self.pv.validate_pipeline_outputs(outputs)
        stage_result = result["results"]["extrair_questoes"]
        self.assertFalse(
            stage_result.get("valid"),
            "extrair_questoes with pdf_size=10 (below 1000 minimum) must fail validation. "
            f"Got: {stage_result}",
        )

    def test_any_failing_stage_makes_overall_valid_false(self):
        """If any stage fails, the top-level 'valid' must be False."""
        self._require_module()
        outputs = {
            "extrair_questoes": {
                "json": {"questoes": ["q1"]},  # missing 'total_questoes'
                "pdf_size": 5000,
            }
        }
        result = self.pv.validate_pipeline_outputs(outputs)
        self.assertFalse(
            result["valid"],
            "validate_pipeline_outputs() must return overall valid=False when any stage fails. "
            f"Got: {result}",
        )

    def test_all_stages_passing_makes_overall_valid_true(self):
        """If all stages pass, the top-level 'valid' must be True."""
        self._require_module()
        outputs = {
            "extrair_questoes": {
                "json": {"questoes": ["q1", "q2"], "total_questoes": 2},
                "pdf_size": 5000,
            },
            "corrigir": {
                "json": {"alunos": ["Ana"], "notas": [8.5], "gabarito": ["A"]},
                "pdf_size": 3000,
            },
        }
        result = self.pv.validate_pipeline_outputs(outputs)
        self.assertTrue(
            result["valid"],
            "validate_pipeline_outputs() must return overall valid=True when all stages pass. "
            f"Got: {result}",
        )

    def test_unknown_stage_is_skipped_not_raised(self):
        """An unknown stage key in outputs must be skipped, not raise an exception."""
        self._require_module()
        outputs = {
            "nonexistent_stage": {
                "json": {"foo": "bar"},
                "pdf_size": 999,
            }
        }
        try:
            result = self.pv.validate_pipeline_outputs(outputs)
        except Exception as e:
            self.fail(
                f"validate_pipeline_outputs() raised {type(e).__name__} for an unknown stage. "
                "Unknown stages must be silently skipped, not cause exceptions."
            )
        self.assertNotIn(
            "nonexistent_stage",
            result["results"],
            "Unknown stages must be omitted from result['results'] (skipped, not validated).",
        )

    def test_each_stage_result_has_valid_and_errors_keys(self):
        """Each per-stage result must have 'valid' (bool) and 'errors' (list) keys."""
        self._require_module()
        outputs = {
            "extrair_questoes": {
                "json": {"questoes": [], "total_questoes": 0},
                "pdf_size": 2000,
            }
        }
        result = self.pv.validate_pipeline_outputs(outputs)
        stage_result = result["results"].get("extrair_questoes", {})
        self.assertIn(
            "valid",
            stage_result,
            "Per-stage result must have 'valid' key.",
        )
        self.assertIn(
            "errors",
            stage_result,
            "Per-stage result must have 'errors' key.",
        )
        self.assertIsInstance(
            stage_result["errors"],
            list,
            "Per-stage 'errors' must be a list.",
        )

    def test_delegates_to_validate_stage_output(self):
        """validate_pipeline_outputs() must use validation_rules.validate_stage_output internally."""
        self._require_module()
        # Verify that passing the same valid data produces the same outcome
        # as calling validate_stage_output directly from validation_rules.
        import tests.ui.investor_journey_agent.validation_rules as vr

        json_content = {"questoes": ["q1"], "total_questoes": 1}
        pdf_size = 2000
        direct_result = vr.validate_stage_output("extrair_questoes", json_content, pdf_size)

        outputs = {"extrair_questoes": {"json": json_content, "pdf_size": pdf_size}}
        pipeline_result = self.pv.validate_pipeline_outputs(outputs)
        stage_result = pipeline_result["results"]["extrair_questoes"]

        self.assertEqual(
            stage_result["valid"],
            direct_result["valid"],
            "validate_pipeline_outputs() stage result['valid'] must match "
            "validation_rules.validate_stage_output() for the same inputs. "
            "Ensure you delegate to validate_stage_output internally.",
        )


# ============================================================
# generate_verification_report()
# ============================================================


class TestGenerateVerificationReport(_PipelineVerificationBase):
    """generate_verification_report() must produce a markdown summary table."""

    @classmethod
    def _make_all_pass_results(cls):
        return {
            "valid": True,
            "results": {
                "extrair_questoes": {"valid": True, "errors": []},
                "corrigir": {"valid": True, "errors": []},
            },
        }

    @classmethod
    def _make_partial_fail_results(cls):
        return {
            "valid": False,
            "results": {
                "extrair_questoes": {"valid": True, "errors": []},
                "corrigir": {
                    "valid": False,
                    "errors": ["Missing required JSON field 'gabarito'"],
                },
            },
        }

    def test_function_exists(self):
        """generate_verification_report must be a callable on the module."""
        self._require_module()
        self.assertTrue(
            callable(getattr(self.pv, "generate_verification_report", None)),
            "pipeline_verification must expose a callable 'generate_verification_report'. "
            "Define: def generate_verification_report(results: dict) -> str: ...",
        )

    def test_returns_a_string(self):
        """generate_verification_report() must return a str."""
        self._require_module()
        result = self.pv.generate_verification_report(self._make_all_pass_results())
        self.assertIsInstance(
            result,
            str,
            f"generate_verification_report() must return a str. Got: {type(result).__name__}",
        )

    def test_returns_non_empty_string(self):
        """generate_verification_report() must not return an empty string."""
        self._require_module()
        result = self.pv.generate_verification_report(self._make_all_pass_results())
        self.assertGreater(
            len(result.strip()),
            0,
            "generate_verification_report() returned an empty string.",
        )

    def test_is_markdown(self):
        """Result must contain at least one markdown heading or table marker."""
        self._require_module()
        result = self.pv.generate_verification_report(self._make_all_pass_results())
        has_markdown = "#" in result or "|" in result or "---" in result
        self.assertTrue(
            has_markdown,
            "generate_verification_report() must return a markdown string with headings (#) "
            "or table rows (|). The result contains no markdown markers.",
        )

    def test_pass_stages_show_pass_label(self):
        """Passing stages must be labeled PASS in the report."""
        self._require_module()
        result = self.pv.generate_verification_report(self._make_all_pass_results())
        self.assertIn(
            "PASS",
            result,
            "generate_verification_report() must include 'PASS' for stages that passed. "
            f"Report:\n{result}",
        )

    def test_fail_stages_show_fail_label(self):
        """Failing stages must be labeled FAIL in the report."""
        self._require_module()
        result = self.pv.generate_verification_report(self._make_partial_fail_results())
        self.assertIn(
            "FAIL",
            result,
            "generate_verification_report() must include 'FAIL' for stages that failed. "
            f"Report:\n{result}",
        )

    def test_each_stage_name_appears_in_report(self):
        """Each stage name from the results must appear in the report."""
        self._require_module()
        results = self._make_partial_fail_results()
        report = self.pv.generate_verification_report(results)
        for stage_name in results["results"]:
            self.assertIn(
                stage_name,
                report,
                f"generate_verification_report() must include stage name '{stage_name}' in the report.",
            )

    def test_error_details_appear_for_failed_stages(self):
        """Error messages from failed stages must appear in the report."""
        self._require_module()
        results = self._make_partial_fail_results()
        report = self.pv.generate_verification_report(results)
        error_msg = "Missing required JSON field 'gabarito'"
        self.assertIn(
            error_msg,
            report,
            f"generate_verification_report() must include error details for failing stages. "
            f"Expected to find: '{error_msg}' in report.",
        )

    def test_all_pass_report_contains_no_fail(self):
        """A fully-passing result must not have FAIL in the report."""
        self._require_module()
        result = self.pv.generate_verification_report(self._make_all_pass_results())
        self.assertNotIn(
            "FAIL",
            result,
            "generate_verification_report() must not include 'FAIL' when all stages pass. "
            f"Report:\n{result}",
        )

    def test_accepts_optional_model_name_in_results(self):
        """If results dict contains a 'model' key, it should appear in the report."""
        self._require_module()
        results = self._make_all_pass_results()
        results["model"] = "gpt-4o"
        try:
            report = self.pv.generate_verification_report(results)
        except Exception as e:
            self.fail(
                f"generate_verification_report() raised {type(e).__name__} when 'model' key "
                f"was present in results: {e}"
            )
        self.assertIn(
            "gpt-4o",
            report,
            "When results contains 'model'='gpt-4o', the report must reference the model name.",
        )


if __name__ == "__main__":
    unittest.main()
