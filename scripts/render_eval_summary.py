"""Render the checked-in deterministic Eval fixture summary."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

try:
    from scripts.evaluate_response import evaluate_response, load_catalog
except ModuleNotFoundError:  # Direct script execution places scripts/ on sys.path.
    from evaluate_response import evaluate_response, load_catalog


ROOT = Path(__file__).resolve().parents[1]
GENERATED_START = "<!-- BEGIN GENERATED EVAL SUMMARY -->"
GENERATED_END = "<!-- END GENERATED EVAL SUMMARY -->"


def render_summary(root: Path) -> str:
    """Return the complete generated Eval result table in catalog order."""
    catalog, rubric = load_catalog(
        root / "evals/cases.yaml",
        root / "evals/rubric.yaml",
    )
    rows = [
        "| Case | Output depth | Baseline | Forward |",
        "| --- | --- | ---: | ---: |",
    ]
    for case in catalog["cases"]:
        case_id = case["id"]
        baseline = evaluate_response(
            case,
            rubric,
            (root / "tests/fixtures/baseline" / f"{case_id}.md").read_text(
                encoding="utf-8"
            ),
        )
        forward = evaluate_response(
            case,
            rubric,
            (root / "tests/fixtures/forward" / f"{case_id}.md").read_text(
                encoding="utf-8"
            ),
        )
        baseline_status = "PASS" if baseline.passed else "FAIL"
        forward_status = "PASS" if forward.passed else "FAIL"
        rows.append(
            f"| `{case_id}` | {case['output_depth']} | "
            f"{baseline.score} {baseline_status} | {forward.score} {forward_status} |"
        )
    rows.extend(
        [
            "",
            "> These keyword fixtures test repository behavior contracts, not clinical "
            "validity or real-world effectiveness.",
        ]
    )
    return "\n".join(rows)


def _generated_block_bounds(data: bytes) -> tuple[int, int]:
    start_marker = GENERATED_START.encode("utf-8")
    end_marker = GENERATED_END.encode("utf-8")
    if data.count(start_marker) != 1 or data.count(end_marker) != 1:
        raise ValueError("Eval README must contain exactly one generated block")
    start = data.index(start_marker) + len(start_marker)
    end = data.index(end_marker, start)
    return start, end


def main(argv: list[str] | None = None, *, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the checked-in generated block is stale",
    )
    args = parser.parse_args(argv)

    readme_path = root / "evals/README.md"
    try:
        data = readme_path.read_bytes()
        start, end = _generated_block_bounds(data)
        expected = ("\n" + render_summary(root) + "\n").encode("utf-8")
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))

    if args.check:
        if data[start:end] != expected:
            print("evals/README.md generated Eval summary is stale")
            return 1
        return 0

    updated = data[:start] + expected + data[end:]
    if updated != data:
        readme_path.write_bytes(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
