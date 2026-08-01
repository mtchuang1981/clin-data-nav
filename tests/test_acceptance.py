import os
from pathlib import Path
import subprocess

import pytest

from scripts.check_public_boundary import scan_repository
from scripts.validate_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clinical-data-research-navigator"


def initialize_repository(path: Path, branch: str = "main") -> None:
    subprocess.run(
        ["git", "init", "-q", "-b", branch, path],
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Acceptance Test"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "acceptance@example.invalid"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", "baseline"],
        cwd=path,
        check=True,
    )


def default_branch_is_main(root: Path) -> bool:
    remote_head = subprocess.run(
        [
            "git",
            "symbolic-ref",
            "--quiet",
            "--short",
            "refs/remotes/origin/HEAD",
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if remote_head.returncode == 0:
        return remote_head.stdout.strip() == "origin/main"
    if remote_head.returncode not in (1, 128):
        return False
    head = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if head.returncode == 0:
        return head.stdout.strip() == "main"
    if head.returncode != 1:
        return False
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", "refs/heads/main"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        return github_base_ref == "main"
    return os.environ.get("GITHUB_REF") == "refs/heads/main"


def test_attached_feature_with_local_main_ref_is_rejected(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    initialize_repository(repository)
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature"],
        cwd=repository,
        check=True,
    )
    monkeypatch.delenv("GITHUB_BASE_REF", raising=False)
    monkeypatch.delenv("GITHUB_REF", raising=False)

    assert not default_branch_is_main(repository)


def test_attached_feature_accepts_origin_defaulting_to_main(tmp_path):
    repository = tmp_path / "repository"
    initialize_repository(repository)
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feature"],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "update-ref",
            "refs/remotes/origin/main",
            "refs/heads/main",
        ],
        cwd=repository,
        check=True,
    )
    subprocess.run(
        [
            "git",
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main",
        ],
        cwd=repository,
        check=True,
    )

    assert default_branch_is_main(repository)


def test_detached_checkout_with_local_main_ref_is_accepted(tmp_path):
    repository = tmp_path / "repository"
    initialize_repository(repository)
    subprocess.run(
        ["git", "checkout", "-q", "--detach", "HEAD"],
        cwd=repository,
        check=True,
    )

    assert default_branch_is_main(repository)


@pytest.mark.parametrize(
    ("base_ref", "ref"),
    [
        ("main", "refs/pull/123/merge"),
        ("", "refs/heads/main"),
    ],
)
def test_detached_checkout_uses_github_main_target(
    tmp_path, monkeypatch, base_ref, ref
):
    repository = tmp_path / "repository"
    initialize_repository(repository, branch="feature")
    subprocess.run(
        ["git", "checkout", "-q", "--detach", "HEAD"],
        cwd=repository,
        check=True,
    )
    monkeypatch.setenv("GITHUB_BASE_REF", base_ref)
    monkeypatch.setenv("GITHUB_REF", ref)

    assert default_branch_is_main(repository)


def test_detached_checkout_rejects_non_main_github_target(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    initialize_repository(repository, branch="feature")
    subprocess.run(
        ["git", "checkout", "-q", "--detach", "HEAD"],
        cwd=repository,
        check=True,
    )
    monkeypatch.setenv("GITHUB_BASE_REF", "release")
    monkeypatch.setenv("GITHUB_REF", "refs/pull/123/merge")

    assert not default_branch_is_main(repository)


def twelve_eval_cases_exist() -> bool:
    import yaml

    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    return len(data["cases"]) == 12


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
    assert default_branch_is_main(ROOT)
    assert validate_skill(SKILL) == []
    assert scan_repository(ROOT) == []
    assert twelve_eval_cases_exist()
    assert build_rwe_sap_is_optional()
    assert tmucrd_profile_is_public_snapshot()
    assert required_repository_policy_exists()
