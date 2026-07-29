from pathlib import Path
import subprocess

import pytest

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


def _repository(tmp_path: Path, version: str = "0.2.2") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
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
