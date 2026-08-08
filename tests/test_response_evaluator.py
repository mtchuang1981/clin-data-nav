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
