"""Fail-closed checks used before publishing a GitHub Release."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
import sys
import tomllib
from zipfile import BadZipFile, ZipFile


TAG_PATTERN = re.compile(
    r"^v(?P<version>(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))$"
)
SKILL_NAME = "clinical-data-research-navigator"
GIT_REPOSITORY_OVERRIDES = frozenset(
    {
        "GIT_DIR",
        "GIT_COMMON_DIR",
        "GIT_WORK_TREE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_GRAFT_FILE",
        "GIT_SHALLOW_FILE",
        "GIT_REPLACE_REF_BASE",
        "GIT_NAMESPACE",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    }
)


class ReleaseVerificationError(ValueError):
    """A release precondition was not satisfied."""


@dataclass(frozen=True)
class ReleaseRef:
    tag: str
    version: str
    commit: str


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        bool(name)
        and "\\" not in name
        and re.match(r"^[A-Za-z]:", name) is None
        and path != PurePosixPath(".")
        and not path.is_absolute()
        and ".." not in path.parts
        and name == path.as_posix()
    )


def verify_release_artifacts(archive: Path, manifest: Path) -> None:
    try:
        _verify_release_artifacts(archive, manifest)
    except ReleaseVerificationError:
        raise
    except (
        OSError,
        UnicodeError,
        json.JSONDecodeError,
        BadZipFile,
        NotImplementedError,
        RuntimeError,
        ValueError,
    ) as error:
        raise ReleaseVerificationError(
            "artifact verification could not be completed safely"
        ) from error


def _verify_release_artifacts(archive: Path, manifest: Path) -> None:
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
        r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)",
        version,
    ) is None:
        raise ReleaseVerificationError("manifest version is invalid")
    expected_archive = f"{SKILL_NAME}-{version}.zip"
    expected_manifest = f"{SKILL_NAME}-{version}.manifest.json"
    if archive.name != expected_archive or data["archive"] != expected_archive:
        raise ReleaseVerificationError("archive name does not match manifest version")
    if manifest.name != expected_manifest:
        raise ReleaseVerificationError("manifest filename does not match version")

    try:
        archive_bytes = archive.read_bytes()
    except OSError as error:
        raise ReleaseVerificationError("archive must be a readable ZIP") from error
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


def _git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess:
    environment = {
        name: value
        for name, value in os.environ.items()
        if name not in GIT_REPOSITORY_OVERRIDES
    }
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
        env=environment,
    )


def verify_release_ref(
    root: Path,
    tag: str,
    main_ref: str = "origin/main",
) -> ReleaseRef:
    try:
        return _verify_release_ref(root, tag, main_ref)
    except ReleaseVerificationError:
        raise
    except (
        OSError,
        KeyError,
        TypeError,
        UnicodeError,
        subprocess.CalledProcessError,
        tomllib.TOMLDecodeError,
    ) as error:
        raise ReleaseVerificationError(
            "release verification could not be completed safely"
        ) from error


def _verify_release_ref(
    root: Path,
    tag: str,
    main_ref: str,
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


if __name__ == "__main__":
    raise SystemExit(main())
