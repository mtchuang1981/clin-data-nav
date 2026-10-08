"""Public-boundary Git identity regressions using synthetic repositories."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_public_boundary import scan_repository


ROOT = Path(__file__).resolve().parents[1]


def _git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments], cwd=root, check=True, capture_output=True,
    )


def _repository(path: Path) -> Path:
    path.mkdir()
    _git(path, "init", "-q")
    return path


def _invalid_nested_root(tmp_path: Path, metadata: str) -> Path:
    ancestor = _repository(tmp_path / "ancestor")
    nested = ancestor / "nested repo"
    nested.mkdir()
    if metadata == "directory":
        (nested / ".git").mkdir()
    else:
        (nested / ".git").write_text("invalid synthetic metadata\n", encoding="utf-8")
    return nested


@pytest.mark.parametrize("metadata", ["directory", "file"])
def test_invalid_nested_git_metadata_fails_before_reading_content(
    tmp_path, monkeypatch, metadata,
):
    nested = _invalid_nested_root(tmp_path, metadata)
    payload = nested / "notes.md"
    payload.write_text("synthetic payload must not be read", encoding="utf-8")
    original_read = Path.read_text
    reads = []

    def observe_read(path, *args, **kwargs):
        if path == payload:
            reads.append(path)
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", observe_read)

    findings = scan_repository(nested)

    assert [(item.path, item.rule) for item in findings] == [
        (".", "tracked-path-query-failed"),
    ]
    assert reads == []


@pytest.mark.parametrize("metadata", ["directory", "file"])
def test_invalid_nested_git_metadata_cli_hides_git_diagnostics(tmp_path, metadata):
    nested = _invalid_nested_root(tmp_path, metadata)

    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_public_boundary.py"), str(nested)],
        check=False, capture_output=True, text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ".: tracked-path-query-failed\n"
    assert result.stderr == ""
    assert str(nested) not in result.stdout


def test_scanner_rejects_git_worktree_root_redirect(tmp_path, monkeypatch):
    ancestor = _repository(tmp_path / "ancestor")
    nested = _repository(ancestor / "nested")
    monkeypatch.setenv("GIT_WORK_TREE", str(ancestor))

    findings = scan_repository(nested)

    assert [(item.path, item.rule) for item in findings] == [
        (".", "tracked-path-query-failed"),
    ]


def test_linked_worktree_preserves_force_tracked_sdd_checks(tmp_path):
    repository = _repository(tmp_path / "repository")
    _git(
        repository, "-c", "user.name=Synthetic Tester", "-c",
        "user.email=synthetic@example.invalid", "commit", "--allow-empty",
        "-q", "-m", "synthetic baseline",
    )
    linked = tmp_path / "linked worktree"
    _git(repository, "worktree", "add", "-q", "--detach", str(linked), "HEAD")
    assert (linked / ".git").is_file()
    relative = ".superpowers/sdd/fixture.pdf"
    fixture = linked / relative
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes(b"synthetic PDF-shaped fixture")
    _git(linked, "add", "-f", "--", relative)

    findings = scan_repository(linked)

    assert [(item.path, item.rule) for item in findings] == [(relative, "pdf-file")]


def test_no_git_child_keeps_filesystem_fallback_inside_ancestor(tmp_path):
    ancestor = _repository(tmp_path / "ancestor")
    nested = ancestor / "plain directory"
    fixture = nested / ".superpowers/sdd/fixture.pdf"
    fixture.parent.mkdir(parents=True)
    fixture.write_bytes(b"synthetic PDF-shaped fixture")

    findings = scan_repository(nested)

    assert [(item.path, item.rule) for item in findings] == [
        (".superpowers/sdd/fixture.pdf", "pdf-file"),
    ]


def test_git_root_accepts_internal_spaces_and_unicode(tmp_path):
    repository = _repository(tmp_path / "public repo 測試")

    assert scan_repository(repository) == []


@pytest.mark.skipif(os.name == "nt", reason="Win32 trailing-space path is not portable")
def test_git_root_preserves_legal_leading_and_trailing_spaces(tmp_path):
    repository = _repository(tmp_path / " repository ")

    assert scan_repository(repository) == []


@pytest.mark.skipif(os.name != "nt", reason="Windows path equivalence contract")
@pytest.mark.parametrize("variant", ["separator", "case"])
def test_git_root_accepts_windows_equivalent_paths(tmp_path, variant):
    repository = _repository(tmp_path / "Case Repository")
    selected = (
        repository.as_posix() if variant == "separator" else str(repository).swapcase()
    )

    assert scan_repository(Path(selected)) == []


@pytest.mark.parametrize("identity", ["different", "unavailable"])
def test_root_identity_mismatch_or_failure_is_not_accepted(
    tmp_path, monkeypatch, identity,
):
    """Simulate the OS identity boundary, not case-sensitive Windows coverage."""
    repository = _repository(tmp_path / "repository")

    def identity_result(path, other):
        if identity == "unavailable":
            raise OSError("synthetic identity lookup failure")
        return False

    monkeypatch.setattr(Path, "samefile", identity_result)

    findings = scan_repository(repository)

    assert [(item.path, item.rule) for item in findings] == [
        (".", "tracked-path-query-failed"),
    ]


def test_case_distinct_physical_roots_cannot_share_git_identity(tmp_path, monkeypatch):
    upper = _repository(tmp_path / "Case Repo")
    lower_path = tmp_path / "case repo"
    if lower_path.exists():
        pytest.skip("filesystem does not support case-distinct sibling directories")
    lower = _repository(lower_path)
    monkeypatch.setenv("GIT_DIR", str(upper / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(upper))

    findings = scan_repository(lower)

    assert [(item.path, item.rule) for item in findings] == [
        (".", "tracked-path-query-failed"),
    ]
