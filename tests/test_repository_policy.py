from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_agents_policy_contains_public_boundary_and_release_stop():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Do not read or copy private TMUCRD adapters" in text
    assert "Do not create or push a GitHub repository" in text
    assert "python -m pytest -q" in text
    assert "python scripts/check_public_boundary.py" in text


def test_agents_policy_requires_skill_sync_and_final_diff_review():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert (
        "When modifying SKILL.md, also review agents/openai.yaml, Evals, and references."
        in text
    )
    assert "Before completion, review git diff." in text


def test_eval_catalog_has_six_unique_cases():
    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == 6
    assert len({case["id"] for case in cases}) == 6
    assert {case["id"] for case in cases} == {
        "teae-sas-spec",
        "institutional-sql-without-dictionary",
        "stale-codingbook",
        "cdisc-variable-definition",
        "omop-phenotype",
        "tmucrd-public-profile",
    }
