"""Synthetic 1.1 foreign-key evidence is separate from structural status."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

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
