from pathlib import Path
import subprocess

import yaml

from scripts.check_public_boundary import scan_repository


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


def test_eval_catalog_has_eleven_unique_cases():
    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == 11
    assert len({case["id"] for case in cases}) == 11
    assert {case["id"] for case in cases} == {
        "teae-sas-spec",
        "sas-optimization-lexjansen",
        "institutional-sql-without-dictionary",
        "stale-codingbook",
        "cdisc-variable-definition",
        "omop-phenotype",
        "tmucrd-public-profile",
        "descriptive-rwd-no-tte",
        "causal-rwd-tte-handoff",
        "causal-rwd-incomplete-readiness",
        "build-rwe-sap-unavailable",
    }


def _initialize_repository(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)


def test_public_boundary_ignores_untracked_local_tool_configuration(tmp_path):
    repository = tmp_path / "repository"
    _initialize_repository(repository)
    configuration = repository / ".baoyu-skills/baoyu-translate/EXTEND.md"
    configuration.parent.mkdir(parents=True)
    configuration.write_text("target_language: zh-TW\n", encoding="utf-8")

    assert scan_repository(repository) == []


def test_public_boundary_rejects_tracked_local_tool_configuration(tmp_path):
    repository = tmp_path / "repository"
    _initialize_repository(repository)
    configuration = repository / ".baoyu-skills/baoyu-translate/EXTEND.md"
    configuration.parent.mkdir(parents=True)
    configuration.write_text("target_language: zh-TW\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "--", ".baoyu-skills/baoyu-translate/EXTEND.md"],
        cwd=repository,
        check=True,
    )

    findings = scan_repository(repository)

    assert [
        (finding.path, finding.rule, finding.detail)
        for finding in findings
    ] == [
        (
            ".baoyu-skills/baoyu-translate/EXTEND.md",
            "unrelated-local-tool-configuration",
            "local tool configuration is not permitted in the public project",
        )
    ]
