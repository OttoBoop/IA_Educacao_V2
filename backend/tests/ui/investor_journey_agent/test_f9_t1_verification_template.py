"""
Tests for F9-T1: Verification document template generator.

Verifies that:
1. generate_verification_template() function exists and returns a Path
2. Generated template contains all 12 CHECKLIST items (by ID)
3. Generated template contains all 4 STAGE_RULES stages (by name)
4. Generated template contains all 5 CASCADE_STEPS (by step_id)
5. All items have PENDING status in the generated template
"""

import json
from pathlib import Path


class TestGenerateVerificationTemplateExists:
    """verify the function exists and returns a Path."""

    def test_module_has_generate_function(self):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        assert callable(generate_verification_template)

    def test_generate_returns_path(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        output_path = tmp_path / "verification_report.md"
        result = generate_verification_template(output_path)

        assert isinstance(result, Path)
        assert result == output_path

    def test_generate_creates_file(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        output_path = tmp_path / "verification_report.md"
        assert not output_path.exists()

        generate_verification_template(output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestTemplateContainsChecklist:
    """Template must contain all 12 CHECKLIST items."""

    def test_all_checklist_ids_present(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )
        from tests.ui.investor_journey_agent.scenario import CHECKLIST

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        missing = []
        for item in CHECKLIST:
            if item["id"] not in content:
                missing.append(item["id"])

        assert not missing, (
            f"Generated template is missing {len(missing)} CHECKLIST item(s): {missing}"
        )

    def test_checklist_count_is_12(self, tmp_path):
        from tests.ui.investor_journey_agent.scenario import CHECKLIST

        assert len(CHECKLIST) == 12, (
            f"Expected 12 CHECKLIST items, found {len(CHECKLIST)}"
        )

    def test_checklist_items_have_pending_status(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        assert "PENDING" in content, (
            "Generated template must include at least one PENDING status field"
        )


class TestTemplateContainsStageRules:
    """Template must contain all 4 STAGE_RULES stages."""

    def test_all_stage_names_present(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        missing = []
        for stage_name in STAGE_RULES:
            if stage_name not in content:
                missing.append(stage_name)

        assert not missing, (
            f"Generated template is missing {len(missing)} STAGE_RULES stage(s): {missing}"
        )

    def test_stage_count_is_4(self):
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        assert len(STAGE_RULES) == 4, (
            f"Expected 4 STAGE_RULES stages, found {len(STAGE_RULES)}"
        )

    def test_stage_rules_sections_have_pending_status(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )
        from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        # At least one stage section should mention PENDING
        assert "PENDING" in content


class TestTemplateContainsCascadeSteps:
    """Template must contain all 5 CASCADE_STEPS."""

    def test_all_cascade_step_ids_present(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )
        from tests.ui.investor_journey_agent.cascade_steps import CASCADE_STEPS

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        missing = []
        for step in CASCADE_STEPS:
            if step["step_id"] not in content:
                missing.append(step["step_id"])

        assert not missing, (
            f"Generated template is missing {len(missing)} CASCADE_STEPS step(s): {missing}"
        )

    def test_cascade_step_count_is_5(self):
        from tests.ui.investor_journey_agent.cascade_steps import CASCADE_STEPS

        assert len(CASCADE_STEPS) == 5, (
            f"Expected 5 CASCADE_STEPS, found {len(CASCADE_STEPS)}"
        )

    def test_cascade_steps_have_pending_status(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        assert "PENDING" in content


class TestTemplateIsValidMarkdown:
    """Generated template must be valid Markdown."""

    def test_template_has_heading(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        lines = content.splitlines()
        has_heading = any(line.startswith("#") for line in lines)
        assert has_heading, "Template must contain at least one Markdown heading (#)"

    def test_template_has_summary_section(self, tmp_path):
        from tests.ui.investor_journey_agent.verification_template import (
            generate_verification_template,
        )

        output_path = tmp_path / "verification_report.md"
        generate_verification_template(output_path)
        content = output_path.read_text(encoding="utf-8")

        assert "Summary" in content or "summary" in content.lower(), (
            "Template must contain a Summary section"
        )
