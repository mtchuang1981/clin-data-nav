"""Packaging and scenario integrity, not a claim of model effectiveness."""
from pathlib import Path
import shutil

import pytest
import yaml

from scripts.package_skill import build_package
from scripts.validate_skill import validate_skill

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clin-nav"
REFERENCE = "references/feasibility-consultation.md"
CASE_IDS = {
    "unflagged-semantic-mismatch", "zero-hit-recovery", "mixed-modalities",
    "unread-pages", "coordinator-decisions", "tool-argument-error",
    "formal-spec-request",
}


def test_consultation_reference_is_packaged_and_reachable(tmp_path):
    assert REFERENCE in (SKILL / "SKILL.md").read_text(encoding="utf-8")
    result = build_package(SKILL, tmp_path / "package")
    assert REFERENCE in result.files
    copied = tmp_path / "skill" / "clin-nav"
    shutil.copytree(SKILL, copied)
    (copied / REFERENCE).unlink()
    assert f"missing reference: {REFERENCE}" in validate_skill(copied)


def test_synthetic_cases_have_reviewable_decisions_and_no_regex_grading():
    catalog = yaml.safe_load(
        (ROOT / "evals/feasibility-consultation/cases.yaml").read_text(encoding="utf-8")
    )
    assert catalog["schema_version"] == "1"
    assert catalog["evaluation_mode"] == "manual-behavior"
    criteria = catalog["criteria"]
    assert {case["id"] for case in catalog["cases"]} == CASE_IDS
    assert len(catalog["cases"]) == len(CASE_IDS)
    for case in catalog["cases"]:
        assert case["prompt"].strip()
        assert case["expected_actions"]
        assert case["reject_actions"]
        assert set(case["criteria"]) <= set(criteria)
        assert all(isinstance(action, str) and action.strip()
                   for action in case["expected_actions"] + case["reject_actions"])
        assert "required_sections" not in case
        assert "required" not in case


@pytest.mark.parametrize("criterion", [
    "semantic-review", "search-completeness", "decision-ownership",
    "argument-validation", "scope-and-progress", "delivery-fit",
])
def test_each_criterion_has_a_positive_action_and_counterexample(criterion):
    catalog = yaml.safe_load(
        (ROOT / "evals/feasibility-consultation/cases.yaml").read_text(encoding="utf-8")
    )
    definition = catalog["criteria"][criterion]
    assert definition["pass_when"].strip()
    assert definition["fail_when"].strip()
    assert any(criterion in case["criteria"] for case in catalog["cases"])
