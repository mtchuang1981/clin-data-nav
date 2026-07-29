from pathlib import Path
import os
import subprocess
import sys

import pytest

import scripts.verify_release as verify_release
from scripts.verify_release import (
    ReleaseVerificationError,
    verify_release_ref,
)


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _repository(
    tmp_path: Path, version: str = "0.2.2", name: str = "repo"
) -> Path:
    repo = tmp_path / name
    repo.mkdir(parents=True)
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.invalid")
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "clin-data-nav"\nversion = "{version}"\n',
        encoding="utf-8",
    )
    _git(repo, "add", "pyproject.toml")
    _git(repo, "commit", "-m", "initial")
    return repo


def test_annotated_version_matched_main_reachable_tag_is_accepted(tmp_path):
    repo = _repository(tmp_path)
    _git(repo, "tag", "-a", "v0.2.2", "-m", "release v0.2.2")

    result = verify_release_ref(repo, "v0.2.2", "main")

    assert result.tag == "v0.2.2"
    assert result.version == "0.2.2"
    assert result.commit == _git(repo, "rev-parse", "HEAD")


def test_lightweight_tag_is_rejected(tmp_path):
    repo = _repository(tmp_path)
    _git(repo, "tag", "v0.2.2")

    with pytest.raises(ReleaseVerificationError, match="annotated"):
        verify_release_ref(repo, "v0.2.2", "main")


@pytest.mark.parametrize("tag", ["0.2.2", "v0.2", "v0.2.2-rc1", "-v0.2.2"])
def test_non_release_tag_shape_is_rejected(tmp_path, tag):
    repo = _repository(tmp_path)

    with pytest.raises(ReleaseVerificationError, match="vX.Y.Z"):
        verify_release_ref(repo, tag, "main")


def test_tag_and_project_version_mismatch_is_rejected(tmp_path):
    repo = _repository(tmp_path, version="0.2.1")
    _git(repo, "tag", "-a", "v0.2.2", "-m", "wrong version")

    with pytest.raises(ReleaseVerificationError, match="project version"):
        verify_release_ref(repo, "v0.2.2", "main")


def test_tag_must_match_checked_out_commit(tmp_path):
    repo = _repository(tmp_path)
    _git(repo, "tag", "-a", "v0.2.2", "-m", "release")
    (repo / "later.txt").write_text("later\n", encoding="utf-8")
    _git(repo, "add", "later.txt")
    _git(repo, "commit", "-m", "later")

    with pytest.raises(ReleaseVerificationError, match="checked-out HEAD"):
        verify_release_ref(repo, "v0.2.2", "main")


def test_tag_commit_must_be_reachable_from_main(tmp_path):
    repo = _repository(tmp_path)
    _git(repo, "switch", "-c", "release-side")
    (repo / "side.txt").write_text("side\n", encoding="utf-8")
    _git(repo, "add", "side.txt")
    _git(repo, "commit", "-m", "side")
    _git(repo, "tag", "-a", "v0.2.2", "-m", "side release")

    with pytest.raises(ReleaseVerificationError, match="reachable from main"):
        verify_release_ref(repo, "v0.2.2", "main")


def test_annotated_tag_that_does_not_peel_to_a_commit_is_rejected(tmp_path):
    repo = _repository(tmp_path)
    _git(repo, "tag", "-a", "v0.2.2", "HEAD^{tree}", "-m", "tree tag")

    with pytest.raises(ReleaseVerificationError, match="could not be completed safely"):
        verify_release_ref(repo, "v0.2.2", "main")


@pytest.mark.parametrize(
    "metadata",
    [None, "not valid toml = [", '[project]\nname = "clin-data-nav"\n'],
    ids=["missing", "malformed", "missing-version"],
)
def test_unreadable_project_metadata_is_rejected_safely(tmp_path, metadata):
    repo = _repository(tmp_path)
    _git(repo, "tag", "-a", "v0.2.2", "-m", "release")
    metadata_path = repo / "pyproject.toml"
    if metadata is None:
        metadata_path.unlink()
    else:
        metadata_path.write_text(metadata, encoding="utf-8")

    with pytest.raises(ReleaseVerificationError, match="could not be completed safely"):
        verify_release_ref(repo, "v0.2.2", "main")


def test_git_environment_cannot_redirect_verification_to_another_repository(
    tmp_path, monkeypatch
):
    repo = _repository(tmp_path, name="root")
    _git(repo, "tag", "-a", "v0.2.2", "-m", "release")
    root_commit = _git(repo, "rev-parse", "HEAD")
    other = _repository(tmp_path, name="other")
    _git(other, "tag", "v0.2.2")
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))

    result = verify_release_ref(repo, "v0.2.2", "main")

    assert result.commit == root_commit


def test_cli_failure_is_safe_when_git_environment_points_to_non_commit_tag(tmp_path):
    repo = _repository(tmp_path)
    _git(repo, "tag", "-a", "v0.2.2", "HEAD^{tree}", "-m", "tree tag")
    environment = os.environ | {"GIT_DIR": str(repo / ".git")}

    result = subprocess.run(
        [sys.executable, "scripts/verify_release.py", "ref", "--tag", "v0.2.2"],
        capture_output=True,
        text=True,
        env=environment,
    )

    assert result.returncode == 1
    assert "release verification failed:" in result.stderr
    assert "Traceback" not in result.stderr


def test_git_environment_filter_keeps_safe_directory_config_and_removes_redirects(
    tmp_path, monkeypatch
):
    captured = {}

    def run(*arguments, **kwargs):
        captured.update(kwargs["env"])
        return subprocess.CompletedProcess(arguments[0], 0, "", "")

    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_NAMESPACE",
    ):
        monkeypatch.setenv(name, "redirect")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "safe.directory")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "*")
    monkeypatch.setattr(verify_release.subprocess, "run", run)

    verify_release._git(tmp_path, "status")

    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_NAMESPACE",
    ):
        assert name not in captured
    assert captured["GIT_CONFIG_COUNT"] == "1"
    assert captured["GIT_CONFIG_KEY_0"] == "safe.directory"
    assert captured["GIT_CONFIG_VALUE_0"] == "*"
