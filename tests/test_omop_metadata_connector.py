from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills/clin-nav/scripts"
CATALOG_PATH = ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json"
CAPABILITIES_PATH = ROOT / "tests/fixtures/omop_metadata/capabilities-safe.json"
INSPECTION_PATH = ROOT / "tests/fixtures/omop_metadata/inspection-compatible.json"
CONNECTOR_PATH = SKILL_SCRIPTS / "omop_metadata_connector.py"
PACKAGED_CLI = SKILL_SCRIPTS / "check_omop_metadata.py"
ROOT_CLI = ROOT / "scripts/check_omop_metadata.py"
AS_OF = "2026-09-20T12:00:00+08:00"
CLI_ERROR = "OMOP metadata validation failed\n"

sys.path.insert(0, str(SKILL_SCRIPTS))
import check_omop_metadata as packaged_checker
import omop_metadata


@pytest.fixture(scope="module")
def connector_module():
    assert CONNECTOR_PATH.is_file(), "OMOP metadata connector module is required"
    spec = importlib.util.spec_from_file_location(
        "clin_nav_omop_metadata_connector", CONNECTOR_PATH
    )
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


def _bytes(payload: object) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def _rehash(payload: dict[str, object]) -> dict[str, object]:
    payload["summary_sha256"] = hashlib.sha256(
        omop_metadata.canonical_json_bytes(payload, omit_key="summary_sha256")
    ).hexdigest()
    return payload


def _operations(capabilities: object, inspection: object):
    calls: list[object] = []

    def get_capabilities() -> bytes:
        calls.append("get_capabilities")
        return capabilities if isinstance(capabilities, bytes) else _bytes(capabilities)

    def inspect_omop_schema(request: dict[str, object]) -> bytes:
        calls.append(("inspect_omop_schema", request))
        return inspection if isinstance(inspection, bytes) else _bytes(inspection)

    return calls, get_capabilities, inspect_omop_schema


def test_safe_capabilities_call_exact_fixed_request_in_order(
    connector_module, catalog, capabilities, compatible
):
    """Calling inspection early or with a non-catalog request breaks the safety gate."""
    calls, get_capabilities, inspect = _operations(capabilities, compatible)

    result = connector_module.assess_connector(
        get_capabilities,
        inspect,
        catalog=catalog,
        as_of=AS_OF,
        hard_max_bytes=65_536,
    )

    assert calls == [
        "get_capabilities",
        (
            "inspect_omop_schema",
            {
                "contract_version": "1.0",
                "omop_cdm_version": "5.4",
                "allowlist_id": "omop-v54-core-research-v1",
                "allowlist_version": "1.0.0",
                "reference_sha256": hashlib.sha256(
                    CATALOG_PATH.read_bytes()
                ).hexdigest(),
                "max_response_bytes": 65_536,
            },
        ),
    ]
    assert result["status"] == "compatible"


@pytest.mark.parametrize(
    "bad_capabilities",
    (
        lambda value: {**value, "row_access": True},
        lambda value: {key: item for key, item in value.items() if key != "row_access"},
        lambda value: b"{PRIVATE-CAPABILITY-MARKER",
        lambda value: b"x" * 1_025,
    ),
)
def test_bad_capabilities_never_call_inspection(
    connector_module, catalog, capabilities, compatible, bad_capabilities
):
    """Unsafe, incomplete, malformed, or oversized handshakes must stop call two."""
    candidate = bad_capabilities(deepcopy(capabilities))
    calls, get_capabilities, inspect = _operations(candidate, compatible)

    result = connector_module.assess_connector(
        get_capabilities,
        inspect,
        catalog=catalog,
        as_of=AS_OF,
        hard_max_bytes=1_024,
    )

    assert calls == ["get_capabilities"]
    assert result["status"] == "invalid-response"
    assert "PRIVATE-CAPABILITY-MARKER" not in json.dumps(result)


def test_oversized_inspection_is_rejected_before_decode_or_parse(
    connector_module, catalog, capabilities
):
    """An oversized response with an invalid UTF-8 tail must fail on bytes first."""
    candidate_capabilities = deepcopy(capabilities)
    candidate_capabilities["max_response_bytes"] = 128
    oversized = b'{"marker":"PRIVATE-INSPECTION-MARKER"}' + b"\xff" * 128
    calls, get_capabilities, inspect = _operations(candidate_capabilities, oversized)

    result = connector_module.assess_connector(
        get_capabilities, inspect, catalog=catalog, as_of=AS_OF
    )

    assert len(calls) == 2
    assert result == {
        "contract_version": "1.0",
        "status": "invalid-response",
        "validation_codes": ["inspection-response-too-large"],
    }


def test_json_numeric_conversion_failure_is_content_free_and_stops_inspection(
    connector_module, catalog, compatible
):
    """Interpreter integer limits must be treated as malformed JSON, not escape."""
    numeric_bomb = b'{"max_response_bytes":' + (b"9" * 5_000) + b"}"
    calls, get_capabilities, inspect = _operations(numeric_bomb, compatible)

    result = connector_module.assess_connector(
        get_capabilities,
        inspect,
        catalog=catalog,
        as_of=AS_OF,
        hard_max_bytes=8_192,
    )

    assert calls == ["get_capabilities"]
    assert result == {
        "contract_version": "1.0",
        "status": "invalid-response",
        "validation_codes": ["capabilities-invalid-json"],
    }


def test_duplicate_json_keys_are_malformed_and_stop_inspection(
    connector_module, catalog, capabilities, compatible
):
    """Conflicting raw safety declarations must not use last-key-wins parsing."""
    serialized = json.dumps(capabilities, separators=(",", ":"))
    duplicate = serialized.replace(
        '"row_access":false', '"row_access":true,"row_access":false'
    ).encode("utf-8")
    calls, get_capabilities, inspect = _operations(duplicate, compatible)

    result = connector_module.assess_connector(
        get_capabilities, inspect, catalog=catalog, as_of=AS_OF
    )

    assert calls == ["get_capabilities"]
    assert result == {
        "contract_version": "1.0",
        "status": "invalid-response",
        "validation_codes": ["capabilities-invalid-json"],
    }


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
@pytest.mark.parametrize("response_side", ("capabilities", "inspection"))
def test_non_finite_json_constants_are_malformed_before_contract_validation(
    connector_module, catalog, capabilities, compatible, response_side, constant
):
    """Python-only non-finite constants must not enter either JSON contract."""
    capability_json = json.dumps(capabilities, separators=(",", ":"))
    inspection_json = json.dumps(compatible, separators=(",", ":"))
    if response_side == "capabilities":
        capability_json = capability_json.replace(
            '"max_response_bytes":262144', f'"max_response_bytes":{constant}'
        )
    else:
        inspection_json = inspection_json.replace(
            '"unexpected_table_count":0', f'"unexpected_table_count":{constant}'
        )
    calls, get_capabilities, inspect = _operations(
        capability_json.encode("utf-8"), inspection_json.encode("utf-8")
    )

    result = connector_module.assess_connector(
        get_capabilities, inspect, catalog=catalog, as_of=AS_OF
    )

    expected_code = f"{response_side}-invalid-json"
    assert result == {
        "contract_version": "1.0",
        "status": "invalid-response",
        "validation_codes": [expected_code],
    }
    if response_side == "capabilities":
        assert calls == ["get_capabilities"]
    else:
        assert len(calls) == 2
        assert calls[0] == "get_capabilities"
        assert calls[1][0] == "inspect_omop_schema"


@pytest.mark.parametrize("failing_operation", ("capabilities", "inspection"))
def test_adapter_exceptions_become_content_free_unavailable(
    connector_module, catalog, capabilities, compatible, failing_operation
):
    """Adapter identifiers and exception text must never enter the assessment."""
    marker = "PRIVATE-ADAPTER-EXCEPTION-91E7"

    def get_capabilities() -> bytes:
        if failing_operation == "capabilities":
            raise RuntimeError(marker)
        return _bytes(capabilities)

    def inspect_omop_schema(request: dict[str, object]) -> bytes:
        if failing_operation == "inspection":
            raise RuntimeError(marker)
        return _bytes(compatible)

    result = connector_module.assess_connector(
        get_capabilities,
        inspect_omop_schema,
        catalog=catalog,
        as_of=AS_OF,
    )

    assert result["status"] == "unavailable"
    assert result["validation_codes"] == ["connector-unavailable"]
    assert marker not in json.dumps(result)


def _case_payloads(compatible: dict[str, object]):
    deviations = deepcopy(compatible)
    deviations["unexpected_table_count"] = 2
    deviations["unexpected_column_count"] = 3
    deviations["tables"][0]["unexpected_column_count"] = 3
    _rehash(deviations)

    incompatible = deepcopy(compatible)
    person = incompatible["tables"][0]
    missing = person["present_standard_columns"].pop(0)
    person["missing_standard_columns"] = [missing]
    _rehash(incompatible)

    stale = deepcopy(compatible)
    stale["observed_at"] = "2026-09-18T11:59:59+08:00"
    _rehash(stale)
    return (
        ("compatible", compatible),
        ("compatible-with-deviations", deviations),
        ("incompatible", incompatible),
        ("stale", stale),
    )


def test_valid_cases_return_deterministic_aggregate_only_summaries(
    connector_module, catalog, capabilities, compatible
):
    """Default assessments must retain aggregate facts but omit names and adapter data."""
    expected_keys = {
        "contract_version",
        "status",
        "observed_at",
        "omop_cdm_version",
        "allowlist_id",
        "allowlist_version",
        "reference_sha256",
        "missing_table_count",
        "missing_standard_column_count",
        "type_mismatch_count",
        "nullability_mismatch_count",
        "primary_key_mismatch_count",
        "foreign_key_mismatch_count",
        "unexpected_table_count",
        "unexpected_column_count",
        "limitation_codes",
        "summary_sha256",
        "validation_codes",
    }
    for expected_status, payload in _case_payloads(compatible):
        calls, get_capabilities, inspect = _operations(capabilities, payload)
        first = connector_module.assess_connector(
            get_capabilities, inspect, catalog=catalog, as_of=AS_OF
        )
        _, get_capabilities_2, inspect_2 = _operations(capabilities, payload)
        second = connector_module.assess_connector(
            get_capabilities_2, inspect_2, catalog=catalog, as_of=AS_OF
        )

        assert first == second
        assert first["status"] == expected_status
        assert set(first) == expected_keys
        assert len(calls) == 2
        serialized = json.dumps(first)
        assert "adapter" not in serialized.lower()
        assert "PERSON" not in serialized
        assert "BIRTH_DATETIME" not in serialized


def _run_cli(
    cli: Path, capabilities_path: Path, inspection_path: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(cli),
            "--capabilities",
            str(capabilities_path),
            "--input",
            str(inspection_path),
            "--as-of",
            AS_OF,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("cli", (ROOT_CLI, PACKAGED_CLI))
def test_root_and_packaged_clis_emit_the_same_safe_summary(
    tmp_path, cli, capabilities, compatible
):
    """Either entry point must expose only the shared packaged implementation."""
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    capabilities_path.write_bytes(_bytes(capabilities))
    inspection_path.write_bytes(_bytes(compatible))

    result = _run_cli(cli, capabilities_path, inspection_path)

    assert result.returncode == 0
    assert result.stderr == ""
    summary = json.loads(result.stdout)
    assert summary["status"] == "compatible"
    assert "adapter_id" not in summary
    assert "tables" not in summary


def test_root_and_packaged_cli_output_is_byte_identical(
    tmp_path, capabilities, compatible
):
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    capabilities_path.write_bytes(_bytes(capabilities))
    inspection_path.write_bytes(_bytes(compatible))

    root = _run_cli(ROOT_CLI, capabilities_path, inspection_path)
    packaged = _run_cli(PACKAGED_CLI, capabilities_path, inspection_path)

    assert (root.returncode, root.stdout, root.stderr) == (
        packaged.returncode,
        packaged.stdout,
        packaged.stderr,
    )


def test_cli_uses_exit_three_for_valid_but_noncompatible_result(
    tmp_path, capabilities, compatible
):
    stale = deepcopy(compatible)
    stale["observed_at"] = "2026-09-18T11:59:59+08:00"
    _rehash(stale)
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    capabilities_path.write_bytes(_bytes(capabilities))
    inspection_path.write_bytes(_bytes(stale))

    result = _run_cli(ROOT_CLI, capabilities_path, inspection_path)

    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "stale"
    assert result.stderr == ""


@pytest.mark.parametrize("path_kind", ("nonexistent", "directory"))
def test_cli_path_failures_use_fixed_invalid_input_error(
    tmp_path, capabilities, compatible, path_kind
):
    """Local path failures are invalid CLI input, never adapter unavailability."""
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    inspection_path.write_bytes(_bytes(compatible))
    if path_kind == "nonexistent":
        assert not capabilities_path.exists()
    else:
        capabilities_path.mkdir()

    result = _run_cli(ROOT_CLI, capabilities_path, inspection_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert str(capabilities_path) not in result.stderr


def test_cli_unreadable_file_uses_fixed_invalid_input_error(
    tmp_path, monkeypatch, capsys, capabilities, compatible
):
    """A platform-independent injected read denial must remain a CLI error."""
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    capabilities_path.write_bytes(_bytes(capabilities))
    inspection_path.write_bytes(_bytes(compatible))
    original_read_bytes = Path.read_bytes

    def deny_capabilities_read(path: Path) -> bytes:
        if path.resolve() == capabilities_path.resolve():
            raise PermissionError("PRIVATE-READ-ERROR-MARKER")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", deny_capabilities_read)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(PACKAGED_CLI),
            "--capabilities",
            str(capabilities_path),
            "--input",
            str(inspection_path),
            "--as-of",
            AS_OF,
        ],
    )

    with pytest.raises(SystemExit) as caught:
        packaged_checker.main()

    output = capsys.readouterr()
    assert caught.value.code == 2
    assert output.out == ""
    assert output.err == CLI_ERROR
    assert "PRIVATE-READ-ERROR-MARKER" not in output.out + output.err


@pytest.mark.parametrize(
    ("capabilities_path", "inspection_path"),
    (
        (CAPABILITIES_PATH, INSPECTION_PATH),
        (CATALOG_PATH, INSPECTION_PATH),
    ),
)
def test_cli_rejects_internal_inputs_without_disclosing_paths(
    capabilities_path, inspection_path
):
    """Repository and installed-Skill paths may not become checker inputs."""
    result = _run_cli(ROOT_CLI, capabilities_path, inspection_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert str(capabilities_path) not in result.stderr
    assert str(inspection_path) not in result.stderr


@pytest.mark.parametrize("malformed_side", ("capabilities", "inspection"))
def test_malformed_cli_input_never_discloses_marker_or_traceback(
    tmp_path, capabilities, compatible, malformed_side
):
    marker = "PRIVATE-MALFORMED-MARKER-7F31"
    capabilities_path = tmp_path / "capabilities.json"
    inspection_path = tmp_path / "inspection.json"
    capabilities_path.write_bytes(
        (b'{"marker":"' + marker.encode())
        if malformed_side == "capabilities"
        else _bytes(capabilities)
    )
    inspection_path.write_bytes(
        (b'{"marker":"' + marker.encode())
        if malformed_side == "inspection"
        else _bytes(compatible)
    )

    result = _run_cli(ROOT_CLI, capabilities_path, inspection_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    for hidden in (marker, "Traceback", str(capabilities_path), str(inspection_path)):
        assert hidden not in result.stdout + result.stderr
