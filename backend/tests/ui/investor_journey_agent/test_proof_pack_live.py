"""Live proof-pack checks for headed journey verification runs."""

import json
import os
from pathlib import Path

import pytest


pytestmark = pytest.mark.live

REQUIRED_RUN_ARTIFACTS = (
    "summary.json",
    "verification_report.md",
    "journey_report.md",
    "phase3_validation.json",
    "artifact_manifest.jsonl",
    "events.jsonl",
    "status.json",
)


def _parse_csv_env(name: str) -> list[str]:
    raw_value = os.environ.get(name, "")
    values = []
    seen = set()
    for chunk in raw_value.split(","):
        value = chunk.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        values.append(value)
    return values


def _proof_run_dir() -> Path:
    raw_value = os.environ.get("JOURNEY_PROOF_RUN_DIR")
    if not raw_value:
        pytest.skip(
            "Set JOURNEY_PROOF_RUN_DIR to a headed proof run directory before running live proof-pack checks."
        )
    run_dir = Path(raw_value)
    assert run_dir.exists(), f"Proof run directory does not exist: {run_dir}"
    return run_dir


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _has_hierarchical_downloads(downloads_dir: Path) -> bool:
    for path in downloads_dir.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(downloads_dir)
        if relative.parts[0] == "desempenho" and len(relative.parts) >= 3:
            return True
        if len(relative.parts) >= 4:
            return True
    return False


def test_scoped_proof_run_creates_single_run_scoped_artifact_pack():
    """A headed proof run should leave one self-contained run directory."""
    run_dir = _proof_run_dir()
    downloads_dir = run_dir / "downloads"
    screenshots_dir = run_dir / "screenshots"

    for name in REQUIRED_RUN_ARTIFACTS:
        assert (run_dir / name).exists(), f"Missing required proof artifact: {run_dir / name}"

    assert screenshots_dir.exists(), "Headed proof run must save screenshots."
    assert any(screenshots_dir.iterdir()), "Headed proof run screenshots directory must not be empty."
    assert downloads_dir.exists(), "Proof run must have a downloads directory."
    assert _has_hierarchical_downloads(downloads_dir), (
        "Proof run downloads must be normalized into the canonical hierarchy."
    )

    incoming_dir = downloads_dir / "_incoming"
    assert not incoming_dir.exists() or not any(incoming_dir.rglob("*")), (
        "Transient _incoming downloads must be normalized before proof review."
    )

    shared_report = run_dir.parent / "verification_report.md"
    assert not shared_report.exists(), (
        "Controller proof runs must not rely on a shared authoritative verification_report.md outside the run directory."
    )

    summary = _load_json(run_dir / "summary.json")
    phase3 = _load_json(run_dir / "phase3_validation.json")
    verification_scope = summary.get("verification_scope", {})

    assert verification_scope, "summary.json must persist verification_scope metadata."
    assert verification_scope.get("requested_models") == phase3.get("requested_models")
    assert verification_scope.get("expected_blocked_models") == phase3.get(
        "expected_blocked_models"
    )
    assert verification_scope.get("phase3_overall_status") == phase3.get("overall_status")
    assert Path(phase3["downloads_dir"]).resolve() == downloads_dir.resolve()


def test_expected_blocked_models_are_recorded_truthfully_without_false_success():
    """Expected blocked providers must stay blocked and must not inflate success reporting."""
    run_dir = _proof_run_dir()
    summary = _load_json(run_dir / "summary.json")
    phase3 = _load_json(run_dir / "phase3_validation.json")
    verification_scope = summary.get("verification_scope", {})
    summary_section = summary.get("summary", {})
    expected_blocked = _parse_csv_env("JOURNEY_PROOF_EXPECTED_BLOCKED_MODELS")

    if not expected_blocked:
        expected_blocked = verification_scope.get("expected_blocked_models", [])
    if not expected_blocked:
        pytest.skip("This proof run does not declare any expected blocked models.")

    assert sorted(verification_scope.get("expected_blocked_models", [])) == sorted(
        expected_blocked
    )
    assert sorted(phase3.get("expected_blocked_models", [])) == sorted(expected_blocked)
    assert verification_scope.get("b5_eligible") is False
    assert summary_section.get("status") in ("blocked", "incomplete"), (
        "Scoped runs with expected blocked providers must not report completed status."
    )
    assert summary_section.get("blocked") or summary_section.get("incomplete")
    assert summary_section.get("success_rate", 0.0) < 1.0, (
        "Blocked-provider proof runs must not inflate success_rate to 1.0."
    )

    for model in expected_blocked:
        model_status = verification_scope.get("model_status", {}).get(model, {})
        assert model_status.get("status") in ("expected_blocked", "expected_blocked_observed"), (
            f"Expected blocked model {model} must be recorded explicitly in verification_scope."
        )

    report_text = (run_dir / "verification_report.md").read_text(encoding="utf-8")
    assert "expected blocked for this proof run scope" in report_text
