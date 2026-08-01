from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest
import yaml

from scripts import evaluate_response as response_evaluator
from scripts.evaluate_response import evaluate_response, validate_catalog


ROOT = Path(__file__).resolve().parents[1]
CASE_OUTPUT_DEPTHS = {
    "adam-quick-explanation": "quick explanation",
    "cdisc-variable-definition": "quick explanation",
    "sas-optimization-lexjansen": "evidence navigation",
    "tmucrd-public-profile": "evidence navigation",
    "descriptive-rwd-no-tte": "research design",
    "causal-rwd-tte-handoff": "research design",
    "causal-rwd-incomplete-readiness": "research design",
    "teae-sas-spec": "implementation specification",
    "institutional-sql-without-dictionary": "implementation specification",
    "stale-codingbook": "implementation specification",
    "omop-phenotype": "implementation specification",
    "build-rwe-sap-unavailable": "implementation specification",
}


def test_output_depths_are_limited_to_the_public_response_contract():
    """Adding an internal or alias label would make catalog output ambiguous."""
    assert response_evaluator.OUTPUT_DEPTHS == {
        "quick explanation",
        "evidence navigation",
        "research design",
        "implementation specification",
    }


GENERATED_START = "<!-- BEGIN GENERATED EVAL SUMMARY -->"
GENERATED_END = "<!-- END GENERATED EVAL SUMMARY -->"


def test_all_catalog_cases_have_paired_response_only_fixture_evidence():
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    rubric = yaml.safe_load(
        (ROOT / "evals/rubric.yaml").read_text(encoding="utf-8")
    )
    cases = catalog["cases"]
    case_ids = {case["id"] for case in cases}
    baseline_ids = {
        path.stem for path in (ROOT / "tests/fixtures/baseline").glob("*.md")
    }
    forward_ids = {
        path.stem for path in (ROOT / "tests/fixtures/forward").glob("*.md")
    }

    assert len(case_ids) == 12
    assert baseline_ids == case_ids
    assert forward_ids == case_ids

    forbidden_fixture_markers = (
        "prompt:",
        "rubric:",
        "expected answer:",
        "score:",
        "test commentary:",
        "system prompt",
        "hidden reasoning",
    )
    for case in cases:
        baseline_text = (
            ROOT / "tests/fixtures/baseline" / f"{case['id']}.md"
        ).read_text(encoding="utf-8")
        forward_text = (
            ROOT / "tests/fixtures/forward" / f"{case['id']}.md"
        ).read_text(encoding="utf-8")
        baseline = evaluate_response(case, rubric, baseline_text)
        forward = evaluate_response(case, rubric, forward_text)

        assert baseline.score < rubric["pass_threshold"], case["id"]
        assert not baseline.passed, case["id"]
        assert forward.score >= rubric["pass_threshold"], case["id"]
        assert forward.passed, case["id"]
        assert not [
            rule
            for rule in forward.results
            if rule.rule.startswith("forbidden:") and not rule.passed
        ], case["id"]
        assert re.findall(
            r"^Output depth: (.+)$", forward_text, flags=re.MULTILINE
        ) == [case["output_depth"]]

        for text in (baseline_text, forward_text):
            assert text.strip(), case["id"]
            lowered = text.lower()
            assert not any(marker in lowered for marker in forbidden_fixture_markers)


def test_rendered_eval_summary_matches_checked_in_generated_block():
    renderer = ROOT / "scripts/render_eval_summary.py"
    assert renderer.is_file()
    from scripts.render_eval_summary import render_summary

    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    rubric = yaml.safe_load(
        (ROOT / "evals/rubric.yaml").read_text(encoding="utf-8")
    )
    readme = (ROOT / "evals/README.md").read_text(encoding="utf-8")
    generated_block = readme.split(GENERATED_START, 1)[1].split(
        GENERATED_END, 1
    )[0].strip("\n")
    rendered = render_summary(ROOT)

    assert rendered == generated_block
    assert rendered.count("\n| `") == len(catalog["cases"])
    for case in catalog["cases"]:
        case_id = case["id"]
        baseline = evaluate_response(
            case,
            rubric,
            (ROOT / "tests/fixtures/baseline" / f"{case_id}.md").read_text(
                encoding="utf-8"
            ),
        )
        forward = evaluate_response(
            case,
            rubric,
            (ROOT / "tests/fixtures/forward" / f"{case_id}.md").read_text(
                encoding="utf-8"
            ),
        )
        baseline_status = "PASS" if baseline.passed else "FAIL"
        forward_status = "PASS" if forward.passed else "FAIL"
        assert (
            f"| `{case_id}` | {case['output_depth']} | "
            f"{baseline.score} {baseline_status} | "
            f"{forward.score} {forward_status} |"
        ) in rendered
    assert "repository behavior contracts" in rendered
    assert "not clinical validity or real-world effectiveness" in rendered
    assert "not proof of semantic correctness or clinical validity" in readme


def test_eval_summary_cli_check_is_idempotent():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/render_eval_summary.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_eval_summary_check_detects_staleness_and_rewrites_only_generated_block(
    tmp_path,
):
    from scripts import render_eval_summary

    shutil.copytree(ROOT / "evals", tmp_path / "evals")
    shutil.copytree(ROOT / "tests/fixtures", tmp_path / "tests/fixtures")
    prefix = "# Preserved prefix\n\n"
    suffix = "\nPreserved suffix.\n"
    readme_path = tmp_path / "evals/README.md"
    readme_path.write_text(
        prefix
        + GENERATED_START
        + "\nstale\n"
        + GENERATED_END
        + suffix,
        encoding="utf-8",
        newline="\n",
    )

    assert render_eval_summary.main(["--check"], root=tmp_path) == 1
    assert readme_path.read_text(encoding="utf-8").startswith(prefix)
    assert readme_path.read_text(encoding="utf-8").endswith(suffix)

    assert render_eval_summary.main([], root=tmp_path) == 0
    rewritten = readme_path.read_text(encoding="utf-8")
    assert rewritten.startswith(prefix)
    assert rewritten.endswith(suffix)
    assert render_eval_summary.main(["--check"], root=tmp_path) == 0


def test_each_case_uses_the_public_eval_schema():
    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert {case["id"] for case in cases} == set(CASE_OUTPUT_DEPTHS)
    assert {case["id"]: case["output_depth"] for case in cases} == CASE_OUTPUT_DEPTHS
    for case in cases:
        assert set(case) == {
            "id",
            "prompt",
            "output_depth",
            "required",
            "forbidden",
            "required_sections",
        }
        assert isinstance(case["id"], str) and case["id"]
        assert isinstance(case["prompt"], str) and case["prompt"]
        assert case["output_depth"] in response_evaluator.OUTPUT_DEPTHS
        for field in ("required", "forbidden", "required_sections"):
            assert isinstance(case[field], list) and all(
                isinstance(value, str) and value for value in case[field]
            )


def test_shared_rubric_is_reproducible_and_strict():
    rubric = yaml.safe_load((ROOT / "evals/rubric.yaml").read_text(encoding="utf-8"))
    assert rubric == {
        "schema_version": "1",
        "pass_threshold": 100,
        "scoring": {
            "required_pattern": 10,
            "required_section": 10,
            "forbidden_pattern": -100,
        },
        "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
    }


def test_catalog_is_valid_and_each_case_can_reach_the_fixed_threshold():
    """The fixed 10-point rubric requires ten meaningful positive rules per case."""
    catalog = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    rubric = yaml.safe_load((ROOT / "evals/rubric.yaml").read_text(encoding="utf-8"))
    assert validate_catalog(catalog, rubric) == []
    for case in catalog["cases"]:
        assert len(case["required"]) + len(case["required_sections"]) >= 10


def test_sas_optimization_case_requires_traceable_paper_level_evidence():
    case = _catalog_case("sas-optimization-lexjansen")
    rubric = yaml.safe_load((ROOT / "evals/rubric.yaml").read_text(encoding="utf-8"))
    complete_response = """
# Decision
Search site:lexjansen.com for the specific SAS technique, then review the
specific paper. Treat it as secondary implementation evidence.

# Evidence table
Record the title, authors, conference, publication year, stable URL, and
access date, together with applicability and platform caveats.

# Data contract
Record code provenance and copyright, license, or reuse terms. Use a
clean-room implementation when permission is unclear.

# Code maturity
Keep the execution gate; a historical example cannot make code executable.

# Validation gaps
If network access is unavailable, state that the paper was not reviewed.
Require performance validation in the target environment.

# Sources
Cite the specific reviewed paper rather than a search snippet.
"""
    incomplete_response = """
# Decision
Use Lex Jansen examples to optimize the SAS program.

# Evidence table
Lex Jansen has many useful papers.

# Data contract
Apply the example to the program.

# Code maturity
The code is optimized.

# Validation gaps
None.

# Sources
Lex Jansen.
"""

    assert evaluate_response(case, rubric, complete_response).passed is True
    assert evaluate_response(case, rubric, incomplete_response).passed is False


def test_tmucrd_forbidden_sql_pattern_matches_a_literal_asterisk():
    cases = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))["cases"]
    tmucrd_case = next(case for case in cases if case["id"] == "tmucrd-public-profile")
    pattern = next(item for item in tmucrd_case["forbidden"] if item.startswith("SELECT"))
    assert re.search(pattern, "SELECT * FROM synthetic_source")


def test_rwe_routing_cases_enforce_safe_boundaries():
    descriptive = _catalog_case("descriptive-rwd-no-tte")
    causal = _catalog_case("causal-rwd-tte-handoff")
    incomplete = _catalog_case("causal-rwd-incomplete-readiness")
    unavailable = _catalog_case("build-rwe-sap-unavailable")

    assert any("TTE" in pattern for pattern in descriptive["forbidden"])
    for component in (
        "eligibility",
        "strateg",
        "assignment",
        "time zero",
        "follow-up",
        "outcome",
        "estimand",
        "analysis plan",
    ):
        assert any(
            component.lower() in pattern.lower()
            for pattern in causal["required"]
        )
    assert "conceptual" in incomplete["required"]
    assert any("executable" in pattern for pattern in incomplete["forbidden"])
    for phrase in (
        "optional",
        "not bundled",
        "not automatically installed",
        "continue",
        "complete SAP",
    ):
        assert any(
            phrase.lower() in pattern.lower()
            for pattern in unavailable["required"]
        )


@pytest.mark.parametrize(
    ("case_id", "unsafe_response"),
    [
        (
            "descriptive-rwd-no-tte",
            "TTE is the default for every RWD question.",
        ),
        (
            "causal-rwd-incomplete-readiness",
            "The causal conclusion is validated and executable.",
        ),
        (
            "build-rwe-sap-unavailable",
            "You must install build-rwe-sap before Core work can continue.",
        ),
    ],
)
def test_rwe_routing_cases_reject_unsafe_shortcuts(case_id, unsafe_response):
    case = _catalog_case(case_id)

    assert any(
        re.search(pattern, unsafe_response, flags=re.IGNORECASE)
        for pattern in case["forbidden"]
    )


@pytest.mark.parametrize(
    ("case_id", "unsafe_response"),
    [
        (
            "teae-sas-spec",
            "Lex Jansen\nis an authoritative standards body.",
        ),
        (
            "sas-optimization-lexjansen",
            "Copy the historical SAS code without checking its license.",
        ),
        (
            "institutional-sql-without-dictionary",
            "SELECT\nperson_identifier\nFROM\nlocal_records",
        ),
        (
            "stale-codingbook",
            "The historical codebook\nis enough to establish the current schema.",
        ),
        (
            "cdisc-variable-definition",
            "A conference paper\nsupersedes the official CDISC definition.",
        ),
        (
            "omop-phenotype",
            "Use OMOP Concept ID: 987654 for the phenotype.",
        ),
        (
            "tmucrd-public-profile",
            "SELECT\n*\nFROM\ncurrent_tmu_source",
        ),
    ],
)
def test_catalog_forbidden_rules_catch_high_signal_multiline_variants(
    case_id,
    unsafe_response,
):
    case = _catalog_case(case_id)

    assert any(
        re.search(pattern, unsafe_response)
        for pattern in case["forbidden"]
    )


@pytest.mark.parametrize(
    ("case_id", "safe_response"),
    [
        (
            "teae-sas-spec",
            "Lex Jansen is not an official standard or validation authority.",
        ),
        (
            "sas-optimization-lexjansen",
            "Do not copy SAS code without checking provenance and license terms.",
        ),
        (
            "stale-codingbook",
            "The historical codingbook is not sufficient to verify the current schema.",
        ),
        (
            "cdisc-variable-definition",
            "A conference paper does not override the official CDISC definition.",
        ),
        (
            "omop-phenotype",
            "Historical examples may discuss Concept IDs; do not invent one.",
        ),
    ],
)
def test_broader_forbidden_rules_allow_legitimate_historical_caveats(
    case_id,
    safe_response,
):
    case = _catalog_case(case_id)

    assert not any(
        re.search(pattern, safe_response)
        for pattern in case["forbidden"]
    )


def test_catalog_validation_rejects_missing_case_key():
    """Removing a required schema field must make catalog validation fail."""
    catalog = {
        "cases": [{"id": "test", "prompt": "x", "required": [], "forbidden": []}]
    }
    errors = validate_catalog(catalog, _valid_rubric())
    assert "case test: missing keys: output_depth, required_sections" in errors


@pytest.mark.parametrize(
    ("output_depth", "expected_error"),
    [
        ("", "case test: output_depth must be a non-empty string"),
        (None, "case test: output_depth must be a non-empty string"),
        (
            "Quick Explanation",
            "case test: output_depth must be one of: evidence navigation, implementation specification, quick explanation, research design",
        ),
        (
            "summary",
            "case test: output_depth must be one of: evidence navigation, implementation specification, quick explanation, research design",
        ),
    ],
)
def test_catalog_validation_rejects_non_exact_output_depths(
    output_depth, expected_error
):
    """Missing validation would let a mislabeled response contract into the catalog."""
    case = _valid_case()
    case["output_depth"] = output_depth

    assert expected_error in validate_catalog({"cases": [case]}, _valid_rubric())


def test_catalog_validation_requires_schema_version():
    """A rubric without the versioned evaluator contract must be rejected."""
    rubric = _valid_rubric()
    del rubric["schema_version"]
    assert "rubric: missing keys: schema_version" in validate_catalog(
        {"cases": [_valid_case()]}, rubric
    )


def test_catalog_validation_rejects_duplicate_ids_and_empty_prompts():
    """Duplicate IDs or whitespace-only prompts must not enter the offline catalog."""
    case = {
        "id": "duplicate",
        "prompt": " ",
        "output_depth": "quick explanation",
        "required": [],
        "forbidden": [],
        "required_sections": [],
    }
    errors = validate_catalog({"cases": [case, {**case, "prompt": "valid"}]}, _valid_rubric())
    assert "duplicate case id: duplicate" in errors
    assert "case duplicate: prompt must not be empty" in errors


def test_catalog_validation_rejects_invalid_regex():
    """An uncompileable rule must fail validation rather than crash evaluation later."""
    case = _valid_case()
    case["required"] = ["["]
    assert "case test: invalid required regex: [" in validate_catalog(
        {"cases": [case]}, _valid_rubric()
    )


def test_catalog_validation_records_invalid_unicode_form_without_normalizing():
    case = _valid_case()
    rubric = _valid_rubric()
    rubric["pass_threshold"] = 20
    rubric["normalization"]["unicode_form"] = "NOT-A-UNICODE-FORM"

    assert validate_catalog({"cases": [case]}, rubric) == [
        "rubric: unicode_form is invalid"
    ]


def test_catalog_validation_rejects_unreachable_threshold():
    """A threshold above every positive rule's total cannot produce a passing result."""
    case = _valid_case()
    case["required"] = [f"requirement {number}" for number in range(9)]
    case["required_sections"] = []
    rubric = _valid_rubric()
    rubric["pass_threshold"] = 100
    assert "pass threshold 100 exceeds maximum possible score 90" in validate_catalog(
        {"cases": [case]}, rubric
    )


def _valid_case():
    return {
        "id": "test",
        "prompt": "valid prompt",
        "output_depth": "quick explanation",
        "required": ["required"],
        "forbidden": [],
        "required_sections": ["Section"],
    }


def _catalog_case(case_id):
    cases = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )["cases"]
    return next(case for case in cases if case["id"] == case_id)


def _valid_rubric():
    return {
        "schema_version": "1",
        "pass_threshold": 30,
        "scoring": {
            "required_pattern": 10,
            "required_section": 10,
            "forbidden_pattern": -100,
        },
        "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
    }
