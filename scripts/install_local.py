"""Install a verified Skill archive into a user-selected directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile
from zipfile import ZipFile

try:
    from scripts.validate_skill import validate_skill
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from validate_skill import validate_skill


SKILL_NAME = "clinical-data-research-navigator"
PACKAGE_VERSION = "0.1.0"


def _validate_member_name(name: str) -> None:
    path = PurePosixPath(name)
    windows_path = PureWindowsPath(name)
    if (
        not name
        or "\\" in name
        or path.is_absolute()
        or windows_path.is_absolute()
        or ".." in path.parts
    ):
        raise ValueError(f"unsafe ZIP member: {name}")


def install_package(
    archive: Path,
    destination: Path,
    overwrite: bool = False,
) -> Path:
    """Install *archive* below *destination*."""
    archive = archive.resolve()
    destination = destination.resolve()
    installed = destination / SKILL_NAME
    manifest_path = archive.with_suffix(".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest["name"] != SKILL_NAME
        or manifest["version"] != PACKAGE_VERSION
    ):
        raise ValueError("manifest identity mismatch")
    if manifest["archive"] != archive.name:
        raise ValueError("manifest archive mismatch")
    archive_digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if archive_digest != manifest["archive_sha256"]:
        raise ValueError("archive hash mismatch")
    records = {record["path"]: record for record in manifest["files"]}
    verified_files: dict[str, bytes] = {}
    with ZipFile(archive) as zip_file:
        member_names: list[str] = []
        for info in zip_file.infolist():
            _validate_member_name(info.filename)
            member_names.append(info.filename)
            record = records.get(info.filename)
            if record is None:
                raise ValueError(
                    "archive members do not match manifest: "
                    f"undeclared {info.filename}"
                )
            data = zip_file.read(info)
            if len(data) != record["size"]:
                raise ValueError(
                    f"manifest size mismatch for {info.filename}"
                )
            digest = hashlib.sha256(data).hexdigest()
            if digest != record["sha256"]:
                raise ValueError(
                    f"manifest hash mismatch for {info.filename}"
                )
            verified_files[info.filename] = data
        if (
            len(member_names) != len(set(member_names))
            or set(member_names) != set(records)
        ):
            raise ValueError("archive members do not match manifest")

    if os.path.lexists(installed) and not overwrite:
        raise FileExistsError(f"installation already exists: {installed}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".clinical-data-research-navigator-",
        dir=destination.parent,
    ) as temporary_name:
        temporary_root = Path(temporary_name)
        staged = temporary_root / SKILL_NAME
        staged.mkdir()
        for relative_name, data in verified_files.items():
            output = staged.joinpath(*PurePosixPath(relative_name).parts)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)

        errors = validate_skill(staged)
        if errors:
            raise ValueError(
                "invalid extracted Skill: " + "; ".join(errors)
            )

        destination.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(installed):
            backup = temporary_root / "previous-installation"
            os.replace(installed, backup)
            try:
                os.replace(staged, installed)
            except BaseException:
                os.replace(backup, installed)
                raise
        else:
            os.replace(staged, installed)
    return installed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--destination",
        type=Path,
        required=True,
        help="User-selected directory that will contain the installed Skill.",
    )
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    installed = install_package(
        args.archive,
        args.destination,
        overwrite=args.overwrite,
    )
    print(installed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
