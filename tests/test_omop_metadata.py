from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills/clin-nav/scripts/omop_metadata.py"
SCHEMA_PATH = ROOT / "skills/clin-nav/references/omop-metadata-response.schema.json"
CATALOG_PATH = ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json"
FIXTURES = ROOT / "tests/fixtures/omop_metadata"
CAPABILITIES_PATH = FIXTURES / "capabilities-safe.json"
INSPECTION_PATH = FIXTURES / "inspection-compatible.json"
AS_OF = "2026-09-20T12:00:00+08:00"

CAPABILITY_KEYS = {
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
PROHIBITED_KEYS = (
    "database_name",
    "schema_name",
    "comment",
    "sql",
    "error",
    "rows",
)
VALID_SEMVER_2_VALUES = (
    "0.0.0",
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-0.3.7",
    "1.0.0-x.7.z.92",
    "1.0.0-alpha+build.1",
    "1.0.0+20130313144700",
)
INVALID_SEMVER_2_VALUES = (
    "1.0.0-..",
    "01.0.0",
    "1.01.0",
    "1.0.01",
    "1.0.0-01",
    "1.0.0-alpha..1",
    "1.0.0-",
    "1.0.0+",
    "1.0.0+build..1",
    "1.0",
)


@pytest.fixture(scope="module")
def metadata_module():
    assert MODULE_PATH.is_file(), "OMOP metadata validator module is required"
    spec = importlib.util.spec_from_file_location("clin_nav_omop_metadata", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def catalog() -> dict[str, object]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def capabilities() -> dict[str, object]:
    return json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def compatible() -> dict[str, object]:
    return json.loads(INSPECTION_PATH.read_text(encoding="utf-8"))


def _rehash(module, payload: dict[str, object]) -> dict[str, object]:
    payload["summary_sha256"] = hashlib.sha256(
        module.canonical_json_bytes(payload, omit_key="summary_sha256")
    ).hexdigest()
    return payload


def _validation(module, payload, catalog, capabilities, raw_size_bytes=None):
    if raw_size_bytes is None:
        raw_size_bytes = len(module.canonical_json_bytes(payload))
    return module.validate_inspection(
        payload,
        catalog=catalog,
        capabilities=capabilities,
        as_of=AS_OF,
        raw_size_bytes=raw_size_bytes,
    )


def test_portable_schema_is_closed_and_bounded():
    """An open object definition would let private fields cross the boundary."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert set(schema["$defs"]) >= {
        "capabilities",
        "allowlistSupport",
        "inspectionSummary",
        "tableResult",
        "typeMismatch",
        "nullabilityMismatch",
    }
    assert schema["oneOf"] == [
        {"$ref": "#/$defs/capabilities"},
        {"$ref": "#/$defs/inspectionSummary"},
    ]

    def assert_closed_objects(node):
        if isinstance(node, dict):
            if node.get("type") == "object":
                assert node.get("additionalProperties") is False
                assert set(node.get("properties", ())) == set(node.get("required", ()))
            for value in node.values():
                assert_closed_objects(value)
        elif isinstance(node, list):
            for value in node:
                assert_closed_objects(value)

    assert_closed_objects(schema)


def test_canonical_json_bytes_are_deterministic_and_lf_terminated(metadata_module):
    """Insertion order and omitted hashes must not change canonical bytes."""
    left = {"z": "測試", "summary_sha256": "ignored", "a": {"b": 1}}
    right = {"a": {"b": 1}, "summary_sha256": "different", "z": "測試"}
    expected = '{"a":{"b":1},"z":"測試"}\n'.encode()
    assert metadata_module.canonical_json_bytes(
        left, omit_key="summary_sha256"
    ) == expected
    assert metadata_module.canonical_json_bytes(
        right, omit_key="summary_sha256"
    ) == expected


def test_safe_capabilities_are_exact_and_valid(metadata_module, capabilities):
    """The known-safe synthetic handshake must satisfy the closed contract."""
    assert set(capabilities) == CAPABILITY_KEYS
    assert metadata_module.validate_capabilities(capabilities) == ()


@pytest.mark.parametrize("missing_key", sorted(CAPABILITY_KEYS))
def test_every_capability_is_required(metadata_module, capabilities, missing_key):
    """Omitting any safety declaration must fail closed."""
    candidate = deepcopy(capabilities)
    del candidate[missing_key]
    assert "missing-key" in metadata_module.validate_capabilities(candidate)


@pytest.mark.parametrize(
    ("key", "unsafe_value"),
    (
        ("metadata_read_only", False),
        ("row_access", True),
        ("sql_execution", True),
        ("raw_schema_export", True),
        ("tbls_inspection_available", False),
    ),
)
def test_flipped_safety_capability_is_rejected(
    metadata_module, capabilities, key, unsafe_value
):
    """A capability that widens access or disables inspection is unsafe."""
    candidate = deepcopy(capabilities)
    candidate[key] = unsafe_value
    assert "capability-unsafe" in metadata_module.validate_capabilities(candidate)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        (lambda value: value.update(extra="value"), "unknown-key"),
        (
            lambda value: value.update(supported_omop_cdm_versions=[]),
            "unsupported-version",
        ),
        (
            lambda value: value.update(
                supported_omop_cdm_versions=["5.4", "5.4"]
            ),
            "duplicate-array",
        ),
        (
            lambda value: value.update(
                supported_omop_cdm_versions=["5.4", "5.3"]
            ),
            "unsorted-array",
        ),
        (lambda value: value.update(supported_allowlists=[]), "unsupported-allowlist"),
        (lambda value: value.update(max_response_bytes=0), "invalid-byte-limit"),
        (lambda value: value.update(adapter_id="x" * 129), "string-too-long"),
    ),
)
def test_capability_bounds_and_support_are_enforced(
    metadata_module, capabilities, mutation, expected_code
):
    """Malformed or non-covering capability declarations must not be accepted."""
    candidate = deepcopy(capabilities)
    mutation(candidate)
    assert expected_code in metadata_module.validate_capabilities(candidate)


def test_build_inspection_request_is_fixed_and_catalog_bound(
    metadata_module, catalog
):
    """The request must contain only public contract identifiers and a byte cap."""
    expected_hash = hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest()
    assert metadata_module.build_inspection_request(
        catalog, max_response_bytes=65536
    ) == {
        "contract_version": "1.0",
        "omop_cdm_version": "5.4",
        "allowlist_id": "omop-v54-core-research-v1",
        "allowlist_version": "1.0.0",
        "reference_sha256": expected_hash,
        "max_response_bytes": 65536,
    }


def _mutate_catalog_identity(catalog):
    catalog["catalog_id"] = "substituted-public-catalog"


def _mutate_catalog_provenance(catalog):
    catalog["source"]["source_commit"] = "0" * 40


def _mutate_catalog_table_order(catalog):
    catalog["tables"][0], catalog["tables"][1] = (
        catalog["tables"][1],
        catalog["tables"][0],
    )


def _mutate_catalog_column_total(catalog):
    catalog["tables"][0]["columns"].pop()


def _mutate_catalog_public_names(catalog):
    catalog["tables"][0]["canonical_table_name"] = "PRIVATE_TABLE"
    catalog["tables"][0]["columns"][0]["canonical_column_name"] = (
        "PRIVATE_COLUMN"
    )


@pytest.mark.parametrize(
    "mutation",
    (
        _mutate_catalog_identity,
        _mutate_catalog_provenance,
        _mutate_catalog_table_order,
        _mutate_catalog_column_total,
        _mutate_catalog_public_names,
    ),
)
def test_build_request_rejects_any_substituted_catalog(
    metadata_module, catalog, mutation
):
    """Shape-compatible catalog substitutions must not redefine the trust root."""
    candidate = deepcopy(catalog)
    mutation(candidate)
    with pytest.raises(ValueError, match="invalid catalog"):
        metadata_module.build_inspection_request(
            candidate, max_response_bytes=262144
        )


@pytest.mark.parametrize(
    "mutation",
    (
        _mutate_catalog_identity,
        _mutate_catalog_provenance,
        _mutate_catalog_table_order,
        _mutate_catalog_column_total,
        _mutate_catalog_public_names,
    ),
)
def test_validation_rejects_any_substituted_catalog(
    metadata_module, catalog, capabilities, compatible, mutation
):
    """Inspection validation must fail before a substituted catalog defines names."""
    candidate = deepcopy(catalog)
    mutation(candidate)
    assert "catalog-invalid" in _validation(
        metadata_module, compatible, candidate, capabilities
    )


@pytest.mark.parametrize("version", VALID_SEMVER_2_VALUES)
def test_semver_2_versions_are_accepted_consistently(
    metadata_module, catalog, capabilities, compatible, version
):
    """Valid SemVer 2 prerelease/build forms must work in Schema and validator."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    semantic_version_pattern = schema["$defs"]["semanticVersion"]["pattern"]
    assert re.fullmatch(semantic_version_pattern, version)

    candidate_capabilities = deepcopy(capabilities)
    candidate_capabilities["adapter_version"] = version
    candidate_capabilities["supported_allowlists"].insert(
        0,
        {
            "allowlist_id": "aaa-synthetic-public",
            "allowlist_version": version,
        },
    )
    assert metadata_module.validate_capabilities(candidate_capabilities) == ()

    candidate_inspection = deepcopy(compatible)
    candidate_inspection["adapter_version"] = version
    candidate_inspection["allowlist_version"] = version
    candidate_inspection["tbls_version"] = version
    _rehash(metadata_module, candidate_inspection)
    assert _validation(
        metadata_module,
        candidate_inspection,
        catalog,
        candidate_capabilities,
    ) == ()


@pytest.mark.parametrize("version", INVALID_SEMVER_2_VALUES)
def test_invalid_semver_2_versions_are_rejected_consistently(
    metadata_module, catalog, capabilities, compatible, version
):
    """Empty identifiers and numeric leading zeroes must fail in both contracts."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    semantic_version_pattern = schema["$defs"]["semanticVersion"]["pattern"]
    assert re.fullmatch(semantic_version_pattern, version) is None

    candidate_capabilities = deepcopy(capabilities)
    candidate_capabilities["adapter_version"] = version
    assert "invalid-value" in metadata_module.validate_capabilities(
        candidate_capabilities
    )

    candidate_inspection = deepcopy(compatible)
    candidate_inspection["allowlist_version"] = version
    candidate_inspection["tbls_version"] = version
    _rehash(metadata_module, candidate_inspection)
    assert "invalid-value" in _validation(
        metadata_module,
        candidate_inspection,
        catalog,
        capabilities,
    )


def test_exact_compatible_fixture_validates_and_classifies(
    metadata_module, catalog, capabilities, compatible
):
    """The complete synthetic public summary is the compatible baseline."""
    assert _validation(metadata_module, compatible, catalog, capabilities) == ()
    result = metadata_module.classify_inspection(
        compatible, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    )
    assert result["status"] == "compatible"
    assert result["missing_table_count"] == 0
    assert result["missing_standard_column_count"] == 0
    assert result["type_mismatch_count"] == 0
    assert result["nullability_mismatch_count"] == 0


def test_inspection_adapter_version_must_match_capabilities(
    metadata_module, catalog, capabilities, compatible
):
    """A summary from a different adapter version must fail the handshake binding."""
    candidate = deepcopy(compatible)
    candidate["adapter_version"] = "2.0.0"
    _rehash(metadata_module, candidate)
    assert "adapter-version-mismatch" in _validation(
        metadata_module, candidate, catalog, capabilities
    )
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    )["status"] == "invalid-response"


def test_missing_table_and_column_are_valid_incompatible_facts(
    metadata_module, catalog, capabilities, compatible
):
    """Public standard gaps must classify incompatible, not malformed."""
    missing_table = deepcopy(compatible)
    table = missing_table["tables"][0]
    table["presence"] = "missing"
    table["present_standard_columns"] = []
    table["missing_standard_columns"] = sorted(
        column["canonical_column_name"] for column in catalog["tables"][0]["columns"]
    )
    table["primary_key_status"] = "missing"
    table["foreign_key_status"] = "missing"
    _rehash(metadata_module, missing_table)

    missing_column = deepcopy(compatible)
    table = missing_column["tables"][0]
    name = table["present_standard_columns"].pop(0)
    table["missing_standard_columns"] = [name]
    _rehash(metadata_module, missing_column)

    for candidate in (missing_table, missing_column):
        assert _validation(metadata_module, candidate, catalog, capabilities) == ()
        assert metadata_module.classify_inspection(
            candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
        )["status"] == "incompatible"


def test_in_memory_classification_retains_only_public_standard_gap_names(
    metadata_module, catalog, capabilities, compatible
):
    """Downstream routing needs public gaps while aggregate output must filter them."""
    candidate = deepcopy(compatible)
    person = candidate["tables"][0]
    missing_column = person["present_standard_columns"].pop(0)
    person["missing_standard_columns"] = [missing_column]
    measurement = next(
        table
        for table in candidate["tables"]
        if table["canonical_table_name"] == "MEASUREMENT"
    )
    measurement["type_mismatches"] = [
        {
            "canonical_column_name": "MEASUREMENT_DATE",
            "expected_type_family": "date",
            "observed_type_family": "datetime",
        }
    ]
    _rehash(metadata_module, candidate)

    result = metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    )

    assert result["public_standard_gaps"] == {
        "missing_tables": [],
        "missing_columns": [f"PERSON.{missing_column}"],
        "type_mismatch_columns": ["MEASUREMENT.MEASUREMENT_DATE"],
        "nullability_mismatch_columns": [],
        "primary_key_tables": [],
        "foreign_key_tables": [],
    }


def test_each_standard_mismatch_classifies_incompatible(
    metadata_module, catalog, capabilities, compatible
):
    """Type, nullability, PK, and FK drift must block compatibility."""
    candidates = []

    type_mismatch = deepcopy(compatible)
    measurement = next(
        table
        for table in type_mismatch["tables"]
        if table["canonical_table_name"] == "MEASUREMENT"
    )
    measurement["type_mismatches"] = [
        {
            "canonical_column_name": "MEASUREMENT_DATE",
            "expected_type_family": "date",
            "observed_type_family": "datetime",
        }
    ]
    candidates.append(type_mismatch)

    nullability = deepcopy(compatible)
    person = nullability["tables"][0]
    person["nullability_mismatches"] = [
        {
            "canonical_column_name": "PERSON_ID",
            "expected_nullable": False,
            "observed_nullable": True,
        }
    ]
    candidates.append(nullability)

    primary_key = deepcopy(compatible)
    primary_key["tables"][0]["primary_key_status"] = "different"
    candidates.append(primary_key)

    foreign_key = deepcopy(compatible)
    foreign_key["tables"][0]["foreign_key_status"] = "unknown"
    candidates.append(foreign_key)

    for candidate in candidates:
        _rehash(metadata_module, candidate)
        assert _validation(metadata_module, candidate, catalog, capabilities) == ()
        assert metadata_module.classify_inspection(
            candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
        )["status"] == "incompatible"


def test_unexpected_counts_classify_compatible_with_deviations(
    metadata_module, catalog, capabilities, compatible
):
    """Redacted non-standard counts are permitted but remain visible as deviations."""
    candidate = deepcopy(compatible)
    candidate["unexpected_table_count"] = 2
    candidate["unexpected_column_count"] = 3
    candidate["tables"][0]["unexpected_column_count"] = 3
    _rehash(metadata_module, candidate)
    assert _validation(metadata_module, candidate, catalog, capabilities) == ()
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    )["status"] == "compatible-with-deviations"


@pytest.mark.parametrize(
    ("mutation", "status"),
    (
        (lambda value: value.update(observed_at="2026-09-18T11:59:59+08:00"), "stale"),
        (lambda value: value.update(omop_cdm_version="5.3"), "version-mismatch"),
        (lambda value: value.update(allowlist_version="9.9.9"), "reference-mismatch"),
        (lambda value: value.update(reference_sha256="0" * 64), "reference-mismatch"),
        (lambda value: value.update(scan_status="partial"), "unavailable"),
        (lambda value: value.update(scan_status="failed"), "unavailable"),
    ),
)
def test_policy_states_have_explicit_classification(
    metadata_module, catalog, capabilities, compatible, mutation, status
):
    """Valid policy mismatches must not be mistaken for structural corruption."""
    candidate = deepcopy(compatible)
    mutation(candidate)
    _rehash(metadata_module, candidate)
    assert _validation(metadata_module, candidate, catalog, capabilities) == ()
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    )["status"] == status


@pytest.mark.parametrize("scan_status", ("partial", "failed"))
def test_incomplete_scans_classify_without_response_facts(
    metadata_module, catalog, capabilities, compatible, scan_status
):
    """An unavailable scan must not publish its otherwise valid response facts."""
    candidate = deepcopy(compatible)
    candidate["scan_status"] = scan_status
    candidate["limitation_codes"] = ["snapshot-incomplete"]
    candidate["unexpected_table_count"] = 7
    candidate["observed_at"] = "2026-09-20T10:00:00+08:00"
    candidate["allowlist_id"] = "private-marker-8c24"
    _rehash(metadata_module, candidate)

    assert _validation(metadata_module, candidate, catalog, capabilities) == ()
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    ) == {
        "status": "unavailable",
        "validation_codes": [],
        "limitation_codes": ["snapshot-incomplete"],
    }


@pytest.mark.parametrize(
    ("key", "marker"),
    (
        ("allowlist_id", "private-marker-8c24"),
        ("allowlist_version", "1.0.0+private-marker-8c24"),
    ),
)
def test_reference_mismatch_classifies_without_untrusted_identity(
    metadata_module, catalog, capabilities, compatible, key, marker
):
    """A syntactically valid private token cannot become a public identifier."""
    candidate = deepcopy(compatible)
    candidate[key] = marker
    _rehash(metadata_module, candidate)

    assert _validation(metadata_module, candidate, catalog, capabilities) == ()
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    ) == {"status": "reference-mismatch", "validation_codes": []}


@pytest.mark.parametrize(
    ("mutation", "status"),
    (
        (lambda value: value.update(omop_cdm_version="5.3"), "version-mismatch"),
        (lambda value: value.update(observed_at="2026-09-18T11:59:59+08:00"), "stale"),
    ),
)
def test_noncomparable_policy_states_classify_without_response_facts(
    metadata_module, catalog, capabilities, compatible, mutation, status
):
    """A version mismatch or expired snapshot cannot authorize fact reporting."""
    candidate = deepcopy(compatible)
    mutation(candidate)
    candidate["unexpected_table_count"] = 7
    _rehash(metadata_module, candidate)

    assert _validation(metadata_module, candidate, catalog, capabilities) == ()
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    ) == {"status": status, "validation_codes": []}


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        (lambda value: value.update(extra="closed"), "unknown-key"),
        (lambda value: value.update(scan_status="other"), "unknown-enum"),
        (lambda value: value.update(unexpected_table_count=-1), "negative-count"),
        (
            lambda value: value.update(unexpected_table_count=2**31),
            "count-too-large",
        ),
        (
            lambda value: value["tables"].__setitem__(
                0, {**value["tables"][0], "standard_column_total": 999}
            ),
            "inconsistent-total",
        ),
        (
            lambda value: value["tables"].reverse(),
            "wrong-table-order",
        ),
        (
            lambda value: value["tables"][0]["present_standard_columns"].append(
                value["tables"][0]["present_standard_columns"][0]
            ),
            "duplicate-array",
        ),
        (
            lambda value: value["tables"][0]["present_standard_columns"].reverse(),
            "unsorted-array",
        ),
        (
            lambda value: value["tables"][0].update(
                canonical_table_name="PRIVATE_TABLE"
            ),
            "non-allowlisted-name",
        ),
        (
            lambda value: value["tables"][0]["present_standard_columns"].__setitem__(
                0, "PRIVATE_COLUMN"
            ),
            "non-allowlisted-name",
        ),
        (lambda value: value.update(observed_at="not-rfc3339"), "invalid-timestamp"),
        (lambda value: value.update(adapter_version="x" * 129), "string-too-long"),
        (
            lambda value: value.update(limitation_codes=["snapshot-incomplete"] * 65),
            "array-too-long",
        ),
    ),
)
def test_malformed_or_overdisclosing_summary_fails_closed(
    metadata_module,
    catalog,
    capabilities,
    compatible,
    mutation,
    expected_code,
):
    """Every closed-contract violation must return a stable content-free code."""
    candidate = deepcopy(compatible)
    mutation(candidate)
    _rehash(metadata_module, candidate)
    errors = _validation(metadata_module, candidate, catalog, capabilities)
    assert expected_code in errors
    assert all("PRIVATE" not in code and "/" not in code for code in errors)
    assert metadata_module.classify_inspection(
        candidate, catalog=catalog, capabilities=capabilities, as_of=AS_OF
    )["status"] == "invalid-response"


@pytest.mark.parametrize("prohibited_key", PROHIBITED_KEYS)
def test_prohibited_keys_never_cross_the_contract(
    metadata_module, catalog, capabilities, compatible, prohibited_key
):
    """Local identifiers, SQL, errors, and row content must be rejected by key shape."""
    candidate = deepcopy(compatible)
    candidate["tables"][0][prohibited_key] = "synthetic-marker"
    _rehash(metadata_module, candidate)
    errors = _validation(metadata_module, candidate, catalog, capabilities)
    assert "prohibited-key" in errors
    assert "synthetic-marker" not in repr(errors)


def test_mismatch_arrays_are_closed_sorted_unique_and_catalog_bound(
    metadata_module, catalog, capabilities, compatible
):
    """Mismatch details may expose only sorted canonical public columns."""
    candidate = deepcopy(compatible)
    candidate["tables"][0]["type_mismatches"] = [
        {
            "canonical_column_name": "YEAR_OF_BIRTH",
            "expected_type_family": "integer",
            "observed_type_family": "string",
        },
        {
            "canonical_column_name": "PERSON_ID",
            "expected_type_family": "integer",
            "observed_type_family": "string",
        },
    ]
    _rehash(metadata_module, candidate)
    assert "unsorted-array" in _validation(
        metadata_module, candidate, catalog, capabilities
    )

    candidate["tables"][0]["type_mismatches"] = [
        {
            "canonical_column_name": "PRIVATE_COLUMN",
            "expected_type_family": "integer",
            "observed_type_family": "string",
        }
    ]
    _rehash(metadata_module, candidate)
    assert "non-allowlisted-name" in _validation(
        metadata_module, candidate, catalog, capabilities
    )


def test_size_depth_timestamp_and_hash_guards_fail_closed(
    metadata_module, catalog, capabilities, compatible
):
    """Pre-parse size, nesting, chronology, and canonical hashes are hard gates."""
    assert "response-too-large" in _validation(
        metadata_module,
        compatible,
        catalog,
        capabilities,
        raw_size_bytes=capabilities["max_response_bytes"] + 1,
    )

    nested = deepcopy(compatible)
    nested["extra"] = {"a": {"b": {"c": {"d": {"e": {"f": {}}}}}}}
    _rehash(metadata_module, nested)
    assert "nesting-too-deep" in _validation(
        metadata_module, nested, catalog, capabilities
    )

    future = deepcopy(compatible)
    future["observed_at"] = "2026-09-20T12:00:01+08:00"
    _rehash(metadata_module, future)
    assert "future-snapshot" in _validation(
        metadata_module, future, catalog, capabilities
    )

    changed = deepcopy(compatible)
    changed["unexpected_table_count"] = 1
    assert "summary-hash-mismatch" in _validation(
        metadata_module, changed, catalog, capabilities
    )


def test_validation_codes_are_deterministic_content_free_and_json_safe(
    metadata_module, catalog, capabilities, compatible
):
    """Multiple failures must return a stable deduplicated tuple without input text."""
    candidate = deepcopy(compatible)
    candidate["database_name"] = "do-not-leak-this"
    candidate["unexpected_table_count"] = -7
    first = _validation(metadata_module, candidate, catalog, capabilities)
    second = _validation(metadata_module, candidate, catalog, capabilities)
    assert first == second == tuple(sorted(set(first)))
    assert "do-not-leak-this" not in json.dumps(first)
    assert "prohibited-key" in first
    assert "negative-count" in first
    assert "summary-hash-mismatch" in first


def test_fixture_timestamp_is_timezone_aware(compatible):
    """The baseline snapshot must remain an explicit RFC 3339 instant."""
    parsed = datetime.fromisoformat(compatible["observed_at"])
    assert parsed.tzinfo is not None
    assert parsed.astimezone(timezone.utc).isoformat() == "2026-09-20T03:30:00+00:00"
