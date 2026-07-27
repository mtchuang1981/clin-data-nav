from pathlib import Path
import re

import yaml

from scripts.evaluate_response import validate_catalog


ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = {
    "teae-sas-spec",
    "institutional-sql-without-dictionary",
    "stale-codingbook",
    "cdisc-variable-definition",
    "omop-phenotype",
    "tmucrd-public-profile",
}


def test_each_case_uses_the_public_eval_schema():
    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert {case["id"] for case in cases} == CASE_IDS
    for case in cases:
        assert set(case) == {
            "id",
            "prompt",
            "required",
            "forbidden",
            "required_sections",
        }
        assert isinstance(case["id"], str) and case["id"]
        assert isinstance(case["prompt"], str) and case["prompt"]
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
            "required_pattern": 20,
            "required_section": 20,
            "forbidden_pattern": -100,
        },
        "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
    }


def test_tmucrd_forbidden_sql_pattern_matches_a_literal_asterisk():
    cases = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))["cases"]
    tmucrd_case = next(case for case in cases if case["id"] == "tmucrd-public-profile")
    pattern = next(item for item in tmucrd_case["forbidden"] if item.startswith("SELECT"))
    assert re.search(pattern, "SELECT * FROM synthetic_source")


def test_controls_are_saved_as_response_only_baselines():
    fixture_dir = ROOT / "tests/fixtures/baseline"
    fixture_ids = {
        "institutional-sql-without-dictionary",
        "stale-codingbook",
        "tmucrd-public-profile",
    }
    assert {path.stem for path in fixture_dir.glob("*.md")} == fixture_ids
    for fixture_id in fixture_ids:
        text = (fixture_dir / f"{fixture_id}.md").read_text(encoding="utf-8")
        assert text.strip()
        lowered = text.lower()
        for marker in (
            "prompt:",
            "rubric:",
            "expected answer:",
            "private dictionary:",
            "existing skill:",
            "system prompt",
            "hidden reasoning",
        ):
            assert marker not in lowered
        assert not lowered.startswith("public-background text (safe to reuse):")


def test_catalog_validation_rejects_missing_case_key():
    """Removing a required schema field must make catalog validation fail."""
    catalog = {"cases": [{"id": "test", "prompt": "x", "required": [], "forbidden": []}]}
    errors = validate_catalog(catalog, {"pass_threshold": 0, "scoring": {"required_pattern": 1, "required_section": 1, "forbidden_pattern": -1}, "normalization": {"case_sensitive": False, "unicode_form": "NFKC"}})
    assert "case test: missing keys: required_sections" in errors


def test_catalog_validation_rejects_duplicate_ids_and_empty_prompts():
    """Duplicate IDs or whitespace-only prompts must not enter the offline catalog."""
    case = {
        "id": "duplicate",
        "prompt": " ",
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


def test_catalog_validation_rejects_unreachable_threshold():
    """A threshold above every positive rule's total cannot produce a passing result."""
    rubric = _valid_rubric()
    rubric["pass_threshold"] = 31
    assert "pass threshold 31 exceeds maximum possible score 30" in validate_catalog(
        {"cases": [_valid_case()]}, rubric
    )


def _valid_case():
    return {
        "id": "test",
        "prompt": "valid prompt",
        "required": ["required"],
        "forbidden": [],
        "required_sections": ["Section"],
    }


def _valid_rubric():
    return {
        "pass_threshold": 30,
        "scoring": {
            "required_pattern": 10,
            "required_section": 20,
            "forbidden_pattern": -100,
        },
        "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
    }
