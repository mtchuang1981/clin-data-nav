"""Consent, handshake and real offline entry-point tests with synthetic inputs."""
import json
import subprocess
import sys

import pytest

from test_omop_metadata_v12 import AS_OF, CATALOG, POLICY, ROOT, rehash, sample_v12
from omop_metadata_connector import assess_connector


def assess(cap, ins, **options):
    return assess_connector(lambda **kwargs: json.dumps(cap).encode(),
                            lambda request: json.dumps(ins).encode(),
                            catalog=CATALOG, as_of=AS_OF,
                            contract_version="1.2", **options)


def test_v12_null_policy_requires_explicit_consent():
    cap, ins = sample_v12()
    calls = []
    def capabilities(**kwargs):
        calls.append(("capabilities", kwargs))
        return json.dumps(cap).encode()
    def inspection(request):
        calls.append(("inspection", request))
        return json.dumps(ins).encode()
    result = assess_connector(capabilities, inspection, catalog=CATALOG, as_of=AS_OF, contract_version="1.2")
    assert result == {"contract_version": "1.2", "status": "unavailable",
                      "validation_codes": ["nonexpiring-dqd-not-authorized"]}
    assert calls == [("capabilities", {"contract_version": "1.2"})]
    calls.clear()
    result = assess_connector(capabilities, inspection, catalog=CATALOG, as_of=AS_OF,
                              contract_version="1.2", allow_nonexpiring_dqd=True)
    assert result["status"] == "compatible"
    assert result[POLICY] is None
    assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"
    assert [c[0] for c in calls] == ["capabilities", "inspection"]
    assert len(calls[1][1]) == 6
    assert "allow_nonexpiring_dqd" not in calls[1][1]
    assert "snapshot_binding_sha256" not in result


@pytest.mark.parametrize("version,value", [
    ("1.0", True), ("1.1", True), ("1.2", 1), ("1.2", 0),
    ("1.2", "yes"), ("1.2", None), ("1.2", []), ("1.2", {}),
])
def test_consent_argument_is_boolean_and_version_scoped(version, value):
    calls = []
    result = assess_connector(lambda **kw: calls.append(kw), lambda req: calls.append(req),
                              catalog=CATALOG, as_of=AS_OF, contract_version=version,
                              allow_nonexpiring_dqd=value)
    assert result == {"contract_version": version, "status": "invalid-response",
                      "validation_codes": ["invalid-nonexpiring-dqd-option"]}
    assert calls == []


def test_finite_policy_cannot_be_overridden_by_consent():
    cap, ins = sample_v12(3600)
    for consent in (False, True):
        result = assess(cap, ins, allow_nonexpiring_dqd=consent)
        assert result["status"] == "compatible"
        assert result["dqd_foreign_key_evidence_status"] == "stale"
        assert result[POLICY] == 3600


@pytest.mark.parametrize("kind,want", [("unsupported", "unavailable"), ("unsafe", "invalid-response"), ("exception", "unavailable")])
def test_v12_unsupported_and_unsafe_capabilities_stop(kind, want):
    cap, ins = sample_v12()
    if kind == "unsupported":
        cap["contract_version"] = "1.1"
        del cap[POLICY]
    elif kind == "unsafe":
        cap["row_access"] = True
    calls = []
    def get_cap(**kwargs):
        calls.append("cap")
        if kind == "exception":
            raise RuntimeError("SYNTHETIC_PRIVATE_MARKER")
        return json.dumps(cap).encode()
    result = assess_connector(get_cap, lambda req: calls.append("inspection"),
                              catalog=CATALOG, as_of=AS_OF, contract_version="1.2",
                              allow_nonexpiring_dqd=True)
    assert result["status"] == want
    assert result["contract_version"] == "1.2"
    assert calls == ["cap"]
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(result)


@pytest.mark.parametrize("kind,want", [("partial", "unavailable"), ("failed", "unavailable"), ("stale", "stale"), ("invalid", "invalid-response")])
def test_v12_partial_invalid_and_stale_outputs_are_redacted(kind, want):
    cap, ins = sample_v12()
    if kind in ("partial", "failed"):
        ins["scan_status"] = kind
    elif kind == "stale":
        ins["observed_at"] = "2026-09-18T11:30:00+08:00"
    else:
        ins["rows"] = "SYNTHETIC_PRIVATE_MARKER"
    rehash(ins)
    result = assess(cap, ins, allow_nonexpiring_dqd=True)
    assert result["status"] == want
    assert set(result) <= {"contract_version", "status", "validation_codes", "limitation_codes"}
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(result)


@pytest.mark.parametrize("raw", [b'{"contract_version":"1.2","contract_version":"1.2"}',
    b'{"v":NaN}', b'{"v":Infinity}', b'\xff', b' ' * 262145,
    b'{"rows":"SYNTHETIC_PRIVATE_MARKER"}', b'{'],
    ids=["duplicate", "nan", "infinity", "utf8", "oversize", "unknown", "syntax"])
def test_v12_json_parsing_remains_closed(raw):
    cap, ins = sample_v12()
    result = assess_connector(lambda **kw: json.dumps(cap).encode(), lambda req: raw,
                              catalog=CATALOG, as_of=AS_OF, contract_version="1.2",
                              allow_nonexpiring_dqd=True)
    assert result["status"] == "invalid-response"
    assert set(result) == {"contract_version", "status", "validation_codes"}
    assert "SYNTHETIC_PRIVATE_MARKER" not in json.dumps(result)


@pytest.mark.parametrize("entry", ["scripts/check_omop_metadata.py", "skills/clin-nav/scripts/check_omop_metadata.py"])
@pytest.mark.parametrize("case,code,status", [
    ("accept", 0, "compatible"), ("no-consent", 3, "unavailable"),
    ("fk", 3, "incompatible"), ("invalid", 2, "invalid-response"),
    ("legacy-flag", 2, None),
])
def test_offline_entry_points_agree(tmp_path, entry, case, code, status):
    cap, ins = sample_v12()
    if case == "fk":
        for table in ins["tables"]:
            table["foreign_key_status"] = "missing"
        rehash(ins)
    elif case == "invalid":
        ins["rows"] = "SYNTHETIC_PRIVATE_MARKER"
        rehash(ins)
    cap_path, ins_path = tmp_path / "cap.json", tmp_path / "ins.json"
    cap_path.write_text(json.dumps(cap), encoding="utf-8")
    ins_path.write_text(json.dumps(ins), encoding="utf-8")
    command = [sys.executable, str(ROOT / entry), "--capabilities", str(cap_path),
               "--input", str(ins_path), "--as-of", AS_OF,
               "--contract-version", "1.1" if case == "legacy-flag" else "1.2"]
    if case != "no-consent":
        command.append("--allow-nonexpiring-dqd")
    process = subprocess.run(command, capture_output=True, text=True, check=False)
    assert process.returncode == code
    assert "SYNTHETIC_PRIVATE_MARKER" not in process.stdout + process.stderr
    if status is None:
        assert process.stdout == ""
        assert process.stderr == "OMOP metadata validation failed\n"
    else:
        result = json.loads(process.stdout)
        assert result["status"] == status
        assert "snapshot_binding_sha256" not in result
        assert "adapter_id" not in result
        assert "tables" not in result
        if case in ("accept", "fk"):
            assert result["dqd_foreign_key_evidence_status"] == "accepted-attestation"
            assert result[POLICY] is None
        if case == "fk":
            assert result["foreign_key_mismatch_count"] == 13
