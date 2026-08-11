"""Validate governance documentation readiness without granting authority."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import re


TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "synthetic_example",
        "pack_id",
        "protocol_commit",
        "prepared_at",
        "controls",
    }
)
CONTROL_KEYS = frozenset(
    {"control_id", "documentation_status", "evidence_reference"}
)
CONTROL_IDS = (
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
PACK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")


def _validate_exact_keys(
    label: str,
    value: Mapping[object, object],
    expected: frozenset[str],
    errors: list[str],
) -> None:
    actual = set(value)
    for key in sorted(expected - actual):
        errors.append(f"{label} missing key: {key}")
    for key in sorted(actual - expected, key=str):
        errors.append(f"{label} unexpected key: {key}")


def _has_utc_offset(value: object) -> bool:
    if type(value) is not str:
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.utcoffset() is not None


def validate_governance_readiness(payload: object) -> list[str]:
    """Return deterministic, content-free errors for a readiness payload."""
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return ["top-level value must be an object"]

    _validate_exact_keys("top-level", payload, TOP_LEVEL_KEYS, errors)

    schema_version = payload.get("schema_version")
    if type(schema_version) is not str or schema_version != "1":
        errors.append("schema_version must be string 1")

    if type(payload.get("synthetic_example")) is not bool:
        errors.append("synthetic_example must be boolean")

    pack_id = payload.get("pack_id")
    if type(pack_id) is not str or PACK_ID_PATTERN.fullmatch(pack_id) is None:
        errors.append("pack_id has invalid format")

    protocol_commit = payload.get("protocol_commit")
    if (
        type(protocol_commit) is not str
        or COMMIT_PATTERN.fullmatch(protocol_commit) is None
    ):
        errors.append("protocol_commit has invalid format")

    if not _has_utc_offset(payload.get("prepared_at")):
        errors.append("prepared_at must include a UTC offset")

    controls = payload.get("controls")
    if type(controls) is not list:
        errors.append("controls must be a list")
        return errors
    if len(controls) != len(CONTROL_IDS):
        errors.append("controls must contain exactly 12 rows")
        return errors

    for index, (row, expected_id) in enumerate(
        zip(controls, CONTROL_IDS, strict=True)
    ):
        label = f"control row {index}"
        if not isinstance(row, Mapping):
            errors.append(f"{label} must be an object")
            continue
        _validate_exact_keys(label, row, CONTROL_KEYS, errors)
        if row.get("control_id") != expected_id:
            errors.append(f"{label} has invalid control_id")

        status = row.get("documentation_status")
        reference = row.get("evidence_reference")
        if status not in {"not-documented", "documented"}:
            errors.append(f"{label} has invalid documentation_status")
        elif status == "not-documented":
            if reference is not None:
                errors.append(f"{label} must not have an evidence reference")
        elif (
            type(reference) is not str
            or REFERENCE_PATTERN.fullmatch(reference) is None
        ):
            errors.append(f"{label} must have a valid evidence reference")

    return errors


def summarize_governance_readiness(payload: dict) -> dict:
    """Build a sanitized summary for an already valid readiness payload."""
    if validate_governance_readiness(payload):
        raise ValueError("invalid governance readiness input")
    missing = [
        row["control_id"]
        for row in payload["controls"]
        if row["documentation_status"] == "not-documented"
    ]
    return {
        "schema_version": "1",
        "status": "incomplete" if missing else "ready-for-institutional-review",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 12 - len(missing),
        "required_controls": 12,
        "missing_control_ids": missing,
    }
