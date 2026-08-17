"""Validate externally asserted benchmark responses without provider verification."""

from __future__ import annotations

from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys

if os.name == "nt":
    import ctypes
    from ctypes import wintypes
    import msvcrt


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.effectiveness_contract import ensure_external_path
    from scripts.prepare_simulation_benchmark import (
        canonical_json_bytes,
        validate_benchmark_plan,
    )
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from effectiveness_contract import ensure_external_path
    from prepare_simulation_benchmark import canonical_json_bytes, validate_benchmark_plan


INDEX_KEYS = frozenset(
    {"schema_version", "plan_sha256", "execution_attestation", "records"}
)
ATTESTATION_KEYS = frozenset(
    {
        "completed_at",
        "model_provider",
        "model_id",
        "model_snapshot",
        "runner_name",
        "runner_version",
        "plan_followed",
        "fresh_sessions",
        "offline",
        "shared_configuration_unchanged",
    }
)
ATTESTATION_BOOLEAN_KEYS = (
    "plan_followed",
    "fresh_sessions",
    "offline",
    "shared_configuration_unchanged",
)
RECORD_KEYS = frozenset(
    {"case_id", "condition", "repeat", "relative_path", "response_sha256", "size"}
)
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
OPEN_BINARY = getattr(os, "O_BINARY", 0)
OPEN_DIRECTORY = getattr(os, "O_DIRECTORY", 0)
OPEN_NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)
DESCRIPTOR_RELATIVE_OPEN = (
    os.open in getattr(os, "supports_dir_fd", set())
    and OPEN_DIRECTORY != 0
    and OPEN_NOFOLLOW != 0
)

if os.name == "nt":
    _WIN_FILE_ATTRIBUTE_DIRECTORY = 0x10
    _WIN_FILE_ATTRIBUTE_REPARSE_POINT = 0x400
    _WIN_FILE_LIST_DIRECTORY = 0x0001
    _WIN_FILE_READ_ATTRIBUTES = 0x0080
    _WIN_SYNCHRONIZE = 0x00100000
    _WIN_SHARE_ALL = 0x00000007
    _WIN_OPEN_EXISTING = 3
    _WIN_FILE_OPEN = 1
    _WIN_FILE_OPEN_REPARSE_POINT = 0x00200000
    _WIN_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    _WIN_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _WIN_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _WIN_FILE_DIRECTORY_INFORMATION = 1
    _WIN_FILE_ID_INFO_CLASS = 0x12
    _WIN_STATUS_NO_MORE_FILES = 0x80000006
    _WIN_DIRECTORY_BUFFER_SIZE = 64 * 1024
    _WIN_INVALID_HANDLE = ctypes.c_void_p(-1).value

    class _WinIoStatusBlock(ctypes.Structure):
        _fields_ = [("status", ctypes.c_void_p), ("information", ctypes.c_size_t)]

    class _WinUnicodeString(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.USHORT),
            ("maximum_length", wintypes.USHORT),
            ("buffer", wintypes.LPWSTR),
        ]

    class _WinObjectAttributes(ctypes.Structure):
        _fields_ = [
            ("length", wintypes.ULONG),
            ("root_directory", wintypes.HANDLE),
            ("object_name", ctypes.POINTER(_WinUnicodeString)),
            ("attributes", wintypes.ULONG),
            ("security_descriptor", ctypes.c_void_p),
            ("security_quality_of_service", ctypes.c_void_p),
        ]

    class _WinFileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class _WinBasicHandleInfo(ctypes.Structure):
        _fields_ = [
            ("attributes", wintypes.DWORD),
            ("creation_time", _WinFileTime),
            ("last_access_time", _WinFileTime),
            ("last_write_time", _WinFileTime),
            ("volume_serial_number", wintypes.DWORD),
            ("file_size_high", wintypes.DWORD),
            ("file_size_low", wintypes.DWORD),
            ("number_of_links", wintypes.DWORD),
            ("file_index_high", wintypes.DWORD),
            ("file_index_low", wintypes.DWORD),
        ]

    class _WinFileId128(ctypes.Structure):
        _fields_ = [("identifier", ctypes.c_ubyte * 16)]

    class _WinFileIdInfo(ctypes.Structure):
        _fields_ = [
            ("volume_serial_number", ctypes.c_ulonglong),
            ("file_id", _WinFileId128),
        ]

    _WIN_KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _WIN_NTDLL = ctypes.WinDLL("ntdll")
    _WIN_CREATE_FILE = _WIN_KERNEL32.CreateFileW
    _WIN_CREATE_FILE.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _WIN_CREATE_FILE.restype = wintypes.HANDLE
    _WIN_CLOSE_HANDLE = _WIN_KERNEL32.CloseHandle
    _WIN_CLOSE_HANDLE.argtypes = [wintypes.HANDLE]
    _WIN_CLOSE_HANDLE.restype = wintypes.BOOL
    _WIN_GET_BASIC_INFO = _WIN_KERNEL32.GetFileInformationByHandle
    _WIN_GET_BASIC_INFO.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_WinBasicHandleInfo),
    ]
    _WIN_GET_BASIC_INFO.restype = wintypes.BOOL
    _WIN_GET_FILE_INFO = _WIN_KERNEL32.GetFileInformationByHandleEx
    _WIN_GET_FILE_INFO.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    ]
    _WIN_GET_FILE_INFO.restype = wintypes.BOOL
    _WIN_NT_CREATE_FILE = _WIN_NTDLL.NtCreateFile
    _WIN_NT_CREATE_FILE.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        ctypes.POINTER(_WinObjectAttributes),
        ctypes.POINTER(_WinIoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
    ]
    _WIN_NT_CREATE_FILE.restype = ctypes.c_long
    _WIN_NT_QUERY_DIRECTORY = _WIN_NTDLL.NtQueryDirectoryFile
    _WIN_NT_QUERY_DIRECTORY.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(_WinIoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        ctypes.c_int,
        wintypes.BOOLEAN,
        ctypes.c_void_p,
        wintypes.BOOLEAN,
    ]
    _WIN_NT_QUERY_DIRECTORY.restype = ctypes.c_long


class IncompleteBenchmark(Exception):
    """Report a safe canonical response prefix without treating it as a result."""

    def __init__(self, *, expected_count: int, observed_count: int) -> None:
        self.expected_count = expected_count
        self.observed_count = observed_count
        super().__init__("simulation benchmark responses are incomplete")


def _exact_keys(
    value: object, expected: frozenset[str], label: str, errors: list[str]
) -> bool:
    if not isinstance(value, dict) or set(value) != expected:
        errors.append(f"{label}: exact keys required")
        return False
    return True


def _aware_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return None
    if value.startswith("/") or value.endswith("/") or "//" in value or ":" in value:
        return None
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if posix_path.is_absolute() or windows_path.is_absolute() or windows_path.drive:
        return None
    if any(part in {"", ".", ".."} for part in value.split("/")):
        return None
    if posix_path.as_posix() != value:
        return None
    return posix_path.as_posix()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def validate_response_index(payload: object, plan: dict) -> list[str]:
    """Validate a closed response index; execution metadata remain external assertions."""
    errors: list[str] = []
    if validate_benchmark_plan(plan):
        return ["response index: invalid benchmark plan"]
    if not _exact_keys(payload, INDEX_KEYS, "response index", errors):
        return errors
    assert isinstance(payload, dict)

    if payload["schema_version"] != "1":
        errors.append("response index: unsupported schema version")
    expected_plan_sha256 = hashlib.sha256(canonical_json_bytes(plan)).hexdigest()
    if payload["plan_sha256"] != expected_plan_sha256:
        errors.append("response index: plan digest mismatch")

    attestation = payload["execution_attestation"]
    if _exact_keys(attestation, ATTESTATION_KEYS, "execution attestation", errors):
        assert isinstance(attestation, dict)
        identities = {
            "model_provider": plan["model"]["provider"],
            "model_id": plan["model"]["id"],
            "model_snapshot": plan["model"]["snapshot"],
            "runner_name": plan["runner"]["name"],
            "runner_version": plan["runner"]["version"],
        }
        for key, expected in identities.items():
            if attestation[key] != expected:
                errors.append(f"execution attestation: {key} mismatch")
        for key in ATTESTATION_BOOLEAN_KEYS:
            if attestation[key] is not True:
                errors.append(f"execution attestation: {key} must be true")
        completed_at = _aware_datetime(attestation["completed_at"])
        created_at = _aware_datetime(plan["created_at"])
        if completed_at is None:
            errors.append("execution attestation: completed_at must be timezone-aware")
        elif created_at is None or completed_at < created_at:
            errors.append("execution attestation: completed_at precedes plan creation")

    records = payload["records"]
    if not isinstance(records, list):
        errors.append("response index: records must be a list")
        return errors

    expected_cells = plan["cells"]
    if len(records) > len(expected_cells):
        errors.append("response index: too many records")

    normalized_paths: set[str] = set()
    cell_identities: set[tuple[str, str, int]] = set()
    canonical_prefix = len(records) <= len(expected_cells)
    for index, record in enumerate(records):
        if not _exact_keys(record, RECORD_KEYS, "response record", errors):
            canonical_prefix = False
            continue
        assert isinstance(record, dict)
        identity = (record["case_id"], record["condition"], record["repeat"])
        identity_is_typed = (
            isinstance(record["case_id"], str)
            and isinstance(record["condition"], str)
            and isinstance(record["repeat"], int)
            and not isinstance(record["repeat"], bool)
        )
        if identity_is_typed:
            if identity in cell_identities:
                errors.append("response record: duplicate cell identity")
            cell_identities.add(identity)

        if index >= len(expected_cells):
            canonical_prefix = False
        else:
            expected = expected_cells[index]
            expected_identity = (
                expected["case_id"],
                expected["condition"],
                expected["repeat"],
            )
            if identity != expected_identity:
                errors.append("response record: cell identity is not in canonical order")
                canonical_prefix = False

        repeat = record["repeat"]
        if (
            not isinstance(repeat, int)
            or isinstance(repeat, bool)
            or not 1 <= repeat <= plan["repeats"]
        ):
            errors.append("response record: invalid repeat")
        if not isinstance(record["condition"], str) or record["condition"] not in (
            "control",
            "intervention",
        ):
            errors.append("response record: invalid condition")
        if not isinstance(record["case_id"], str) or record["case_id"] not in plan[
            "case_ids"
        ]:
            errors.append("response record: invalid case ID")

        normalized = _safe_relative_path(record["relative_path"])
        if normalized is None:
            errors.append("response record: invalid relative path")
        elif normalized in normalized_paths:
            errors.append("response record: duplicate normalized path")
        else:
            normalized_paths.add(normalized)
        if not _is_sha256(record["response_sha256"]):
            errors.append("response record: invalid response digest")
        size = record["size"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            errors.append("response record: invalid size")

    if not errors and canonical_prefix and len(records) < len(expected_cells):
        raise IncompleteBenchmark(
            expected_count=len(expected_cells), observed_count=len(records)
        )
    return errors


def _is_reparse_or_symlink(file_stat: os.stat_result) -> bool:
    attributes = getattr(file_stat, "st_file_attributes", 0)
    return stat.S_ISLNK(file_stat.st_mode) or bool(attributes & REPARSE_POINT)


def _identity(file_stat: os.stat_result) -> tuple[int, int]:
    return file_stat.st_dev, file_stat.st_ino


def _before_directory_scan(directory: Path) -> None:
    """Narrow test seam for a directory-replacement race."""


def _before_response_file_open(response_path: Path) -> None:
    """Narrow test seam for a response-path replacement race."""


def _after_windows_file_precheck_before_relative_open(
    parent_path: Path, name: str
) -> None:
    """Narrow test seam at the Windows file ABA window."""


def _after_windows_directory_precheck_before_relative_open(
    parent_path: Path, name: str
) -> None:
    """Narrow test seam at the Windows directory ABA window."""


def _after_windows_relative_open(parent_path: Path, name: str) -> None:
    """Narrow test seam for restoring a Windows pathname after relative open."""


class _WindowsOpenedFile:
    __slots__ = ("descriptor", "identity", "size")

    def __init__(
        self, descriptor: int, identity: tuple[int, bytes], size: int
    ) -> None:
        self.descriptor = descriptor
        self.identity = identity
        self.size = size


def _windows_handle_number(handle: object) -> int:
    value = getattr(handle, "value", handle)
    if not isinstance(value, int) or value in {0, _WIN_INVALID_HANDLE}:
        raise ValueError
    return value


def _windows_close_handle(handle: object) -> None:
    try:
        value = _windows_handle_number(handle)
    except ValueError:
        return
    _WIN_CLOSE_HANDLE(wintypes.HANDLE(value))


def _windows_handle_info(handle: object) -> tuple[int, tuple[int, bytes], int]:
    value = _windows_handle_number(handle)
    basic = _WinBasicHandleInfo()
    file_id = _WinFileIdInfo()
    if not _WIN_GET_BASIC_INFO(wintypes.HANDLE(value), ctypes.byref(basic)):
        raise ValueError
    if not _WIN_GET_FILE_INFO(
        wintypes.HANDLE(value),
        _WIN_FILE_ID_INFO_CLASS,
        ctypes.byref(file_id),
        ctypes.sizeof(file_id),
    ):
        raise ValueError
    identifier = bytes(file_id.file_id.identifier)
    if not any(identifier):
        raise ValueError
    size = (basic.file_size_high << 32) | basic.file_size_low
    return (
        basic.attributes,
        (file_id.volume_serial_number, identifier),
        size,
    )


def _windows_stat_identity(file_stat: os.stat_result) -> tuple[int, bytes]:
    try:
        identifier = file_stat.st_ino.to_bytes(16, "little", signed=False)
    except (AttributeError, OverflowError):
        raise ValueError from None
    return file_stat.st_dev, identifier


def _windows_open_absolute(path: Path, *, list_directory: bool) -> int:
    desired_access = _WIN_FILE_READ_ATTRIBUTES | _WIN_SYNCHRONIZE
    if list_directory:
        desired_access |= _WIN_FILE_LIST_DIRECTORY
    handle = _WIN_CREATE_FILE(
        str(path),
        desired_access,
        _WIN_SHARE_ALL,
        None,
        _WIN_OPEN_EXISTING,
        _WIN_FILE_FLAG_BACKUP_SEMANTICS | _WIN_FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    return _windows_handle_number(handle)


def _windows_open_root(root: Path) -> int:
    expected = root.lstat()
    handle = _windows_open_absolute(root, list_directory=True)
    try:
        attributes, identity, _ = _windows_handle_info(handle)
        if (
            attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT
            or not attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY
            or identity != _windows_stat_identity(expected)
        ):
            raise ValueError
    except (OSError, ValueError):
        _windows_close_handle(handle)
        raise
    return handle


def _windows_require_path_matches_handle(
    path: Path, expected_handle: int, *, directory: bool
) -> None:
    observed_handle = _windows_open_absolute(path, list_directory=directory)
    try:
        attributes, identity, _ = _windows_handle_info(observed_handle)
        expected_attributes, expected_identity, _ = _windows_handle_info(
            expected_handle
        )
        if (
            attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT
            or bool(attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY) != directory
            or bool(expected_attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY) != directory
            or identity != expected_identity
        ):
            raise ValueError
    finally:
        _windows_close_handle(observed_handle)


def _windows_directory_entries(directory_handle: int) -> tuple[tuple[str, int], ...]:
    entries: list[tuple[str, int]] = []
    restart = True
    while True:
        buffer = ctypes.create_string_buffer(_WIN_DIRECTORY_BUFFER_SIZE)
        io_status = _WinIoStatusBlock()
        status = _WIN_NT_QUERY_DIRECTORY(
            wintypes.HANDLE(directory_handle),
            None,
            None,
            None,
            ctypes.byref(io_status),
            buffer,
            len(buffer),
            _WIN_FILE_DIRECTORY_INFORMATION,
            False,
            None,
            restart,
        )
        status_code = status & 0xFFFFFFFF
        if status_code == _WIN_STATUS_NO_MORE_FILES:
            return tuple(entries)
        if status != 0 or io_status.information == 0:
            raise ValueError
        used = io_status.information
        offset = 0
        while True:
            if offset + 64 > used:
                raise ValueError
            next_offset = int.from_bytes(buffer[offset : offset + 4], "little")
            attributes = int.from_bytes(buffer[offset + 56 : offset + 60], "little")
            name_length = int.from_bytes(buffer[offset + 60 : offset + 64], "little")
            name_end = offset + 64 + name_length
            if name_length % 2 or name_end > used:
                raise ValueError
            name = bytes(buffer[offset + 64 : name_end]).decode(
                "utf-16-le", errors="strict"
            )
            if name not in {".", ".."}:
                if not name or any(character in name for character in ("/", "\\", ":")):
                    raise ValueError
                entries.append((name, attributes))
            if next_offset == 0:
                break
            if next_offset < 64 or offset + next_offset >= used:
                raise ValueError
            offset += next_offset
        restart = False


def _windows_open_relative(parent_handle: int, name: str) -> int:
    encoded = name.encode("utf-16-le")
    if len(encoded) > 0xFFFC:
        raise ValueError
    name_buffer = ctypes.create_unicode_buffer(name)
    unicode_name = _WinUnicodeString(
        len(encoded),
        len(encoded) + 2,
        ctypes.cast(name_buffer, wintypes.LPWSTR),
    )
    object_attributes = _WinObjectAttributes(
        ctypes.sizeof(_WinObjectAttributes),
        wintypes.HANDLE(parent_handle),
        ctypes.pointer(unicode_name),
        0,
        None,
        None,
    )
    child_handle = wintypes.HANDLE()
    io_status = _WinIoStatusBlock()
    status = _WIN_NT_CREATE_FILE(
        ctypes.byref(child_handle),
        _WIN_FILE_LIST_DIRECTORY | _WIN_FILE_READ_ATTRIBUTES | _WIN_SYNCHRONIZE,
        ctypes.byref(object_attributes),
        ctypes.byref(io_status),
        None,
        0,
        _WIN_SHARE_ALL,
        _WIN_FILE_OPEN,
        _WIN_FILE_OPEN_REPARSE_POINT | _WIN_FILE_SYNCHRONOUS_IO_NONALERT,
        None,
        0,
    )
    if status < 0:
        raise ValueError
    return _windows_handle_number(child_handle)


def _windows_walk_directory(
    directory_handle: int,
    directory_path: Path,
    relative_parts: tuple[str, ...],
    opened_files: dict[str, _WindowsOpenedFile],
    identities: set[tuple[int, bytes]],
) -> None:
    _before_directory_scan(directory_path)
    _windows_require_path_matches_handle(
        directory_path, directory_handle, directory=True
    )
    for name, enumerated_attributes in _windows_directory_entries(directory_handle):
        if enumerated_attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError
        is_directory = bool(
            enumerated_attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY
        )
        child_path = directory_path / name
        if is_directory:
            _after_windows_directory_precheck_before_relative_open(
                directory_path, name
            )
        else:
            _before_response_file_open(child_path)
            _after_windows_file_precheck_before_relative_open(directory_path, name)
        child_handle = _windows_open_relative(directory_handle, name)
        try:
            _after_windows_relative_open(directory_path, name)
            attributes, identity, size = _windows_handle_info(child_handle)
            if (
                attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT
                or bool(attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY) != is_directory
            ):
                raise ValueError
            _windows_require_path_matches_handle(
                child_path, child_handle, directory=is_directory
            )
            child_parts = (*relative_parts, name)
            if is_directory:
                _windows_walk_directory(
                    child_handle,
                    child_path,
                    child_parts,
                    opened_files,
                    identities,
                )
            else:
                if identity in identities:
                    raise ValueError
                identities.add(identity)
                descriptor = msvcrt.open_osfhandle(
                    child_handle, os.O_RDONLY | OPEN_BINARY
                )
                child_handle = 0
                opened_files["/".join(child_parts)] = _WindowsOpenedFile(
                    descriptor, identity, size
                )
        finally:
            _windows_close_handle(child_handle)


def _windows_open_response_tree(root: Path) -> dict[str, _WindowsOpenedFile]:
    opened_files: dict[str, _WindowsOpenedFile] = {}
    root_handle = 0
    try:
        root_handle = _windows_open_root(root)
        _windows_walk_directory(
            root_handle, root, (), opened_files, set()
        )
        return opened_files
    except (OSError, UnicodeError, ValueError):
        for opened in opened_files.values():
            os.close(opened.descriptor)
        raise ValueError("invalid response files") from None
    finally:
        _windows_close_handle(root_handle)


def _windows_same_opened_tree(
    first: dict[str, _WindowsOpenedFile],
    second: dict[str, _WindowsOpenedFile],
) -> bool:
    return set(first) == set(second) and all(
        first[path].identity == second[path].identity
        and first[path].size == second[path].size
        for path in first
    )


def _windows_verified_descriptors(
    root: Path, expected_paths: set[str]
) -> dict[str, _WindowsOpenedFile]:
    opened = _windows_open_response_tree(root)
    try:
        if set(opened) != expected_paths:
            raise ValueError
        confirmed = _windows_open_response_tree(root)
        try:
            if not _windows_same_opened_tree(opened, confirmed):
                raise ValueError
        finally:
            for item in confirmed.values():
                os.close(item.descriptor)
        return opened
    except (OSError, ValueError):
        for item in opened.values():
            os.close(item.descriptor)
        raise ValueError("invalid response files") from None


def _require_same_entry(
    path: Path, expected: os.stat_result, *, directory: bool
) -> os.stat_result:
    current = path.lstat()
    expected_kind = stat.S_ISDIR if directory else stat.S_ISREG
    if (
        _is_reparse_or_symlink(current)
        or not expected_kind(current.st_mode)
        or _identity(current) != _identity(expected)
    ):
        raise ValueError
    return current


def _external_regular_root(responses_root: Path) -> Path:
    try:
        root_stat = responses_root.lstat()
        if _is_reparse_or_symlink(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
            raise ValueError
        return ensure_external_path(responses_root, ROOT)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("invalid response files") from None


def _scan_regular_files(
    root: Path,
) -> tuple[dict[str, os.stat_result], dict[str, os.stat_result]]:
    observed: dict[str, os.stat_result] = {}
    directories: dict[str, os.stat_result] = {}
    identities: set[tuple[int, int]] = set()
    try:
        root_stat = root.lstat()
        if _is_reparse_or_symlink(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
            raise ValueError
        directories[""] = root_stat
        pending = [(root, root_stat)]
        while pending:
            directory, expected_directory = pending.pop()
            _before_directory_scan(directory)
            _require_same_entry(directory, expected_directory, directory=True)
            with os.scandir(directory) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    entry_stat = entry_path.lstat()
                    if _is_reparse_or_symlink(entry_stat):
                        raise ValueError
                    if stat.S_ISDIR(entry_stat.st_mode):
                        relative = entry_path.relative_to(root).as_posix()
                        directories[relative] = entry_stat
                        pending.append((entry_path, entry_stat))
                    elif stat.S_ISREG(entry_stat.st_mode):
                        relative = entry_path.relative_to(root).as_posix()
                        identity = _identity(entry_stat)
                        if identity in identities:
                            raise ValueError
                        identities.add(identity)
                        observed[relative] = entry_stat
                    else:
                        raise ValueError
            _require_same_entry(directory, expected_directory, directory=True)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("invalid response files") from None
    return observed, directories


def _same_snapshot(
    first: tuple[dict[str, os.stat_result], dict[str, os.stat_result]],
    second: tuple[dict[str, os.stat_result], dict[str, os.stat_result]],
) -> bool:
    return all(
        set(left) == set(right)
        and all(_identity(left[key]) == _identity(right[key]) for key in left)
        for left, right in zip(first, second, strict=True)
    )


def _validate_directory_chain(
    root: Path,
    parent_parts: tuple[str, ...],
    directories: dict[str, os.stat_result],
) -> None:
    _require_same_entry(root, directories[""], directory=True)
    current = root
    prefix: list[str] = []
    for part in parent_parts:
        prefix.append(part)
        current = current / part
        _require_same_entry(
            current, directories["/".join(prefix)], directory=True
        )


def _require_open_file_identity(
    file_descriptor: int, expected: os.stat_result
) -> os.stat_result:
    opened = os.fstat(file_descriptor)
    if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(expected):
        raise ValueError
    return opened


def _open_response_windows(
    root: Path,
    parts: tuple[str, ...],
    files: dict[str, os.stat_result],
    directories: dict[str, os.stat_result],
) -> int:
    relative_path = "/".join(parts)
    response_path = root.joinpath(*parts)
    _validate_directory_chain(root, parts[:-1], directories)
    _require_same_entry(response_path, files[relative_path], directory=False)
    file_descriptor = os.open(response_path, os.O_RDONLY | OPEN_BINARY)
    try:
        _require_open_file_identity(file_descriptor, files[relative_path])
        _validate_directory_chain(root, parts[:-1], directories)
        _require_same_entry(response_path, files[relative_path], directory=False)
    except (OSError, ValueError):
        os.close(file_descriptor)
        raise
    return file_descriptor


def _open_response_relative(
    root: Path,
    root_descriptor: int,
    parts: tuple[str, ...],
    files: dict[str, os.stat_result],
    directories: dict[str, os.stat_result],
) -> int:
    parent_descriptor = os.dup(root_descriptor)
    prefix: list[str] = []
    try:
        for part in parts[:-1]:
            prefix.append(part)
            child_descriptor = os.open(
                part,
                os.O_RDONLY | OPEN_DIRECTORY | OPEN_NOFOLLOW,
                dir_fd=parent_descriptor,
            )
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor
            expected_directory = directories["/".join(prefix)]
            opened_directory = os.fstat(parent_descriptor)
            if (
                not stat.S_ISDIR(opened_directory.st_mode)
                or _identity(opened_directory) != _identity(expected_directory)
            ):
                raise ValueError
            _require_same_entry(
                root.joinpath(*prefix), expected_directory, directory=True
            )

        relative_path = "/".join(parts)
        file_descriptor = os.open(
            parts[-1],
            os.O_RDONLY | OPEN_BINARY | OPEN_NOFOLLOW,
            dir_fd=parent_descriptor,
        )
        try:
            _require_open_file_identity(file_descriptor, files[relative_path])
            _require_same_entry(
                root.joinpath(*parts), files[relative_path], directory=False
            )
        except (OSError, ValueError):
            os.close(file_descriptor)
            raise
        return file_descriptor
    finally:
        os.close(parent_descriptor)


def _open_response_descriptor(
    root: Path,
    root_descriptor: int | None,
    relative_path: str,
    files: dict[str, os.stat_result],
    directories: dict[str, os.stat_result],
) -> int:
    parts = PurePosixPath(relative_path).parts
    response_path = root.joinpath(*parts)
    _before_response_file_open(response_path)
    if root_descriptor is None:
        return _open_response_windows(root, parts, files, directories)
    return _open_response_relative(
        root, root_descriptor, parts, files, directories
    )


def _read_descriptor(file_descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(file_descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def load_response_cells(
    plan: dict, index: dict, responses_root: Path
) -> tuple[dict, ...]:
    """Load verified UTF-8 text once, without retaining paths or raw response bytes."""
    errors = validate_response_index(index, plan)
    if errors:
        raise ValueError("invalid response index")

    root = _external_regular_root(Path(responses_root))
    expected_paths = {record["relative_path"] for record in index["records"]}

    cells: list[dict] = []
    descriptors: list[int] = []
    ordered_descriptors: list[int] = []
    root_descriptor: int | None = None
    try:
        if os.name == "nt":
            windows_opened = _windows_verified_descriptors(root, expected_paths)
            descriptors.extend(
                item.descriptor for item in windows_opened.values()
            )
            for record in index["records"]:
                opened = windows_opened[record["relative_path"]]
                attributes, identity, size = _windows_handle_info(
                    msvcrt.get_osfhandle(opened.descriptor)
                )
                if (
                    attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT
                    or attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY
                    or identity != opened.identity
                    or size != opened.size
                    or size != record["size"]
                ):
                    raise ValueError
                ordered_descriptors.append(opened.descriptor)
        else:
            snapshot = _scan_regular_files(root)
            observed, directories = snapshot
            if set(observed) != expected_paths:
                raise ValueError
            if DESCRIPTOR_RELATIVE_OPEN:
                root_descriptor = os.open(
                    root, os.O_RDONLY | OPEN_DIRECTORY | OPEN_NOFOLLOW
                )
                opened_root = os.fstat(root_descriptor)
                if (
                    not stat.S_ISDIR(opened_root.st_mode)
                    or _identity(opened_root) != _identity(directories[""])
                ):
                    raise ValueError
                _require_same_entry(root, directories[""], directory=True)

            for record in index["records"]:
                descriptor = _open_response_descriptor(
                    root,
                    root_descriptor,
                    record["relative_path"],
                    observed,
                    directories,
                )
                descriptors.append(descriptor)
                ordered_descriptors.append(descriptor)

            confirmed_snapshot = _scan_regular_files(root)
            if not _same_snapshot(snapshot, confirmed_snapshot):
                raise ValueError

            for file_descriptor, record in zip(
                ordered_descriptors, index["records"], strict=True
            ):
                opened = _require_open_file_identity(
                    file_descriptor, observed[record["relative_path"]]
                )
                if opened.st_size != record["size"]:
                    raise ValueError

        for planned, record, file_descriptor in zip(
            plan["cells"], index["records"], ordered_descriptors, strict=True
        ):
            raw = _read_descriptor(file_descriptor)
            if len(raw) != record["size"]:
                raise ValueError
            if hashlib.sha256(raw).hexdigest() != record["response_sha256"]:
                raise ValueError
            text = raw.decode("utf-8", errors="strict")
            cells.append(
                {
                    "case_id": planned["case_id"],
                    "condition": planned["condition"],
                    "repeat": planned["repeat"],
                    "sequence": planned["sequence"],
                    "text": text,
                }
            )
    except (OSError, UnicodeError, ValueError):
        raise ValueError("invalid response files") from None
    finally:
        for file_descriptor in descriptors:
            os.close(file_descriptor)
        if root_descriptor is not None:
            os.close(root_descriptor)
    return tuple(cells)
