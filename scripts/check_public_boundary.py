"""Check a repository for files that do not belong in the public core."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    detail: str


class TrackedPathQueryError(RuntimeError):
    """Git tracked paths could not be enumerated."""


PRIVATE_NAMES = {
    "tmucrd-v2.16-dictionary.txt",
    "tmucrd-v2.16-guide.md",
}
PRIVATE_PARTS = ("codingbook", "codebook", "dictionary.txt")
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|token|password)\b\s*[:=]\s*['\"][^'\"]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".toml"}
DATA_SUFFIXES = {
    ".arrow",
    ".csv",
    ".db",
    ".dta",
    ".feather",
    ".parquet",
    ".rdata",
    ".rds",
    ".sas7bdat",
    ".sav",
    ".sqlite",
    ".tsv",
    ".xls",
    ".xlsx",
    ".xpt",
}
DATA_ARTIFACT_ALLOWLIST: set[str] = set()
SKIP_DIRECTORIES = {".git", ".pytest_cache", "__pycache__", "dist"}
SDD_SCRATCH_DIRECTORY = Path(".superpowers/sdd")
UNRELATED_LOCAL_TOOL_DIRECTORY = ".baoyu-skills"
LARGE_TEXT_ALLOWLIST = {
    "skills/clinical-data-research-navigator/references/tmucrd-public-profile.md"
}
SYNTHETIC_EVAL_FIXTURES = {
    "tests/fixtures/baseline/stale-codingbook.md",
    "tests/fixtures/forward/stale-codingbook.md",
}


def _tracked_paths(root: Path) -> set[str] | None:
    if not (root / ".git").exists():
        return None
    try:
        repository = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if repository.returncode != 0 or repository.stdout.strip() != b"true":
            return None
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
        )
    except OSError as error:
        raise TrackedPathQueryError from error
    if result.returncode != 0:
        raise TrackedPathQueryError
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }


def _is_sdd_scratch_path(relative_path: Path) -> bool:
    return (
        relative_path == SDD_SCRATCH_DIRECTORY
        or SDD_SCRATCH_DIRECTORY in relative_path.parents
    )


def scan_repository(root: Path, max_text_bytes: int = 200_000) -> list[Finding]:
    """Return deterministic public-boundary findings below *root*."""
    findings: list[Finding] = []
    root = root.resolve()
    try:
        tracked_paths = _tracked_paths(root)
    except TrackedPathQueryError:
        return [
            Finding(
                ".",
                "tracked-path-query-failed",
                "Git tracked paths could not be verified",
            )
        ]

    if tracked_paths is not None:
        for relative_path in tracked_paths:
            if (
                relative_path == UNRELATED_LOCAL_TOOL_DIRECTORY
                or relative_path.startswith(f"{UNRELATED_LOCAL_TOOL_DIRECTORY}/")
            ):
                findings.append(
                    Finding(
                        relative_path,
                        "unrelated-local-tool-configuration",
                        "local tool configuration is not permitted in the public project",
                    )
                )

    for directory, child_directories, filenames in os.walk(root):
        directory_path = Path(directory)
        child_directories[:] = sorted(
            name
            for name in child_directories
            if name not in SKIP_DIRECTORIES
        )
        for filename in sorted(filenames):
            path = directory_path / filename
            relative = path.relative_to(root)
            relative_path = relative.as_posix()
            if (
                _is_sdd_scratch_path(relative)
                and tracked_paths is not None
                and relative_path not in tracked_paths
            ):
                continue
            lowercase_name = filename.lower()

            if lowercase_name == ".env" or lowercase_name.startswith(".env."):
                findings.append(
                    Finding(
                        relative_path,
                        "environment-file",
                        "environment files are not permitted",
                    )
                )
                continue

            has_private_name = lowercase_name in PRIVATE_NAMES or any(
                part in lowercase_name for part in PRIVATE_PARTS
            )
            if has_private_name and relative_path not in SYNTHETIC_EVAL_FIXTURES:
                findings.append(
                    Finding(
                        relative_path,
                        "private-filename",
                        "filename matches a private-material pattern",
                    )
                )

            if path.suffix.lower() == ".pdf":
                findings.append(
                    Finding(relative_path, "pdf-file", "PDF files are not permitted"))
                continue

            if (
                path.suffix.lower() in DATA_SUFFIXES
                and relative_path not in DATA_ARTIFACT_ALLOWLIST
            ):
                findings.append(
                    Finding(
                        relative_path,
                        "data-artifact",
                        "data artifacts require an explicit public allowlist entry",
                    )
                )
                continue

            if path.suffix.lower() not in TEXT_SUFFIXES:
                continue

            if (
                path.stat().st_size > max_text_bytes
                and relative_path not in LARGE_TEXT_ALLOWLIST
            ):
                findings.append(
                    Finding(
                        relative_path,
                        "large-text-file",
                        f"text file exceeds the {max_text_bytes}-byte limit",
                    )
                )

            text = path.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                findings.append(
                    Finding(
                        relative_path,
                        "possible-secret",
                        "text matches a credential pattern",
                    )
                )

    return sorted(findings, key=lambda finding: (finding.path, finding.rule))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    args = parser.parse_args(argv)

    findings = scan_repository(args.root)
    for finding in findings:
        print(f"{finding.path}: {finding.rule}: {finding.detail}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
