from pathlib import Path
import subprocess

from scripts.check_public_boundary import scan_repository
from scripts.validate_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clinical-data-research-navigator"


def default_branch_is_main() -> bool:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == "main"


def six_eval_cases_exist() -> bool:
    import yaml

    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    return len(data["cases"]) == 6


def build_rwe_sap_is_optional() -> bool:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
    return "build-rwe-sap" in text and "optional" in text


def tmucrd_profile_is_public_snapshot() -> bool:
    text = (SKILL / "references/tmucrd-public-profile.md").read_text(
        encoding="utf-8"
    )
    return (
        "public source snapshot" in text
        and "not a data dictionary" in text
        and "10.1136/bmjhci-2023-100890" in text
    )


def required_repository_policy_exists() -> bool:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    return (
        "Do not read or copy private TMUCRD adapters" in text
        and "Do not create or push a GitHub repository" in text
    )


def test_v010_acceptance_contract():
    assert default_branch_is_main()
    assert validate_skill(SKILL) == []
    assert scan_repository(ROOT) == []
    assert six_eval_cases_exist()
    assert build_rwe_sap_is_optional()
    assert tmucrd_profile_is_public_snapshot()
    assert required_repository_policy_exists()
