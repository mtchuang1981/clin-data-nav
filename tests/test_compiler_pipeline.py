"""Capability validation checks declarations, not permission or execution."""

from copy import deepcopy
import importlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/clin-nav/scripts"))


def declaration():
    return {
        "version": "1",
        "operations": ["resolve_concept", "validate_spec", "compile_spec", "run_fixture_test"],
        "spec_format": "SYNTH-STUDY-SPEC@1",
        "fixture": "synthetic",
        "scope": ["feasibility-counts"],
    }


def validate(payload):
    assert importlib.util.find_spec("compiler_pipeline") is not None, "capability validator is absent"
    module = importlib.import_module("compiler_pipeline")
    return module.validate_compiler_pipeline_capability(payload)


@pytest.mark.parametrize("fixture", ["synthetic", "approved-deidentified"])
def test_complete_pipeline_is_valid(fixture):
    payload = declaration()
    payload["fixture"] = fixture
    before = deepcopy(payload)
    assert validate(payload) == ()
    assert payload == before


def test_operation_order_is_not_execution_order():
    payload = declaration()
    payload["operations"].reverse()
    assert validate(payload) == ()


@pytest.mark.parametrize("operations,want", [
    (["resolve_concept", "validate_spec", "compile_spec", "execute_real_data"], "invalid-value"),
    (["resolve_concept", "validate_spec", "compile_spec", "compile_spec"], "duplicate-value"),
    (["resolve_concept", "validate_spec", "compile_spec"], "invalid-value"),
    ([], "invalid-value"),
    (["resolve_concept"] * 5, "limit-exceeded"),
    ([[], "validate_spec", "compile_spec", "run_fixture_test"], "invalid-type"),
    ([1, "validate_spec", "compile_spec", "run_fixture_test"], "invalid-type"),
    (["resolve_concept", "validate_spec", "compile_spec", None], "invalid-type"),
])
def test_unknown_duplicate_and_missing_operations_fail(operations, want):
    payload = declaration()
    payload["operations"] = operations
    assert want in validate(payload)


@pytest.mark.parametrize("payload", [None, True, 1, "1", [], (), set()])
def test_non_dictionary_payloads_fail_closed(payload):
    assert validate(payload) == ("invalid-type",)


@pytest.mark.parametrize("key,value,want", [
    ("version", True, "invalid-type"),
    ("version", 1, "invalid-type"),
    ("version", 1.0, "invalid-type"),
    ("version", "2", "unsupported-version"),
    ("version", "1.2", "unsupported-version"),
    ("version", "", "unsupported-version"),
    ("operations", (), "invalid-type"),
    ("operations", None, "invalid-type"),
    ("scope", ("feasibility-counts",), "invalid-type"),
    ("scope", [None], "invalid-type"),
    ("scope", [[]], "invalid-type"),
    ("scope", ["same", "same"], "duplicate-value"),
    ("fixture", "real-data", "invalid-value"),
    ("fixture", True, "invalid-type"),
    ("fixture", [], "invalid-type"),
    ("spec_format", False, "invalid-type"),
    ("spec_format", [], "invalid-type"),
])
def test_closed_shape_and_exact_types(key, value, want):
    payload = declaration()
    payload[key] = value
    before = deepcopy(payload)
    errors = validate(payload)
    assert want in errors
    assert errors == tuple(sorted(set(errors)))
    assert payload == before


@pytest.mark.parametrize("key", ["version", "operations", "spec_format", "fixture", "scope"])
def test_all_fields_are_required(key):
    payload = declaration()
    del payload[key]
    assert "missing-key" in validate(payload)


def test_unknown_key_and_dictionary_subclass_fail_closed():
    payload = declaration()
    payload["undeclared"] = True
    assert "unknown-key" in validate(payload)
    payload = declaration()
    payload[1] = "not-a-field"
    assert "unknown-key" in validate(payload)

    class UntrustedDictionary(dict):
        def __iter__(self):
            raise AssertionError("subclass methods must not run")

    assert validate(UntrustedDictionary(declaration())) == ("invalid-type",)


@pytest.mark.parametrize("key,value,want", [
    ("spec_format", "", "invalid-value"),
    ("spec_format", "a" * 128, None),
    ("spec_format", "a" * 129, "limit-exceeded"),
    ("spec_format", "SYNTH format v1", "invalid-value"),
    ("spec_format", "SYNTH@1\n", "invalid-value"),
    ("spec_format", "規格@1", "invalid-value"),
    ("scope", [], "invalid-value"),
    ("scope", ["a" * 64], None),
    ("scope", ["a" * 65], "limit-exceeded"),
    ("scope", [""], "invalid-value"),
    ("scope", ["Upper"], "invalid-value"),
    ("scope", ["a--b"], "invalid-value"),
    ("scope", ["a\n"], "invalid-value"),
    ("scope", [f"scope-{i}" for i in range(16)], None),
    ("scope", [f"scope-{i}" for i in range(17)], "limit-exceeded"),
])
def test_string_and_collection_boundaries(key, value, want):
    payload = declaration()
    payload[key] = value
    if want is None:
        assert validate(payload) == ()
    else:
        assert want in validate(payload)


def test_diagnostics_never_echo_synthetic_private_marker():
    payload = declaration()
    payload["SYNTH-PRIVATE-MARKER"] = {"not": "a declared field"}
    payload["operations"][-1] = "SYNTH-PRIVATE-MARKER"
    payload["spec_format"] = "SYNTH-PRIVATE-MARKER\n"
    errors = validate(payload)
    assert errors == ("invalid-value", "unknown-key")
    assert "SYNTH-PRIVATE-MARKER" not in repr(errors)
    assert len(repr(errors)) < 256


def test_string_and_list_subclasses_are_not_accepted():
    class Text(str):
        pass

    class Values(list):
        pass

    for key, value in [("version", Text("1")), ("scope", Values(["safe"]))]:
        payload = declaration()
        payload[key] = value
        assert "invalid-type" in validate(payload)
