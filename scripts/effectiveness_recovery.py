from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import re

from scripts.effectiveness_analysis import (
    compute_environment_fingerprint,
    validate_study_manifest,
)


RECOVERY_KEYS = frozenset(
    {
        "schema_version",
        "synthetic_example",
        "affected_study_id",
        "affected_task_commitment_sha256",
        "affected_batch_disposition",
        "incident_status",
        "incident_closed_at",
        "incident_record_sha256",
        "restart_decision",
        "restart_decided_at",
        "restart_record_sha256",
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
    }
)

SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
LOWER_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")

AFFECTED_DISPOSITION = "excluded-from-effectiveness-analysis"
RESTART_DECISIONS = {None, "not-authorized", "authorized-for-replacement-batch"}

_INCIDENT_FIELDS = ("incident_status", "incident_closed_at", "incident_record_sha256")
_RESTART_FIELDS = ("restart_decision", "restart_decided_at", "restart_record_sha256")
_BINDING_FIELDS = (
    "replacement_study_id",
    "replacement_protocol_commit",
    "replacement_skill_name",
    "replacement_skill_version",
    "replacement_skill_commit",
    "replacement_task_commitment_sha256",
    "replacement_assignment_version",
    "replacement_environment_fingerprint",
)
_COLLECTION_FIELDS = (
    "collection_status",
    "collection_closed_at",
    "collection_record_sha256",
)
_INTEGRITY_FIELDS = (
    "integrity_attested_at",
    "integrity_record_sha256",
    "environment_change_detected",
    "task_pack_leakage_detected",
    "reportable_incident_detected",
)


def _group_state(record: Mapping[str, object], fields: tuple[str, ...]) -> str:
    values = [record[field] for field in fields]
    if all(value is None for value in values):
        return "empty"
    if all(value is not None for value in values):
        return "complete"
    return "incomplete"


def _group_error(record: Mapping[str, object], fields: tuple[str, ...]) -> str | None:
    if _group_state(record, fields) != "incomplete":
        return None
    for field in fields:
        if record[field] is None:
            return f"incomplete lifecycle group: {field}"
    return f"incomplete lifecycle group: {fields[0]}"


def _is_aware_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and SAFE_ID.fullmatch(value) is not None


def _valid_hex(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def validate_recovery_record(payload: object) -> list[str]:
    """Return deterministic, content-free validation errors for a recovery record."""
    if not isinstance(payload, Mapping):
        return ["recovery record must be an object"]

    keys = set(payload)
    for key in sorted(RECOVERY_KEYS - keys):
        return [f"missing key: {key}"]
    if keys - RECOVERY_KEYS:
        return ["unexpected key"]

    record = payload
    if record["schema_version"] != "1":
        return ["invalid schema_version"]
    if type(record["synthetic_example"]) is not bool:
        return ["invalid synthetic_example"]
    if record["affected_batch_disposition"] != AFFECTED_DISPOSITION:
        return ["invalid affected_batch_disposition"]

    affected_fields = ("affected_study_id", "affected_task_commitment_sha256")
    group_error = _group_error(record, affected_fields)
    if group_error:
        return [group_error]

    if record["affected_study_id"] is not None and not _valid_identifier(
        record["affected_study_id"]
    ):
        return ["invalid affected_study_id"]
    if record["affected_task_commitment_sha256"] is not None and not _valid_hex(
        record["affected_task_commitment_sha256"], LOWER_HEX_64
    ):
        return ["invalid affected_task_commitment_sha256"]

    incident_status = record["incident_status"]
    if incident_status not in {"open", "closed"}:
        return ["invalid incident_status"]
    incident_state = _group_state(record, _INCIDENT_FIELDS)
    if incident_status == "open":
        if incident_state != "empty":
            for field in _INCIDENT_FIELDS[1:]:
                if record[field] is not None:
                    return [f"incomplete lifecycle group: {field}"]
        incident_state = "empty"
    else:
        group_error = _group_error(record, _INCIDENT_FIELDS)
        if group_error:
            return [group_error]

    for fields in (_RESTART_FIELDS, _BINDING_FIELDS, _COLLECTION_FIELDS, _INTEGRITY_FIELDS):
        group_error = _group_error(record, fields)
        if group_error:
            return [group_error]

    if incident_status == "closed":
        if not _is_aware_timestamp(record["incident_closed_at"]):
            return ["invalid incident_closed_at"]
        if not _valid_hex(record["incident_record_sha256"], LOWER_HEX_64):
            return ["invalid incident_record_sha256"]

    if record["restart_decision"] not in RESTART_DECISIONS:
        return ["invalid restart_decision"]
    if _group_state(record, _RESTART_FIELDS) == "complete":
        if incident_status != "closed":
            return ["restart requires incident closure"]
        if not _is_aware_timestamp(record["restart_decided_at"]):
            return ["invalid restart_decided_at"]
        if not _valid_hex(record["restart_record_sha256"], LOWER_HEX_64):
            return ["invalid restart_record_sha256"]

    if record["restart_decision"] == "authorized-for-replacement-batch" and _group_state(
        record, affected_fields
    ) != "complete":
        return ["affected identity is required for authorized restart"]

    if _group_state(record, _BINDING_FIELDS) == "complete":
        if record["restart_decision"] != "authorized-for-replacement-batch":
            return ["replacement bindings require restart authorization"]
        for field in (
            "replacement_study_id",
            "replacement_assignment_version",
            "replacement_environment_fingerprint",
        ):
            if not _valid_identifier(record[field]):
                return [f"invalid {field}"]
        for field in ("replacement_protocol_commit", "replacement_skill_commit"):
            if not _valid_hex(record[field], LOWER_HEX_40):
                return [f"invalid {field}"]
        if record["replacement_skill_name"] != "clin-nav":
            return ["invalid replacement_skill_name"]
        if record["replacement_skill_version"] != "0.5.0":
            return ["invalid replacement_skill_version"]
        if not _valid_hex(record["replacement_task_commitment_sha256"], LOWER_HEX_64):
            return ["invalid replacement_task_commitment_sha256"]

    if _group_state(record, _COLLECTION_FIELDS) == "complete":
        if _group_state(record, _BINDING_FIELDS) != "complete":
            return ["collection requires replacement bindings"]
        if record["collection_status"] != "closed":
            return ["invalid collection_status"]
        if not _is_aware_timestamp(record["collection_closed_at"]):
            return ["invalid collection_closed_at"]
        if not _valid_hex(record["collection_record_sha256"], LOWER_HEX_64):
            return ["invalid collection_record_sha256"]

    if _group_state(record, _INTEGRITY_FIELDS) == "complete":
        if _group_state(record, _COLLECTION_FIELDS) != "complete":
            return ["integrity attestation requires collection closure"]
        if not _is_aware_timestamp(record["integrity_attested_at"]):
            return ["invalid integrity_attested_at"]
        if not _valid_hex(record["integrity_record_sha256"], LOWER_HEX_64):
            return ["invalid integrity_record_sha256"]
        for field in _INTEGRITY_FIELDS[2:]:
            if type(record[field]) is not bool:
                return [f"invalid {field}"]

    if (
        record["affected_study_id"] is not None
        and record["replacement_study_id"] is not None
        and record["affected_study_id"] == record["replacement_study_id"]
    ):
        return ["affected and replacement study IDs must differ"]
    if (
        record["affected_task_commitment_sha256"] is not None
        and record["replacement_task_commitment_sha256"] is not None
        and record["affected_task_commitment_sha256"]
        == record["replacement_task_commitment_sha256"]
    ):
        return ["affected and replacement task commitments must differ"]

    timestamps = []
    if incident_status == "closed":
        timestamps.append(record["incident_closed_at"])
    if _group_state(record, _RESTART_FIELDS) == "complete":
        timestamps.append(record["restart_decided_at"])
    if _group_state(record, _COLLECTION_FIELDS) == "complete":
        timestamps.append(record["collection_closed_at"])
    if _group_state(record, _INTEGRITY_FIELDS) == "complete":
        timestamps.append(record["integrity_attested_at"])
    if any(later <= earlier for earlier, later in zip(map(_timestamp, timestamps), map(_timestamp, timestamps[1:]))):
        return ["timestamps must be chronological"]

    return []


def compute_record_state(record: dict) -> dict:
    """Compute only the closed record's pre-collection recovery state."""
    if validate_recovery_record(record):
        raise ValueError("invalid recovery record")

    passed = ["affected-batch-excluded"]
    blocked: list[str] = []
    status = "blocked-incident-open"

    if record["incident_status"] != "closed":
        blocked.append("incident-closure")
    else:
        passed.append("incident-closure")
        status = "ready-for-restart-review"
        if record["restart_decision"] == "authorized-for-replacement-batch":
            passed.append("restart-authorization")
        else:
            blocked.append("restart-authorization")
        if _group_state(record, _BINDING_FIELDS) == "complete":
            passed.append("replacement-bindings")
        else:
            blocked.append("replacement-bindings")
        if not blocked:
            status = "authorized-for-fresh-batch"

    return {
        "schema_version": "1",
        "status": status,
        "passed_gate_ids": passed,
        "blocked_gate_ids": blocked,
        "synthetic_example": record["synthetic_example"],
    }


def restart_status(record: dict) -> dict:
    """Return the highest permitted sanitized pre-collection state."""
    return compute_record_state(record)


def collection_status(record: dict, manifest: dict) -> dict:
    """Bind a closed, clean replacement collection to its validated manifest."""
    state = restart_status(record)
    if state["status"] != "authorized-for-fresh-batch":
        return state

    passed = list(state["passed_gate_ids"])
    blocked = list(state["blocked_gate_ids"])
    if validate_study_manifest(manifest):
        blocked.append("replacement-study-manifest")
        return _sanitized_state(record, state["status"], passed, blocked)

    bindings = (
        ("replacement-study-id", "replacement_study_id", "study_id"),
        ("replacement-protocol-commit", "replacement_protocol_commit", "protocol_commit"),
        ("replacement-skill-version", "replacement_skill_version", "skill_version"),
        ("replacement-skill-commit", "replacement_skill_commit", "skill_commit"),
        (
            "replacement-task-commitment",
            "replacement_task_commitment_sha256",
            "task_commitment_sha256",
        ),
    )
    for gate_id, record_field, manifest_field in bindings:
        if record[record_field] == manifest[manifest_field]:
            passed.append(gate_id)
        else:
            blocked.append(gate_id)

    if record["replacement_environment_fingerprint"] == compute_environment_fingerprint(
        manifest
    ):
        passed.append("replacement-environment-fingerprint")
    else:
        blocked.append("replacement-environment-fingerprint")

    assignment_versions = {
        session["assignment_version"] for session in manifest["sessions"]
    }
    if (
        len(assignment_versions) == 1
        and record["replacement_assignment_version"] in assignment_versions
    ):
        passed.append("replacement-assignment-version")
    else:
        blocked.append("replacement-assignment-version")

    if _group_state(record, _COLLECTION_FIELDS) == "complete" and record[
        "collection_status"
    ] == "closed":
        passed.append("replacement-collection-closed")
    else:
        blocked.append("replacement-collection-closed")

    if _group_state(record, _INTEGRITY_FIELDS) != "complete":
        blocked.append("replacement-integrity-attestation")
    elif all(record[field] is False for field in _INTEGRITY_FIELDS[2:]):
        passed.append("replacement-integrity-clean")
    else:
        blocked.append("replacement-integrity-clean")

    status = "ready-for-blinded-rating" if not blocked else state["status"]
    return _sanitized_state(record, status, passed, blocked)


def _sanitized_state(
    record: Mapping[str, object],
    status: str,
    passed: list[str],
    blocked: list[str],
) -> dict:
    return {
        "schema_version": "1",
        "status": status,
        "passed_gate_ids": passed,
        "blocked_gate_ids": blocked,
        "synthetic_example": record["synthetic_example"],
    }
