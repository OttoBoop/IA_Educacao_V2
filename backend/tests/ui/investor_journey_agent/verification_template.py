"""
F9-T1: Verification document template generator.

Generates a Markdown verification report template from the existing
scenario.py, validation_rules.py, and cascade_steps.py data structures.
Each item starts with PENDING status for Claude Code to fill in during a run.
"""

from datetime import datetime
from pathlib import Path

from tests.ui.investor_journey_agent.scenario import CHECKLIST, MODELS, PIPELINE_STAGES
from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES
from tests.ui.investor_journey_agent.cascade_steps import CASCADE_STEPS


def generate_verification_template(output_path: Path) -> Path:
    """Generate the verification report template as a Markdown file.

    Args:
        output_path: Destination path for the generated .md file.

    Returns:
        The path to the generated file (same as output_path).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []

    # Header
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines += [
        "# Pipeline Verification Report",
        f"**Generated:** {timestamp}",
        f"**Persona:** tester | **Viewport:** desktop | **Models:** {len(MODELS)}",
        "",
        "---",
        "",
    ]

    # --- Pipeline Triggers (CHECKLIST pipeline category) ---
    pipeline_items = [item for item in CHECKLIST if item["category"] == "pipeline"]
    lines += [
        "## Pipeline Triggers",
        "",
        "| ID | Description | Status | Observations |",
        "|----|-------------|--------|-------------|",
    ]
    for item in pipeline_items:
        lines.append(f"| {item['id']} | {item['description']} | PENDING | |")
    lines.append("")

    # --- Downloads (CHECKLIST download category) ---
    download_items = [item for item in CHECKLIST if item["category"] == "download"]
    lines += [
        "## Downloads",
        "",
        "| ID | Description | Status | Observations |",
        "|----|-------------|--------|-------------|",
    ]
    for item in download_items:
        lines.append(f"| {item['id']} | {item['description']} | PENDING | |")
    lines.append("")

    # --- Validation (CHECKLIST validation category) ---
    validation_items = [item for item in CHECKLIST if item["category"] == "validation"]
    lines += [
        "## Content Validation",
        "",
    ]
    for item in validation_items:
        lines += [
            f"### Checklist: {item['id']}",
            "",
            f"**Description:** {item['description']}",
            "",
            "| Status | Observations |",
            "|--------|-------------|",
            "| PENDING | |",
            "",
        ]

    # --- Stage Rules (STAGE_RULES) ---
    lines += [
        "## Stage Validation Rules",
        "",
    ]
    for stage_name, rule in STAGE_RULES.items():
        expected_fields = ", ".join(rule["expected_json_fields"])
        pdf_min = rule["pdf_min_bytes"]
        description = rule.get("description", "")
        lines += [
            f"### Stage: {stage_name}",
            "",
            f"*{description}*",
            "",
            "| Check | Expected | Status | Observations |",
            "|-------|----------|--------|-------------|",
            f"| JSON fields: {expected_fields} | Present | PENDING | |",
            f"| PDF size | >= {pdf_min} bytes | PENDING | |",
            "",
        ]

    # --- Desempenho Cascade ---
    desempenho_items = [item for item in CHECKLIST if item["category"] == "desempenho"]
    lines += [
        "## Desempenho Cascade",
        "",
    ]
    # Checklist items for desempenho
    if desempenho_items:
        lines += [
            "### Checklist",
            "",
            "| ID | Description | Status | Observations |",
            "|----|-------------|--------|-------------|",
        ]
        for item in desempenho_items:
            lines.append(f"| {item['id']} | {item['description']} | PENDING | |")
        lines.append("")

    # Cascade steps
    lines += [
        "### Cascade Steps",
        "",
        "| Step | Action | Level | Status | Observations |",
        "|------|--------|-------|--------|-------------|",
    ]
    for step in CASCADE_STEPS:
        lines.append(
            f"| {step['step_id']} | {step['action']} | {step['level']} | PENDING | |"
        )
    lines.append("")

    # --- Summary ---
    total = len(CHECKLIST) + len(STAGE_RULES) * 2 + len(CASCADE_STEPS)
    lines += [
        "---",
        "",
        "## Summary",
        "",
        f"- Total checks: {total}",
        "- OBSERVED: 0",
        "- FAILED: 0",
        "- BLOCKED: 0",
        "- UNVERIFIED: 0",
        f"- PENDING: {total}",
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
