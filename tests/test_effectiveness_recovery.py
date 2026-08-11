import copy
import json
from pathlib import Path

import pytest

from scripts.effectiveness_recovery import (
    RECOVERY_KEYS,
    compute_record_state,
    validate_recovery_record,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "evals/effectiveness/recovery/recovery-template.json"
SYNTHETIC = ROOT / "evals/effectiveness/recovery/examples/synthetic-recovery.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def invalid_errors(payload: object) -> list[str]:
    errors = validate_recovery_record(payload)
    assert errors
    return errors


def test_template_is_valid_and_blocked_without_external_closure():
    payload = load_json(TEMPLATE)

    assert validate_recovery_record(payload) == []
    assert compute_record_state(payload)["status"] == "blocked-incident-open"


def test_synthetic_record_never_claims_terminal_human_evidence():
    payload = load_json(SYNTHETIC)

    assert payload["synthetic_example"] is True
    assert validate_recovery_record(payload) == []
    assert compute_record_state(payload)["status"] == "authorized-for-fresh-batch"


def test_public_fixtures_are_canonical_json_with_one_final_newline():
    for path in (TEMPLATE, SYNTHETIC):
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))

        assert raw == (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")


@pytest.mark.parametrize("key", sorted(RECOVERY_KEYS))
def test_schema_rejects_every_missing_top_level_key(key):
    payload = load_json(SYNTHETIC)
    del payload[key]

    assert invalid_errors(payload) == [f"missing key: {key}"]


@pytest.mark.parametrize("key", ("status", "green", "approved", "authorization"))
def test_schema_rejects_status_and_approval_shortcuts(key):
    payload = load_json(SYNTHETIC)
    payload[key] = True

    assert invalid_errors(payload) == ["unexpected key"]


def test_schema_reports_missing_keys_before_unexpected_keys():
    payload = load_json(SYNTHETIC)
    del payload["schema_version"]
    payload["status"] = "evaluation-green"

    assert invalid_errors(payload) == ["missing key: schema_version"]


@pytest.mark.parametrize(
    "field,value",
    (
        ("affected_task_commitment_sha256", "A" * 64),
        ("replacement_skill_commit", "a" * 39),
        ("incident_record_sha256", "b" * 63),
        ("affected_study_id", "bad id"),
        ("replacement_assignment_version", "a"),
        ("incident_closed_at", "2026-08-11T09:00:00"),
    ),
)
def test_schema_rejects_invalid_hash_identifier_and_timestamp_values(field, value):
    payload = load_json(SYNTHETIC)
    payload[field] = value

    assert invalid_errors(payload) == [f"invalid {field}"]


@pytest.mark.parametrize(
    "field",
    (
        "incident_closed_at",
        "restart_decided_at",
        "replacement_skill_name",
        "collection_closed_at",
        "integrity_attested_at",
    ),
)
def test_schema_rejects_inconsistent_lifecycle_groups(field):
    payload = load_json(SYNTHETIC)
    payload[field] = None

    assert invalid_errors(payload) == [f"incomplete lifecycle group: {field}"]


@pytest.mark.parametrize(
    "field",
    (
        "environment_change_detected",
        "task_pack_leakage_detected",
        "reportable_incident_detected",
    ),
)
def test_schema_requires_boolean_integrity_flags(field):
    payload = load_json(SYNTHETIC)
    payload[field] = "false"

    assert invalid_errors(payload) == [f"invalid {field}"]


def test_schema_rejects_reused_affected_bindings():
    payload = load_json(SYNTHETIC)
    payload["replacement_study_id"] = payload["affected_study_id"]

    assert invalid_errors(payload) == ["affected and replacement study IDs must differ"]

    payload = load_json(SYNTHETIC)
    payload["replacement_task_commitment_sha256"] = payload[
        "affected_task_commitment_sha256"
    ]

    assert invalid_errors(payload) == ["affected and replacement task commitments must differ"]


@pytest.mark.parametrize(
    "field,value",
    (
        ("replacement_skill_name", "clinical-data-research-navigator"),
        ("replacement_skill_version", "0.4.0"),
    ),
)
def test_schema_requires_the_frozen_replacement_skill(field, value):
    payload = load_json(SYNTHETIC)
    payload[field] = value

    assert invalid_errors(payload) == [f"invalid {field}"]


def test_schema_rejects_non_chronological_lifecycle_timestamps():
    payload = load_json(SYNTHETIC)
    payload["restart_decided_at"] = payload["incident_closed_at"]

    assert invalid_errors(payload) == ["timestamps must be chronological"]


def test_state_is_sanitized_and_record_only():
    state = compute_record_state(load_json(SYNTHETIC))

    assert state == {
        "schema_version": "1",
        "status": "authorized-for-fresh-batch",
        "passed_gate_ids": [
            "affected-batch-excluded",
            "incident-closure",
            "restart-authorization",
            "replacement-bindings",
        ],
        "blocked_gate_ids": [],
        "synthetic_example": True,
    }


def test_state_requires_external_incident_closure_before_restart_review():
    payload = load_json(TEMPLATE)
    payload["affected_study_id"] = "synthetic-affected-study"
    payload["affected_task_commitment_sha256"] = "a" * 64

    assert compute_record_state(payload) == {
        "schema_version": "1",
        "status": "blocked-incident-open",
        "passed_gate_ids": ["affected-batch-excluded"],
        "blocked_gate_ids": ["incident-closure"],
        "synthetic_example": False,
    }


def test_state_blocks_restart_when_authorization_or_bindings_are_incomplete():
    payload = load_json(SYNTHETIC)
    payload["restart_decision"] = None
    payload["restart_decided_at"] = None
    payload["restart_record_sha256"] = None
    for field in (
        "replacement_study_id",
        "replacement_protocol_commit",
        "replacement_skill_name",
        "replacement_skill_version",
        "replacement_skill_commit",
        "replacement_task_commitment_sha256",
        "replacement_assignment_version",
        "replacement_environment_fingerprint",
        "collection_status",
        "collection_closed_at",
        "collection_record_sha256",
        "integrity_attested_at",
        "integrity_record_sha256",
        "environment_change_detected",
        "task_pack_leakage_detected",
        "reportable_incident_detected",
    ):
        payload[field] = None

    assert compute_record_state(payload) == {
        "schema_version": "1",
        "status": "ready-for-restart-review",
        "passed_gate_ids": ["affected-batch-excluded", "incident-closure"],
        "blocked_gate_ids": ["restart-authorization", "replacement-bindings"],
        "synthetic_example": True,
    }


def test_state_rejects_invalid_record_without_echoing_input_values():
    payload = copy.deepcopy(load_json(SYNTHETIC))
    marker = "unsafe marker"
    payload["affected_study_id"] = marker

    with pytest.raises(ValueError, match="^invalid recovery record$"):
        compute_record_state(payload)
