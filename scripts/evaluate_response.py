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
OUTPUT_DEPTHS = {
    "quick explanation",
    "evidence navigation",
    "research design",
    "implementation specification",
}
COMMON_HEADER_PATTERNS = (
    r"(?:^|\n)[ \t]*Decision:[ \t]+\S",
    r"(?:^|\n)[ \t]*Confirmed facts:[ \t]+\S",
    r"(?:^|\n)[ \t]*Assumptions:[ \t]+\S",
    r"(?:^|\n)[ \t]*Limitations:[ \t]+\S",
    r"(?:^|\n)[ \t]*Sources actually consulted:[ \t]+\S",
)
_DEPTH_REQUIRED_SECTIONS = {
    "quick explanation": (
        "Direct answer",
        "Why it matters",
        "Common confusions or limits",
    ),
    "evidence navigation": (
        "Search scope",
        "Authority-ordered route",
        "Evidence table",
        "Conflicts and unreviewed gaps",
    ),
    "research design": (
        "Primary intent and design route",
        "Design fields and time anchors",
        "Data suitability and claim boundary",
        "Bias and validation gaps",
        "Analysis or diagnostics",
    ),
    "implementation specification": (
        "Governing evidence",
        "Data contract",
        "Code maturity",
        "Validation gaps",
        "Execution gate",
    ),
}
_DEPTH_OPTIONAL_SECTIONS = {
    "quick explanation": (),
    "evidence navigation": (),
    "research design": ("Handoff status",),
    "implementation specification": (),
}
_ALL_DEPTH_SECTIONS = frozenset(
    section
    for sections in _DEPTH_REQUIRED_SECTIONS.values()
    for section in sections
) | frozenset(
    section
    for sections in _DEPTH_OPTIONAL_SECTIONS.values()
    for section in sections
)
DEPTH_SECTION_CONTRACTS = {
    depth: {
        "required": required,
        "allowed": required + _DEPTH_OPTIONAL_SECTIONS[depth],
        "forbidden": tuple(
            sorted(
                _ALL_DEPTH_SECTIONS
                - set(required)
                - set(_DEPTH_OPTIONAL_SECTIONS[depth])
            )
        ),
    }
    for depth, required in _DEPTH_REQUIRED_SECTIONS.items()
}
CASE_KEYS = {
    "id",
    "prompt",
    "output_depth",
    "required",
    "forbidden",
    "required_sections",
}
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


def _normalize_regex(pattern: str, rubric: dict) -> str:
    """Normalize regex literals without changing case-sensitive escapes."""
    form = rubric["normalization"]["unicode_form"]
    return unicodedata.normalize(form, pattern)


def _regex_flags(rubric: dict, flags: int = 0) -> int:
    """Apply the rubric's case policy without casefolding regex syntax."""
    if not rubric["normalization"]["case_sensitive"]:
        flags |= re.IGNORECASE
    return flags


def strip_markdown_code(text: str) -> str:
    """Remove fenced and indented code while preserving line boundaries."""
    visible_lines: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        line_ending = line[len(content):]

        if fence_character is not None:
            closing_fence = rf"^ {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*$"
            if re.match(closing_fence, content):
                fence_character = None
                fence_length = 0
            visible_lines.append(line_ending)
            continue

        opening_fence = re.match(r"^ {0,3}(?P<fence>`{3,}|~{3,}).*$", content)
        if opening_fence:
            fence = opening_fence.group("fence")
            fence_character = fence[0]
            fence_length = len(fence)
            visible_lines.append(line_ending)
            continue

        if re.match(r"^(?: {4,}|\t)", content):
            visible_lines.append(line_ending)
            continue

        visible_lines.append(line)

    return "".join(visible_lines)


def _h2_pattern(section: str, rubric: dict) -> str:
    """Return a strict top-level Markdown H2 pattern for *section*."""
    normalized_section = re.escape(normalize(section, rubric))
    return rf"^ {{0,3}}##[ \t]+{normalized_section}[ \t]*$"


def evaluate_response(case: dict, rubric: dict, response: str) -> Evaluation:
    """Score one response using required, heading, then forbidden rules."""
    normalized_response = normalize(response, rubric)
    normalized_positive_response = normalize(strip_markdown_code(response), rubric)
    scoring = rubric["scoring"]
    results: list[RuleResult] = []

    for pattern in COMMON_HEADER_PATTERNS:
        matched = bool(
            re.search(
                _normalize_regex(pattern, rubric),
                normalized_positive_response,
                flags=_regex_flags(rubric),
            )
        )
        points = scoring["required_pattern"] if matched else 0
        results.append(
            RuleResult(
                rule=f"common-header:{pattern}",
                passed=matched,
                points=points,
                message=(
                    "common header field matched"
                    if matched
                    else "common header field missing"
                ),
            )
        )

    depth_contract = DEPTH_SECTION_CONTRACTS[case["output_depth"]]
    for section in depth_contract["required"]:
        heading = _h2_pattern(section, rubric)
        matched = bool(
            re.search(
                heading,
                normalized_positive_response,
                flags=re.MULTILINE,
            )
        )
        points = scoring["required_section"] if matched else 0
        results.append(
            RuleResult(
                rule=f"depth-section:{section}",
                passed=matched,
                points=points,
                message="depth section matched" if matched else "depth section missing",
            )
        )

    response_sections = {
        heading.strip()
        for heading in re.findall(
            r"^ {0,3}#{1,6}[ \t]+(.+?)[ \t]*#*[ \t]*$",
            normalized_positive_response,
            re.MULTILINE,
        )
    }
    allowed_sections = {
        normalize(section, rubric) for section in depth_contract["allowed"]
    }
    for section in sorted(response_sections - allowed_sections):
        results.append(
            RuleResult(
                rule=f"forbidden-section:{section}",
                passed=False,
                points=scoring["forbidden_pattern"],
                message="section is not allowed at the selected output depth",
            )
        )

    for pattern in case["required"]:
        matched = bool(
            re.search(
                _normalize_regex(pattern, rubric),
                normalized_positive_response,
                flags=_regex_flags(rubric),
            )
        )
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
        heading = _h2_pattern(section, rubric)
        matched = bool(
            re.search(
                heading,
                normalized_positive_response,
                flags=re.MULTILINE,
            )
        )
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
        matched = bool(
            re.search(
                _normalize_regex(pattern, rubric),
                normalized_response,
                flags=_regex_flags(rubric),
            )
        )
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
        (
            item.rule.startswith("forbidden:")
            or item.rule.startswith("forbidden-section:")
        )
        and not item.passed
        for item in results
    )
    depth_contract_missing = any(
        (
            item.rule.startswith("common-header:")
            or item.rule.startswith("depth-section:")
        )
        and not item.passed
        for item in results
    )
    required_content_missing = any(
        item.rule.startswith("required:") and not item.passed
        for item in results
    )
    return Evaluation(
        case_id=case["id"],
        score=score,
        passed=(
            score >= rubric["pass_threshold"]
            and not forbidden_matched
            and not depth_contract_missing
            and not required_content_missing
        ),
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
        output_depth = case["output_depth"]
        if not isinstance(output_depth, str) or not output_depth.strip():
            errors.append(f"case {label}: output_depth must be a non-empty string")
        elif output_depth not in OUTPUT_DEPTHS:
            errors.append(
                f"case {label}: output_depth must be one of: "
                + ", ".join(sorted(OUTPUT_DEPTHS))
            )
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
                    re.compile(
                        _normalize_regex(pattern, rubric),
                        flags=_regex_flags(rubric),
                    )
                except re.error:
                    errors.append(f"case {label}: invalid {field} regex: {pattern}")
        if all(isinstance(case[field], list) for field in ("required", "required_sections")):
            maximum = (
                len(case["required"]) * scoring["required_pattern"]
                + len(case["required_sections"]) * scoring["required_section"]
                + len(COMMON_HEADER_PATTERNS) * scoring["required_pattern"]
                + len(
                    DEPTH_SECTION_CONTRACTS.get(
                        case.get("output_depth"),
                        {},
                    ).get("required", ())
                )
                * scoring["required_section"]
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
