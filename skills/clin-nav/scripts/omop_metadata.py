"""Fail-closed validation for redacted OMOP metadata connector responses.

This module intentionally uses only the Python standard library.  The adjacent
JSON Schema is the portable wire contract; the checks here add ordering,
catalog, total, freshness, and canonical-hash semantics that JSON Schema does
not express.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
import hashlib
import json
import re
from typing import Any


CONTRACT_VERSION = "1.0"
OMOP_CDM_VERSION = "5.4"
ALLOWLIST_ID = "omop-v54-core-research-v1"
ALLOWLIST_VERSION = "1.0.0"
HARD_MAX_RESPONSE_BYTES = 262_144
MAX_NESTING_DEPTH = 6
MAX_STRING_LENGTH = 128

_CAPABILITY_KEYS = frozenset(
    {
        "contract_version",
        "adapter_id",
        "adapter_version",
        "metadata_read_only",
        "row_access",
        "sql_execution",
        "raw_schema_export",
        "supported_omop_cdm_versions",
        "supported_allowlists",
        "max_snapshot_age_seconds",
        "tbls_inspection_available",
        "max_response_bytes",
    }
)
_ALLOWLIST_SUPPORT_KEYS = frozenset({"allowlist_id", "allowlist_version"})
_INSPECTION_KEYS = frozenset(
    {
        "contract_version",
        "adapter_version",
        "omop_cdm_version",
        "allowlist_id",
        "allowlist_version",
        "reference_sha256",
        "observed_at",
        "tbls_version",
        "scan_status",
        "summary_sha256",
        "unexpected_table_count",
        "unexpected_column_count",
        "limitation_codes",
        "tables",
    }
)
_TABLE_KEYS = frozenset(
    {
        "canonical_table_name",
        "presence",
        "standard_column_total",
        "present_standard_columns",
        "missing_standard_columns",
        "type_mismatches",
        "nullability_mismatches",
        "primary_key_status",
        "foreign_key_status",
        "unexpected_column_count",
    }
)
_TYPE_MISMATCH_KEYS = frozenset(
    {
        "canonical_column_name",
        "expected_type_family",
        "observed_type_family",
    }
)
_NULLABILITY_MISMATCH_KEYS = frozenset(
    {
        "canonical_column_name",
        "expected_nullable",
        "observed_nullable",
    }
)
_PROHIBITED_KEYS = frozenset(
    {"database_name", "schema_name", "comment", "sql", "error", "rows"}
)
_TYPE_FAMILIES = frozenset(
    {"binary", "boolean", "date", "datetime", "decimal", "integer", "string"}
)
_PRESENCE_VALUES = frozenset({"present", "missing", "unknown"})
_KEY_STATUS_VALUES = frozenset({"matches", "missing", "different", "unknown"})
_SCAN_STATUS_VALUES = frozenset({"complete", "partial", "failed"})
_LIMITATION_CODES = frozenset(
    {
        "snapshot-incomplete",
        "metadata-permission-limited",
        "tbls-normalization-limited",
        "constraint-metadata-limited",
    }
)

_CANONICAL_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,127}$")
_PUBLIC_TOKEN_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_ADAPTER_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:[-+][0-9A-Za-z.-]+)?$"
)
_OMOP_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?"
    r"(?:Z|[+-]\d{2}:\d{2})$"
)


class _Errors:
    def __init__(self) -> None:
        self._codes: set[str] = set()

    def add(self, code: str) -> None:
        self._codes.add(code)

    def result(self) -> tuple[str, ...]:
        return tuple(sorted(self._codes))


def canonical_json_bytes(
    payload: Mapping[str, object], *, omit_key: str | None = None
) -> bytes:
    """Return canonical UTF-8 JSON with sorted keys and exactly one trailing LF."""
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    rendered_payload: Mapping[str, object]
    if omit_key is None:
        rendered_payload = payload
    else:
        rendered_payload = {key: value for key, value in payload.items() if key != omit_key}
    return (
        json.dumps(
            rendered_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_recursive_limits(
    value: object,
    errors: _Errors,
    *,
    depth: int = 1,
    ancestors: frozenset[int] = frozenset(),
) -> None:
    if depth > MAX_NESTING_DEPTH:
        errors.add("nesting-too-deep")
        return
    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            errors.add("string-too-long")
        return
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in ancestors:
            errors.add("invalid-structure")
            return
        next_ancestors = ancestors | {identity}
        for key, child in value.items():
            if not isinstance(key, str):
                errors.add("invalid-structure")
                continue
            if key in _PROHIBITED_KEYS:
                errors.add("prohibited-key")
            _check_recursive_limits(
                child, errors, depth=depth + 1, ancestors=next_ancestors
            )
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        identity = id(value)
        if identity in ancestors:
            errors.add("invalid-structure")
            return
        if len(value) > 178:
            errors.add("array-too-long")
        next_ancestors = ancestors | {identity}
        for child in value:
            _check_recursive_limits(
                child, errors, depth=depth + 1, ancestors=next_ancestors
            )


def _closed_object(value: object, keys: frozenset[str], errors: _Errors) -> bool:
    if not isinstance(value, Mapping):
        errors.add("invalid-structure")
        return False
    actual = set(value)
    if keys - actual:
        errors.add("missing-key")
    if actual - keys:
        errors.add("unknown-key")
    return True


def _check_text(
    value: object,
    errors: _Errors,
    *,
    pattern: re.Pattern[str] | None = None,
    invalid_code: str = "invalid-value",
    max_length: int = MAX_STRING_LENGTH,
) -> bool:
    if not isinstance(value, str):
        errors.add("invalid-type")
        return False
    if len(value) > max_length:
        errors.add("string-too-long")
        return False
    if pattern is not None and pattern.fullmatch(value) is None:
        errors.add(invalid_code)
        return False
    return True


def _check_nonnegative_int(
    value: object, errors: _Errors, *, maximum: int = 2_147_483_647
) -> bool:
    if not _is_int(value):
        errors.add("invalid-type")
        return False
    if value < 0:
        errors.add("negative-count")
        return False
    if value > maximum:
        errors.add("count-too-large")
        return False
    return True


def _check_sorted_unique(values: list[Any], errors: _Errors) -> None:
    try:
        if values != sorted(values):
            errors.add("unsorted-array")
        if len(values) != len(set(values)):
            errors.add("duplicate-array")
    except (TypeError, ValueError):
        errors.add("invalid-type")


def _check_string_array(
    value: object,
    errors: _Errors,
    *,
    max_items: int,
    pattern: re.Pattern[str] | None = None,
    allowed: frozenset[str] | set[str] | None = None,
    invalid_name_code: str = "noncanonical-name",
) -> list[str] | None:
    if not isinstance(value, list):
        errors.add("invalid-structure")
        return None
    if len(value) > max_items:
        errors.add("array-too-long")
    valid_strings: list[str] = []
    for item in value:
        if _check_text(item, errors, pattern=pattern, invalid_code=invalid_name_code):
            valid_strings.append(item)
            if allowed is not None and item not in allowed:
                errors.add("non-allowlisted-name")
    if len(valid_strings) == len(value):
        _check_sorted_unique(valid_strings, errors)
    return valid_strings


def _parse_rfc3339(value: object, errors: _Errors) -> datetime | None:
    if not _check_text(
        value,
        errors,
        pattern=_RFC3339_RE,
        invalid_code="invalid-timestamp",
        max_length=64,
    ):
        return None
    assert isinstance(value, str)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.add("invalid-timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.add("invalid-timestamp")
        return None
    return parsed


def validate_capabilities(payload: object) -> tuple[str, ...]:
    """Validate the closed safety handshake and fixed connector support."""
    errors = _Errors()
    _check_recursive_limits(payload, errors)
    if not _closed_object(payload, _CAPABILITY_KEYS, errors):
        return errors.result()
    assert isinstance(payload, Mapping)

    if payload.get("contract_version") != CONTRACT_VERSION:
        errors.add("unsupported-contract-version")
    _check_text(payload.get("contract_version"), errors, max_length=8)
    _check_text(
        payload.get("adapter_id"),
        errors,
        pattern=_ADAPTER_ID_RE,
        invalid_code="invalid-value",
    )
    _check_text(
        payload.get("adapter_version"),
        errors,
        pattern=_SEMVER_RE,
        invalid_code="invalid-value",
        max_length=64,
    )
    safety_values = {
        "metadata_read_only": True,
        "row_access": False,
        "sql_execution": False,
        "raw_schema_export": False,
        "tbls_inspection_available": True,
    }
    for key, expected in safety_values.items():
        value = payload.get(key)
        if not isinstance(value, bool):
            errors.add("invalid-type")
        if value is not expected:
            errors.add("capability-unsafe")

    versions = payload.get("supported_omop_cdm_versions")
    checked_versions = _check_string_array(
        versions,
        errors,
        max_items=16,
        pattern=_OMOP_VERSION_RE,
    )
    if checked_versions is None or OMOP_CDM_VERSION not in checked_versions:
        errors.add("unsupported-version")

    supports = payload.get("supported_allowlists")
    support_pairs: list[tuple[str, str]] = []
    if not isinstance(supports, list):
        errors.add("invalid-structure")
    else:
        if len(supports) > 16:
            errors.add("array-too-long")
        for support in supports:
            if not _closed_object(support, _ALLOWLIST_SUPPORT_KEYS, errors):
                continue
            assert isinstance(support, Mapping)
            allowlist_id = support.get("allowlist_id")
            allowlist_version = support.get("allowlist_version")
            valid_id = _check_text(
                allowlist_id,
                errors,
                pattern=_PUBLIC_TOKEN_RE,
                invalid_code="invalid-value",
            )
            valid_version = _check_text(
                allowlist_version,
                errors,
                pattern=_SEMVER_RE,
                invalid_code="invalid-value",
                max_length=64,
            )
            if valid_id and valid_version:
                assert isinstance(allowlist_id, str)
                assert isinstance(allowlist_version, str)
                support_pairs.append((allowlist_id, allowlist_version))
        _check_sorted_unique(support_pairs, errors)
    if (ALLOWLIST_ID, ALLOWLIST_VERSION) not in support_pairs:
        errors.add("unsupported-allowlist")

    snapshot_age = payload.get("max_snapshot_age_seconds")
    if not _is_int(snapshot_age):
        errors.add("invalid-type")
    elif not 1 <= snapshot_age <= 31_536_000:
        errors.add("invalid-value")

    byte_limit = payload.get("max_response_bytes")
    if not _is_int(byte_limit):
        errors.add("invalid-type")
        errors.add("invalid-byte-limit")
    elif not 1 <= byte_limit <= HARD_MAX_RESPONSE_BYTES:
        errors.add("invalid-byte-limit")
    return errors.result()


def _catalog_index(
    catalog: Mapping[str, object], errors: _Errors
) -> tuple[list[str], dict[str, dict[str, tuple[str, bool]]]] | None:
    try:
        if not isinstance(catalog, Mapping):
            raise TypeError
        tables = catalog["tables"]
        if not isinstance(tables, list) or len(tables) != 13:
            raise TypeError
        order: list[str] = []
        index: dict[str, dict[str, tuple[str, bool]]] = {}
        for table in tables:
            if not isinstance(table, Mapping):
                raise TypeError
            table_name = table["canonical_table_name"]
            columns = table["columns"]
            if (
                not isinstance(table_name, str)
                or _CANONICAL_NAME_RE.fullmatch(table_name) is None
                or not isinstance(columns, list)
            ):
                raise TypeError
            column_index: dict[str, tuple[str, bool]] = {}
            for column in columns:
                if not isinstance(column, Mapping):
                    raise TypeError
                column_name = column["canonical_column_name"]
                type_family = column["type_family"]
                nullable = column["nullable"]
                if (
                    not isinstance(column_name, str)
                    or _CANONICAL_NAME_RE.fullmatch(column_name) is None
                    or type_family not in _TYPE_FAMILIES
                    or not isinstance(nullable, bool)
                    or column_name in column_index
                ):
                    raise TypeError
                column_index[column_name] = (type_family, nullable)
            if table_name in index:
                raise TypeError
            order.append(table_name)
            index[table_name] = column_index
        return order, index
    except (KeyError, TypeError, ValueError):
        errors.add("catalog-invalid")
        return None


def _catalog_reference_sha256(catalog: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_json_bytes(catalog)).hexdigest()


def build_inspection_request(
    catalog: Mapping[str, object], *, max_response_bytes: int
) -> dict[str, object]:
    """Build the fixed, public-only request for ``inspect_omop_schema``."""
    errors = _Errors()
    catalog_index = _catalog_index(catalog, errors)
    if catalog_index is None:
        raise ValueError("invalid catalog")
    if (
        catalog.get("omop_cdm_version") != OMOP_CDM_VERSION
        or catalog.get("allowlist_id") != ALLOWLIST_ID
        or catalog.get("allowlist_version") != ALLOWLIST_VERSION
    ):
        raise ValueError("unsupported catalog")
    if (
        not _is_int(max_response_bytes)
        or not 1 <= max_response_bytes <= HARD_MAX_RESPONSE_BYTES
    ):
        raise ValueError("invalid max_response_bytes")
    return {
        "contract_version": CONTRACT_VERSION,
        "omop_cdm_version": OMOP_CDM_VERSION,
        "allowlist_id": ALLOWLIST_ID,
        "allowlist_version": ALLOWLIST_VERSION,
        "reference_sha256": _catalog_reference_sha256(catalog),
        "max_response_bytes": max_response_bytes,
    }


def _check_type_mismatches(
    value: object,
    *,
    column_index: dict[str, tuple[str, bool]],
    present_columns: set[str],
    errors: _Errors,
) -> None:
    if not isinstance(value, list):
        errors.add("invalid-structure")
        return
    if len(value) > 32:
        errors.add("array-too-long")
    names: list[str] = []
    for mismatch in value:
        if not _closed_object(mismatch, _TYPE_MISMATCH_KEYS, errors):
            continue
        assert isinstance(mismatch, Mapping)
        name = mismatch.get("canonical_column_name")
        if _check_text(
            name,
            errors,
            pattern=_CANONICAL_NAME_RE,
            invalid_code="noncanonical-name",
        ):
            assert isinstance(name, str)
            names.append(name)
            if name not in column_index:
                errors.add("non-allowlisted-name")
            elif name not in present_columns:
                errors.add("inconsistent-total")
        expected = mismatch.get("expected_type_family")
        observed = mismatch.get("observed_type_family")
        for family in (expected, observed):
            if not isinstance(family, str):
                errors.add("invalid-type")
            elif family not in _TYPE_FAMILIES:
                errors.add("unknown-enum")
        if isinstance(name, str) and name in column_index:
            if expected != column_index[name][0] or observed == expected:
                errors.add("inconsistent-mismatch")
    if names:
        _check_sorted_unique(names, errors)


def _check_nullability_mismatches(
    value: object,
    *,
    column_index: dict[str, tuple[str, bool]],
    present_columns: set[str],
    errors: _Errors,
) -> None:
    if not isinstance(value, list):
        errors.add("invalid-structure")
        return
    if len(value) > 32:
        errors.add("array-too-long")
    names: list[str] = []
    for mismatch in value:
        if not _closed_object(mismatch, _NULLABILITY_MISMATCH_KEYS, errors):
            continue
        assert isinstance(mismatch, Mapping)
        name = mismatch.get("canonical_column_name")
        if _check_text(
            name,
            errors,
            pattern=_CANONICAL_NAME_RE,
            invalid_code="noncanonical-name",
        ):
            assert isinstance(name, str)
            names.append(name)
            if name not in column_index:
                errors.add("non-allowlisted-name")
            elif name not in present_columns:
                errors.add("inconsistent-total")
        expected = mismatch.get("expected_nullable")
        observed = mismatch.get("observed_nullable")
        if not isinstance(expected, bool) or not isinstance(observed, bool):
            errors.add("invalid-type")
        elif isinstance(name, str) and name in column_index:
            if expected is not column_index[name][1] or observed is expected:
                errors.add("inconsistent-mismatch")
    if names:
        _check_sorted_unique(names, errors)


def validate_inspection(
    payload: object,
    *,
    catalog: Mapping[str, object],
    capabilities: Mapping[str, object],
    as_of: str,
    raw_size_bytes: int,
) -> tuple[str, ...]:
    """Validate a summary without ever returning response-derived text."""
    errors = _Errors()
    _check_recursive_limits(payload, errors)

    if not _is_int(raw_size_bytes) or raw_size_bytes < 0:
        errors.add("invalid-size")
    else:
        capability_limit = capabilities.get("max_response_bytes")
        effective_limit = HARD_MAX_RESPONSE_BYTES
        if _is_int(capability_limit) and capability_limit > 0:
            effective_limit = min(effective_limit, capability_limit)
        if raw_size_bytes > effective_limit:
            errors.add("response-too-large")

    if validate_capabilities(capabilities):
        errors.add("invalid-capabilities")
    catalog_data = _catalog_index(catalog, errors)
    as_of_value = _parse_rfc3339(as_of, errors)

    if not _closed_object(payload, _INSPECTION_KEYS, errors):
        return errors.result()
    assert isinstance(payload, Mapping)

    if payload.get("contract_version") != CONTRACT_VERSION:
        errors.add("unsupported-contract-version")
    _check_text(payload.get("contract_version"), errors, max_length=8)
    _check_text(
        payload.get("adapter_version"),
        errors,
        pattern=_SEMVER_RE,
        invalid_code="invalid-value",
        max_length=64,
    )
    if payload.get("adapter_version") != capabilities.get("adapter_version"):
        errors.add("adapter-version-mismatch")
    _check_text(
        payload.get("omop_cdm_version"),
        errors,
        pattern=_OMOP_VERSION_RE,
        invalid_code="invalid-value",
        max_length=16,
    )
    _check_text(
        payload.get("allowlist_id"),
        errors,
        pattern=_PUBLIC_TOKEN_RE,
        invalid_code="invalid-value",
    )
    _check_text(
        payload.get("allowlist_version"),
        errors,
        pattern=_SEMVER_RE,
        invalid_code="invalid-value",
        max_length=64,
    )
    _check_text(
        payload.get("reference_sha256"),
        errors,
        pattern=_SHA256_RE,
        invalid_code="invalid-value",
        max_length=64,
    )
    observed_at = _parse_rfc3339(payload.get("observed_at"), errors)
    if observed_at is not None and as_of_value is not None and observed_at > as_of_value:
        errors.add("future-snapshot")
    _check_text(
        payload.get("tbls_version"),
        errors,
        pattern=_SEMVER_RE,
        invalid_code="invalid-value",
        max_length=64,
    )
    scan_status = payload.get("scan_status")
    if not isinstance(scan_status, str):
        errors.add("invalid-type")
    elif scan_status not in _SCAN_STATUS_VALUES:
        errors.add("unknown-enum")
    _check_text(
        payload.get("summary_sha256"),
        errors,
        pattern=_SHA256_RE,
        invalid_code="invalid-value",
        max_length=64,
    )
    _check_nonnegative_int(payload.get("unexpected_table_count"), errors)
    _check_nonnegative_int(payload.get("unexpected_column_count"), errors)

    limitations = _check_string_array(
        payload.get("limitation_codes"),
        errors,
        max_items=64,
        allowed=_LIMITATION_CODES,
    )
    if limitations is not None:
        for code in limitations:
            if code not in _LIMITATION_CODES:
                errors.add("unknown-enum")

    table_counts: list[int] = []
    tables = payload.get("tables")
    if not isinstance(tables, list):
        errors.add("invalid-structure")
    elif catalog_data is not None:
        expected_order, catalog_index = catalog_data
        if len(tables) != len(expected_order):
            errors.add("inconsistent-total")
        if len(tables) > 13:
            errors.add("array-too-long")
        table_names = [
            table.get("canonical_table_name") if isinstance(table, Mapping) else None
            for table in tables
        ]
        if table_names != expected_order:
            errors.add("wrong-table-order")
        valid_table_names = [name for name in table_names if isinstance(name, str)]
        if len(valid_table_names) != len(set(valid_table_names)):
            errors.add("duplicate-array")

        for table in tables:
            if not _closed_object(table, _TABLE_KEYS, errors):
                continue
            assert isinstance(table, Mapping)
            table_name = table.get("canonical_table_name")
            valid_table_name = _check_text(
                table_name,
                errors,
                pattern=_CANONICAL_NAME_RE,
                invalid_code="noncanonical-name",
            )
            column_index = (
                catalog_index.get(table_name, {})
                if valid_table_name and isinstance(table_name, str)
                else {}
            )
            if valid_table_name and not column_index:
                errors.add("non-allowlisted-name")
            allowed_columns = set(column_index)

            presence = table.get("presence")
            if not isinstance(presence, str):
                errors.add("invalid-type")
            elif presence not in _PRESENCE_VALUES:
                errors.add("unknown-enum")

            standard_total = table.get("standard_column_total")
            if _check_nonnegative_int(standard_total, errors) and column_index:
                if standard_total != len(column_index):
                    errors.add("inconsistent-total")

            present = _check_string_array(
                table.get("present_standard_columns"),
                errors,
                max_items=178,
                pattern=_CANONICAL_NAME_RE,
                allowed=allowed_columns,
            )
            missing = _check_string_array(
                table.get("missing_standard_columns"),
                errors,
                max_items=178,
                pattern=_CANONICAL_NAME_RE,
                allowed=allowed_columns,
            )
            present_set = set(present or ())
            missing_set = set(missing or ())
            if present_set & missing_set:
                errors.add("inconsistent-total")
            if column_index:
                if presence == "present" and present_set | missing_set != allowed_columns:
                    errors.add("inconsistent-total")
                elif presence == "missing" and (
                    present_set or missing_set != allowed_columns
                ):
                    errors.add("inconsistent-total")
                elif presence == "unknown" and (present_set or missing_set):
                    errors.add("inconsistent-total")

            _check_type_mismatches(
                table.get("type_mismatches"),
                column_index=column_index,
                present_columns=present_set,
                errors=errors,
            )
            _check_nullability_mismatches(
                table.get("nullability_mismatches"),
                column_index=column_index,
                present_columns=present_set,
                errors=errors,
            )
            for key in ("primary_key_status", "foreign_key_status"):
                value = table.get(key)
                if not isinstance(value, str):
                    errors.add("invalid-type")
                elif value not in _KEY_STATUS_VALUES:
                    errors.add("unknown-enum")
            unexpected = table.get("unexpected_column_count")
            if _check_nonnegative_int(unexpected, errors):
                assert isinstance(unexpected, int)
                table_counts.append(unexpected)

    total_unexpected = payload.get("unexpected_column_count")
    if _is_int(total_unexpected) and total_unexpected >= 0 and table_counts:
        if total_unexpected != sum(table_counts):
            errors.add("inconsistent-total")

    try:
        expected_summary_hash = hashlib.sha256(
            canonical_json_bytes(payload, omit_key="summary_sha256")
        ).hexdigest()
    except (TypeError, ValueError, OverflowError):
        errors.add("canonicalization-error")
    else:
        if payload.get("summary_sha256") != expected_summary_hash:
            errors.add("summary-hash-mismatch")
    return errors.result()


def classify_inspection(
    payload: Mapping[str, object],
    *,
    catalog: Mapping[str, object],
    capabilities: Mapping[str, object],
    as_of: str,
) -> dict[str, object]:
    """Classify a validated summary and return content-free aggregate facts."""
    try:
        raw_size = len(canonical_json_bytes(payload))
    except (TypeError, ValueError, OverflowError):
        return {"status": "invalid-response", "validation_codes": ["canonicalization-error"]}
    errors = validate_inspection(
        payload,
        catalog=catalog,
        capabilities=capabilities,
        as_of=as_of,
        raw_size_bytes=raw_size,
    )
    if errors:
        return {"status": "invalid-response", "validation_codes": list(errors)}

    tables = payload["tables"]
    assert isinstance(tables, list)
    typed_tables = [table for table in tables if isinstance(table, Mapping)]
    missing_table_count = sum(table["presence"] == "missing" for table in typed_tables)
    missing_standard_column_count = sum(
        len(table["missing_standard_columns"]) for table in typed_tables
    )
    type_mismatch_count = sum(len(table["type_mismatches"]) for table in typed_tables)
    nullability_mismatch_count = sum(
        len(table["nullability_mismatches"]) for table in typed_tables
    )
    primary_key_mismatch_count = sum(
        table["primary_key_status"] != "matches" for table in typed_tables
    )
    foreign_key_mismatch_count = sum(
        table["foreign_key_status"] != "matches" for table in typed_tables
    )

    status: str
    if payload["scan_status"] in {"failed", "partial"}:
        status = "unavailable"
    elif payload["omop_cdm_version"] != catalog["omop_cdm_version"]:
        status = "version-mismatch"
    elif payload["omop_cdm_version"] not in capabilities["supported_omop_cdm_versions"]:
        status = "version-mismatch"
    elif (
        payload["allowlist_id"] != catalog["allowlist_id"]
        or payload["allowlist_version"] != catalog["allowlist_version"]
        or payload["reference_sha256"] != _catalog_reference_sha256(catalog)
    ):
        status = "reference-mismatch"
    else:
        observed_at = datetime.fromisoformat(
            str(payload["observed_at"]).replace("Z", "+00:00")
        )
        reference_time = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        age_seconds = (reference_time - observed_at).total_seconds()
        if age_seconds > capabilities["max_snapshot_age_seconds"]:
            status = "stale"
        elif (
            any(table["presence"] != "present" for table in typed_tables)
            or missing_standard_column_count
            or type_mismatch_count
            or nullability_mismatch_count
            or primary_key_mismatch_count
            or foreign_key_mismatch_count
        ):
            status = "incompatible"
        elif payload["unexpected_table_count"] or payload["unexpected_column_count"]:
            status = "compatible-with-deviations"
        else:
            status = "compatible"

    return {
        "status": status,
        "validation_codes": [],
        "missing_table_count": missing_table_count,
        "missing_standard_column_count": missing_standard_column_count,
        "type_mismatch_count": type_mismatch_count,
        "nullability_mismatch_count": nullability_mismatch_count,
        "primary_key_mismatch_count": primary_key_mismatch_count,
        "foreign_key_mismatch_count": foreign_key_mismatch_count,
        "unexpected_table_count": payload["unexpected_table_count"],
        "unexpected_column_count": payload["unexpected_column_count"],
        "limitation_codes": list(payload["limitation_codes"]),
        "summary_sha256": payload["summary_sha256"],
    }
