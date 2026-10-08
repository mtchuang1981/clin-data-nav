"""Synthetic 1.1 foreign-key evidence is separate from structural status."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/clin-nav/scripts"))

from omop_metadata import (  # noqa: E402
    canonical_json_bytes,
    classify_inspection,
    expected_fk_check_set,
    validate_capabilities,
    validate_inspection,
)
from omop_metadata_connector import assess_connector  # noqa: E402

FIXTURES = ROOT / "tests/fixtures/omop_metadata"
CATALOG = json.loads((ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json").read_text())
AS_OF = "2026-09-20T12:00:00+08:00"


def sample():
    capabilities = json.loads((FIXTURES / "capabilities-safe.json").read_text())
    inspection = json.loads((FIXTURES / "inspection-compatible.json").read_text())
    capabilities["contract_version"] = "1.1"
    inspection["contract_version"] = "1.1"
    inspection["snapshot_binding_sha256"] = "a" * 64
    checks = expected_fk_check_set(CATALOG)
    inspection["dqd_foreign_key_evidence"] = {
        "binding_kind": "content-sha256",
        "snapshot_binding_sha256": "a" * 64,
        "checked_at": "2026-09-20T11:30:00+08:00",
        "reference_sha256": inspection["reference_sha256"],
        "checked_fk_set_sha256": hashlib.sha256(canonical_json_bytes({"checks": checks})).hexdigest(),
        "expected_fk_check_count": len(checks),
        "checked_fk_count": len(checks),
        "failed_fk_count": 0,
    }
    rehash(inspection)
    return capabilities, inspection


def rehash(inspection):
    inspection["summary_sha256"] = hashlib.sha256(
        canonical_json_bytes(inspection, omit_key="summary_sha256")
    ).hexdigest()


def validate(capabilities, inspection):
    return validate_inspection(
        inspection, catalog=CATALOG, capabilities=capabilities,
        as_of=AS_OF, raw_size_bytes=len(canonical_json_bytes(inspection)),
    )


def test_v10_baseline_is_unchanged():
    capabilities = json.loads((FIXTURES / "capabilities-safe.json").read_text())
    inspection = json.loads((FIXTURES / "inspection-compatible.json").read_text())
    assert validate_capabilities(capabilities) == ()
    assert validate(capabilities, inspection) == ()
    assert classify_inspection(inspection, catalog=CATALOG, capabilities=capabilities, as_of=AS_OF)["status"] == "compatible"
    assert "dqd_foreign_key_evidence" not in inspection


def test_v11_complete_strong_evidence_does_not_promote_physical_fk():
    capabilities, inspection = sample()
    inspection["tables"][0]["foreign_key_status"] = "missing"
    rehash(inspection)
    assert validate_capabilities(capabilities, contract_version="1.1") == ()
    assert validate( capabilities, inspection) == ()
    result = classify_inspection(inspection, catalog=CATALOG, capabilities=capabilities, as_of=AS_OF)
    assert result["status"] == "incompatible"
    assert result["foreign_key_mismatch_count"] == 1
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"
    assert len(expected_fk_check_set(CATALOG)) == 79


def test_v11_unsupported_is_unavailable_without_inspection():
    capabilities = json.loads((FIXTURES / "capabilities-safe.json").read_text())
    calls = []
    result = assess_connector(
        lambda **kwargs: json.dumps(capabilities).encode(),
        lambda request: calls.append(request),
        catalog=CATALOG, as_of=AS_OF, contract_version="1.1",
    )
    assert result["status"] == "unavailable"
    assert calls == []


def test_v11_evidence_outcomes_are_independent_of_structural_status():
    capabilities, base = sample()
    mutations = [
        (lambda e: e.update(binding_kind="size-mtime", snapshot_binding_sha256=None), "weak-binding"),
        (lambda e: e.update(checked_at="2026-09-18T11:30:00+08:00"), "stale"),
        (lambda e: e.update(checked_fk_count=78), "incomplete-coverage"),
        (lambda e: e.update(checked_fk_set_sha256="0" * 64), "incomplete-coverage"),
        (lambda e: e.update(failed_fk_count=1), "failed-checks"),
    ]
    for mutate, expected in mutations:
        inspection = deepcopy(base)
        mutate(inspection["dqd_foreign_key_evidence"])
        if expected == "weak-binding":
            inspection["snapshot_binding_sha256"] = None
        rehash(inspection)
        assert validate(capabilities, inspection) == ()
        result = classify_inspection(inspection, catalog=CATALOG, capabilities=capabilities, as_of=AS_OF)
        assert result["status"] == "compatible"
        assert result["dqd_foreign_key_evidence_status"] == expected


def test_v11_missing_evidence_is_unavailable():
    capabilities, inspection = sample()
    inspection["dqd_foreign_key_evidence"] = None
    rehash(inspection)
    assert validate(capabilities, inspection) == ()
    result = classify_inspection(inspection, catalog=CATALOG, capabilities=capabilities, as_of=AS_OF)
    assert result["dqd_foreign_key_evidence_status"] == "unavailable"


def test_v11_missing_field_and_v10_extra_field_are_invalid():
    capabilities, inspection = sample()
    del inspection["dqd_foreign_key_evidence"]
    rehash(inspection)
    assert "missing-key" in validate(capabilities, inspection)

    capabilities["contract_version"] = "1.0"
    inspection["contract_version"] = "1.0"
    inspection["dqd_foreign_key_evidence"] = None
    rehash(inspection)
    assert "unknown-key" in validate(capabilities, inspection)


def test_v11_schema_requires_evidence_only_for_v11():
    schema = json.loads((ROOT / "skills/clin-nav/references/omop-metadata-response.schema.json").read_text())
    summary = schema["$defs"]["inspectionSummary"]
    assert schema["$defs"]["contractVersion"]["enum"] == ["1.0", "1.1"]
    assert summary["properties"]["dqd_foreign_key_evidence"]["oneOf"]
    assert summary["allOf"][0]["then"] == {"required": ["dqd_foreign_key_evidence", "snapshot_binding_sha256"]}
    assert summary["allOf"][0]["else"]["not"]["anyOf"] == [
        {"required": ["dqd_foreign_key_evidence"]},
        {"required": ["snapshot_binding_sha256"]},
    ]


def test_v11_malformed_evidence_and_hash_fail_closed():
    capabilities, base = sample()
    mutations = [
        lambda e: e.update(private_table="SECRET"),
        lambda e: e.update(expected_fk_check_count=1000000),
        lambda e: e.update(snapshot_binding_sha256="bad"),
        lambda e: e.update(snapshot_binding_sha256="b" * 64),
        lambda e: e.update(reference_sha256="0" * 64),
    ]
    for mutate in mutations:
        inspection = deepcopy(base)
        mutate(inspection["dqd_foreign_key_evidence"])
        rehash(inspection)
        assert validate(capabilities, inspection)
    inspection = deepcopy(base)
    inspection["dqd_foreign_key_evidence"]["failed_fk_count"] = 1
    assert "summary-hash-mismatch" in validate(capabilities, inspection)


def test_v11_request_is_explicit_and_summary_contains_only_safe_status():
    capabilities, inspection = sample()
    calls = []
    result = assess_connector(
        lambda **kwargs: json.dumps(capabilities).encode(),
        lambda request: calls.append(request) or json.dumps(inspection).encode(),
        catalog=CATALOG, as_of=AS_OF, contract_version="1.1",
    )
    assert calls[0]["contract_version"] == "1.1"
    assert result["status"] == "compatible"
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"
    assert "snapshot_binding_sha256" not in result


def test_v11_cli_keeps_incompatible_exit_three_with_accepted_evidence(tmp_path):
    capabilities, inspection = sample()
    inspection["tables"][0]["foreign_key_status"] = "missing"
    rehash(inspection)
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    capabilities_path.write_text(json.dumps(capabilities), encoding="utf-8")
    inspection_path.write_text(json.dumps(inspection), encoding="utf-8")
    process = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts/check_omop_metadata.py"),
            "--capabilities", str(capabilities_path), "--input", str(inspection_path),
            "--as-of", AS_OF, "--contract-version", "1.1",
        ],
        capture_output=True, text=True, check=False,
    )
    assert process.returncode == 3
    result = json.loads(process.stdout)
    assert result["status"] == "incompatible"
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"
    assert "snapshot_binding_sha256" not in result


DUCKDB_LIMITATION = "duckdb-cyclic-fk-ddl-limited"


def assess(capabilities, inspection):
    return assess_connector(
        lambda **kwargs: json.dumps(capabilities).encode(),
        lambda request: json.dumps(inspection).encode(),
        catalog=CATALOG, as_of=AS_OF, contract_version="1.1",
    )


def test_v11_duckdb_code_reports_attestation_without_fk_promotion():
    capabilities, inspection = sample()
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    for table in inspection["tables"]:
        table["foreign_key_status"] = "missing"
    rehash(inspection)
    assert validate(capabilities, inspection) == ()
    result = assess(capabilities, inspection)
    assert result["limitation_codes"] == [DUCKDB_LIMITATION]
    assert result["status"] == "incompatible"
    assert result["foreign_key_mismatch_count"] == 13
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"


def test_v10_still_rejects_duckdb_code():
    capabilities = json.loads((FIXTURES / "capabilities-safe.json").read_text())
    inspection = json.loads((FIXTURES / "inspection-compatible.json").read_text())
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    rehash(inspection)
    assert "unknown-enum" in validate(capabilities, inspection)


def test_v11_missing_fk_does_not_infer_duckdb_code():
    capabilities, inspection = sample()
    inspection["tables"][0]["foreign_key_status"] = "missing"
    rehash(inspection)
    result = assess(capabilities, inspection)
    assert result["status"] == "incompatible"
    assert DUCKDB_LIMITATION not in result["limitation_codes"]


def test_v11_duckdb_code_does_not_hide_other_structural_differences():
    capabilities, inspection = sample()
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    inspection["tables"][0]["primary_key_status"] = "different"
    rehash(inspection)
    result = assess(capabilities, inspection)
    assert result["status"] == "incompatible"
    assert result["primary_key_mismatch_count"] == 1
    assert result["foreign_key_mismatch_count"] == 0


@pytest.mark.parametrize("evidence, expected", [(None, "unavailable"), (1, "failed-checks")])
def test_v11_duckdb_code_does_not_supply_or_repair_evidence(evidence, expected):
    capabilities, inspection = sample()
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    if evidence is None:
        inspection["dqd_foreign_key_evidence"] = None
    else:
        inspection["dqd_foreign_key_evidence"]["failed_fk_count"] = evidence
    rehash(inspection)
    result = assess(capabilities, inspection)
    assert result["status"] == "compatible"
    assert result["dqd_foreign_key_evidence_status"] == expected


@pytest.mark.parametrize("scan", ["partial", "failed"])
def test_v11_duckdb_code_cannot_repair_scan_or_leak_summary(scan):
    capabilities, inspection = sample()
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    inspection["scan_status"] = scan
    rehash(inspection)
    assert assess(capabilities, inspection) == {
        "contract_version": "1.1", "status": "unavailable",
        "validation_codes": [], "limitation_codes": [DUCKDB_LIMITATION],
    }


@pytest.mark.parametrize("codes, error", [
    ([DUCKDB_LIMITATION, DUCKDB_LIMITATION], "duplicate-array"),
    ([DUCKDB_LIMITATION, "constraint-metadata-limited"], "unsorted-array"),
    ([DUCKDB_LIMITATION, "not-an-approved-code"], "unknown-enum"),
    ([DUCKDB_LIMITATION] * 65, "array-too-long"),
])
def test_v11_duckdb_code_preserves_closed_array_checks(codes, error):
    capabilities, inspection = sample()
    inspection["limitation_codes"] = codes
    rehash(inspection)
    result = assess(capabilities, inspection)
    assert result["status"] == "invalid-response"
    assert error in result["validation_codes"]
    assert "limitation_codes" not in result


def test_v11_duckdb_code_is_hash_bound():
    capabilities, inspection = sample()
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    assert "summary-hash-mismatch" in validate(capabilities, inspection)
    rehash(inspection)
    assert validate(capabilities, inspection) == ()


def test_v11_duckdb_code_cli_preserves_exit_three(tmp_path):
    capabilities, inspection = sample()
    inspection["limitation_codes"] = [DUCKDB_LIMITATION]
    inspection["tables"][10]["foreign_key_status"] = "missing"
    rehash(inspection)
    cap_path, inspection_path = tmp_path / "cap.json", tmp_path / "inspection.json"
    cap_path.write_text(json.dumps(capabilities), encoding="utf-8")
    inspection_path.write_text(json.dumps(inspection), encoding="utf-8")
    result = subprocess.run([
        sys.executable, str(ROOT / "scripts/check_omop_metadata.py"),
        "--capabilities", str(cap_path), "--input", str(inspection_path),
        "--as-of", AS_OF, "--contract-version", "1.1",
    ], capture_output=True, text=True, check=False)
    assert result.returncode == 3
    summary = json.loads(result.stdout)
    assert summary["status"] == "incompatible"
    assert summary["limitation_codes"] == [DUCKDB_LIMITATION]
    assert summary["dqd_foreign_key_evidence_status"] == "accepted-attestation"
    assert result.stderr == ""


def test_portable_schema_declares_duckdb_code_only_in_v11():
    schema = json.loads((ROOT / "skills/clin-nav/references/omop-metadata-response.schema.json").read_text())
    summary = schema["$defs"]["inspectionSummary"]
    # Read the portable version condition, independently of the Python enums.
    version_rule = next((
        rule for rule in summary["allOf"]
        if "properties" in rule.get("then", {})
        and "limitation_codes" in rule["then"]["properties"]
    ), None)
    assert version_rule is not None, "schema needs version-specific limitation enums"
    assert version_rule["if"]["properties"]["contract_version"]["const"] == "1.1"
    allowed_11 = version_rule["then"]["properties"]["limitation_codes"]["items"]["enum"]
    allowed_10 = version_rule["else"]["properties"]["limitation_codes"]["items"]["enum"]
    assert DUCKDB_LIMITATION in allowed_11
    assert DUCKDB_LIMITATION not in allowed_10
    assert set(allowed_10) == {
        "constraint-metadata-limited", "metadata-permission-limited",
        "snapshot-incomplete", "tbls-normalization-limited",
    }
    assert set(allowed_11) == set(allowed_10) | {DUCKDB_LIMITATION}
    assert set(allowed_11) <= set(summary["properties"]["limitation_codes"]["items"]["enum"])


@pytest.mark.parametrize("version", ["1.0", "1.1"])
@pytest.mark.parametrize("failure", [
    "capabilities-bytes", "capabilities-json", "capabilities-size", "unsafe",
    "catalog", "inspection-exception", "inspection-bytes", "inspection-json",
    "inspection-size", "inspection-invalid", "hard-max",
])
def test_requested_version_is_preserved_on_failures(version, failure):
    capabilities, inspection = sample()
    if version == "1.0":
        capabilities = json.loads((FIXTURES / "capabilities-safe.json").read_text())
        inspection = json.loads((FIXTURES / "inspection-compatible.json").read_text())
    cap_raw, inspection_raw = json.dumps(capabilities).encode(), json.dumps(inspection).encode()
    catalog, maximum = CATALOG, 262144
    if failure == "capabilities-bytes":
        cap_raw = None
    elif failure == "capabilities-json":
        cap_raw = b'{"SYNTHETIC_PRIVATE_MARKER":'
    elif failure == "capabilities-size":
        cap_raw = b" " * 262145
    elif failure == "unsafe":
        capabilities["row_access"] = True
        cap_raw = json.dumps(capabilities).encode()
    elif failure == "catalog":
        catalog = {}
    elif failure == "inspection-bytes":
        inspection_raw = None
    elif failure == "inspection-json":
        inspection_raw = b'{"SYNTHETIC_PRIVATE_MARKER":'
    elif failure == "inspection-size":
        inspection_raw = b" " * 262145
    elif failure == "inspection-invalid":
        inspection["summary_sha256"] = "0" * 64
        inspection_raw = json.dumps(inspection).encode()
    elif failure == "hard-max":
        maximum = 0

    def inspect(request):
        if failure == "inspection-exception":
            raise RuntimeError("SYNTHETIC_PRIVATE_MARKER")
        return inspection_raw

    result = assess_connector(
        lambda **kwargs: cap_raw, inspect,
        catalog=catalog, as_of=AS_OF, contract_version=version, hard_max_bytes=maximum,
    )
    assert result["contract_version"] == version
    assert result["status"] == ("unavailable" if failure == "inspection-exception" else "invalid-response")
    assert set(result) == {"contract_version", "status", "validation_codes"}
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(result)


@pytest.mark.parametrize("value", [[], {}, None])
def test_malformed_inspection_version_fails_closed_without_exception(value):
    capabilities = json.loads((FIXTURES / "capabilities-safe.json").read_text())
    inspection = json.loads((FIXTURES / "inspection-compatible.json").read_text())
    inspection["contract_version"] = value
    rehash(inspection)
    errors = validate(capabilities, inspection)
    assert "invalid-type" in errors
    assert "unsupported-contract-version" in errors
    result = classify_inspection(inspection, catalog=CATALOG, capabilities=capabilities, as_of=AS_OF)
    assert result["status"] == "invalid-response"


@pytest.mark.parametrize("value", [[], {}, None])
def test_malformed_dqd_binding_kind_fails_closed_without_exception(value):
    capabilities, inspection = sample()
    inspection["dqd_foreign_key_evidence"]["binding_kind"] = value
    rehash(inspection)
    assert "invalid-type" in validate(capabilities, inspection)
    result = assess(capabilities, inspection)
    assert result["status"] == "invalid-response"
    assert "dqd_foreign_key_evidence_status" not in result
