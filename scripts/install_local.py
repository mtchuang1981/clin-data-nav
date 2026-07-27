"""Install a verified Skill archive into a user-selected directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import tempfile
from zipfile import ZipFile, ZipInfo

try:
    from scripts.validate_skill import validate_skill
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from validate_skill import validate_skill


SKILL_NAME = "clinical-data-research-navigator"
PACKAGE_VERSION = "0.1.0"


class InstallRollbackError(RuntimeError):
    """Report where an original installation remains after rollback failure."""

    def __init__(
        self,
        recovery_path: Path,
        install_error: BaseException,
        rollback_error: BaseException,
    ) -> None:
        self.recovery_path = recovery_path
        super().__init__(
            f"installation replacement failed ({install_error}); "
            f"rollback failed ({rollback_error}); "
            f"recovery backup preserved at {recovery_path}"
        )


def _validate_member(info: ZipInfo) -> None:
    name = info.filename
    path = PurePosixPath(name)
    windows_path = PureWindowsPath(name)
    components = name.split("/")
    unix_mode = (info.external_attr >> 16) & 0xFFFF
    file_type = stat.S_IFMT(unix_mode)
    if (
        not name
        or "\\" in name
        or windows_path.drive
        or path.is_absolute()
        or windows_path.is_absolute()
        or any(component in {"", ".", ".."} for component in components)
        or path.as_posix() != name
        or info.is_dir()
        or file_type not in {0, stat.S_IFREG}
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
            _validate_member(info)
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
        staged_root = staged.resolve()
        planned_outputs: list[tuple[Path, bytes]] = []
        resolved_outputs: set[Path] = set()
        for relative_name, data in verified_files.items():
            output = staged.joinpath(*PurePosixPath(relative_name).parts)
            resolved_output = output.resolve(strict=False)
            if (
                not resolved_output.is_relative_to(staged_root)
                or resolved_output in resolved_outputs
            ):
                raise ValueError(
                    f"unsafe ZIP member output: {relative_name}"
                )
            resolved_outputs.add(resolved_output)
            planned_outputs.append((output, data))

        for output, data in planned_outputs:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(data)

        errors = validate_skill(staged)
        if errors:
            raise ValueError(
                "invalid extracted Skill: " + "; ".join(errors)
            )

        destination.mkdir(parents=True, exist_ok=True)
        if os.path.lexists(installed):
            backup_root = Path(
                tempfile.mkdtemp(
                    prefix=".clinical-data-research-navigator-backup-",
                    dir=destination.parent,
                )
            )
            backup = backup_root / SKILL_NAME
            try:
                os.replace(installed, backup)
            except BaseException:
                backup_root.rmdir()
                raise
            try:
                os.replace(staged, installed)
            except BaseException as install_error:
                try:
                    os.replace(backup, installed)
                except BaseException as rollback_error:
                    raise InstallRollbackError(
                        backup,
                        install_error,
                        rollback_error,
                    ) from rollback_error
                backup_root.rmdir()
                raise
            shutil.rmtree(backup_root)
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
