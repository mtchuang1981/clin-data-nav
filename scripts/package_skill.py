"""Build a deterministic archive for the public Skill."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

try:
    from scripts.validate_skill import validate_skill
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from validate_skill import validate_skill


SKILL_NAME = "clinical-data-research-navigator"
PACKAGE_VERSION = "0.2.0"
ARCHIVE_NAME = f"{SKILL_NAME}-{PACKAGE_VERSION}.zip"
MANIFEST_NAME = f"{SKILL_NAME}-{PACKAGE_VERSION}.manifest.json"
INCLUDED_DIRECTORIES = ("agents", "references", "scripts", "assets")
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class PackageResult:
    archive: Path
    manifest: Path
    files: tuple[str, ...]


def _package_files(skill_dir: Path) -> tuple[Path, ...]:
    files = [skill_dir / "SKILL.md"]
    for directory_name in INCLUDED_DIRECTORIES:
        directory = skill_dir / directory_name
        if directory.is_dir():
            files.extend(path for path in directory.rglob("*") if path.is_file())
    return tuple(sorted(files, key=lambda path: path.relative_to(skill_dir).as_posix()))


def build_package(skill_dir: Path, output_dir: Path) -> PackageResult:
    """Validate and package *skill_dir* with reproducible metadata."""
    skill_dir = skill_dir.resolve()
    errors = validate_skill(skill_dir)
    if errors:
        raise ValueError("invalid Skill: " + "; ".join(errors))

    files = _package_files(skill_dir)
    relative_names = tuple(
        path.relative_to(skill_dir).as_posix() for path in files
    )
    file_records = []
    file_bytes: dict[str, bytes] = {}
    for path, relative_name in zip(files, relative_names, strict=True):
        if path.is_symlink() or not path.resolve().is_relative_to(skill_dir):
            raise ValueError(f"package file must be inside Skill: {relative_name}")
        data = path.read_bytes()
        file_bytes[relative_name] = data
        file_records.append(
            {
                "path": relative_name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / ARCHIVE_NAME
    with ZipFile(
        archive,
        "w",
        compression=ZIP_DEFLATED,
        compresslevel=9,
    ) as zip_file:
        for relative_name in relative_names:
            info = ZipInfo(relative_name, date_time=ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            zip_file.writestr(
                info,
                file_bytes[relative_name],
                compress_type=ZIP_DEFLATED,
                compresslevel=9,
            )

    manifest_data = {
        "archive": ARCHIVE_NAME,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files": file_records,
        "name": SKILL_NAME,
        "version": PACKAGE_VERSION,
    }
    manifest = output_dir / MANIFEST_NAME
    manifest.write_bytes(
        json.dumps(
            manifest_data,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    return PackageResult(archive, manifest, relative_names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "skills"
        / SKILL_NAME,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dist",
    )
    parser.add_argument("--check-reproducible", action="store_true")
    args = parser.parse_args(argv)

    if args.check_reproducible:
        with tempfile.TemporaryDirectory() as first_dir:
            with tempfile.TemporaryDirectory() as second_dir:
                first = build_package(args.skill_dir, Path(first_dir))
                second = build_package(args.skill_dir, Path(second_dir))
                archive_matches = (
                    first.archive.read_bytes() == second.archive.read_bytes()
                )
                manifest_matches = (
                    first.manifest.read_bytes() == second.manifest.read_bytes()
                )
                return 0 if archive_matches and manifest_matches else 1

    result = build_package(args.skill_dir, args.output_dir)
    print(result.archive)
    print(result.manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
