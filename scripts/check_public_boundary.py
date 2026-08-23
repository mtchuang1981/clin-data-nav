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


class TrackedPathQueryError(RuntimeError):
    """Git tracked paths could not be enumerated."""


PRIVATE_NAMES = {
    "tmucrd-v2.16-dictionary.txt",
    "tmucrd-v2.16-guide.md",
}
PRIVATE_PARTS = ("codingbook", "codebook", "dictionary.txt")
PRIVATE_STUDY_ROOTS = {
    Path("study-data"),
    Path("study-governance"),
}
PRIVATE_EFFECTIVENESS_PARTS = {"raw", "private", "participant-data"}
PUBLIC_RECOVERY_FILES = {
    "evals/effectiveness/recovery/README.md",
    "evals/effectiveness/recovery/checklist.md",
    "evals/effectiveness/recovery/checklist.zh-TW.md",
    "evals/effectiveness/recovery/recovery-template.json",
    "evals/effectiveness/recovery/examples/synthetic-recovery.json",
}
PUBLIC_BENCHMARK_FILES = {
    ".github/ISSUE_TEMPLATE/benchmark-result.yml",
    ".github/ISSUE_TEMPLATE/usability-feedback.yml",
    "evals/benchmark/README.md",
    "evals/benchmark/benchmark-plan-template.json",
    "evals/benchmark/released-skill-bindings.json",
    "evals/benchmark/report-template.md",
    "evals/benchmark/report-template.zh-TW.md",
    "evals/benchmark/response-index-template.json",
    "evals/benchmark/summary-schema.md",
    "evals/benchmark/examples/synthetic-report.md",
    "evals/benchmark/examples/synthetic-report.zh-TW.md",
    "evals/benchmark/examples/synthetic-summary.json",
}
BENCHMARK_ROOT = Path("evals/benchmark")
PUBLIC_BENCHMARK_DIRECTORIES = {
    BENCHMARK_ROOT,
    BENCHMARK_ROOT / "examples",
}
PRIVATE_BENCHMARK_PARTS = {
    "accesstoken",
    "accesstokens",
    "apikey",
    "apikeys",
    "credential",
    "credentials",
    "humanstudy",
    "institutionalschema",
    "output",
    "outputs",
    "participant",
    "participantdata",
    "participants",
    "patientdata",
    "rawresponse",
    "rawresponses",
    "result",
    "results",
    "run",
    "runs",
    "taskpack",
    "taskpacks",
    "token",
    "tokens",
}
PRIVATE_BENCHMARK_BASENAMES = {
    "index",
    "indexes",
    "output",
    "outputs",
    "plan",
    "plans",
    "result",
    "results",
    "run",
    "runs",
}
PRIVATE_BENCHMARK_ARTIFACT_NAME = re.compile(
    r"(?i)^(?:"
    r"benchmark[-_. ]?(?:plans?|reports?|results?|summar(?:y|ies)|runs?|outputs?|index(?:es)?)|"
    r"response[-_. ]?(?:bundles?|index(?:es)?|outputs?)|"
    r"raw[-_. ]?responses?|"
    r"provider[-_. ]?logs?|"
    r"api[-_. ]?keys?|"
    r"access[-_. ]?tokens?|"
    r"tokens?|"
    r"credentials?|"
    r"private[-_. ]?tasks?|"
    r"task[-_. ]?packs?|"
    r"human[-_. ]?study|"
    r"participants?(?:[-_. ]?(?:data|inputs?|answers?|scores?))?|"
    r"patient[-_. ]?data|"
    r"institutional[-_. ]?schema"
    r")(?:[-_. ].*)?$"
)
PRIVATE_RECOVERY_ARTIFACT_NAME = re.compile(
    r"(?i)^(?:"
    r"recovery[-_]?records?|"
    r"incident|"
    r"condition[-_]?keys?|"
    r"human[-_](?:inputs?|answers?|scores?|task[-_]?packs?)|"
    r"participant[-_](?:inputs?|answers?|scores?)|"
    r"study[-_]?manifest|"
    r"nonces?|"
    r"assignments?"
    r")(?:[-_.].*)?$"
)
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
SKIP_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "dist",
}
SDD_SCRATCH_DIRECTORY = Path(".superpowers/sdd")
UNRELATED_LOCAL_TOOL_DIRECTORY = ".baoyu-skills"
LARGE_TEXT_ALLOWLIST = {
    "skills/clin-nav/references/tmucrd-public-profile.md"
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
            raise TrackedPathQueryError
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


def _is_private_study_path(relative_path: Path) -> bool:
    if any(
        relative_path == root or root in relative_path.parents
        for root in PRIVATE_STUDY_ROOTS
    ):
        return True
    effectiveness = Path("evals/effectiveness")
    if effectiveness not in relative_path.parents:
        return False
    remainder = relative_path.relative_to(effectiveness)
    return bool(remainder.parts) and remainder.parts[0] in PRIVATE_EFFECTIVENESS_PARTS


def _is_private_recovery_path(relative_path: Path) -> bool:
    if relative_path.as_posix() in PUBLIC_RECOVERY_FILES:
        return False
    recovery = Path("evals/effectiveness/recovery")
    return recovery in relative_path.parents or bool(
        PRIVATE_RECOVERY_ARTIFACT_NAME.fullmatch(relative_path.name)
    )


def _is_private_benchmark_path(relative_path: Path) -> bool:
    if relative_path.as_posix() in PUBLIC_BENCHMARK_FILES:
        return False
    if relative_path == BENCHMARK_ROOT or BENCHMARK_ROOT in relative_path.parents:
        return relative_path not in PUBLIC_BENCHMARK_DIRECTORIES
    lowercase_parts = tuple(part.casefold() for part in relative_path.parts)
    normalized_parts = tuple(
        re.sub(r"[-_. ]+", "", part) for part in lowercase_parts
    )
    normalized_stem = re.sub(
        r"[-_. ]+", "", relative_path.stem.casefold()
    )
    return (
        any(part in PRIVATE_BENCHMARK_PARTS for part in normalized_parts)
        or normalized_stem in PRIVATE_BENCHMARK_BASENAMES
        or bool(PRIVATE_BENCHMARK_ARTIFACT_NAME.fullmatch(relative_path.name))
    )


def _is_private_benchmark_directory_path(relative_path: Path) -> bool:
    if relative_path == BENCHMARK_ROOT or BENCHMARK_ROOT in relative_path.parents:
        return relative_path not in PUBLIC_BENCHMARK_DIRECTORIES
    normalized_parts = tuple(
        re.sub(r"[-_. ]+", "", part.casefold()) for part in relative_path.parts
    )
    return any(part in PRIVATE_BENCHMARK_PARTS for part in normalized_parts)


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
                    )
                )

    for directory, child_directories, filenames in os.walk(root):
        directory_path = Path(directory)
        retained_directories = []
        for name in sorted(child_directories):
            if name in SKIP_DIRECTORIES or (
                directory_path == root and name == ".worktrees"
            ):
                continue
            child_relative = (directory_path / name).relative_to(root)
            if _is_private_study_path(child_relative):
                retained_directories.append(name)
                continue
            if _is_private_recovery_path(child_relative):
                if BENCHMARK_ROOT in child_relative.parents:
                    findings.append(
                        Finding(
                            child_relative.as_posix(),
                            "private-recovery-artifact",
                        )
                    )
                    continue
                retained_directories.append(name)
                continue
            if _is_private_benchmark_directory_path(child_relative):
                findings.append(
                    Finding(
                        child_relative.as_posix(),
                        "private-benchmark-artifact",
                    )
                )
                continue
            retained_directories.append(name)
        child_directories[:] = retained_directories
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
            if _is_private_study_path(relative):
                findings.append(
                    Finding(
                        relative_path,
                        "private-study-data",
                    )
                )
                continue
            if _is_private_recovery_path(relative):
                findings.append(
                    Finding(
                        relative_path,
                        "private-recovery-artifact",
                    )
                )
                continue
            if _is_private_benchmark_path(relative):
                findings.append(
                    Finding(
                        relative_path,
                        "private-benchmark-artifact",
                    )
                )
                continue
            lowercase_name = filename.lower()

            if lowercase_name == ".env" or lowercase_name.startswith(".env."):
                findings.append(
                    Finding(
                        relative_path,
                        "environment-file",
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
                    )
                )

            if path.suffix.lower() == ".pdf":
                findings.append(Finding(relative_path, "pdf-file"))
                continue

            if (
                path.suffix.lower() in DATA_SUFFIXES
                and relative_path not in DATA_ARTIFACT_ALLOWLIST
            ):
                findings.append(
                    Finding(
                        relative_path,
                        "data-artifact",
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
                    )
                )

            text = path.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(text) for pattern in SECRET_PATTERNS):
                findings.append(
                    Finding(
                        relative_path,
                        "possible-secret",
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
        print(f"{finding.path}: {finding.rule}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
