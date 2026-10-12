"""Synthetic policy tests: null removes age expiry, not evidence safeguards."""
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/clin-nav/scripts"))
from omop_metadata import (  # noqa: E402
    build_inspection_request, canonical_json_bytes, classify_inspection,
    expected_fk_check_set, validate_capabilities, validate_inspection,
)

FIXTURES = ROOT / "tests/fixtures/omop_metadata"
CATALOG = json.loads((ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json").read_text(encoding="utf-8"))
AS_OF = "2026-09-20T12:00:00+08:00"
POLICY = "max_dqd_evidence_age_seconds"


def rehash(inspection):
    inspection["summary_sha256"] = hashlib.sha256(
        canonical_json_bytes(inspection, omit_key="summary_sha256")
    ).hexdigest()


def sample_v12(limit=None, *, checked_at="2025-09-20T11:30:00+08:00"):
    cap = json.loads((FIXTURES / "capabilities-safe.json").read_text(encoding="utf-8"))
    ins = json.loads((FIXTURES / "inspection-compatible.json").read_text(encoding="utf-8"))
    cap.update(contract_version="1.2", **{POLICY: limit})
    ins.update(contract_version="1.2", snapshot_binding_sha256="a" * 64, **{POLICY: limit})
    ins["dqd_foreign_key_evidence"] = {
        "binding_kind": "content-sha256", "snapshot_binding_sha256": "a" * 64,
        "checked_at": checked_at, "reference_sha256": ins["reference_sha256"],
        "checked_fk_set_sha256": hashlib.sha256(canonical_json_bytes(
            {"checks": expected_fk_check_set(CATALOG)})).hexdigest(),
        "expected_fk_check_count": 79, "checked_fk_count": 79, "failed_fk_count": 0,
    }
    rehash(ins)
    return cap, ins


def validate(cap, ins):
    return validate_inspection(ins, catalog=CATALOG, capabilities=cap,
                               as_of=AS_OF, raw_size_bytes=len(canonical_json_bytes(ins)))


def classify(cap, ins):
    return classify_inspection(ins, catalog=CATALOG, capabilities=cap, as_of=AS_OF)


def test_v12_null_policy_preserves_strong_attestation():
    cap, ins = sample_v12()
    assert validate_capabilities(cap, contract_version="1.2") == ()
    assert validate(cap, ins) == ()
    result = classify(cap, ins)
    assert result["status"] == "compatible"
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"
    assert result[POLICY] is None


@pytest.mark.parametrize("age,want", [(3599, "accepted-attestation"), (3600, "accepted-attestation"), (3601, "stale")])
def test_v12_finite_age_boundary(age, want):
    checked = (datetime.fromisoformat(AS_OF) - timedelta(seconds=age)).isoformat()
    cap, ins = sample_v12(3600, checked_at=checked)
    result = classify(cap, ins)
    assert result["status"] == "compatible"
    assert result["dqd_foreign_key_evidence_status"] == want
    assert result[POLICY] == 3600


def test_v12_metadata_age_is_independent():
    cap, ins = sample_v12()
    ins["observed_at"] = (datetime.fromisoformat(AS_OF) - timedelta(seconds=86401)).isoformat()
    rehash(ins)
    assert classify(cap, ins) == {"status": "stale", "validation_codes": []}


@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "86400", [], {}, 31536001])
def test_v12_invalid_policy_types_and_missing_key(value):
    cap, ins = sample_v12(value)
    assert validate_capabilities(cap, contract_version="1.2")
    assert classify(cap, ins)["status"] == "invalid-response"


@pytest.mark.parametrize("where", ["capability", "inspection"])
def test_v12_missing_policy_is_not_null(where):
    cap, ins = sample_v12()
    if where == "capability":
        del cap[POLICY]
        assert "missing-key" in validate_capabilities(cap, contract_version="1.2")
    else:
        del ins[POLICY]
        rehash(ins)
        assert "missing-key" in validate(cap, ins)


def test_v12_policy_mismatch_and_hash_tamper():
    cap, ins = sample_v12()
    ins[POLICY] = 86400
    assert "summary-hash-mismatch" in validate(cap, ins)
    rehash(ins)
    assert "evidence-age-policy-mismatch" in validate(cap, ins)
    cap[POLICY] = 86400
    assert validate(cap, ins) == ()


@pytest.mark.parametrize("mutation,want", [
    ("missing", "unavailable"), ("weak", "weak-binding"),
    ("coverage", "incomplete-coverage"), ("set", "incomplete-coverage"),
    ("failed", "failed-checks"),
])
def test_v12_null_does_not_repair_evidence(mutation, want):
    cap, ins = sample_v12()
    e = ins["dqd_foreign_key_evidence"]
    if mutation == "missing":
        ins["dqd_foreign_key_evidence"] = None
    elif mutation == "weak":
        e.update(binding_kind="size-mtime", snapshot_binding_sha256=None)
        ins["snapshot_binding_sha256"] = None
    elif mutation == "coverage":
        e["checked_fk_count"] = 78
    elif mutation == "set":
        e["checked_fk_set_sha256"] = "0" * 64
    else:
        e["failed_fk_count"] = 1
    rehash(ins)
    result = classify(cap, ins)
    assert result["status"] == "compatible"
    assert result["dqd_foreign_key_evidence_status"] == want


@pytest.mark.parametrize("key,value,code", [
    ("snapshot_binding_sha256", "b" * 64, "evidence-binding-mismatch"),
    ("reference_sha256", "0" * 64, "evidence-reference-mismatch"),
    ("checked_at", "2026-09-21T12:00:00+08:00", "future-snapshot"),
    ("checked_at", "2026-09-20T11:31:00+08:00", "evidence-time-order-invalid"),
])
def test_v12_binding_reference_and_time_fail_closed(key, value, code):
    cap, ins = sample_v12()
    ins["dqd_foreign_key_evidence"][key] = value
    rehash(ins)
    result = classify(cap, ins)
    assert result["status"] == "invalid-response"
    assert code in result["validation_codes"]
    assert POLICY not in result


def test_v12_constraints_remain_independent():
    cap, ins = sample_v12()
    ins["limitation_codes"] = ["duckdb-cyclic-fk-ddl-limited"]
    for table in ins["tables"]:
        table["foreign_key_status"] = "missing"
    rehash(ins)
    result = classify(cap, ins)
    assert result["status"] == "incompatible"
    assert result["foreign_key_mismatch_count"] == 13
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"


@pytest.mark.parametrize("version", ["1.0", "1.1"])
def test_legacy_versions_reject_policy_fields(version):
    cap, ins = sample_v12()
    cap["contract_version"] = ins["contract_version"] = version
    if version == "1.0":
        del ins["snapshot_binding_sha256"]
        del ins["dqd_foreign_key_evidence"]
    rehash(ins)
    assert "unknown-key" in validate_capabilities(cap, contract_version=version)
    assert "unknown-key" in validate(cap, ins)
    del cap[POLICY]
    del ins[POLICY]
    rehash(ins)
    assert validate_capabilities(cap, contract_version=version) == ()
    assert validate(cap, ins) == ()
    result = classify(cap, ins)
    assert result["status"] == "compatible"
    assert POLICY not in result
    if version == "1.1":
        assert result["dqd_foreign_key_evidence_status"] == "stale"


def test_v12_request_keeps_six_public_fields():
    request = build_inspection_request(CATALOG, max_response_bytes=262144, contract_version="1.2")
    assert request == {
        "contract_version": "1.2", "omop_cdm_version": "5.4",
        "allowlist_id": "omop-v54-core-research-v1", "allowlist_version": "1.0.0",
        "reference_sha256": "300646898e87297b8b75b013fd8398b361e0426e89ec8bfe698757d5f57b0e1e",
        "max_response_bytes": 262144,
    }


def test_v12_schema_policy_shape_matches_validator():
    schema = json.loads((ROOT / "skills/clin-nav/references/omop-metadata-response.schema.json").read_text(encoding="utf-8"))
    assert schema["$defs"]["contractVersion"]["enum"] == ["1.0", "1.1", "1.2"]
    assert schema["$defs"]["dqdEvidenceAge"]["oneOf"] == [
        {"type": "null"}, {"type": "integer", "minimum": 1, "maximum": 31536000},
    ]
    for name in ("capabilities", "inspectionSummary"):
        shape = schema["$defs"][name]
        assert shape["additionalProperties"] is False
        assert shape["properties"][POLICY] == {"$ref": "#/$defs/dqdEvidenceAge"}
        rule = next(rule for rule in shape["allOf"] if rule.get("then", {}).get("required") == [POLICY])
        assert rule["if"]["properties"]["contract_version"] == {"const": "1.2"}
        assert rule["else"] == {"not": {"required": [POLICY]}}


@pytest.mark.parametrize("limit", [1, 31536000])
def test_v12_valid_integer_policy_bounds(limit):
    cap, ins = sample_v12(limit, checked_at="2026-09-20T11:30:00+08:00")
    assert validate_capabilities(cap, contract_version="1.2") == ()
    assert validate(cap, ins) == ()
