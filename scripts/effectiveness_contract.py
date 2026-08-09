"""Validate public effectiveness-evaluation contracts."""

from __future__ import annotations

from pathlib import Path
import re

import yaml

from scripts.evaluate_response import OUTPUT_DEPTHS


ROOT = Path(__file__).resolve().parents[1]
CATALOG_KEYS = {"schema_version", "task_pairs"}
PAIR_KEYS = {
    "id",
    "output_depth",
    "expected_minutes",
    "difficulty",
    "mandatory_criteria",
    "quality_criteria",
    "variants",
}
VARIANT_KEYS = {"prompt"}
RUBRIC_KEYS = {
    "schema_version",
    "minimum_quality_fraction",
    "criteria",
    "critical_violations",
}
CRITERION_KEYS = {"id", "kind", "description"}
CRITICAL_VIOLATION_KEYS = {"id", "description"}
PAIR_ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def ensure_external_path(path: Path, repository_root: Path = ROOT) -> Path:
    resolved = path.resolve()
    if resolved == repository_root.resolve() or resolved.is_relative_to(
        repository_root.resolve()
    ):
        raise ValueError("human-study output must be outside the repository")
    return resolved


def validate_effectiveness_contract(catalog: object, rubric: object) -> list[str]:
    """Return deterministic closed-schema errors for public task contracts."""
    errors: list[str] = []
    _validate_catalog_shape(catalog, errors)
    _validate_rubric_shape(rubric, errors)
    if not isinstance(catalog, dict) or not isinstance(rubric, dict):
        return errors

    criteria = _validate_criteria(rubric, errors)
    _validate_critical_violations(rubric, errors)
    _validate_pairs(catalog, criteria, errors)
    return errors


def load_effectiveness_contract(
    tasks_path: Path, rubric_path: Path
) -> tuple[dict, dict]:
    """Load UTF-8 public contracts and reject every invalid schema condition."""
    catalog = yaml.safe_load(tasks_path.read_text(encoding="utf-8"))
    rubric = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    errors = validate_effectiveness_contract(catalog, rubric)
    if errors:
        raise ValueError("invalid effectiveness contract: " + "; ".join(errors))
    assert isinstance(catalog, dict)
    assert isinstance(rubric, dict)
    return catalog, rubric


def task_variants(catalog: dict) -> tuple[dict, ...]:
    """Expand paired tasks into catalog-ordered public task variants."""
    return tuple(
        {
            "pair_id": pair["id"],
            "output_depth": pair["output_depth"],
            "expected_minutes": pair["expected_minutes"],
            "difficulty": pair["difficulty"],
            "variant": variant,
            "prompt": pair["variants"][variant]["prompt"],
        }
        for pair in catalog["task_pairs"]
        for variant in ("A", "B")
    )


def _validate_catalog_shape(catalog: object, errors: list[str]) -> None:
    if not isinstance(catalog, dict):
        errors.append("catalog: must be a mapping")
        return
    _validate_exact_keys("catalog", catalog, CATALOG_KEYS, errors)
    if catalog.get("schema_version") != "1":
        errors.append('catalog: schema_version must be "1"')
    if not isinstance(catalog.get("task_pairs"), list):
        errors.append("catalog: task_pairs must be a list")


def _validate_rubric_shape(rubric: object, errors: list[str]) -> None:
    if not isinstance(rubric, dict):
        errors.append("rubric: must be a mapping")
        return
    _validate_exact_keys("rubric", rubric, RUBRIC_KEYS, errors)
    if rubric.get("schema_version") != "1":
        errors.append('rubric: schema_version must be "1"')
    fraction = rubric.get("minimum_quality_fraction")
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float)) or fraction != 0.8:
        errors.append("rubric: minimum_quality_fraction must be numeric 0.8")
    if not isinstance(rubric.get("criteria"), list):
        errors.append("rubric: criteria must be a list")
    if not isinstance(rubric.get("critical_violations"), list):
        errors.append("rubric: critical_violations must be a list")


def _validate_criteria(rubric: dict, errors: list[str]) -> dict[str, str]:
    criteria_by_id: dict[str, str] = {}
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list):
        return criteria_by_id
    if not criteria:
        errors.append("rubric: criteria must not be empty")
    for index, criterion in enumerate(criteria):
        label = f"criterion {index}"
        if not isinstance(criterion, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_exact_keys(label, criterion, CRITERION_KEYS, errors)
        criterion_id = criterion.get("id")
        if not isinstance(criterion_id, str) or not criterion_id:
            errors.append(f"{label}: id must be a non-empty string")
            continue
        if criterion_id in criteria_by_id:
            errors.append(f"duplicate criterion id: {criterion_id}")
        kind = criterion.get("kind")
        if kind not in {"mandatory", "quality"}:
            errors.append(f"criterion {criterion_id}: kind must be mandatory or quality")
        else:
            criteria_by_id[criterion_id] = kind
        if not isinstance(criterion.get("description"), str) or not criterion["description"].strip():
            errors.append(f"criterion {criterion_id}: description must be a non-empty string")
    return criteria_by_id


def _validate_critical_violations(rubric: dict, errors: list[str]) -> None:
    violations = rubric.get("critical_violations")
    if not isinstance(violations, list):
        return
    violation_ids: set[str] = set()
    for index, violation in enumerate(violations):
        label = f"critical violation {index}"
        if not isinstance(violation, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_exact_keys(label, violation, CRITICAL_VIOLATION_KEYS, errors)
        violation_id = violation.get("id")
        if not isinstance(violation_id, str) or not violation_id:
            errors.append(f"{label}: id must be a non-empty string")
        elif violation_id in violation_ids:
            errors.append(f"duplicate critical violation id: {violation_id}")
        else:
            violation_ids.add(violation_id)
        if not isinstance(violation.get("description"), str) or not violation["description"].strip():
            errors.append(f"{label}: description must be a non-empty string")


def _validate_pairs(catalog: dict, criteria: dict[str, str], errors: list[str]) -> None:
    pairs = catalog.get("task_pairs")
    if not isinstance(pairs, list):
        return
    pair_ids: set[str] = set()
    for index, pair in enumerate(pairs):
        label = _pair_label(pair, index)
        if not isinstance(pair, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_exact_keys(label, pair, PAIR_KEYS, errors)
        pair_id = pair.get("id")
        if not isinstance(pair_id, str) or not PAIR_ID_PATTERN.fullmatch(pair_id):
            errors.append(f"{label}: id must be lowercase hyphenated")
        elif pair_id in pair_ids:
            errors.append(f"duplicate pair id: {pair_id}")
        else:
            pair_ids.add(pair_id)
        _validate_pair_properties(pair, label, criteria, errors)


def _validate_pair_properties(
    pair: dict, label: str, criteria: dict[str, str], errors: list[str]
) -> None:
    output_depth = pair.get("output_depth")
    if output_depth not in OUTPUT_DEPTHS:
        errors.append(
            f"{label}: output_depth must be one of: {', '.join(sorted(OUTPUT_DEPTHS))}"
        )
    expected_minutes = pair.get("expected_minutes")
    if isinstance(expected_minutes, bool) or not isinstance(expected_minutes, int) or not 5 <= expected_minutes <= 45:
        errors.append(f"{label}: expected_minutes must be an integer from 5 through 45")
    difficulty = pair.get("difficulty")
    if isinstance(difficulty, bool) or not isinstance(difficulty, int) or not 1 <= difficulty <= 3:
        errors.append(f"{label}: difficulty must be an integer from 1 through 3")
    _validate_pair_criteria(pair, label, criteria, errors)
    _validate_variants(pair.get("variants"), label, errors)


def _validate_pair_criteria(
    pair: dict, label: str, criteria: dict[str, str], errors: list[str]
) -> None:
    for field, expected_kind in (("mandatory_criteria", "mandatory"), ("quality_criteria", "quality")):
        references = pair.get(field)
        display_name = field.removesuffix("_criteria")
        if not isinstance(references, list):
            errors.append(f"{label}: {field} must be a list")
            continue
        seen: set[str] = set()
        for criterion_id in references:
            if not isinstance(criterion_id, str) or not criterion_id:
                errors.append(f"{label}: {display_name} criterion must be a non-empty string")
                continue
            if criterion_id in seen:
                errors.append(f"{label}: duplicate {display_name} criterion: {criterion_id}")
            seen.add(criterion_id)
            if criterion_id not in criteria:
                errors.append(f"{label}: unknown {display_name} criterion: {criterion_id}")
            elif criteria[criterion_id] != expected_kind:
                errors.append(
                    f"{label}: {display_name} criterion must have kind {expected_kind}: {criterion_id}"
                )


def _validate_variants(variants: object, label: str, errors: list[str]) -> None:
    if not isinstance(variants, dict):
        errors.append(f"{label}: variants must be a mapping")
        return
    _validate_exact_keys(f"{label}: variants", variants, {"A", "B"}, errors)
    prompts: dict[str, str] = {}
    for variant in ("A", "B"):
        value = variants.get(variant)
        variant_label = f"{label} variant {variant}"
        if not isinstance(value, dict):
            errors.append(f"{variant_label}: must be a mapping")
            continue
        _validate_exact_keys(variant_label, value, VARIANT_KEYS, errors)
        prompt = value.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{variant_label}: prompt must be a non-empty string")
            continue
        prompts[variant] = prompt
        if "synthetic" not in prompt.casefold():
            errors.append(f"{variant_label}: prompt must contain synthetic")
    if len(prompts) == 2 and prompts["A"] == prompts["B"]:
        errors.append(f"{label}: variant prompts must be distinct")


def _validate_exact_keys(
    label: str, value: dict, expected_keys: set[str], errors: list[str]
) -> None:
    missing = sorted(expected_keys - set(value))
    unexpected = sorted(set(value) - expected_keys)
    if missing:
        errors.append(f"{label}: missing keys: {', '.join(missing)}")
    if unexpected:
        errors.append(f"{label}: unexpected keys: {', '.join(unexpected)}")


def _pair_label(pair: object, index: int) -> str:
    if isinstance(pair, dict) and isinstance(pair.get("id"), str) and pair["id"]:
        return f"pair {pair['id']}"
    return f"pair {index}"
