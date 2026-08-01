"""Fail closed when two package directories are not byte-identical."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


def _package_entries(directory: Path, label: str) -> tuple[str, str]:
    """Return the ZIP and manifest names after validating *directory*."""
    if not directory.exists():
        raise ValueError(f"{label}: directory does not exist")
    if not directory.is_dir():
        raise ValueError(f"{label}: path is not a directory")

    entries = tuple(sorted(directory.iterdir(), key=lambda entry: entry.name))
    for entry in entries:
        if entry.is_dir():
            raise ValueError(f"{label}: nested directory: {entry.name}")
        if entry.is_symlink() or not entry.is_file():
            raise ValueError(f"{label}: unexpected entry: {entry.name}")

    zip_entries = tuple(entry for entry in entries if entry.name.endswith(".zip"))
    if len(zip_entries) != 1:
        raise ValueError(
            f"{label}: expected exactly one .zip file, found {len(zip_entries)}"
        )

    manifest_entries = tuple(
        entry for entry in entries if entry.name.endswith(".manifest.json")
    )
    if len(manifest_entries) != 1:
        raise ValueError(
            f"{label}: expected exactly one .manifest.json file, "
            f"found {len(manifest_entries)}"
        )

    package_names = {zip_entries[0].name, manifest_entries[0].name}
    for entry in entries:
        if entry.name not in package_names:
            raise ValueError(f"{label}: unexpected entry: {entry.name}")

    return zip_entries[0].name, manifest_entries[0].name


def _compare_packages(
    first: Path, second: Path
) -> tuple[tuple[str, str], ...]:
    """Validate matching package directories and retain verified digests."""
    first_zip, first_manifest = _package_entries(first, "first")
    second_zip, second_manifest = _package_entries(second, "second")

    for first_name, second_name in (
        (first_zip, second_zip),
        (first_manifest, second_manifest),
    ):
        if first_name != second_name:
            raise ValueError(
                f"package file names differ: {first_name} != {second_name}"
            )

    verified_files = []
    for name in sorted((first_zip, first_manifest)):
        first_bytes = (first / name).read_bytes()
        second_bytes = (second / name).read_bytes()
        if first_bytes != second_bytes:
            raise ValueError(f"byte mismatch: {name}")
        verified_files.append((name, hashlib.sha256(first_bytes).hexdigest()))
    return tuple(verified_files)


def compare_package_directories(first: Path, second: Path) -> tuple[str, ...]:
    """Return sorted names after fail-closed package-directory comparison."""
    return tuple(name for name, _ in _compare_packages(first, second))


def main(argv: list[str] | None = None) -> int:
    """Compare two package directories and print their verified SHA-256 values."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", required=True, type=Path)
    parser.add_argument("--second", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        verified_files = _compare_packages(args.first, args.second)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1

    for name, digest in verified_files:
        print(f"{name} {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
