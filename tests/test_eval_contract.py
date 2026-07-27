from pathlib import Path

import yaml


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
            "required_pattern": 10,
            "required_section": 10,
            "forbidden_pattern": -100,
        },
        "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
    }


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
        assert "System prompt" not in text
        assert "hidden reasoning" not in text.lower()
