"""Install a verified Skill archive into a user-selected directory."""

from __future__ import annotations

import argparse
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import shutil
import stat
import sys
import tempfile
import unicodedata
from zipfile import ZipFile, ZipInfo

try:
    from scripts.validate_skill import validate_skill
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from validate_skill import validate_skill


SKILL_NAME = "clinical-data-research-navigator"
PACKAGE_VERSION = "0.1.1"
READ_CHUNK_BYTES = 64 * 1024
MAX_MANIFEST_BYTES = 1 * 1024 * 1024
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_MANIFEST_FILE_COUNT = 256
MAX_MEMBER_COUNT = 256
MAX_MEMBER_COMPRESSED_BYTES = 10 * 1024 * 1024
MAX_MEMBER_UNCOMPRESSED_BYTES = 10 * 1024 * 1024
MAX_TOTAL_COMPRESSED_BYTES = 20 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 40 * 1024 * 1024
AT_FDCWD = -100
RENAME_NOREPLACE = 1
DARWIN_RENAME_EXCL = 0x00000004


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
        or any(
            component.endswith((".", " ")) or ":" in component
            for component in components
        )
        or path.as_posix() != name
        or info.is_dir()
        or bool(info.external_attr & 0x10)
        or file_type not in {0, stat.S_IFREG}
    ):
        raise ValueError(f"unsafe ZIP member: {name}")


def _portable_path_key(name: str) -> tuple[str, ...]:
    return tuple(
        unicodedata.normalize("NFC", component).casefold()
        for component in name.split("/")
    )


def _load_manifest(manifest_path: Path) -> dict:
    try:
        manifest_size = manifest_path.stat().st_size
    except OSError:
        raise
    if manifest_size > MAX_MANIFEST_BYTES:
        raise ValueError("manifest size limit exceeded")
    with manifest_path.open("rb") as manifest_file:
        raw_manifest = manifest_file.read(MAX_MANIFEST_BYTES + 1)
    if len(raw_manifest) > MAX_MANIFEST_BYTES:
        raise ValueError("manifest size limit exceeded")
    try:
        manifest = json.loads(raw_manifest.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("invalid manifest JSON") from error
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    return manifest


def _manifest_records(manifest: dict) -> dict[str, dict]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("manifest files must be a list")
    if len(files) > MAX_MANIFEST_FILE_COUNT:
        raise ValueError("manifest member count limit exceeded")

    records: dict[str, dict] = {}
    for record in files:
        if not isinstance(record, dict) or set(record) != {
            "path",
            "sha256",
            "size",
        }:
            raise ValueError("invalid manifest file record")
        path = record["path"]
        digest = record["sha256"]
        size = record["size"]
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
        ):
            raise ValueError("invalid manifest file record")
        if path in records:
            raise ValueError("duplicate manifest file path")
        records[path] = record
    return records


def _hash_stream(stream) -> str:
    digest = hashlib.sha256()
    while chunk := stream.read(READ_CHUNK_BYTES):
        digest.update(chunk)
    return digest.hexdigest()


def _preflight_members(
    infos: list[ZipInfo],
    records: dict[str, dict],
) -> None:
    if len(infos) > MAX_MEMBER_COUNT:
        raise ValueError("archive member count limit exceeded")

    member_names: list[str] = []
    portable_names: dict[tuple[str, ...], str] = {}
    total_compressed = 0
    total_uncompressed = 0
    for info in infos:
        _validate_member(info)
        if info.compress_size > MAX_MEMBER_COMPRESSED_BYTES:
            raise ValueError(
                f"ZIP member compressed size limit exceeded: {info.filename}"
            )
        if info.file_size > MAX_MEMBER_UNCOMPRESSED_BYTES:
            raise ValueError(
                f"ZIP member uncompressed size limit exceeded: {info.filename}"
            )
        total_compressed += info.compress_size
        total_uncompressed += info.file_size
        if total_compressed > MAX_TOTAL_COMPRESSED_BYTES:
            raise ValueError("ZIP aggregate compressed size limit exceeded")
        if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
            raise ValueError("ZIP aggregate uncompressed size limit exceeded")

        portable_key = _portable_path_key(info.filename)
        existing_name = portable_names.get(portable_key)
        if existing_name is not None and existing_name != info.filename:
            raise ValueError(
                "portable path collision: "
                f"{existing_name} and {info.filename}"
            )
        portable_names[portable_key] = info.filename
        member_names.append(info.filename)
        record = records.get(info.filename)
        if record is None:
            raise ValueError(
                "archive members do not match manifest: "
                f"undeclared {info.filename}"
            )
        if info.file_size != record["size"]:
            raise ValueError(f"manifest size mismatch for {info.filename}")

    for portable_key, name in portable_names.items():
        for component_count in range(1, len(portable_key)):
            ancestor_key = portable_key[:component_count]
            ancestor_name = portable_names.get(ancestor_key)
            if ancestor_name is not None:
                raise ValueError(
                    "portable path ancestor conflict: "
                    f"{ancestor_name} and {name}"
                )
    if (
        len(member_names) != len(set(member_names))
        or set(member_names) != set(records)
    ):
        raise ValueError("archive members do not match manifest")


def _stream_members(
    zip_file: ZipFile,
    infos: list[ZipInfo],
    records: dict[str, dict],
    staged: Path,
) -> None:
    staged_root = staged.resolve()
    resolved_outputs: set[Path] = set()
    total_written = 0
    for info in infos:
        output = staged.joinpath(*PurePosixPath(info.filename).parts)
        resolved_output = output.resolve(strict=False)
        if (
            not resolved_output.is_relative_to(staged_root)
            or resolved_output in resolved_outputs
        ):
            raise ValueError(f"unsafe ZIP member output: {info.filename}")
        resolved_outputs.add(resolved_output)
        output.parent.mkdir(parents=True, exist_ok=True)

        digest = hashlib.sha256()
        member_written = 0
        with zip_file.open(info, "r") as source, output.open("xb") as target:
            while chunk := source.read(READ_CHUNK_BYTES):
                member_written += len(chunk)
                total_written += len(chunk)
                if member_written > MAX_MEMBER_UNCOMPRESSED_BYTES:
                    raise ValueError(
                        "ZIP member uncompressed size limit exceeded: "
                        f"{info.filename}"
                    )
                if total_written > MAX_TOTAL_UNCOMPRESSED_BYTES:
                    raise ValueError(
                        "ZIP aggregate uncompressed size limit exceeded"
                    )
                digest.update(chunk)
                target.write(chunk)

        record = records[info.filename]
        if member_written != record["size"]:
            raise ValueError(f"manifest size mismatch for {info.filename}")
        if digest.hexdigest() != record["sha256"]:
            raise ValueError(f"manifest hash mismatch for {info.filename}")


def _call_native_rename(
    function_name: str,
    argument_types: tuple,
    arguments: tuple,
    target: Path,
) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    rename_function = getattr(libc, function_name, None)
    if rename_function is None:
        raise OSError(
            errno.ENOTSUP,
            "atomic no-replace directory installation is unsupported",
            target,
        )
    rename_function.argtypes = argument_types
    rename_function.restype = ctypes.c_int
    result = rename_function(*arguments)
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(
            error_number,
            os.strerror(error_number),
            target,
        )


def _rename_no_replace(source: Path, target: Path) -> None:
    if os.name == "nt":
        os.rename(source, target)
        return
    if sys.platform.startswith("linux"):
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
    if sys.platform == "darwin":
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


def _install_without_overwrite(staged: Path, installed: Path) -> None:
    staged.chmod(0o755)
    try:
        _rename_no_replace(staged, installed)
    except FileExistsError:
        raise FileExistsError(
            f"installation already exists: {installed}"
        ) from None


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
    manifest = _load_manifest(manifest_path)
    if (
        manifest.get("name") != SKILL_NAME
        or manifest.get("version") != PACKAGE_VERSION
    ):
        raise ValueError("manifest identity mismatch")
    if manifest.get("archive") != archive.name:
        raise ValueError("manifest archive mismatch")
    records = _manifest_records(manifest)

    with archive.open("rb") as archive_file:
        archive_size = os.fstat(archive_file.fileno()).st_size
        if archive_size > MAX_ARCHIVE_BYTES:
            raise ValueError("archive size limit exceeded")
        archive_digest = _hash_stream(archive_file)
        if archive_digest != manifest.get("archive_sha256"):
            raise ValueError("archive hash mismatch")
        archive_file.seek(0)

        with ZipFile(archive_file) as zip_file:
            infos = zip_file.infolist()
            _preflight_members(infos, records)
            if os.path.lexists(installed) and not overwrite:
                raise FileExistsError(
                    f"installation already exists: {installed}"
                )

            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix=".clinical-data-research-navigator-",
                dir=destination.parent,
            ) as temporary_name:
                temporary_root = Path(temporary_name)
                staged = temporary_root / SKILL_NAME
                staged.mkdir()
                _stream_members(zip_file, infos, records, staged)

                errors = validate_skill(staged)
                if errors:
                    raise ValueError(
                        "invalid extracted Skill: " + "; ".join(errors)
                    )

                destination.mkdir(parents=True, exist_ok=True)
                if not overwrite:
                    _install_without_overwrite(staged, installed)
                    return installed
                if not os.path.lexists(installed):
                    try:
                        _install_without_overwrite(staged, installed)
                    except FileExistsError:
                        pass
                    else:
                        return installed

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
