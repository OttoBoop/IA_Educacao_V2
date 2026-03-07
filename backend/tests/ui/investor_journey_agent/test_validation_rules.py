"""
Tests for F6-T2: Content Validation Rules Per Stage.

These tests verify that validation_rules.py defines:
- STAGE_RULES: a dict mapping each pipeline stage to expected content rules
- validate_stage_output: a callable that checks a stage's JSON + PDF output

All tests are expected to FAIL initially (RED phase) because
validation_rules.py does not exist yet.
"""

import unittest


REQUIRED_STAGES = [
    "extrair_questoes",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]


class TestStageRulesExists(unittest.TestCase):
    """Test that the STAGE_RULES constant is importable and well-formed."""

    def test_module_is_importable(self):
        """Test that validation_rules module can be imported."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES  # noqa: F401

    def test_stage_rules_is_dict(self):
        """Test that STAGE_RULES is a dict."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        self.assertIsInstance(STAGE_RULES, dict)

    def test_stage_rules_has_at_least_four_entries(self):
        """Test that STAGE_RULES contains at least 4 entries."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        self.assertGreaterEqual(len(STAGE_RULES), 4)

    def test_all_required_stage_names_are_present(self):
        """Test that all 4 required stage names appear as keys in STAGE_RULES."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        for stage in REQUIRED_STAGES:
            self.assertIn(
                stage,
                STAGE_RULES,
                msg=f"Stage '{stage}' is missing from STAGE_RULES",
            )


class TestStageRuleSchema(unittest.TestCase):
    """Test that every rule dict inside STAGE_RULES has the expected schema."""

    def _get_rules(self):
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        return STAGE_RULES

    def test_each_rule_has_expected_json_fields_key(self):
        """Test that every stage rule contains 'expected_json_fields'."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertIn(
                "expected_json_fields",
                rule,
                msg=f"Stage '{stage}' rule is missing 'expected_json_fields'",
            )

    def test_expected_json_fields_is_a_list(self):
        """Test that 'expected_json_fields' is a list for every stage."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertIsInstance(
                rule["expected_json_fields"],
                list,
                msg=f"Stage '{stage}': 'expected_json_fields' must be a list",
            )

    def test_expected_json_fields_is_non_empty(self):
        """Test that 'expected_json_fields' is non-empty for every stage."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertGreater(
                len(rule["expected_json_fields"]),
                0,
                msg=f"Stage '{stage}': 'expected_json_fields' must not be empty",
            )

    def test_each_rule_has_pdf_min_bytes_key(self):
        """Test that every stage rule contains 'pdf_min_bytes'."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertIn(
                "pdf_min_bytes",
                rule,
                msg=f"Stage '{stage}' rule is missing 'pdf_min_bytes'",
            )

    def test_pdf_min_bytes_is_int(self):
        """Test that 'pdf_min_bytes' is an int for every stage."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertIsInstance(
                rule["pdf_min_bytes"],
                int,
                msg=f"Stage '{stage}': 'pdf_min_bytes' must be an int",
            )

    def test_pdf_min_bytes_is_at_least_1000(self):
        """Test that 'pdf_min_bytes' is >= 1000 for every stage."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertGreaterEqual(
                rule["pdf_min_bytes"],
                1000,
                msg=f"Stage '{stage}': 'pdf_min_bytes' must be >= 1000, got {rule['pdf_min_bytes']}",
            )

    def test_each_rule_has_description_key(self):
        """Test that every stage rule contains 'description'."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertIn(
                "description",
                rule,
                msg=f"Stage '{stage}' rule is missing 'description'",
            )

    def test_description_is_non_empty_string(self):
        """Test that 'description' is a non-empty string for every stage."""
        rules = self._get_rules()
        for stage, rule in rules.items():
            self.assertIsInstance(
                rule["description"],
                str,
                msg=f"Stage '{stage}': 'description' must be a str",
            )
            self.assertGreater(
                len(rule["description"].strip()),
                0,
                msg=f"Stage '{stage}': 'description' must not be blank",
            )


class TestValidateStageFunctionExists(unittest.TestCase):
    """Test that validate_stage_output is callable and importable."""

    def test_validate_stage_output_is_importable(self):
        """Test that validate_stage_output can be imported."""
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output  # noqa: F401

    def test_validate_stage_output_is_callable(self):
        """Test that validate_stage_output is a callable."""
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output

        self.assertTrue(callable(validate_stage_output))


class TestValidateStageFunctionReturnShape(unittest.TestCase):
    """Test that validate_stage_output returns the expected dict shape."""

    def _validate(self, stage, json_content, pdf_size):
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output

        return validate_stage_output(stage, json_content, pdf_size)

    def _get_good_json_for(self, stage):
        """Return a json_content dict that satisfies all expected_json_fields for a stage."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        fields = STAGE_RULES[stage]["expected_json_fields"]
        return {field: "test_value" for field in fields}

    def _get_good_pdf_size_for(self, stage):
        """Return a pdf_size that meets the minimum for a stage."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        return STAGE_RULES[stage]["pdf_min_bytes"] + 1000

    def test_returns_dict(self):
        """Test that validate_stage_output returns a dict."""
        stage = "extrair_questoes"
        json_content = self._get_good_json_for(stage)
        pdf_size = self._get_good_pdf_size_for(stage)

        result = self._validate(stage, json_content, pdf_size)

        self.assertIsInstance(result, dict)

    def test_result_has_valid_key(self):
        """Test that result dict contains a 'valid' key."""
        stage = "extrair_questoes"
        json_content = self._get_good_json_for(stage)
        pdf_size = self._get_good_pdf_size_for(stage)

        result = self._validate(stage, json_content, pdf_size)

        self.assertIn("valid", result)

    def test_result_has_errors_key(self):
        """Test that result dict contains an 'errors' key."""
        stage = "extrair_questoes"
        json_content = self._get_good_json_for(stage)
        pdf_size = self._get_good_pdf_size_for(stage)

        result = self._validate(stage, json_content, pdf_size)

        self.assertIn("errors", result)

    def test_errors_is_a_list(self):
        """Test that 'errors' in result is always a list."""
        stage = "extrair_questoes"
        json_content = self._get_good_json_for(stage)
        pdf_size = self._get_good_pdf_size_for(stage)

        result = self._validate(stage, json_content, pdf_size)

        self.assertIsInstance(result["errors"], list)


class TestValidateStageGoodData(unittest.TestCase):
    """Test that validate_stage_output returns valid=True for correct inputs."""

    def _validate(self, stage, json_content, pdf_size):
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output

        return validate_stage_output(stage, json_content, pdf_size)

    def _good_inputs_for(self, stage):
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        rule = STAGE_RULES[stage]
        json_content = {field: "test_value" for field in rule["expected_json_fields"]}
        pdf_size = rule["pdf_min_bytes"] + 5000
        return json_content, pdf_size

    def test_valid_true_for_extrair_questoes_with_good_data(self):
        """Test valid=True when extrair_questoes output meets all rules."""
        json_content, pdf_size = self._good_inputs_for("extrair_questoes")
        result = self._validate("extrair_questoes", json_content, pdf_size)

        self.assertTrue(result["valid"], msg=f"Expected valid=True but got errors: {result['errors']}")
        self.assertEqual(result["errors"], [])

    def test_valid_true_for_corrigir_with_good_data(self):
        """Test valid=True when corrigir output meets all rules."""
        json_content, pdf_size = self._good_inputs_for("corrigir")
        result = self._validate("corrigir", json_content, pdf_size)

        self.assertTrue(result["valid"], msg=f"Expected valid=True but got errors: {result['errors']}")
        self.assertEqual(result["errors"], [])

    def test_valid_true_for_analisar_habilidades_with_good_data(self):
        """Test valid=True when analisar_habilidades output meets all rules."""
        json_content, pdf_size = self._good_inputs_for("analisar_habilidades")
        result = self._validate("analisar_habilidades", json_content, pdf_size)

        self.assertTrue(result["valid"], msg=f"Expected valid=True but got errors: {result['errors']}")
        self.assertEqual(result["errors"], [])

    def test_valid_true_for_gerar_relatorio_with_good_data(self):
        """Test valid=True when gerar_relatorio output meets all rules."""
        json_content, pdf_size = self._good_inputs_for("gerar_relatorio")
        result = self._validate("gerar_relatorio", json_content, pdf_size)

        self.assertTrue(result["valid"], msg=f"Expected valid=True but got errors: {result['errors']}")
        self.assertEqual(result["errors"], [])


class TestValidateStageMissingJsonFields(unittest.TestCase):
    """Test that validate_stage_output returns valid=False when required JSON fields are missing."""

    def _validate(self, stage, json_content, pdf_size):
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output

        return validate_stage_output(stage, json_content, pdf_size)

    def _good_pdf_size_for(self, stage):
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        return STAGE_RULES[stage]["pdf_min_bytes"] + 5000

    def test_valid_false_when_json_fields_missing_extrair_questoes(self):
        """Test valid=False when extrair_questoes output is missing required JSON fields."""
        stage = "extrair_questoes"
        pdf_size = self._good_pdf_size_for(stage)
        empty_json = {}

        result = self._validate(stage, empty_json, pdf_size)

        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_valid_false_when_json_fields_missing_corrigir(self):
        """Test valid=False when corrigir output is missing required JSON fields."""
        stage = "corrigir"
        pdf_size = self._good_pdf_size_for(stage)
        empty_json = {}

        result = self._validate(stage, empty_json, pdf_size)

        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_errors_mention_missing_field_name(self):
        """Test that error messages mention which field is missing."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        stage = "extrair_questoes"
        expected_fields = STAGE_RULES[stage]["expected_json_fields"]
        pdf_size = STAGE_RULES[stage]["pdf_min_bytes"] + 5000
        empty_json = {}

        result = self._validate(stage, empty_json, pdf_size)

        # At least one error should mention a missing field name
        errors_text = " ".join(result["errors"])
        found_field_mention = any(field in errors_text for field in expected_fields)
        self.assertTrue(
            found_field_mention,
            msg=f"Expected error messages to mention missing field names. Errors: {result['errors']}",
        )

    def test_valid_false_when_only_some_fields_present(self):
        """Test valid=False when json_content has some but not all required fields."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        stage = "extrair_questoes"
        rule = STAGE_RULES[stage]
        fields = rule["expected_json_fields"]

        # Only provide the first field if there are multiple, else skip
        if len(fields) < 2:
            self.skipTest("Stage has fewer than 2 required fields; partial test not applicable")

        partial_json = {fields[0]: "present_value"}
        pdf_size = rule["pdf_min_bytes"] + 5000

        result = self._validate(stage, partial_json, pdf_size)

        self.assertFalse(result["valid"])


class TestValidateStagePdfTooSmall(unittest.TestCase):
    """Test that validate_stage_output returns valid=False when PDF size is below minimum."""

    def _validate(self, stage, json_content, pdf_size):
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output

        return validate_stage_output(stage, json_content, pdf_size)

    def _good_json_for(self, stage):
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        fields = STAGE_RULES[stage]["expected_json_fields"]
        return {field: "test_value" for field in fields}

    def test_valid_false_when_pdf_size_zero(self):
        """Test valid=False when pdf_size is 0."""
        stage = "extrair_questoes"
        json_content = self._good_json_for(stage)

        result = self._validate(stage, json_content, 0)

        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_valid_false_when_pdf_size_below_minimum(self):
        """Test valid=False when pdf_size is below the stage's pdf_min_bytes."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        stage = "corrigir"
        min_bytes = STAGE_RULES[stage]["pdf_min_bytes"]
        json_content = self._good_json_for(stage)

        # One byte below minimum
        result = self._validate(stage, json_content, min_bytes - 1)

        self.assertFalse(result["valid"])

    def test_pdf_size_error_message_is_descriptive(self):
        """Test that error message for small PDF is descriptive."""
        stage = "extrair_questoes"
        json_content = self._good_json_for(stage)

        result = self._validate(stage, json_content, 0)

        errors_text = " ".join(result["errors"]).lower()
        self.assertTrue(
            "pdf" in errors_text or "bytes" in errors_text or "size" in errors_text or "tamanho" in errors_text,
            msg=f"Expected error to mention PDF/bytes/size. Errors: {result['errors']}",
        )

    def test_valid_true_at_exact_minimum_pdf_size(self):
        """Test valid=True when pdf_size equals exactly pdf_min_bytes (boundary)."""
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        stage = "extrair_questoes"
        rule = STAGE_RULES[stage]
        json_content = self._good_json_for(stage)

        result = self._validate(stage, json_content, rule["pdf_min_bytes"])

        self.assertTrue(
            result["valid"],
            msg=f"Expected valid=True at exact minimum pdf_size. Errors: {result['errors']}",
        )


class TestValidateStageUnknownStage(unittest.TestCase):
    """Test that validate_stage_output handles unknown stage names gracefully."""

    def _validate(self, stage, json_content, pdf_size):
        from tests.ui.investor_journey_agent.validation_rules import validate_stage_output

        return validate_stage_output(stage, json_content, pdf_size)

    def test_unknown_stage_raises_or_returns_invalid(self):
        """Test that an unknown stage name either raises an exception or returns valid=False."""
        unknown_stage = "this_stage_does_not_exist"
        json_content = {"some_field": "some_value"}
        pdf_size = 10000

        try:
            result = self._validate(unknown_stage, json_content, pdf_size)
            # If it doesn't raise, it must return valid=False with an error
            self.assertFalse(
                result["valid"],
                msg="Unknown stage should return valid=False, not valid=True",
            )
            self.assertGreater(
                len(result["errors"]),
                0,
                msg="Unknown stage should populate errors list",
            )
        except (KeyError, ValueError, LookupError):
            # Raising an exception for unknown stage is also acceptable
            pass


if __name__ == "__main__":
    unittest.main()
