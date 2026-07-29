# Public Trust Repair v0.2.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make fresh Python 3.11 contribution, dual-platform validation, and fail-closed GitHub publishing trustworthy for the `v0.2.2` patch release.

**Architecture:** Declare the repository's Python package boundary explicitly, isolate operating-system selection behind one test seam, and put release-ref plus artifact checks in a standard-library Python verifier shared by tests and GitHub Actions. Keep documentation and Eval claims tied to filesystem-derived contract tests, then prove the complete result on native Windows, clean Linux, and GitHub Actions.

**Tech Stack:** Python 3.11, setuptools/PEP 517, pytest, PyYAML, GitHub Actions, GitHub CLI, PowerShell, POSIX shell, deterministic ZIP/JSON manifests.

## Global Constraints

- Start execution from approved design commit `6150412` in an isolated worktree created with `superpowers:using-git-worktrees`.
- Support exactly Python `>=3.11,<3.12`; do not broaden the supported Python range in this patch.
- Preserve all 168 existing tests; do not delete, skip, xfail, or weaken one to obtain a green result.
- Preserve atomic no-overwrite installation: no generic rename, copy-and-delete, delete-before-move, or overwrite fallback.
- Run the four-command verification set on both Windows and Linux:
  `python -m pytest -q`, `python scripts/validate_skill.py`,
  `python scripts/check_public_boundary.py`, and
  `python scripts/package_skill.py --check-reproducible`.
- Keep validation jobs at `contents: read`; only the post-validation publish job may receive `contents: write`.
- Preserve the public Core boundary: no private adapters, codingbooks, data dictionaries, schemas, credentials, login-gated documents, or non-synthetic institutional values.
- Do not guess clinical schema or design inputs, do not treat LexJansen as a governing authority, and do not silently install `build-rwe-sap`.
- Do not push, create or move a tag, dispatch the release workflow, change branch protection, or create a GitHub Release without a separate explicit approval.
- Keep English and Traditional Chinese README meaning and section order aligned.
- Use `0.2.2` for current release surfaces and preserve historical version records verbatim.

---

## File responsibility map

- `pyproject.toml`: project dependencies, PEP 517 backend, and explicit
  `scripts` package boundary.
- `.gitignore`: ignore setuptools' editable-install metadata.
- `scripts/install_local.py`: real-host platform classification and atomic
  no-replace publication.
- `scripts/verify_release.py`: standard-library checks for an annotated,
  version-matched, main-reachable tag and for ZIP/manifest integrity.
- `.github/workflows/validate.yml`: read-only Ubuntu/Windows validation matrix.
- `.github/workflows/release.yml`: manually dispatched preflight, validation,
  and least-privilege publication jobs.
- `docs/release.md`: human release procedure and authorization boundary.
- `docs/architecture.md`: validation and release trust boundaries.
- `evals/README.md`: truthful catalog-versus-fixture evidence statement.
- `README.md`, `README.zh-TW.md`: prerequisites, terminal/Codex boundary,
  first success, update path, and current version examples.
- `tests/test_project_metadata.py`: packaging, workflow, README, version, and
  architecture contracts.
- `tests/test_install_local.py`: portable platform behavior and fail-closed
  installer tests.
- `tests/test_release_verification.py`: release-ref and artifact-verifier unit
  tests.
- `tests/test_eval_contract.py`: filesystem-derived Eval documentation
  contract.
- `tests/test_repository_policy.py`: removal of unrelated local-tool state.
- `tests/test_packaging.py`: current archive/manifest version contract.
- `CITATION.cff`, `scripts/package_skill.py`, `scripts/install_local.py`,
  `CHANGELOG.md`, and `CHANGELOG.zh-TW.md`: synchronized `0.2.2` metadata.
- `docs/releases/0.2.2.md`: bilingual GitHub Release notes consumed by the
  guarded workflow.
- `docs/verification/2026-07-29-v0.2.1-assessment.md`: baseline findings,
  remediation evidence, deferrals, and remaining external settings.

---

### Task 1: Repair the fresh editable-install boundary

**Files:**
- Modify: `tests/test_project_metadata.py`
- Modify: `pyproject.toml`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: the existing `scripts/__init__.py` package and current
  `project.optional-dependencies.dev`.
- Produces: PEP 517 backend `setuptools.build_meta` and explicit package list
  `["scripts"]`; all later CI tasks use `python -m pip install -e ".[dev]"`.

- [ ] **Step 1: Add a failing packaging-metadata test**

Add this test to `tests/test_project_metadata.py`:

```python
def test_pyproject_declares_explicit_setuptools_package_boundary():
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert project["build-system"] == {
        "requires": ["setuptools>=68"],
        "build-backend": "setuptools.build_meta",
    }
    assert project["tool"]["setuptools"]["packages"] == ["scripts"]
```

- [ ] **Step 2: Run the test and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_project_metadata.py::test_pyproject_declares_explicit_setuptools_package_boundary -q
```

Expected: FAIL with `KeyError: 'build-system'`.

- [ ] **Step 3: Declare the build backend and package boundary**

Add before `[project]` in `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["scripts"]
```

Add this line to `.gitignore`:

```gitignore
*.egg-info/
```

Do not replace the editable install with direct `pip install PyYAML pytest`
commands.

- [ ] **Step 4: Run the focused contract**

Run:

```powershell
python -m pytest tests/test_project_metadata.py::test_pyproject_declares_explicit_setuptools_package_boundary -q
```

Expected: PASS.

- [ ] **Step 5: Prove a disposable fresh Windows install**

Run from PowerShell:

```powershell
$verifyVenv = Join-Path ([System.IO.Path]::GetTempPath()) ("clin-data-nav-" + [guid]::NewGuid())
py -3.11 -m venv $verifyVenv
& "$verifyVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$verifyVenv\Scripts\python.exe" -m pip install -e ".[dev]"
& "$verifyVenv\Scripts\python.exe" -c "import scripts, yaml, pytest; print(scripts.__file__)"
```

Expected: every command exits zero and the final output points to this
repository's editable `scripts` package. Clean up only this GUID-named
temporary environment:

```powershell
$resolvedVerifyVenv = (Resolve-Path -LiteralPath $verifyVenv).Path
$temporaryRoot = [System.IO.Path]::GetTempPath().TrimEnd('\')
if ((Split-Path -Parent $resolvedVerifyVenv) -ne $temporaryRoot) {
    throw "Refusing to remove a virtual environment outside the temporary root"
}
Remove-Item -LiteralPath $resolvedVerifyVenv -Recurse -Force
```

- [ ] **Step 6: Commit the packaging repair**

```powershell
git add -- pyproject.toml .gitignore tests/test_project_metadata.py
git commit -m "fix: declare Python package boundary"
```

---

### Task 2: Make platform tests portable without weakening atomic install

**Files:**
- Modify: `tests/test_install_local.py`
- Modify: `scripts/install_local.py`

**Interfaces:**
- Consumes: `os.name`, `sys.platform`, `_call_native_rename()`, and existing
  platform constants.
- Produces: `_platform_family() -> str`, returning exactly `"windows"`,
  `"linux"`, `"darwin"`, or `"unsupported"`.

- [ ] **Step 1: Change platform simulations to the new seam**

In `tests/test_install_local.py`, add:

```python
def test_platform_family_reports_the_running_host():
    family = install_local_module._platform_family()

    if install_local_module.os.name == "nt":
        assert family == "windows"
    elif install_local_module.sys.platform.startswith("linux"):
        assert family == "linux"
    elif install_local_module.sys.platform == "darwin":
        assert family == "darwin"
    else:
        assert family == "unsupported"
```

In `test_darwin_uses_atomic_exclusive_rename()`, replace the `sys.platform`
monkeypatch with:

```python
monkeypatch.setattr(
    install_local_module,
    "_platform_family",
    lambda: "darwin",
)
```

In `test_missing_native_no_replace_primitive_fails_closed()`, rename the
parameter to `platform_family` and patch:

```python
monkeypatch.setattr(
    install_local_module,
    "_platform_family",
    lambda: platform_family,
)
```

In `test_unsupported_platform_fails_closed()`, patch:

```python
monkeypatch.setattr(
    install_local_module,
    "_platform_family",
    lambda: "unsupported",
)
```

No test in this group may mutate global `os.name` or `sys.platform`.

- [ ] **Step 2: Run the platform tests and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_install_local.py -k "platform_family or darwin or missing_native or unsupported_platform" -q
```

Expected: FAIL because `_platform_family` does not exist.

- [ ] **Step 3: Add the real-host classifier and branch on it**

Add to `scripts/install_local.py` immediately before `_rename_no_replace()`:

```python
def _platform_family() -> str:
    if os.name == "nt":
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    return "unsupported"
```

Change `_rename_no_replace()` to compute `platform_family =
_platform_family()` once and use:

```python
def _rename_no_replace(source: Path, target: Path) -> None:
    platform_family = _platform_family()
    if platform_family == "windows":
        os.rename(source, target)
        return
    if platform_family == "linux":
        _call_native_rename(
            "renameat2",
            (
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_int,
                ctypes.c_char_p,
                ctypes.c_uint,
            ),
            (
                AT_FDCWD,
                os.fsencode(source),
                AT_FDCWD,
                os.fsencode(target),
                RENAME_NOREPLACE,
            ),
            target,
        )
        return
    if platform_family == "darwin":
        _call_native_rename(
            "renamex_np",
            (
                ctypes.c_char_p,
                ctypes.c_char_p,
                ctypes.c_uint,
            ),
            (
                os.fsencode(source),
                os.fsencode(target),
                DARWIN_RENAME_EXCL,
            ),
            target,
        )
        return
    raise OSError(
        errno.ENOTSUP,
        "atomic no-replace directory installation is unsupported",
        target,
    )
```

This keeps the native function names, argument types, arguments, and flags
unchanged.

- [ ] **Step 4: Run focused and complete installer tests**

Run:

```powershell
python -m pytest tests/test_install_local.py -q
```

Expected: all installer tests pass on native Windows, including the four that
failed in the `v0.2.1` baseline.

- [ ] **Step 5: Commit the platform seam**

```powershell
git add -- scripts/install_local.py tests/test_install_local.py
git commit -m "fix: isolate installer platform selection"
```

---

### Task 3: Add fail-closed release-ref verification

**Files:**
- Create: `scripts/verify_release.py`
- Create: `tests/test_release_verification.py`

**Interfaces:**
- Consumes: a repository root, an input tag, a main ref, `pyproject.toml`, and
  local Git objects.
- Produces:
  `ReleaseRef(tag: str, version: str, commit: str)`,
  `verify_release_ref(root: Path, tag: str, main_ref: str) -> ReleaseRef`, and
  CLI `python scripts/verify_release.py ref --tag TAG --main-ref REF`.

- [ ] **Step 1: Add real-Git tests for annotated-tag acceptance**

Create `tests/test_release_verification.py` with these helpers and first test:

```python
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
```

- [ ] **Step 2: Add rejection tests**

Add these tests to the same file:

```python
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
```

- [ ] **Step 3: Run the new test module and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_release_verification.py -q
```

Expected: collection FAIL because `scripts.verify_release` does not exist.

- [ ] **Step 4: Implement the release-ref verifier**

Create `scripts/verify_release.py` with these public types and functions:

```python
"""Fail-closed checks used before publishing a GitHub Release."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
import tomllib


TAG_PATTERN = re.compile(
    r"^v(?P<version>(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))$"
)


class ReleaseVerificationError(ValueError):
    """A release precondition was not satisfied."""


@dataclass(frozen=True)
class ReleaseRef:
    tag: str
    version: str
    commit: str


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
    )


def verify_release_ref(
    root: Path,
    tag: str,
    main_ref: str = "origin/main",
) -> ReleaseRef:
    root = root.resolve()
    match = TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise ReleaseVerificationError("release tag must have exact shape vX.Y.Z")
    version = match.group("version")

    try:
        object_type = _git(root, "cat-file", "-t", f"refs/tags/{tag}").stdout.strip()
    except subprocess.CalledProcessError as error:
        raise ReleaseVerificationError(f"release tag does not exist: {tag}") from error
    if object_type != "tag":
        raise ReleaseVerificationError("release tag must be annotated")

    commit = _git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}").stdout.strip()
    head = _git(root, "rev-parse", "HEAD").stdout.strip()
    if commit != head:
        raise ReleaseVerificationError(
            "release tag commit must match checked-out HEAD"
        )

    project = tomllib.loads(
        (root / "pyproject.toml").read_text(encoding="utf-8")
    )
    project_version = project["project"]["version"]
    if version != project_version:
        raise ReleaseVerificationError(
            f"tag version {version} does not match project version {project_version}"
        )

    ancestry = _git(
        root,
        "merge-base",
        "--is-ancestor",
        commit,
        main_ref,
        check=False,
    )
    if ancestry.returncode != 0:
        raise ReleaseVerificationError(
            f"release tag commit must be reachable from {main_ref}"
        )
    return ReleaseRef(tag=tag, version=version, commit=commit)
```

Add this CLI below the verifier:

```python
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    ref_parser = subparsers.add_parser("ref", help="verify a release tag")
    ref_parser.add_argument("--tag", required=True)
    ref_parser.add_argument("--main-ref", default="origin/main")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        if args.command == "ref":
            result = verify_release_ref(root, args.tag, args.main_ref)
            print(result.version)
            return 0
    except ReleaseVerificationError as error:
        print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run focused tests and the CLI help**

Run:

```powershell
python -m pytest tests/test_release_verification.py -q
python scripts/verify_release.py --help
python scripts/verify_release.py ref --help
```

Expected: all tests pass and both help commands exit zero without mutating Git
or GitHub state.

- [ ] **Step 6: Commit the release-ref boundary**

```powershell
git add -- scripts/verify_release.py tests/test_release_verification.py
git commit -m "feat: verify release tag preconditions"
```

---

### Task 4: Verify ZIP and manifest integrity before publication

**Files:**
- Modify: `scripts/verify_release.py`
- Modify: `tests/test_release_verification.py`

**Interfaces:**
- Consumes: deterministic ZIP and manifest paths produced by
  `scripts.package_skill.build_package()`.
- Produces:
  `verify_release_artifacts(archive: Path, manifest: Path) -> None` and CLI
  `python scripts/verify_release.py artifacts --archive ZIP --manifest JSON`.

- [ ] **Step 1: Add a passing artifact test**

Add imports:

```python
import hashlib
import json
from zipfile import ZipFile

from scripts.package_skill import build_package
from scripts.verify_release import verify_release_artifacts
```

Add:

```python
def test_packager_output_passes_release_artifact_verification(tmp_path):
    package = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path / "dist",
    )

    verify_release_artifacts(package.archive, package.manifest)
```

- [ ] **Step 2: Add fail-closed tamper tests**

Add:

```python
def test_archive_sha_mismatch_is_rejected(tmp_path):
    package = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path / "dist",
    )
    package.archive.write_bytes(package.archive.read_bytes() + b"tamper")

    with pytest.raises(ReleaseVerificationError, match="archive SHA-256"):
        verify_release_artifacts(package.archive, package.manifest)


def test_member_hash_mismatch_is_rejected(tmp_path):
    package = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path / "dist",
    )
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    package.manifest.write_text(
        json.dumps(manifest, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(ReleaseVerificationError, match="member SHA-256"):
        verify_release_artifacts(package.archive, package.manifest)


def test_undeclared_archive_member_is_rejected(tmp_path):
    package = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path / "dist",
    )
    with ZipFile(package.archive, "a") as archive:
        archive.writestr("undeclared.txt", b"not in manifest")
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["archive_sha256"] = hashlib.sha256(
        package.archive.read_bytes()
    ).hexdigest()
    package.manifest.write_text(
        json.dumps(manifest, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(ReleaseVerificationError, match="member set"):
        verify_release_artifacts(package.archive, package.manifest)


@pytest.mark.parametrize("unsafe_path", ["../outside.txt", r"..\outside.txt"])
def test_unsafe_manifest_member_is_rejected(tmp_path, unsafe_path):
    package = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path / "dist",
    )
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = unsafe_path
    package.manifest.write_text(
        json.dumps(manifest, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(ReleaseVerificationError, match="unsafe"):
        verify_release_artifacts(package.archive, package.manifest)
```

- [ ] **Step 3: Run the three new checks and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_release_verification.py -k "artifact or archive_sha or member_hash or undeclared" -q
```

Expected: FAIL because `verify_release_artifacts` does not exist.

- [ ] **Step 4: Implement artifact verification without extraction**

Add standard-library imports `hashlib`, `json`, `PurePosixPath`, `BadZipFile`,
and `ZipFile` to `scripts/verify_release.py`, then add:

```python
SKILL_NAME = "clinical-data-research-navigator"


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and path != PurePosixPath(".")
        and not path.is_absolute()
        and ".." not in path.parts
    )


def verify_release_artifacts(archive: Path, manifest: Path) -> None:
    archive = archive.resolve()
    manifest = manifest.resolve()
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ReleaseVerificationError("manifest must be valid UTF-8 JSON") from error

    required = {"archive", "archive_sha256", "files", "name", "version"}
    if not isinstance(data, dict) or set(data) != required:
        raise ReleaseVerificationError("manifest keys do not match release schema")
    if data["name"] != SKILL_NAME:
        raise ReleaseVerificationError("manifest Skill name is invalid")
    if not isinstance(data["archive_sha256"], str) or re.fullmatch(
        r"[0-9a-f]{64}",
        data["archive_sha256"],
    ) is None:
        raise ReleaseVerificationError("manifest archive SHA-256 is invalid")
    version = data["version"]
    if not isinstance(version, str) or re.fullmatch(
        r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)",
        version,
    ) is None:
        raise ReleaseVerificationError("manifest version is invalid")
    expected_archive = f"{SKILL_NAME}-{version}.zip"
    expected_manifest = f"{SKILL_NAME}-{version}.manifest.json"
    if archive.name != expected_archive or data["archive"] != expected_archive:
        raise ReleaseVerificationError("archive name does not match manifest version")
    if manifest.name != expected_manifest:
        raise ReleaseVerificationError("manifest filename does not match version")

    archive_bytes = archive.read_bytes()
    actual_archive_hash = hashlib.sha256(archive_bytes).hexdigest()
    if actual_archive_hash != data["archive_sha256"]:
        raise ReleaseVerificationError("archive SHA-256 does not match manifest")

    records = data["files"]
    if not isinstance(records, list):
        raise ReleaseVerificationError("manifest files must be a list")
    by_path = {}
    for record in records:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "size"}:
            raise ReleaseVerificationError("manifest file record is invalid")
        path = record["path"]
        if not isinstance(path, str) or not _safe_member_name(path):
            raise ReleaseVerificationError("manifest member path is unsafe")
        if not isinstance(record["size"], int) or record["size"] < 0:
            raise ReleaseVerificationError("manifest member size is invalid")
        if not isinstance(record["sha256"], str) or re.fullmatch(
            r"[0-9a-f]{64}",
            record["sha256"],
        ) is None:
            raise ReleaseVerificationError("manifest member SHA-256 is invalid")
        if path in by_path:
            raise ReleaseVerificationError("manifest contains duplicate members")
        by_path[path] = record

    try:
        with ZipFile(archive) as zip_file:
            infos = zip_file.infolist()
            names = [info.filename for info in infos]
            if len(names) != len(set(names)):
                raise ReleaseVerificationError("archive contains duplicate members")
            if any(
                info.is_dir() or not _safe_member_name(info.filename)
                for info in infos
            ):
                raise ReleaseVerificationError("archive member path is unsafe")
            if set(names) != set(by_path):
                raise ReleaseVerificationError(
                    "archive and manifest member sets differ"
                )
            for info in infos:
                member_bytes = zip_file.read(info)
                record = by_path[info.filename]
                if len(member_bytes) != record["size"]:
                    raise ReleaseVerificationError(
                        f"member size mismatch: {info.filename}"
                    )
                if hashlib.sha256(member_bytes).hexdigest() != record["sha256"]:
                    raise ReleaseVerificationError(
                        f"member SHA-256 mismatch: {info.filename}"
                    )
    except (OSError, BadZipFile) as error:
        raise ReleaseVerificationError("archive must be a readable ZIP") from error
```

Replace `_build_parser()` and `main()` with the combined CLI:

```python
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    ref_parser = subparsers.add_parser("ref", help="verify a release tag")
    ref_parser.add_argument("--tag", required=True)
    ref_parser.add_argument("--main-ref", default="origin/main")

    artifact_parser = subparsers.add_parser(
        "artifacts",
        help="verify a release ZIP and manifest",
    )
    artifact_parser.add_argument("--archive", required=True, type=Path)
    artifact_parser.add_argument("--manifest", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    try:
        if args.command == "ref":
            result = verify_release_ref(root, args.tag, args.main_ref)
            print(result.version)
            return 0
        if args.command == "artifacts":
            verify_release_artifacts(args.archive, args.manifest)
            print("release artifacts verified")
            return 0
    except ReleaseVerificationError as error:
        print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {args.command}")
```

- [ ] **Step 5: Run the complete release-verification module**

Run:

```powershell
python -m pytest tests/test_release_verification.py -q
python scripts/verify_release.py artifacts --help
```

Expected: all tests pass and CLI help exits zero.

- [ ] **Step 6: Commit the artifact gate**

```powershell
git add -- scripts/verify_release.py tests/test_release_verification.py
git commit -m "feat: verify release archive manifest"
```

---

### Task 5: Add dual-platform validation and guarded Release workflows

**Files:**
- Modify: `tests/test_project_metadata.py`
- Modify: `.github/workflows/validate.yml`
- Create: `.github/workflows/release.yml`
- Modify: `docs/release.md`
- Modify: `docs/architecture.md`

**Interfaces:**
- Consumes: both `verify_release.py` subcommands and the repository's
  four-command verification set.
- Produces: `validate` jobs on Ubuntu/Windows and manually dispatched
  `release` jobs `preflight -> validate -> publish`.

- [ ] **Step 1: Tighten validation-workflow contracts**

Replace `test_ci_has_read_only_permissions_and_required_commands()` with:

```python
def test_ci_has_dual_platform_read_only_jobs_and_required_commands():
    workflow_path = ROOT / ".github/workflows/validate.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    job = workflow["jobs"]["test"]

    assert workflow["permissions"] == {"contents": "read"}
    assert job["runs-on"] == "${{ matrix.os }}"
    assert set(job["strategy"]["matrix"]["os"]) == {
        "ubuntu-latest",
        "windows-latest",
    }
    rendered = workflow_path.read_text(encoding="utf-8")
    for command in (
        'python -m pip install -e ".[dev]"',
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    ):
        assert command in rendered
    assert "continue-on-error" not in rendered
    assert "secrets." not in rendered
```

- [ ] **Step 2: Add a fail-closed Release-workflow contract**

Add:

```python
def test_release_workflow_is_manual_fail_closed_and_least_privilege():
    path = ROOT / ".github/workflows/release.yml"
    rendered = path.read_text(encoding="utf-8")
    workflow = yaml.load(rendered, Loader=yaml.BaseLoader)

    assert "workflow_dispatch" in workflow["on"]
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["jobs"]) == {"preflight", "validate", "publish"}
    assert workflow["jobs"]["validate"]["needs"] == "preflight"
    assert workflow["jobs"]["publish"]["permissions"] == {"contents": "write"}
    assert set(workflow["jobs"]["publish"]["needs"]) == {
        "preflight",
        "validate",
    }
    assert rendered.count("contents: write") == 1
    assert "python scripts/verify_release.py ref" in rendered
    assert "python scripts/verify_release.py artifacts" in rendered
    assert "python scripts/package_skill.py" in rendered
    assert "gh release create" in rendered
    assert "--verify-tag" in rendered
    assert "continue-on-error" not in rendered
    assert "release edit" not in rendered
    assert "git tag -f" not in rendered
```

- [ ] **Step 3: Run both contracts and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_project_metadata.py -k "dual_platform or release_workflow" -q
```

Expected: validation matrix assertion FAIL and release workflow
`FileNotFoundError`.

- [ ] **Step 4: Convert validation to an OS matrix**

Make `.github/workflows/validate.yml`:

```yaml
name: validate

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e ".[dev]"
      - run: python -m pytest -q
      - run: python scripts/validate_skill.py
      - run: python scripts/check_public_boundary.py
      - run: python scripts/package_skill.py --check-reproducible
```

- [ ] **Step 5: Create the guarded manual Release workflow**

Create `.github/workflows/release.yml`:

```yaml
name: release

on:
  workflow_dispatch:
    inputs:
      tag:
        description: Existing annotated vX.Y.Z tag to publish
        required: true
        type: string

permissions:
  contents: read

jobs:
  preflight:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.verify.outputs.version }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ inputs.tag }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: git fetch origin main:refs/remotes/origin/main
      - id: verify
        shell: bash
        env:
          TAG: ${{ inputs.tag }}
        run: |
          version="$(python scripts/verify_release.py ref --tag "$TAG" --main-ref origin/main)"
          echo "version=$version" >> "$GITHUB_OUTPUT"
      - name: Refuse an existing Release and fail closed on API errors
        shell: bash
        env:
          GH_TOKEN: ${{ github.token }}
          TAG: ${{ inputs.tag }}
        run: |
          status="$(curl --silent --show-error --output release-response.json --write-out '%{http_code}' \
            --header "Accept: application/vnd.github+json" \
            --header "Authorization: Bearer $GH_TOKEN" \
            --header "X-GitHub-Api-Version: 2022-11-28" \
            "https://api.github.com/repos/$GITHUB_REPOSITORY/releases/tags/$TAG")"
          case "$status" in
            404) ;;
            200) echo "Release already exists: $TAG" >&2; exit 1 ;;
            *) echo "GitHub Release lookup failed with HTTP $status" >&2; exit 1 ;;
          esac

  validate:
    needs: preflight
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.tag }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e ".[dev]"
      - run: python -m pytest -q
      - run: python scripts/validate_skill.py
      - run: python scripts/check_public_boundary.py
      - run: python scripts/package_skill.py --check-reproducible

  publish:
    needs: [preflight, validate]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.tag }}
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e ".[dev]"
      - run: python scripts/package_skill.py
      - name: Verify and publish immutable assets
        shell: bash
        env:
          GH_TOKEN: ${{ github.token }}
          TAG: ${{ inputs.tag }}
          VERSION: ${{ needs.preflight.outputs.version }}
        run: |
          archive="dist/clinical-data-research-navigator-$VERSION.zip"
          manifest="dist/clinical-data-research-navigator-$VERSION.manifest.json"
          notes="docs/releases/$VERSION.md"
          test -f "$notes"
          python scripts/verify_release.py artifacts --archive "$archive" --manifest "$manifest"
          gh release create "$TAG" "$archive" "$manifest" \
            --repo "$GITHUB_REPOSITORY" \
            --verify-tag \
            --title "$TAG" \
            --notes-file "$notes"
```

Do not add a tag-push trigger. Manual dispatch is the publication approval
boundary.

- [ ] **Step 6: Document architecture and operator flow**

In `docs/architecture.md`, add a `Release trust boundary` section stating:

```markdown
## Release trust boundary

The validation workflow runs the same four-command verification set on Ubuntu
and Windows with read-only repository permissions. The manually dispatched
release workflow checks an existing annotated, version-matched tag that is
reachable from `origin/main`, repeats both platform jobs against that tag, and
grants `contents: write` only to the dependent publish job. The publish job
rebuilds and verifies the deterministic ZIP and manifest before creating a new
Release; it cannot edit an existing Release.
```

Replace `docs/release.md` with:

````markdown
# Release process

Release preparation is local and read-only until separate user approval for
GitHub publishing is given.

## Local preparation

1. Run the complete local verification set:

   ```bash
   python -m pytest -q
   python scripts/validate_skill.py
   python scripts/check_public_boundary.py
   python scripts/package_skill.py --check-reproducible
   ```

2. Confirm the version is synchronized in project metadata, installer,
   packager, citation, changelogs, READMEs, tests, and
   `docs/releases/X.Y.Z.md`.
3. Confirm `git status` is clean.
4. Generate the package and manifest with `python scripts/package_skill.py`.
5. Run `python scripts/verify_release.py artifacts` against those two files and
   manually review the public contents.

Stop here. Do not push, create or move a tag, dispatch a workflow, or create a
GitHub Release without separate explicit approval.

## Approved GitHub publication

After approval:

1. Push the verified commit to `main`.
2. Require the exact commit's Ubuntu and Windows `validate` matrix jobs to
   succeed with no skipped verification step.
3. Create an annotated `vX.Y.Z` tag at that commit and push only that new tag.
4. Manually dispatch `.github/workflows/release.yml` with the annotated tag.
   The workflow revalidates the tag on Ubuntu and Windows, rebuilds the assets,
   verifies the ZIP and manifest, and grants write permission only to its final
   publish job.
5. Confirm the public Release points to the intended tag and contains exactly
   `clinical-data-research-navigator-X.Y.Z.zip` and
   `clinical-data-research-navigator-X.Y.Z.manifest.json`.
6. Download both assets and independently confirm the ZIP SHA-256 equals
   `archive_sha256` in the manifest.

Never force-move a published tag or rerun publication to overwrite an existing
Release. Prepare a new patch version instead.
````

- [ ] **Step 7: Run workflow and architecture contracts**

Run:

```powershell
python -m pytest tests/test_project_metadata.py -k "ci_has or release_workflow or architecture" -q
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit the workflow gates**

```powershell
git add -- .github/workflows/validate.yml .github/workflows/release.yml docs/release.md docs/architecture.md tests/test_project_metadata.py
git commit -m "ci: gate validation and releases on both platforms"
```

---

### Task 6: Make Eval evidence scope self-verifying

**Files:**
- Modify: `tests/test_eval_contract.py`
- Modify: `evals/README.md`

**Interfaces:**
- Consumes: IDs from `evals/cases.yaml` and filenames under
  `tests/fixtures/baseline` and `tests/fixtures/forward`.
- Produces: a score table whose row IDs equal the intersection of complete
  baseline/forward fixture pairs and prose that reports derived counts.

- [ ] **Step 1: Add a filesystem-derived documentation contract**

Add imports `re` and `Path` only if absent, then add:

```python
def test_eval_readme_distinguishes_catalog_from_scored_fixture_pairs():
    case_ids = {
        case["id"]
        for case in yaml.safe_load(
            (ROOT / "evals/cases.yaml").read_text(encoding="utf-8")
        )["cases"]
    }
    baseline_ids = {
        path.stem for path in (ROOT / "tests/fixtures/baseline").glob("*.md")
    }
    forward_ids = {
        path.stem for path in (ROOT / "tests/fixtures/forward").glob("*.md")
    }
    paired_ids = baseline_ids & forward_ids
    readme = (ROOT / "evals/README.md").read_text(encoding="utf-8")
    table_ids = set(
        re.findall(r"^\| `([^`]+)` \|", readme, flags=re.MULTILINE)
    )

    assert f"{len(case_ids)} catalog cases" in readme
    assert f"{len(paired_ids)} scored fixture pairs" in readme
    assert paired_ids <= case_ids
    assert table_ids == paired_ids
    assert "not proof of semantic correctness or clinical validity" in readme
```

- [ ] **Step 2: Run the contract and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_eval_contract.py::test_eval_readme_distinguishes_catalog_from_scored_fixture_pairs -q
```

Expected: FAIL because the current README does not state the two derived
counts.

- [ ] **Step 3: Clarify catalog and scored-fixture scope**

Change the opening of `evals/README.md` to:

```markdown
# Offline Eval Results

`cases.yaml` defines 11 catalog cases. The table below covers only the 3 scored
fixture pairs that currently have both a checked-in baseline response and a
checked-in forward response.
```

Keep the three existing score rows unchanged. Replace the final note with:

```markdown
Scores are deterministic outputs of `scripts/evaluate_response.py` using the
catalog and rubric in this directory. They are regression evidence for the
three checked-in response pairs, not proof of semantic correctness or clinical
validity and not complete coverage of all 11 catalog cases.
```

- [ ] **Step 4: Run focused and full Eval tests**

Run:

```powershell
python -m pytest tests/test_eval_contract.py tests/test_response_evaluator.py -q
```

Expected: all selected tests pass and the existing score values remain
unchanged.

- [ ] **Step 5: Commit the Eval disclosure**

```powershell
git add -- evals/README.md tests/test_eval_contract.py
git commit -m "docs: clarify Eval evidence coverage"
```

---

### Task 7: Add a bilingual 60-second first-success path

**Files:**
- Modify: `tests/test_project_metadata.py`
- Modify: `README.md`
- Modify: `README.zh-TW.md`

**Interfaces:**
- Consumes: current `npx skills` CLI commands and the existing installed Skill
  identifier.
- Produces: aligned prerequisite, install, discovery, invocation, update, and
  first-response expectation sections.

- [ ] **Step 1: Add bilingual onboarding contracts**

Add:

```python
def test_readmes_define_prerequisites_command_boundaries_and_first_success():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    for text in (english, traditional_chinese):
        for command in (
            "node --version",
            "npm --version",
            "npx skills add mtchuang1981/clin-data-nav",
            "npx skills update clinical-data-research-navigator --project --yes",
            "/skills",
            "$clinical-data-research-navigator",
        ):
            assert command in text
        assert ".agents/skills" in text

    assert "## Quick start prerequisites" in english
    assert "## 60-second first success" in english
    assert "not terminal commands" in english
    assert "question clarification" in english
    assert "missing-information list" in english

    assert "## 快速開始的必要條件" in traditional_chinese
    assert "## 60 秒完成第一次使用" in traditional_chinese
    assert "不是終端機指令" in traditional_chinese
    assert "問題釐清" in traditional_chinese
    assert "缺少資訊清單" in traditional_chinese
```

- [ ] **Step 2: Run the contract and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_project_metadata.py::test_readmes_define_prerequisites_command_boundaries_and_first_success -q
```

Expected: FAIL at the first missing prerequisite heading.

- [ ] **Step 3: Add the English prerequisite and command-boundary text**

Insert before `## Quick start` in `README.md`:

````markdown
## Quick start prerequisites

The npx installation path requires Node.js with npm/npx and a Codex interface
that supports Skills. In a terminal, confirm that both commands work:

```bash
node --version
npm --version
```

No Python installation is required to use the installed Skill. Python 3.11 is
only a contributor dependency described later in this README.
````

After the existing add command, make the command boundary explicit:

````markdown
`npx skills add mtchuang1981/clin-data-nav` is a terminal command and installs
the Skill for the current project under `.agents/skills`. `/skills` and
`$clinical-data-research-navigator` are entered in Codex; they are not terminal
commands. Run `/skills` to confirm discovery, then invoke the Skill explicitly.

To update this project-local installation later, run in the terminal:

```bash
npx skills update clinical-data-research-navigator --project --yes
```
````

- [ ] **Step 4: Add the English first-success section**

Insert immediately after quick start:

````markdown
## 60-second first success

1. Run `/skills` in Codex and confirm that **Clinical Data Research
   Navigator** appears.
2. Enter this minimal request in Codex:

   ```text
   $clinical-data-research-navigator Help me frame a descriptive study of
   health-care utilisation using synthetic real-world data. Do not invent a
   schema or codes.
   ```

3. Expect question clarification, source and schema boundaries, a recommended
   workflow, and a missing-information list. With incomplete inputs, expect a
   specification and validation gaps—not production SQL, a complete SAP, or a
   causal conclusion.
````

- [ ] **Step 5: Add aligned Traditional Chinese content**

Insert before `## 快速開始` in `README.zh-TW.md`:

````markdown
## 快速開始的必要條件

使用 npx 安裝需要 Node.js 與 npm/npx，也需要支援 Skills 的 Codex
介面。請先在終端機確認下列指令可執行：

```bash
node --version
npm --version
```

使用已安裝的 Skill 不需要 Python。Python 3.11 只供後文所述的專案貢獻者
執行測試與發布工具。
````

After the add command, add:

````markdown
`npx skills add mtchuang1981/clin-data-nav` 是終端機指令，預設會把 Skill
安裝到目前專案的 `.agents/skills`。`/skills` 與
`$clinical-data-research-navigator` 要輸入在 Codex 對話中，不是終端機指令。
先用 `/skills` 確認 Codex 已找到 Skill，再明確叫用它。

日後若要更新此專案內的安裝，請在終端機執行：

```bash
npx skills update clinical-data-research-navigator --project --yes
```
````

Insert immediately after quick start:

````markdown
## 60 秒完成第一次使用

1. 在 Codex 輸入 `/skills`，確認清單中出現 **Clinical Data Research
   Navigator**。
2. 在 Codex 輸入這個最小範例：

   ```text
   $clinical-data-research-navigator 請協助我規劃使用合成真實世界資料的
   醫療利用描述性研究；不要自行猜測 schema 或代碼。
   ```

3. 預期第一份回覆會包含問題釐清、來源與 schema 界線、建議工作流程及
   缺少資訊清單。輸入不完整時，應得到規格與驗證缺口，而不是可上線 SQL、
   完整 SAP 或因果結論。
````

- [ ] **Step 6: Run both README contract groups**

Run:

```powershell
python -m pytest tests/test_project_metadata.py -k "readmes" -q
```

Expected: every existing and new bilingual README contract passes.

- [ ] **Step 7: Commit the onboarding repair**

```powershell
git add -- README.md README.zh-TW.md tests/test_project_metadata.py
git commit -m "docs: add first-success onboarding"
```

---

### Task 8: Remove unrelated local-tool configuration

**Files:**
- Modify: `tests/test_repository_policy.py`
- Delete: `.baoyu-skills/baoyu-translate/EXTEND.md`

**Interfaces:**
- Consumes: the tracked repository tree.
- Produces: a policy assertion that `.baoyu-skills` is not part of the public
  project.

- [ ] **Step 1: Add the failing repository-policy test**

Add:

```python
def test_repository_excludes_unrelated_local_tool_configuration():
    assert not (ROOT / ".baoyu-skills").exists()
```

- [ ] **Step 2: Run the test and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_repository_policy.py::test_repository_excludes_unrelated_local_tool_configuration -q
```

Expected: FAIL because `.baoyu-skills` exists.

- [ ] **Step 3: Remove only the approved unrelated file**

Resolve and verify that
`.baoyu-skills/baoyu-translate/EXTEND.md` is inside the isolated worktree, then
delete that tracked file. Remove its now-empty parent directories. Do not
delete any `.agents`, `.codex`, or user-home configuration.

- [ ] **Step 4: Run the policy test and public boundary**

Run:

```powershell
python -m pytest tests/test_repository_policy.py -q
python scripts/check_public_boundary.py
```

Expected: all policy tests pass and the boundary scanner exits zero.

- [ ] **Step 5: Commit the cleanup**

```powershell
git add -A -- .baoyu-skills tests/test_repository_policy.py
git commit -m "chore: remove unrelated translation config"
```

---

### Task 9: Synchronize `v0.2.2` metadata and release notes

**Files:**
- Modify: `tests/test_project_metadata.py`
- Modify: `tests/test_packaging.py`
- Modify: `pyproject.toml`
- Modify: `CITATION.cff`
- Modify: `scripts/package_skill.py`
- Modify: `scripts/install_local.py`
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `CHANGELOG.md`
- Modify: `CHANGELOG.zh-TW.md`
- Create: `docs/releases/0.2.2.md`

**Interfaces:**
- Consumes: all current version constants and examples.
- Produces: synchronized current version `0.2.2`, proposed tag `v0.2.2`, and
  notes path consumed by `.github/workflows/release.yml`.

- [ ] **Step 1: Change tests to require the new current version**

In `tests/test_project_metadata.py`, change current-version assertions to:

```python
assert citation["version"] == "0.2.2"
assert project["project"]["version"] == "0.2.2"
assert citation["version"] == "0.2.2"
assert PACKAGER_VERSION == "0.2.2"
assert INSTALLER_VERSION == "0.2.2"
assert "## 0.2.2 - 2026-07-29" in changelog
assert "## 0.2.2 - 2026-07-29" in changelog_zh_tw
```

Change the current README release assertion from `v0.2.1` to `v0.2.2`.

In `tests/test_packaging.py`, rename the test to
`test_v022_package_and_manifest_names_match_release_version` and require:

```python
assert result.archive.name == "clinical-data-research-navigator-0.2.2.zip"
assert (
    result.manifest.name
    == "clinical-data-research-navigator-0.2.2.manifest.json"
)
assert manifest["version"] == "0.2.2"
```

- [ ] **Step 2: Run version contracts and verify the intended red state**

Run:

```powershell
python -m pytest tests/test_project_metadata.py::test_release_version_is_synchronized tests/test_packaging.py::test_v022_package_and_manifest_names_match_release_version -q
```

Expected: both tests FAIL because production metadata is still `0.2.1`.

- [ ] **Step 3: Update every current version surface**

Change to `0.2.2` in:

- `pyproject.toml` project version;
- `CITATION.cff` version;
- `scripts/package_skill.py` `PACKAGE_VERSION`;
- `scripts/install_local.py` `PACKAGE_VERSION`;
- current Release examples and archive names in both READMEs.

Run:

```powershell
rg -n "0\.2\.1|v0\.2\.1" --glob "!docs/superpowers/**" --glob "!docs/verification/**" .
```

Expected: remaining matches occur only in historical changelog sections. A
current installation command, test assertion, constant, or citation match is a
failure.

- [ ] **Step 4: Add bilingual changelog entries**

Prepend to `CHANGELOG.md`:

```markdown
## 0.2.2 - 2026-07-29

### Fixed

- Make fresh Python 3.11 editable installation deterministic by declaring the
  setuptools package boundary.
- Make atomic installer platform tests portable across Windows and POSIX hosts
  without adding an overwrite fallback.
- Run the complete validation set on Ubuntu and Windows and add a fail-closed,
  manually dispatched GitHub Release workflow.

### Documentation

- Add prerequisites, terminal-versus-Codex command boundaries, an update
  command, and a 60-second first-success path in both READMEs.
- Distinguish the 11-case Eval catalog from the three scored fixture pairs.
```

Prepend the aligned entry to `CHANGELOG.zh-TW.md`:

```markdown
## 0.2.2 - 2026-07-29

### 修正

- 明確宣告 setuptools 套件界線，讓全新的 Python 3.11 環境可穩定執行
  editable install。
- 讓原子安裝的平台測試可在 Windows 與 POSIX 主機穩定執行，且不加入可能
  覆寫既有安裝的 fallback。
- 在 Ubuntu 與 Windows 執行完整驗證，並加入遇到不一致就停止、需手動觸發
  的 GitHub Release workflow。

### 文件

- 在雙語 README 加入必要條件、終端機與 Codex 指令界線、更新指令及 60 秒
  第一次成功流程。
- 清楚區分 11 個 Eval 案例目錄與 3 組已評分 fixture。
```

- [ ] **Step 5: Create the exact Release notes consumed by the workflow**

Create `docs/releases/0.2.2.md`:

````markdown
# Clinical Data Research Navigator v0.2.2

This patch repairs the public installation, validation, and release trust
boundary without changing the Skill's clinical source-authority rules.

## Highlights

- Fresh Python 3.11 contributors can install `.[dev]` through the declared
  setuptools package boundary.
- Ubuntu and Windows both run the complete test suite, Skill validator, public
  boundary scan, and reproducible-package check.
- A manually dispatched Release workflow rejects lightweight, version-mismatched,
  non-main, non-reproducible, or already-published releases.
- Both READMEs now include npx prerequisites, terminal-versus-Codex command
  guidance, an update command, and a 60-second first-success path.
- Eval documentation now distinguishes 11 catalog cases from the three scored
  fixture pairs.

## 安裝與驗證信任修復

- 全新的 Python 3.11 貢獻環境可透過明確的 setuptools 套件界線安裝
  `.[dev]`。
- Ubuntu 與 Windows 都會執行完整測試、Skill 驗證、公開邊界掃描及可重現
  封裝檢查。
- 手動觸發的 Release workflow 會拒絕輕量 tag、版本不符、無法由 main
  追溯、不可重現或已發布的版本。
- 雙語 README 已補上 npx 必要條件、終端機與 Codex 指令界線、更新指令及
  60 秒第一次成功流程。
- Eval 文件已區分 11 個案例目錄與 3 組已評分 fixture。

Install for the current project:

```bash
npx skills add mtchuang1981/clin-data-nav
```

The attached manifest records the ZIP SHA-256 and every packaged file hash.
````

- [ ] **Step 6: Run version, packaging, and README contracts**

Run:

```powershell
python -m pytest tests/test_project_metadata.py tests/test_packaging.py -q
python scripts/package_skill.py --check-reproducible
```

Expected: all selected tests pass and the reproducibility check exits zero.

- [ ] **Step 7: Commit version preparation**

```powershell
git add -- pyproject.toml CITATION.cff scripts/package_skill.py scripts/install_local.py README.md README.zh-TW.md CHANGELOG.md CHANGELOG.zh-TW.md docs/releases/0.2.2.md tests/test_project_metadata.py tests/test_packaging.py
git commit -m "chore: prepare v0.2.2 release metadata"
```

---

### Task 10: Prove Windows/Linux acceptance and write the revalidation record

**Files:**
- Create: `docs/verification/2026-07-29-v0.2.1-assessment.md`

**Interfaces:**
- Consumes: the complete isolated-worktree state and command output from native
  Windows and a clean Linux Python 3.11 container.
- Produces: exact local evidence, a confirmed/fixed/open/deferred assessment
  table, and a clean candidate commit.

- [ ] **Step 1: Review scope before claiming success**

Run:

```powershell
git status --short
git diff 6150412...HEAD --stat
git diff 6150412...HEAD -- . ":!docs/superpowers/plans/2026-07-29-public-trust-repair.md"
```

Expected: only approved P0 files changed; no private material, generated
`.agents`, `skills-lock.json`, local virtual environment, or `dist` artifact is
tracked.

- [ ] **Step 2: Run the native Windows four-command set**

Run:

```powershell
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Expected: pytest reports more than 168 passed with zero failures/skips caused
by this plan, and every command exits zero.

- [ ] **Step 3: Prove a clean Windows editable install**

Create a new GUID-named virtual environment under the Windows temporary
directory and run:

```powershell
$freshVenv = Join-Path ([System.IO.Path]::GetTempPath()) ("clin-data-nav-acceptance-" + [guid]::NewGuid())
py -3.11 -m venv $freshVenv
& "$freshVenv\Scripts\python.exe" -m pip install --upgrade pip
& "$freshVenv\Scripts\python.exe" -m pip install -e ".[dev]"
& "$freshVenv\Scripts\python.exe" -m pytest -q
& "$freshVenv\Scripts\python.exe" scripts/validate_skill.py
& "$freshVenv\Scripts\python.exe" scripts/check_public_boundary.py
& "$freshVenv\Scripts\python.exe" scripts/package_skill.py --check-reproducible
```

Expected: installation and all four commands exit zero. Resolve the exact
temporary path, verify its parent is the Windows temporary directory, then
remove only that disposable virtual environment:

```powershell
$resolvedFreshVenv = (Resolve-Path -LiteralPath $freshVenv).Path
$temporaryRoot = [System.IO.Path]::GetTempPath().TrimEnd('\')
if ((Split-Path -Parent $resolvedFreshVenv) -ne $temporaryRoot) {
    throw "Refusing to remove a virtual environment outside the temporary root"
}
Remove-Item -LiteralPath $resolvedFreshVenv -Recurse -Force
```

- [ ] **Step 4: Run the clean Linux Python 3.11 matrix**

From PowerShell with Docker Desktop:

```powershell
docker run --rm --volume "${PWD}:/workspace" --workdir /workspace python:3.11-slim sh -lc "python -m pip install --upgrade pip && python -m pip install -e '.[dev]' && python -m pytest -q && python scripts/validate_skill.py && python scripts/check_public_boundary.py && python scripts/package_skill.py --check-reproducible"
```

Expected: editable installation succeeds; pytest reports the same collected
and passed count as native Windows; all four commands exit zero.

- [ ] **Step 5: Independently build and verify public assets**

Run:

```powershell
python scripts/package_skill.py --output-dir dist
python scripts/verify_release.py artifacts --archive dist/clinical-data-research-navigator-0.2.2.zip --manifest dist/clinical-data-research-navigator-0.2.2.manifest.json
$archiveHash = (Get-FileHash dist/clinical-data-research-navigator-0.2.2.zip -Algorithm SHA256).Hash.ToLowerInvariant()
$releaseManifest = Get-Content dist/clinical-data-research-navigator-0.2.2.manifest.json -Raw | ConvertFrom-Json
if ($archiveHash -ne $releaseManifest.archive_sha256) { throw "SHA-256 mismatch" }
$archiveHash
$releaseManifest.files.Count
```

Expected: verifier exits zero and PowerShell's lowercase-normalized ZIP hash
equals `archive_sha256` in the manifest. `dist` remains ignored and is not
committed.

- [ ] **Step 6: Write the dated revalidation report**

Create `docs/verification/2026-07-29-v0.2.1-assessment.md` with:

- baseline commit/tag and the failing GitHub Actions run URL;
- a table for editable install, Windows platform tests, Linux/Windows CI,
  four gates, Release gate, README onboarding, Eval scope, unrelated config,
  and version synchronization;
- status values limited to `Confirmed and fixed`, `Confirmed; external
  verification pending`, `Deferred to v0.3.0`, and `Remaining P2`;
- exact native Windows and Linux command summaries from Steps 2–4;
- ZIP filename, exact SHA-256, manifest verification result, and public-file
  count from Step 5;
- branch protection, GitHub topics, richer `CITATION.cff` author identity, and
  optional Skill icon/color as P2 or external settings rather than completed
  claims;
- the four output depths, broader glossary/navigation, and additional scored
  Eval fixtures as the next `v0.3.0` design scope;
- no claim that GitHub Actions is green until Task 11 proves it.

Preserve `docs/verification/2026-07-27-v0.1.0.md` unchanged.

- [ ] **Step 7: Run the complete local acceptance set again**

Run:

```powershell
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
git diff --check
git status --short
```

Expected: all verification commands exit zero; only the new report is
uncommitted.

- [ ] **Step 8: Commit the evidence record**

```powershell
git add -- docs/verification/2026-07-29-v0.2.1-assessment.md
git commit -m "docs: record v0.2.1 remediation evidence"
```

- [ ] **Step 9: Verify the local candidate is clean**

Run:

```powershell
git status --short
git log --oneline --decorate 6150412..HEAD
```

Expected: clean working tree and one reviewed commit per task.

---

### Task 11: Approval-gated GitHub validation

**Files:**
- Modify only if remote CI exposes a real defect; any fix must repeat its
  focused red-green cycle and local acceptance checks before another push.

**Interfaces:**
- Consumes: clean, locally verified candidate commits.
- Produces: authoritative Ubuntu and Windows GitHub Actions results for the
  exact remote `main` commit.

- [ ] **Step 1: Stop and obtain explicit push approval**

Report the commit list, native Windows result, clean Linux result, ZIP
SHA-256, and remaining external/P2 items. Do not infer approval from design or
implementation approval.

- [ ] **Step 2: Push only after explicit approval**

Run:

```powershell
git push origin main
```

Do not push a tag.

- [ ] **Step 3: Monitor validation for the exact commit**

Run:

```powershell
$candidateCommit = git rev-parse HEAD
gh run list --workflow validate.yml --commit $candidateCommit
```

Watch the matching run to completion with `gh run watch`. Expected: both
`ubuntu-latest` and `windows-latest` jobs succeed and none of the four
verification steps is skipped.

- [ ] **Step 4: Confirm GitHub registered both workflows**

Run:

```powershell
gh workflow view validate.yml
gh workflow view release.yml
```

Expected: both workflows are recognized. Do not dispatch `release.yml`.

- [ ] **Step 5: Read branch-protection state without changing it**

Run:

```powershell
gh api repos/mtchuang1981/clin-data-nav/branches/main/protection
```

Record whether required checks include both validation matrix jobs. If the API
is unavailable or protection is not configured, report it as an external
setting; do not mutate it.

- [ ] **Step 6: Update evidence only with proven remote results**

Update `docs/verification/2026-07-29-v0.2.1-assessment.md` with the exact
GitHub Actions run URL, commit, job conclusions, and branch-protection
observation. Run the four local commands again, commit the report update, push
that documentation commit only with explicit approval, and confirm its own
validation run is green.

- [ ] **Step 7: Stop at the publication boundary**

Hand off:

- exact remote `main` commit and green workflow URL;
- complete Windows/Linux test and gate results;
- ZIP and manifest names plus SHA-256;
- proposed `v0.2.2` Release notes;
- annotated tag command and manual Release workflow input;
- remaining P1/P2 list.

Do not create or push `v0.2.2`, dispatch the Release workflow, or create a
GitHub Release until the user separately approves those publication actions.
