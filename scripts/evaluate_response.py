"""Evaluate a response against the repository's offline behavior catalog."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import unicodedata

import yaml


ROOT = Path(__file__).resolve().parents[1]
CASE_KEYS = {"id", "prompt", "required", "forbidden", "required_sections"}
RUBRIC_KEYS = {"schema_version", "pass_threshold", "scoring", "normalization"}
REQUIRED_RUBRIC_KEYS = RUBRIC_KEYS
SCORING_KEYS = {"required_pattern", "required_section", "forbidden_pattern"}
NORMALIZATION_KEYS = {"case_sensitive", "unicode_form"}


@dataclass(frozen=True)
class RuleResult:
    rule: str
    passed: bool
    points: int
    message: str


@dataclass(frozen=True)
class Evaluation:
    case_id: str
    score: int
    passed: bool
    results: list[RuleResult]


def normalize(text: str, rubric: dict) -> str:
    """Apply the rubric's Unicode and case-comparison policy to *text*."""
    form = rubric["normalization"]["unicode_form"]
    value = unicodedata.normalize(form, text)
    if not rubric["normalization"]["case_sensitive"]:
        value = value.casefold()
    return value


def evaluate_response(case: dict, rubric: dict, response: str) -> Evaluation:
    """Score one response using required, heading, then forbidden rules."""
    normalized_response = normalize(response, rubric)
    scoring = rubric["scoring"]
    results: list[RuleResult] = []

    for pattern in case["required"]:
        matched = bool(re.search(normalize(pattern, rubric), normalized_response))
        points = scoring["required_pattern"] if matched else 0
        results.append(
            RuleResult(
                rule=f"required:{pattern}",
                passed=matched,
                points=points,
                message="required pattern matched" if matched else "required pattern missing",
            )
        )

    for section in case["required_sections"]:
        heading = rf"^\s*##\s+{re.escape(normalize(section, rubric))}\s*$"
        matched = bool(re.search(heading, normalized_response, flags=re.MULTILINE))
        points = scoring["required_section"] if matched else 0
        results.append(
            RuleResult(
                rule=f"section:{section}",
                passed=matched,
                points=points,
                message="required section matched" if matched else "required section missing",
            )
        )

    for pattern in case["forbidden"]:
        matched = bool(re.search(normalize(pattern, rubric), normalized_response))
        points = scoring["forbidden_pattern"] if matched else 0
        results.append(
            RuleResult(
                rule=f"forbidden:{pattern}",
                passed=not matched,
                points=points,
                message="forbidden pattern matched" if matched else "forbidden pattern absent",
            )
        )

    score = sum(item.points for item in results)
    forbidden_matched = any(
        item.rule.startswith("forbidden:") and not item.passed for item in results
    )
    return Evaluation(
        case_id=case["id"],
        score=score,
        passed=score >= rubric["pass_threshold"] and not forbidden_matched,
        results=results,
    )


def validate_catalog(catalog: dict, rubric: dict) -> list[str]:
    """Return deterministic errors for an unusable evaluation catalog."""
    errors: list[str] = []
    cases = catalog.get("cases") if isinstance(catalog, dict) else None
    if not isinstance(cases, list):
        return ["catalog: cases must be a list"]

    if not isinstance(rubric, dict):
        return ["rubric must be a mapping"]
    missing_rubric_keys = sorted(REQUIRED_RUBRIC_KEYS - set(rubric))
    if missing_rubric_keys:
        errors.append("rubric: missing keys: " + ", ".join(missing_rubric_keys))
        return errors
    if not set(rubric).issubset(RUBRIC_KEYS):
        errors.append("rubric: unexpected keys: " + ", ".join(sorted(set(rubric) - RUBRIC_KEYS)))

    scoring = rubric["scoring"]
    if not isinstance(scoring, dict) or set(scoring) != SCORING_KEYS:
        errors.append("rubric: scoring must contain required_pattern, required_section, forbidden_pattern")
        return errors
    if not all(isinstance(value, int) and not isinstance(value, bool) for value in scoring.values()):
        errors.append("rubric: scoring values must be integers")
        return errors

    normalization = rubric["normalization"]
    if not isinstance(normalization, dict) or set(normalization) != NORMALIZATION_KEYS:
        errors.append("rubric: normalization must contain case_sensitive and unicode_form")
        return errors
    normalization_is_usable = True
    if not isinstance(normalization["case_sensitive"], bool):
        errors.append("rubric: case_sensitive must be a boolean")
    if not isinstance(normalization["unicode_form"], str):
        errors.append("rubric: unicode_form must be a string")
        normalization_is_usable = False
    else:
        try:
            unicodedata.normalize(normalization["unicode_form"], "test")
        except ValueError:
            errors.append("rubric: unicode_form is invalid")
            normalization_is_usable = False

    threshold = rubric["pass_threshold"]
    if not isinstance(threshold, int) or isinstance(threshold, bool):
        errors.append("rubric: pass_threshold must be an integer")
        return errors

    ids: set[str] = set()
    for index, case in enumerate(cases):
        label = case.get("id", f"at index {index}") if isinstance(case, dict) else f"at index {index}"
        if not isinstance(case, dict):
            errors.append(f"case {label}: must be a mapping")
            continue
        missing_case_keys = sorted(CASE_KEYS - set(case))
        if missing_case_keys:
            errors.append(f"case {label}: missing keys: " + ", ".join(missing_case_keys))
            continue
        extra_case_keys = sorted(set(case) - CASE_KEYS)
        if extra_case_keys:
            errors.append(f"case {label}: unexpected keys: " + ", ".join(extra_case_keys))
        case_id = case["id"]
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"case {label}: id must be a non-empty string")
        elif case_id in ids:
            errors.append(f"duplicate case id: {case_id}")
        else:
            ids.add(case_id)
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            errors.append(f"case {label}: prompt must not be empty")
        for field in ("required", "forbidden", "required_sections"):
            values = case[field]
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value for value in values
            ):
                errors.append(f"case {label}: {field} must be a list of non-empty strings")
                continue
            if field == "required_sections" or not normalization_is_usable:
                continue
            for pattern in values:
                try:
                    re.compile(normalize(pattern, rubric))
                except re.error:
                    errors.append(f"case {label}: invalid {field} regex: {pattern}")
        if all(isinstance(case[field], list) for field in ("required", "required_sections")):
            maximum = (
                len(case["required"]) * scoring["required_pattern"]
                + len(case["required_sections"]) * scoring["required_section"]
            )
            if threshold > maximum:
                errors.append(
                    f"pass threshold {threshold} exceeds maximum possible score {maximum}"
                )
    return errors


def load_catalog(cases_path: Path, rubric_path: Path) -> tuple[dict, dict]:
    """Load and validate the YAML inputs used by the evaluator CLI."""
    catalog = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    rubric = yaml.safe_load(rubric_path.read_text(encoding="utf-8"))
    errors = validate_catalog(catalog, rubric)
    if errors:
        raise ValueError("invalid evaluation catalog: " + "; ".join(errors))
    return catalog, rubric


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, dest="case_id")
    parser.add_argument("--response", required=True, type=Path)
    parser.add_argument("--cases", type=Path, default=ROOT / "evals/cases.yaml")
    parser.add_argument("--rubric", type=Path, default=ROOT / "evals/rubric.yaml")
    args = parser.parse_args(argv)

    try:
        catalog, rubric = load_catalog(args.cases, args.rubric)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))
    case = next((item for item in catalog["cases"] if item["id"] == args.case_id), None)
    if case is None:
        parser.error(f"unknown case: {args.case_id}")
    try:
        response = args.response.read_text(encoding="utf-8")
    except OSError as error:
        parser.error(str(error))

    evaluation = evaluate_response(case, rubric, response)
    print(json.dumps(asdict(evaluation), ensure_ascii=False, sort_keys=True))
    return 0 if evaluation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
