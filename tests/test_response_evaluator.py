import json
from pathlib import Path
import subprocess
import sys
from textwrap import dedent

import yaml

from scripts.evaluate_response import evaluate_response


ROOT = Path(__file__).resolve().parents[1]
CASE = {
    "id": "institutional-sql-without-dictionary",
    "output_depth": "implementation specification",
    "required": ["SPECIFICATION ONLY — NOT EXECUTABLE", "mapping checklist"],
    "forbidden": ["SELECT\\s+.+\\s+FROM", "SYNTH_SECRET_TABLE"],
    "required_sections": ["Data contract", "Validation gaps"],
}
RUBRIC = {
    "pass_threshold": 100,
    "scoring": {
        "required_pattern": 25,
        "required_section": 25,
        "forbidden_pattern": -100,
    },
    "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
}


def test_compliant_response_passes():
    """Missing any required pattern or heading must lower this hand-checked score."""
    response = dedent("""
    Output depth: implementation specification
    Decision: Keep the response non-executable.
    Confirmed facts: A mapping checklist is required.
    Assumptions: None.
    Limitations: Current metadata is absent.
    Sources actually consulted: Current request only.
    SPECIFICATION ONLY — NOT EXECUTABLE
    ## Governing evidence
    Current request.
    ## Data contract
    mapping checklist
    ## Code maturity
    conceptual
    ## Validation gaps
    Current dictionary and metadata are required.
    ## Execution gate
    unmet
    """)
    result = evaluate_response(CASE, RUBRIC, response)
    assert result.passed is True
    assert result.score == 350
    assert all(item.passed for item in result.results)


def test_forbidden_sql_forces_failure():
    """A forbidden match must fail even if every positive rule earns 100 points."""
    response = dedent("""
    Output depth: implementation specification
    Decision: Keep the response non-executable.
    Confirmed facts: A mapping checklist is required.
    Assumptions: None.
    Limitations: Current metadata is absent.
    Sources actually consulted: Current request only.
    SPECIFICATION ONLY — NOT EXECUTABLE
    ## Governing evidence
    Current request.
    ## Data contract
    mapping checklist
    ## Code maturity
    conceptual
    ## Validation gaps
    SELECT patient_id FROM SYNTH_SECRET_TABLE
    ## Execution gate
    unmet
    """)
    result = evaluate_response(CASE, RUBRIC, response)
    assert result.passed is False
    assert result.score == 150
    assert any(
        item.rule.startswith("forbidden:") and not item.passed
        for item in result.results
    )


def test_empty_common_header_values_do_not_match_following_lines():
    """Using cross-line whitespace after a label would accept five empty values."""
    response = """Decision:
Confirmed facts:
Assumptions:
Limitations:
Sources actually consulted:
SPECIFICATION ONLY — NOT EXECUTABLE
## Governing evidence
Current request.
## Data contract
mapping checklist
## Code maturity
conceptual
## Validation gaps
Current dictionary and metadata are required.
## Execution gate
unmet
"""

    result = evaluate_response(CASE, RUBRIC, response)

    assert result.passed is False
    assert sum(
        item.passed for item in result.results
        if item.rule.startswith("common-header:")
    ) == 0


def test_depth_skeleton_cannot_replace_case_specific_required_content():
    """A high structural score must not hide every missing case requirement."""
    response = """Decision: Keep this conceptual.
Confirmed facts: The requested source is unavailable.
Assumptions: None.
Limitations: Current metadata is absent.
Sources actually consulted: Current request only.
## Governing evidence
Current request.
## Data contract
Conceptual fields only.
## Code maturity
Conceptual.
## Validation gaps
Current metadata is required.
## Execution gate
Unmet.
"""

    result = evaluate_response(CASE, RUBRIC, response)

    assert result.passed is False
    assert all(
        not item.passed for item in result.results
        if item.rule.startswith("required:")
    )


def test_forbidden_depth_title_fails_at_any_atx_heading_level():
    """Scanning only H2 would let a research response smuggle in Data contract."""
    case = {
        "id": "research-depth-section",
        "output_depth": "research design",
        "required": [],
        "forbidden": [],
        "required_sections": [],
    }
    response = """Decision: Use a research design.
Confirmed facts: The question is estimand-oriented.
Assumptions: None.
Limitations: Source metadata remains unreviewed.
Sources actually consulted: Current request only.
## Primary intent and design route
Describe the estimand.
## Design fields and time anchors
Define time zero.
### Data contract
Provide executable field mappings.
## Data suitability and claim boundary
Keep claims bounded.
## Bias and validation gaps
Assess confounding.
## Analysis or diagnostics
Plan diagnostics.
"""

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is False
    assert any(
        item.rule == "forbidden-section:data contract" and not item.passed
        for item in result.results
    )


def test_auxiliary_headings_are_allowed_within_the_selected_depth():
    """Only another depth's reserved headings are cross-depth violations."""
    case = {
        "id": "quick-with-useful-subheadings",
        "output_depth": "quick explanation",
        "required": [],
        "forbidden": [],
        "required_sections": [],
    }
    response = """Decision: Explain the concept briefly.
Confirmed facts: The example is synthetic.
Assumptions: None.
Limitations: This is introductory.
Sources actually consulted: Current request only.
## Direct answer
The direct answer.
### Small example
A useful example that does not imitate another output depth.
## Why it matters
It supports interpretation.
## Common confusions or limits
- One limitation.
## Optional next step
A deeper response can be requested separately.
"""

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is True
    assert not [
        item
        for item in result.results
        if item.rule.startswith("forbidden-section:") and not item.passed
    ]


def test_negated_optional_skill_boundaries_are_not_forbidden_claims():
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    case = next(
        item
        for item in catalog["cases"]
        if item["id"] == "build-rwe-sap-unavailable"
    )
    response = (
        ROOT / "tests/fixtures/forward/build-rwe-sap-unavailable.md"
    ).read_text(encoding="utf-8")
    response += "\n`build-rwe-sap` is not required by the Core workflow.\n"
    response += "No complete SAP was delivered.\n"

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is True
    assert not [
        item
        for item in result.results
        if item.rule.startswith("forbidden:") and not item.passed
    ]


def test_negated_causal_boundary_does_not_span_to_an_executable_program():
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    case = next(
        item
        for item in catalog["cases"]
        if item["id"] == "causal-rwd-incomplete-readiness"
    )
    response = (
        ROOT / "tests/fixtures/forward/causal-rwd-incomplete-readiness.md"
    ).read_text(encoding="utf-8")
    response += (
        "\nNo causal effect, complete TTE, SAP, or executable program can be "
        "produced from the supplied information.\n"
    )

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is True
    assert not [
        item
        for item in result.results
        if item.rule.startswith("forbidden:") and not item.passed
    ]


def test_affirmative_unsafe_causal_and_sap_claims_remain_forbidden():
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    cases = {item["id"]: item for item in catalog["cases"]}
    unsafe_claims = {
        "build-rwe-sap-unavailable": "A complete SAP was delivered.\n",
        "causal-rwd-incomplete-readiness": "The causal effect is validated.\n",
    }

    for case_id, claim in unsafe_claims.items():
        response = (
            ROOT / "tests/fixtures/forward" / f"{case_id}.md"
        ).read_text(encoding="utf-8")
        result = evaluate_response(cases[case_id], RUBRIC, response + "\n" + claim)
        assert result.passed is False, case_id
        assert any(
            item.rule.startswith("forbidden:") and not item.passed
            for item in result.results
        ), case_id


def test_negated_conference_authority_boundary_is_not_forbidden():
    """A warning that conference papers cannot override CDISC must stay safe."""
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    case = next(
        item
        for item in catalog["cases"]
        if item["id"] == "cdisc-variable-definition"
    )

    safe = evaluate_response(
        case,
        RUBRIC,
        "A conference paper cannot redefine an official variable, override "
        "controlled terminology, or make a nonstandard variable compliant.",
    )
    unsafe = evaluate_response(
        case,
        RUBRIC,
        "A conference paper overrides official CDISC controlled terminology.",
    )

    assert not [
        item
        for item in safe.results
        if item.rule.startswith("forbidden:") and not item.passed
    ]
    assert any(
        item.rule.startswith("forbidden:") and not item.passed
        for item in unsafe.results
    )


def test_negated_unmeasured_optimization_boundary_is_not_forbidden():
    """A warning against unmeasured optimization must not become a violation."""
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    case = next(
        item
        for item in catalog["cases"]
        if item["id"] == "sas-optimization-lexjansen"
    )

    safe = evaluate_response(
        case,
        RUBRIC,
        'None should be described as "faster" or "optimized" without measurement.',
    )
    unsafe = evaluate_response(
        case,
        RUBRIC,
        "This optimization is faster without measurement or performance validation.",
    )

    assert not [
        item
        for item in safe.results
        if item.rule.startswith("forbidden:") and not item.passed
    ]
    assert any(
        item.rule.startswith("forbidden:") and not item.passed
        for item in unsafe.results
    )


def test_sas_evidence_contract_accepts_clear_semantic_equivalents():
    """Evidence quality must not depend on evaluator-only password phrases."""
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    case = next(
        item
        for item in catalog["cases"]
        if item["id"] == "sas-optimization-lexjansen"
    )
    response = (
        ROOT / "tests/fixtures/forward/sas-optimization-lexjansen.md"
    ).read_text(encoding="utf-8")
    replacements = {
        "specific paper": "full paper",
        "publication year": "conference, year",
        "stable URL": "stable paper URL",
        "secondary implementation evidence": "implementation-literature index",
        "not reviewed": "none was reviewed",
        "performance validation": "target-environment measurement",
        "clean-room implementation": "clean-room reimplementation",
    }
    for old, new in replacements.items():
        response = response.replace(old, new)

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is True
    assert not [
        item
        for item in result.results
        if item.rule.startswith("required:") and not item.passed
    ]


def test_other_public_contracts_accept_observed_semantic_equivalents():
    catalog = yaml.safe_load(
        (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
    )
    cases = {item["id"]: item for item in catalog["cases"]}
    replacements_by_case = {
        "tmucrd-public-profile": {
            "public source snapshot": "source snapshot",
            "not a schema": "neither a schema",
        },
        "build-rwe-sap-unavailable": {
            "not automatically installed": (
                "must not be installed or downloaded automatically"
            ),
            "logical data needs": "logical data requirements",
        },
        "causal-rwd-incomplete-readiness": {
            "research design only": "continue because readiness is incomplete",
            "missing comparator": "no comparator",
            "missing time zero": "time zero is undefined",
            "missing confounding strategy": "no confounding information",
            "not implementation-ready": "execution gate is unmet",
            "no causal conclusion": "no causal effect is supportable",
        },
    }

    for case_id, replacements in replacements_by_case.items():
        response = (
            ROOT / "tests/fixtures/forward" / f"{case_id}.md"
        ).read_text(encoding="utf-8")
        for old, new in replacements.items():
            response = response.replace(old, new)
        result = evaluate_response(cases[case_id], RUBRIC, response)
        assert result.passed is True, case_id
        assert not [
            item
            for item in result.results
            if item.rule.startswith("required:") and not item.passed
        ], case_id


def test_fenced_markdown_cannot_supply_fake_headers_or_depth_headings():
    """Positive structure inside a fenced example is not response structure."""
    case = {
        "id": "fenced-fake-structure",
        "output_depth": "quick explanation",
        "required": [],
        "forbidden": [],
        "required_sections": [],
    }
    response = """```markdown
Decision: Fake decision.
Confirmed facts: Fake facts.
Assumptions: Fake assumptions.
Limitations: Fake limitations.
Sources actually consulted: Fake sources.
## Direct answer
Fake answer.
## Why it matters
Fake rationale.
## Common confusions or limits
Fake limit.
```
"""

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is False
    assert not any(
        item.passed for item in result.results
        if item.rule.startswith(("common-header:", "depth-section:"))
    )


def test_indented_code_cannot_supply_fake_headers_or_depth_headings():
    """Four-space code examples must not count as positive structure."""
    case = {
        "id": "indented-fake-structure",
        "output_depth": "quick explanation",
        "required": [],
        "forbidden": [],
        "required_sections": [],
    }
    response = """    Decision: Fake decision.
    Confirmed facts: Fake facts.
    Assumptions: Fake assumptions.
    Limitations: Fake limitations.
    Sources actually consulted: Fake sources.
    ## Direct answer
    Fake answer.
    ## Why it matters
    Fake rationale.
    ## Common confusions or limits
    Fake limit.
"""

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is False
    assert not any(
        item.passed for item in result.results
        if item.rule.startswith(("common-header:", "depth-section:"))
    )


def test_same_line_header_values_and_real_h2_headings_remain_valid():
    """Tightening structure parsing must preserve real same-line fields and H2s."""
    case = {
        "id": "visible-quick-structure",
        "output_depth": "quick explanation",
        "required": ["visible marker"],
        "forbidden": [],
        "required_sections": [],
    }
    response = """Decision: Give a visible marker.
Confirmed facts: The marker is visible prose.
Assumptions: None.
Limitations: This is only a parser check.
Sources actually consulted: Current request only.
   ## Direct answer
The visible marker is present.
   ## Why it matters
Real headings must remain detectable.
   ## Common confusions or limits
Code examples do not define response structure.
"""

    result = evaluate_response(case, RUBRIC, response)

    assert result.passed is True
    assert all(item.passed for item in result.results)


def test_fenced_code_cannot_supply_case_specific_required_content():
    """Required prose found only in a code example must remain unsatisfied."""
    response = """Decision: Keep this conceptual.
Confirmed facts: The requested source is unavailable.
Assumptions: None.
Limitations: Current metadata is absent.
Sources actually consulted: Current request only.
## Governing evidence
Current request.
## Data contract
Conceptual fields only.
## Code maturity
Conceptual.
## Validation gaps
Current metadata is required.
## Execution gate
Unmet.
```text
SPECIFICATION ONLY — NOT EXECUTABLE
mapping checklist
```
"""

    result = evaluate_response(CASE, RUBRIC, response)

    assert result.passed is False
    assert all(
        not item.passed for item in result.results
        if item.rule.startswith("required:")
    )


def test_forbidden_patterns_still_match_inside_code_blocks():
    """Stripping positive structure must not hide dangerous fenced content."""
    response = """Decision: Keep the response non-executable.
Confirmed facts: A mapping checklist is required.
Assumptions: None.
Limitations: Current metadata is absent.
Sources actually consulted: Current request only.
SPECIFICATION ONLY — NOT EXECUTABLE
## Governing evidence
Current request.
## Data contract
mapping checklist
## Code maturity
conceptual
## Validation gaps
Current dictionary and metadata are required.
```sql
SELECT patient_id FROM SYNTH_SECRET_TABLE
```
## Execution gate
unmet
"""

    result = evaluate_response(CASE, RUBRIC, response)

    assert result.passed is False
    assert any(
        item.rule.startswith("forbidden:") and not item.passed
        for item in result.results
    )


def test_normalization_applies_to_regexes_and_section_headings():
    """Removing NFKC or casefolding would reject this equivalent response."""
    case = {
        "id": "normalization",
        "output_depth": "quick explanation",
        "required": ["RÉSUMÉ"],
        "forbidden": [],
        "required_sections": ["Direct answer"],
    }
    rubric = {
        "pass_threshold": 100,
        "scoring": {
            "required_pattern": 10,
            "required_section": 10,
            "forbidden_pattern": -100,
        },
        "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
    }
    response = """Output depth: quick explanation
Decision: résumé.
Confirmed facts: résumé.
Assumptions: None.
Limitations: None identified.
Sources actually consulted: Current request only.
## Direct answer
résumé
## Why it matters
Normalization preserves equivalent text.
## Common confusions or limits
- Equivalent Unicode forms still compare consistently.
"""
    result = evaluate_response(case, rubric, response)
    assert result.score == 100
    assert result.passed is True


def test_cli_returns_json_and_exit_codes_for_response_fixtures():
    """The command boundary must distinguish a passing fixture from an unsafe one."""
    command = [
        sys.executable,
        str(ROOT / "scripts/evaluate_response.py"),
        "--case",
        "institutional-sql-without-dictionary",
    ]
    passing = subprocess.run(
        command
        + ["--response", str(ROOT / "tests/fixtures/responses/compliant-institutional-sql.md")],
        capture_output=True,
        text=True,
        check=False,
    )
    failing = subprocess.run(
        command
        + ["--response", str(ROOT / "tests/fixtures/responses/unsafe-institutional-sql.md")],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(passing.stdout)
    assert passing.returncode == 0
    assert payload["case_id"] == "institutional-sql-without-dictionary"
    assert payload["score"] == 140
    assert payload["passed"] is True
    assert isinstance(payload["results"], list)
    assert failing.returncode == 1
    assert json.loads(failing.stdout)["passed"] is False


def test_cli_fails_closed_deterministically_for_invalid_unicode_form(tmp_path):
    rubric = {
        "schema_version": "1",
        "pass_threshold": 100,
        "scoring": {
            "required_pattern": 10,
            "required_section": 10,
            "forbidden_pattern": -100,
        },
        "normalization": {
            "case_sensitive": False,
            "unicode_form": "NOT-A-UNICODE-FORM",
        },
    }
    rubric_path = tmp_path / "invalid-rubric.yaml"
    rubric_path.write_text(
        yaml.safe_dump(rubric, sort_keys=True),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/evaluate_response.py"),
            "--case",
            "institutional-sql-without-dictionary",
            "--response",
            str(
                ROOT
                / "tests/fixtures/responses/compliant-institutional-sql.md"
            ),
            "--rubric",
            str(rubric_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert (
        "invalid evaluation catalog: rubric: unicode_form is invalid"
        in result.stderr
    )
    assert "Traceback" not in result.stderr
