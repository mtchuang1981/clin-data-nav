"""Validate and summarize a machine-auditable evidence ledger."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
import re


TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "ledger_id", "prepared_on", "sources", "claims"}
)
SOURCE_KEYS = frozenset(
    {
        "source_id",
        "title",
        "stable_identifier",
        "authority_level",
        "publication_date",
        "version_or_snapshot",
        "review_status",
        "reviewed_on",
        "review_due_on",
        "applicability",
        "limitations",
    }
)
CLAIM_KEYS = frozenset(
    {
        "claim_id",
        "claim",
        "claim_type",
        "source_ids",
        "evidence_location",
        "support_status",
        "applicability",
        "limitations",
    }
)
AUTHORITY_LEVELS = frozenset(
    {"official", "study-specific", "peer-reviewed", "implementation", "institutional"}
)
REVIEW_STATUSES = frozenset({"reviewed", "not-reviewed", "unavailable"})
CLAIM_TYPES = frozenset({"external-fact", "request-provided", "inference"})
SUPPORT_STATUSES = frozenset(
    {"direct-support", "partial-support", "unsupported", "not-assessed"}
)
ASSESSED_SUPPORT_STATUSES = frozenset(
    {"direct-support", "partial-support", "unsupported"}
)
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _exact_keys(
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


def _date_value(value: object) -> date | None:
    if type(value) is not str or len(value) != 10:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def _optional_date(label: str, value: object, errors: list[str]) -> date | None:
    if value is None:
        return None
    parsed = _date_value(value)
    if parsed is None:
        errors.append(f"{label} must be an ISO date or null")
    return parsed


def _required_text(label: str, value: object, errors: list[str]) -> None:
    if type(value) is not str or not value.strip():
        errors.append(f"{label} must be a non-empty string")


def validate_evidence_ledger(payload: object, *, as_of: str) -> list[str]:
    """Return deterministic validation errors without echoing evidence text."""
    errors: list[str] = []
    audit_date = _date_value(as_of)
    if audit_date is None:
        return ["as_of must be an ISO date"]
    if not isinstance(payload, Mapping):
        return ["top-level value must be an object"]

    _exact_keys("top-level", payload, TOP_LEVEL_KEYS, errors)
    if payload.get("schema_version") != "1":
        errors.append("schema_version must be string 1")

    ledger_id = payload.get("ledger_id")
    if type(ledger_id) is not str or ID_PATTERN.fullmatch(ledger_id) is None:
        errors.append("ledger_id has invalid format")

    prepared_on = _date_value(payload.get("prepared_on"))
    if prepared_on is None:
        errors.append("prepared_on must be an ISO date")
    elif prepared_on > audit_date:
        errors.append("prepared_on must not be after as_of")

    sources = payload.get("sources")
    claims = payload.get("claims")
    if type(sources) is not list:
        errors.append("sources must be a list")
        sources = []
    if type(claims) is not list:
        errors.append("claims must be a list")
        claims = []
    elif not claims:
        errors.append("claims must not be empty")

    source_statuses: dict[str, object] = {}
    for index, row in enumerate(sources):
        label = f"source row {index}"
        if not isinstance(row, Mapping):
            errors.append(f"{label} must be an object")
            continue
        _exact_keys(label, row, SOURCE_KEYS, errors)
        source_id = row.get("source_id")
        if type(source_id) is not str or ID_PATTERN.fullmatch(source_id) is None:
            errors.append(f"{label} has invalid source_id")
        elif source_id in source_statuses:
            errors.append(f"duplicate source_id: {source_id}")
        else:
            source_statuses[source_id] = row.get("review_status")

        for field in ("title", "applicability", "limitations"):
            _required_text(f"{label} {field}", row.get(field), errors)
        identifier = row.get("stable_identifier")
        if identifier is not None:
            _required_text(f"{label} stable_identifier", identifier, errors)
        if row.get("authority_level") not in AUTHORITY_LEVELS:
            errors.append(f"{label} has invalid authority_level")
        version = row.get("version_or_snapshot")
        if version is not None:
            _required_text(f"{label} version_or_snapshot", version, errors)

        publication = _optional_date(
            f"{label} publication_date", row.get("publication_date"), errors
        )
        reviewed = _optional_date(f"{label} reviewed_on", row.get("reviewed_on"), errors)
        review_due = _optional_date(
            f"{label} review_due_on", row.get("review_due_on"), errors
        )
        for field, parsed in (("publication_date", publication), ("reviewed_on", reviewed)):
            if parsed is not None and parsed > audit_date:
                errors.append(f"{label} {field} must not be after as_of")

        review_status = row.get("review_status")
        if review_status not in REVIEW_STATUSES:
            errors.append(f"{label} has invalid review_status")
        elif review_status == "reviewed" and reviewed is None:
            errors.append(f"{label} reviewed_on is required when reviewed")
        elif review_status != "reviewed" and row.get("reviewed_on") is not None:
            errors.append(f"{label} reviewed_on must be null unless reviewed")
        if reviewed is not None and publication is not None and reviewed < publication:
            errors.append(f"{label} reviewed_on must not precede publication_date")
        if review_due is not None and reviewed is not None and review_due < reviewed:
            errors.append(f"{label} review_due_on must not precede reviewed_on")

    claim_ids: set[str] = set()
    for index, row in enumerate(claims):
        label = f"claim row {index}"
        if not isinstance(row, Mapping):
            errors.append(f"{label} must be an object")
            continue
        _exact_keys(label, row, CLAIM_KEYS, errors)
        claim_id = row.get("claim_id")
        if type(claim_id) is not str or ID_PATTERN.fullmatch(claim_id) is None:
            errors.append(f"{label} has invalid claim_id")
            claim_label = label
        else:
            claim_label = f"claim {claim_id}"
            if claim_id in claim_ids:
                errors.append(f"duplicate claim_id: {claim_id}")
            claim_ids.add(claim_id)

        for field in ("claim", "applicability", "limitations"):
            _required_text(f"{label} {field}", row.get(field), errors)
        claim_type = row.get("claim_type")
        if claim_type not in CLAIM_TYPES:
            errors.append(f"{label} has invalid claim_type")
        support_status = row.get("support_status")
        if support_status not in SUPPORT_STATUSES:
            errors.append(f"{label} has invalid support_status")

        source_ids = row.get("source_ids")
        if type(source_ids) is not list:
            errors.append(f"{label} source_ids must be a list")
            source_ids = []
        elif any(type(item) is not str or ID_PATTERN.fullmatch(item) is None for item in source_ids):
            errors.append(f"{label} source_ids contain an invalid id")
        elif len(source_ids) != len(set(source_ids)):
            errors.append(f"{label} source_ids must be unique")

        if claim_type in {"external-fact", "inference"} and not source_ids:
            errors.append(f"{claim_label} requires at least one source")
        if support_status in ASSESSED_SUPPORT_STATUSES:
            if not source_ids:
                errors.append(f"{claim_label} requires at least one source for assessed support")
            if type(row.get("evidence_location")) is not str or not row["evidence_location"].strip():
                errors.append(f"{claim_label} requires evidence_location for assessed support")
        elif row.get("evidence_location") is not None:
            _required_text(f"{label} evidence_location", row.get("evidence_location"), errors)

        for source_id in source_ids:
            if source_id not in source_statuses:
                errors.append(f"{claim_label} references unknown source_id")
            elif (
                support_status in ASSESSED_SUPPORT_STATUSES
                and source_statuses[source_id] != "reviewed"
            ):
                errors.append(f"{claim_label} assessed support requires reviewed sources")

    return errors


def summarize_evidence_ledger(payload: dict, *, as_of: str) -> dict:
    """Return a content-free status summary for an already valid ledger."""
    if validate_evidence_ledger(payload, as_of=as_of):
        raise ValueError("invalid evidence ledger input")
    audit_date = date.fromisoformat(as_of)
    review_due: list[str] = []
    unknown_freshness: list[str] = []
    unreviewed: list[str] = []
    unavailable: list[str] = []
    unidentified: list[str] = []
    for source in payload["sources"]:
        status = source["review_status"]
        if source["stable_identifier"] is None:
            unidentified.append(source["source_id"])
        if status == "not-reviewed":
            unreviewed.append(source["source_id"])
        elif status == "unavailable":
            unavailable.append(source["source_id"])
        due = source["review_due_on"]
        if status != "reviewed" or due is None:
            unknown_freshness.append(source["source_id"])
        elif audit_date >= date.fromisoformat(due):
            review_due.append(source["source_id"])

    claim_status_ids = {
        status: [
            claim["claim_id"]
            for claim in payload["claims"]
            if claim["support_status"] == status
        ]
        for status in ("partial-support", "unsupported", "not-assessed")
    }
    outstanding = any(
        (
            review_due,
            unknown_freshness,
            unreviewed,
            unavailable,
            unidentified,
            *claim_status_ids.values(),
        )
    )
    return {
        "schema_version": "1",
        "status": "review-required" if outstanding else "complete",
        "as_of": as_of,
        "source_count": len(payload["sources"]),
        "claim_count": len(payload["claims"]),
        "review_due_source_ids": review_due,
        "unknown_freshness_source_ids": unknown_freshness,
        "unreviewed_source_ids": unreviewed,
        "unavailable_source_ids": unavailable,
        "unidentified_source_ids": unidentified,
        "partial_support_claim_ids": claim_status_ids["partial-support"],
        "unsupported_claim_ids": claim_status_ids["unsupported"],
        "not_assessed_claim_ids": claim_status_ids["not-assessed"],
    }
