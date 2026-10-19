"""Validate an optional declaration, never authority or execution readiness.

This pure helper consumes only capabilities.compiler_pipeline. Its caller
handles an absent capability using legacy routing. Explicit null is invalid.
"""

import re

_FIELDS = frozenset({"version", "operations", "spec_format", "fixture", "scope"})
_OPERATIONS = frozenset({"resolve_concept", "validate_spec", "compile_spec", "run_fixture_test"})
_FORMAT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/@+-]*", re.ASCII)
_SCOPE = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", re.ASCII)


def validate_compiler_pipeline_capability(payload: object) -> tuple[str, ...]:
    """Return sorted, content-free error codes, or () for a valid shape.

    Declaration validity does not verify format-version meaning, tool mappings,
    dictionary approval, fixture approval, provenance, or permission to execute.
    """
    if type(payload) is not dict:
        return ("invalid-type",)
    # Reject shape before dictionary lookups: a str-subclass key can execute
    # custom equality during membership tests even in an ordinary dictionary.
    # Size is checked before iterating keys; values are untouched on rejection.
    if len(payload) > len(_FIELDS) or any(
        type(field) is not str or field not in _FIELDS for field in payload
    ):
        return ("unknown-key",)
    errors: set[str] = set()
    if any(field not in payload for field in _FIELDS):
        errors.add("missing-key")

    for field, allowed, max_length in (
        ("version", {"1"}, 16),
        ("fixture", {"synthetic", "approved-deidentified"}, 64),
    ):
        if field not in payload:
            continue
        value = payload[field]
        if type(value) is not str:
            errors.add("invalid-type")
        elif len(value) > max_length:
            errors.add("limit-exceeded")
        elif value not in allowed:
            errors.add("unsupported-version" if field == "version" else "invalid-value")

    if "spec_format" in payload:
        value = payload["spec_format"]
        if type(value) is not str:
            errors.add("invalid-type")
        elif len(value) > 128:
            errors.add("limit-exceeded")
        elif _FORMAT.fullmatch(value) is None:
            errors.add("invalid-value")

    for field, max_items, max_length in (("operations", 4, 64), ("scope", 16, 64)):
        if field not in payload:
            continue
        values = payload[field]
        if type(values) is not list:
            errors.add("invalid-type")
            continue
        if len(values) > max_items:
            errors.add("limit-exceeded")
            continue
        if not values or (field == "operations" and len(values) != 4):
            errors.add("invalid-value")
        seen: set[str] = set()
        for value in values:
            if type(value) is not str:
                errors.add("invalid-type")
                continue
            if len(value) > max_length:
                errors.add("limit-exceeded")
                continue
            if value in seen:
                errors.add("duplicate-value")
            seen.add(value)
            if field == "operations":
                if value not in _OPERATIONS:
                    errors.add("invalid-value")
            elif _SCOPE.fullmatch(value) is None:
                errors.add("invalid-value")
        if field == "operations" and seen != _OPERATIONS:
            errors.add("invalid-value")
    return tuple(sorted(errors))
