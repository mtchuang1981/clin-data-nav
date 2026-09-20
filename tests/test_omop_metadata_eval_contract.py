from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills/clin-nav/scripts"
CATALOG_PATH = ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json"
CAPABILITIES_PATH = ROOT / "tests/fixtures/omop_metadata/capabilities-safe.json"
SCENARIO_PATH = ROOT / "evals/omop-metadata-connector/cases.yaml"
FIXTURE_DIR = ROOT / "tests/fixtures/omop_metadata"
CONNECTOR_PATH = SKILL_SCRIPTS / "omop_metadata_connector.py"
AS_OF = "2026-09-20T12:00:00+08:00"

sys.path.insert(0, str(SKILL_SCRIPTS))

ORIGINAL_EVAL_IDS = {
    "adam-quick-explanation",
    "build-rwe-sap-unavailable",
    "causal-rwd-incomplete-readiness",
    "causal-rwd-tte-handoff",
    "cdisc-variable-definition",
    "descriptive-rwd-no-tte",
    "institutional-sql-without-dictionary",
    "omop-phenotype",
    "sas-optimization-lexjansen",
    "stale-codingbook",
    "teae-sas-spec",
    "tmucrd-public-profile",
}

EXPECTED_CASES = {
    "unauthorized-or-absent": {
        "expected_calls": [],
        "expected_status": "unavailable",
        "execution_maturity_ceiling": "specification only",
    },
    "authorized-compatible-with-deviations": {
        "expected_calls": ["get_capabilities", "inspect_omop_schema"],
        "expected_status": "compatible-with-deviations",
        "execution_maturity_ceiling": "implementation-ready",
    },
    "authorized-incompatible": {
        "expected_calls": ["get_capabilities", "inspect_omop_schema"],
        "expected_status": "incompatible",
        "execution_maturity_ceiling": "specification only",
    },
}


@pytest.fixture(scope="module")
def connector_module():
    assert CONNECTOR_PATH.is_file(), "OMOP metadata connector module is required"
    spec = importlib.util.spec_from_file_location(
        "clin_nav_omop_metadata_connector_eval_contract", CONNECTOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def catalog() -> dict[str, object]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _authorized_operations(capabilities: bytes, inspection: bytes):
    calls: list[str] = []

    def get_capabilities() -> bytes:
        calls.append("get_capabilities")
        return capabilities

    def inspect_omop_schema(request: dict[str, object]) -> bytes:
        calls.append("inspect_omop_schema")
        return inspection

    return calls, get_capabilities, inspect_omop_schema


def test_separate_synthetic_connector_catalog_has_exact_three_cases_and_keys():
    """A renamed, extra, or incomplete scenario would weaken the behavior contract."""
    catalog = _load_yaml(SCENARIO_PATH)

    assert set(catalog) == {"schema_version", "cases"}
    assert catalog["schema_version"] == "1"
    cases = catalog["cases"]
    assert isinstance(cases, list)
    assert len(cases) == 3
    assert len({case["id"] for case in cases}) == 3
    assert {case["id"] for case in cases} == set(EXPECTED_CASES)
    for case in cases:
        assert set(case) == {
            "id",
            "expected_calls",
            "expected_status",
            "execution_maturity_ceiling",
        }
        assert {
            key: case[key]
            for key in EXPECTED_CASES[case["id"]]
        } == EXPECTED_CASES[case["id"]]


def test_existing_response_eval_catalog_remains_the_original_twelve_cases():
    """Connector scenarios must not reinterpret the established response benchmark."""
    catalog = _load_yaml(ROOT / "evals/cases.yaml")
    cases = catalog["cases"]

    assert len(cases) == 12
    assert [case["id"] for case in cases] == [
        "adam-quick-explanation",
        "teae-sas-spec",
        "sas-optimization-lexjansen",
        "institutional-sql-without-dictionary",
        "stale-codingbook",
        "cdisc-variable-definition",
        "omop-phenotype",
        "tmucrd-public-profile",
        "descriptive-rwd-no-tte",
        "causal-rwd-tte-handoff",
        "causal-rwd-incomplete-readiness",
        "build-rwe-sap-unavailable",
    ]
    assert {case["id"] for case in cases} == ORIGINAL_EVAL_IDS


def test_unauthorized_scenario_requires_no_connector_callable():
    """An absent authorization cannot reach either synthetic connector operation."""
    scenario = next(
        case
        for case in _load_yaml(SCENARIO_PATH)["cases"]
        if case["id"] == "unauthorized-or-absent"
    )
    calls: list[str] = []

    assert scenario["expected_calls"] == calls
    assert scenario["expected_status"] == "unavailable"
    assert scenario["execution_maturity_ceiling"] == "specification only"


@pytest.mark.parametrize(
    ("case_id", "fixture_name"),
    (
        ("authorized-compatible-with-deviations", "inspection-deviations.json"),
        ("authorized-incompatible", "inspection-incompatible.json"),
    ),
)
def test_authorized_scenarios_use_the_task_three_harness_and_emit_only_safe_summaries(
    connector_module, catalog, case_id, fixture_name
):
    """Unsafe disclosure or maturity promotion would make a synthetic contract misleading."""
    scenario = next(
        case for case in _load_yaml(SCENARIO_PATH)["cases"] if case["id"] == case_id
    )
    calls, get_capabilities, inspect_omop_schema = _authorized_operations(
        CAPABILITIES_PATH.read_bytes(), (FIXTURE_DIR / fixture_name).read_bytes()
    )

    response = connector_module.assess_connector(
        get_capabilities,
        inspect_omop_schema,
        catalog=catalog,
        as_of=AS_OF,
    )

    assert calls == scenario["expected_calls"]
    assert response["status"] == scenario["expected_status"]
    serialized = json.dumps(response, sort_keys=True)
    for forbidden in (
        "SELECT",
        "SYNTHETIC-PRIVATE-MARKER",
        "LOCAL_NONSTANDARD_OBJECT",
        "executable",
        "validated",
    ):
        assert forbidden not in serialized
    assert scenario["execution_maturity_ceiling"] in {
        "specification only",
        "implementation-ready",
    }
