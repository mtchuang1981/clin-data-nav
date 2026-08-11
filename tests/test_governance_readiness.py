import copy
import json
from pathlib import Path

import pytest

from scripts.governance_readiness import (
    summarize_governance_readiness,
    validate_governance_readiness,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "evals/effectiveness/governance/readiness-template.json"
SYNTHETIC = (
    ROOT
    / "evals/effectiveness/governance/examples/synthetic-readiness.json"
)
EXPECTED_CONTROL_IDS = (
    "study-owner-role",
    "institutional-path-request",
    "scope-risk-benefit",
    "external-storage",
    "access-minimization",
    "retention-deletion",
    "consent-material",
    "recruitment-plan",
    "incident-response",
    "environment-freeze",
    "rater-readiness",
    "task-pack-commitment-plan",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_template_is_valid_incomplete_and_never_authorized():
    payload = load_json(TEMPLATE)

    assert validate_governance_readiness(payload) == []
    assert [row["control_id"] for row in payload["controls"]] == list(
        EXPECTED_CONTROL_IDS
    )
    assert summarize_governance_readiness(payload) == {
        "schema_version": "1",
        "status": "incomplete",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 0,
        "required_controls": 12,
        "missing_control_ids": list(EXPECTED_CONTROL_IDS),
    }


def test_synthetic_example_is_review_ready_but_never_authorized():
    payload = load_json(SYNTHETIC)

    assert payload["synthetic_example"] is True
    assert validate_governance_readiness(payload) == []
    assert summarize_governance_readiness(payload) == {
        "schema_version": "1",
        "status": "ready-for-institutional-review",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 12,
        "required_controls": 12,
        "missing_control_ids": [],
    }


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.update(extra=True),
        lambda value: value.pop("prepared_at"),
        lambda value: value.__setitem__("schema_version", 1),
        lambda value: value.__setitem__("synthetic_example", "true"),
        lambda value: value.__setitem__("pack_id", "Contains Spaces"),
        lambda value: value.__setitem__("protocol_commit", "A" * 40),
        lambda value: value.__setitem__(
            "prepared_at", "2026-08-11T12:00:00"
        ),
    ),
)
def test_top_level_schema_mutations_fail_closed(mutate):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    mutate(payload)

    assert validate_governance_readiness(payload)


@pytest.mark.parametrize(
    "forbidden_key",
    (
        "approved",
        "authorized",
        "review_not_required",
        "ethics_outcome",
        "ready_to_recruit",
    ),
)
def test_institutional_outcome_fields_are_rejected(forbidden_key):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    payload[forbidden_key] = False

    assert validate_governance_readiness(payload)


def _remove_control(payload: dict) -> None:
    payload["controls"].pop()


def _duplicate_control(payload: dict) -> None:
    payload["controls"][-1] = copy.deepcopy(payload["controls"][0])


def _swap_controls(payload: dict) -> None:
    payload["controls"][0], payload["controls"][1] = (
        payload["controls"][1],
        payload["controls"][0],
    )


def _unknown_control(payload: dict) -> None:
    payload["controls"][0]["control_id"] = "unknown-control"


def _extra_control_key(payload: dict) -> None:
    payload["controls"][0]["extra"] = "synthetic"


@pytest.mark.parametrize(
    "mutate",
    (
        _remove_control,
        _duplicate_control,
        _swap_controls,
        _unknown_control,
        _extra_control_key,
    ),
)
def test_control_structure_mutations_fail_closed(mutate):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    mutate(payload)

    assert validate_governance_readiness(payload)


@pytest.mark.parametrize(
    ("status", "reference"),
    (
        ("complete", "SYNTH.STUDY-OWNER-ROLE.V1"),
        ("not-documented", "SYNTH.STUDY-OWNER-ROLE.V1"),
        ("documented", None),
        ("documented", "contains whitespace"),
        ("documented", "contains@marker"),
        ("documented", "contains/slash"),
        ("documented", "contains\\backslash"),
    ),
)
def test_status_and_reference_mutations_fail_closed(status, reference):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    payload["controls"][0]["documentation_status"] = status
    payload["controls"][0]["evidence_reference"] = reference

    errors = validate_governance_readiness(payload)

    assert errors
    if reference:
        assert reference not in "\n".join(errors)


@pytest.mark.parametrize("index", range(12))
def test_each_missing_documentation_control_makes_summary_incomplete(index):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    payload["controls"][index]["documentation_status"] = "not-documented"
    payload["controls"][index]["evidence_reference"] = None

    summary = summarize_governance_readiness(payload)

    assert summary["status"] == "incomplete"
    assert summary["authorization"] == "not-authorized-to-recruit"
    assert summary["missing_control_ids"] == [EXPECTED_CONTROL_IDS[index]]


def test_summary_rejects_invalid_input():
    payload = copy.deepcopy(load_json(SYNTHETIC))
    payload["approved"] = True

    with pytest.raises(ValueError, match="^invalid governance readiness input$"):
        summarize_governance_readiness(payload)
