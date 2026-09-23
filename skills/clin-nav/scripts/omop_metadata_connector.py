"""Bounded, MCP-independent harness for redacted OMOP metadata inspection."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json

from omop_metadata import (
    CONTRACT_VERSION,
    HARD_MAX_RESPONSE_BYTES,
    build_inspection_request,
    classify_inspection,
    validate_capabilities,
    validate_inspection,
)


BytesOperation = Callable[..., bytes]

_AGGREGATE_KEYS = (
    "missing_table_count",
    "missing_standard_column_count",
    "type_mismatch_count",
    "nullability_mismatch_count",
    "primary_key_mismatch_count",
    "foreign_key_mismatch_count",
    "unexpected_table_count",
    "unexpected_column_count",
)
_IDENTITY_KEYS = (
    "observed_at",
    "omop_cdm_version",
    "allowlist_id",
    "allowlist_version",
    "reference_sha256",
)


def _result(status: str, *codes: str) -> dict[str, object]:
    return {
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "validation_codes": sorted(set(codes)),
    }


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if key in parsed:
            raise ValueError("duplicate JSON key")
        parsed[key] = value
    return parsed


def _reject_nonfinite_constant(value: str) -> object:
    raise ValueError("non-finite JSON constant")


def _parse_bytes(
    raw: object, *, maximum: int, label: str
) -> tuple[object | None, dict[str, object] | None]:
    if not isinstance(raw, bytes):
        return None, _result("invalid-response", f"{label}-invalid-bytes")
    if len(raw) > maximum:
        return None, _result("invalid-response", f"{label}-response-too-large")
    try:
        text = raw.decode("utf-8", errors="strict")
        return (
            json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_nonfinite_constant,
            ),
            None,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        return None, _result("invalid-response", f"{label}-invalid-json")


def _safe_summary(
    inspection: Mapping[str, object], classification: Mapping[str, object]
) -> dict[str, object]:
    status = classification["status"]
    if status == "unavailable":
        return {
            **_result("unavailable"),
            "limitation_codes": list(classification["limitation_codes"]),
        }
    if status in {"version-mismatch", "reference-mismatch", "stale"}:
        return _result(str(status))
    if status not in {"compatible", "compatible-with-deviations", "incompatible"}:
        return _result("invalid-response", "unclassified-status")

    summary: dict[str, object] = {
        "contract_version": CONTRACT_VERSION,
        "status": status,
    }
    for key in _IDENTITY_KEYS:
        summary[key] = inspection[key]
    for key in _AGGREGATE_KEYS:
        summary[key] = classification[key]
    summary["limitation_codes"] = list(classification["limitation_codes"])
    summary["summary_sha256"] = inspection["summary_sha256"]
    summary["validation_codes"] = list(classification["validation_codes"])
    return summary


def assess_connector(
    get_capabilities: BytesOperation,
    inspect_omop_schema: BytesOperation,
    *,
    catalog: Mapping[str, object],
    as_of: str,
    hard_max_bytes: int = HARD_MAX_RESPONSE_BYTES,
) -> dict[str, object]:
    """Run the two-operation connector protocol and return only safe summary data."""
    if (
        not isinstance(hard_max_bytes, int)
        or isinstance(hard_max_bytes, bool)
        or not 1 <= hard_max_bytes <= HARD_MAX_RESPONSE_BYTES
    ):
        return _result("invalid-response", "invalid-hard-max-bytes")

    try:
        capabilities_raw = get_capabilities()
    except Exception:
        return _result("unavailable", "connector-unavailable")

    capabilities, parse_error = _parse_bytes(
        capabilities_raw, maximum=hard_max_bytes, label="capabilities"
    )
    if parse_error is not None:
        return parse_error

    capability_errors = validate_capabilities(capabilities)
    if capability_errors:
        return _result("invalid-response", *capability_errors)
    assert isinstance(capabilities, Mapping)
    capability_limit = capabilities["max_response_bytes"]
    assert isinstance(capability_limit, int)
    accepted_bytes = min(hard_max_bytes, capability_limit)
    try:
        request = build_inspection_request(
            catalog, max_response_bytes=accepted_bytes
        )
    except (TypeError, ValueError, OverflowError):
        return _result("invalid-response", "catalog-invalid")

    try:
        inspection_raw = inspect_omop_schema(request)
    except Exception:
        return _result("unavailable", "connector-unavailable")

    inspection, parse_error = _parse_bytes(
        inspection_raw, maximum=accepted_bytes, label="inspection"
    )
    if parse_error is not None:
        return parse_error

    errors = validate_inspection(
        inspection,
        catalog=catalog,
        capabilities=capabilities,
        as_of=as_of,
        raw_size_bytes=len(inspection_raw),
    )
    if errors:
        return _result("invalid-response", *errors)
    assert isinstance(inspection, Mapping)
    classification = classify_inspection(
        inspection,
        catalog=catalog,
        capabilities=capabilities,
        as_of=as_of,
    )
    return _safe_summary(inspection, classification)
