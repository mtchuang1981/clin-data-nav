"""Check a repository for files that do not belong in the public core."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import re


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    detail: str


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
SKIP_DIRECTORIES = {".git", ".pytest_cache", ".superpowers", "__pycache__", "dist"}
LARGE_TEXT_ALLOWLIST = {
    "skills/clinical-data-research-navigator/references/tmucrd-public-profile.md"
}
SYNTHETIC_EVAL_FIXTURES = {
    "tests/fixtures/baseline/stale-codingbook.md",
    "tests/fixtures/forward/stale-codingbook.md",
}


def scan_repository(root: Path, max_text_bytes: int = 200_000) -> list[Finding]:
    """Return deterministic public-boundary findings below *root*."""
    findings: list[Finding] = []
    root = root.resolve()

    for directory, child_directories, filenames in os.walk(root):
        child_directories[:] = sorted(
            name for name in child_directories if name not in SKIP_DIRECTORIES
        )
        directory_path = Path(directory)
        for filename in sorted(filenames):
            path = directory_path / filename
            relative_path = path.relative_to(root).as_posix()
            lowercase_name = filename.lower()

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
