"""Fail-closed checks used before publishing a GitHub Release."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
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
    environment = {
        name: value for name, value in os.environ.items() if not name.startswith("GIT_")
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
