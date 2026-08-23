"""Validate externally asserted benchmark responses without provider verification."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import secrets
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
    from scripts.evaluate_response import evaluate_response, load_catalog
    from scripts.effectiveness_contract import ensure_external_path
    from scripts.prepare_simulation_benchmark import (
        BINDING_KEYS,
        MODEL_KEYS,
        SAFE_BENCHMARK_ID,
        _valid_binding,
        _valid_identifier,
        canonical_json_bytes,
        validate_benchmark_plan,
    )
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from evaluate_response import evaluate_response, load_catalog
    from effectiveness_contract import ensure_external_path
    from prepare_simulation_benchmark import (
        BINDING_KEYS,
        MODEL_KEYS,
        SAFE_BENCHMARK_ID,
        _valid_binding,
        _valid_identifier,
        canonical_json_bytes,
        validate_benchmark_plan,
    )


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
SUMMARY_KEYS = frozenset(
    {
        "benchmark_id",
        "case_results",
        "catalog_sha256",
        "cell_counts",
        "claim_boundaries",
        "direction",
        "execution_attestation",
        "forbidden_violations",
        "model",
        "output_depth_results",
        "overall",
        "paired_counts",
        "plan_sha256",
        "repeats",
        "rubric_sha256",
        "schema_version",
        "skill",
        "status",
        "synthetic_example",
    }
)
SUMMARY_ATTESTATION_KEYS = ATTESTATION_KEYS | {"assertion_basis"}
PAIR_COUNT_KEYS = frozenset({"both_fail", "both_pass", "improved", "worsened"})
FORBIDDEN_COUNT_KEYS = frozenset({"control", "intervention"})
STABILITY_KEYS = frozenset({"control", "intervention"})
CASE_RESULT_KEYS = frozenset(
    {
        "case_id",
        "control_passes",
        "forbidden_violations",
        "intervention_passes",
        "output_depth",
        "paired_counts",
        "stability",
    }
)
OVERALL_KEYS = frozenset(
    {
        "control_passes",
        "control_pass_rate",
        "difference",
        "intervention_passes",
        "intervention_pass_rate",
        "pairs",
    }
)
DEPTH_RESULT_KEYS = OVERALL_KEYS | frozenset(
    {"case_count", "forbidden_violations", "output_depth", "paired_counts"}
)
CLAIM_BOUNDARIES = [
    "public-synthetic-prompts-only",
    "deterministic-contract-checks-only",
    "no-representative-user-evidence",
    "no-clinical-causal-patient-outcome-or-deployment-claim",
]
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
CLI_ERROR = b"simulation benchmark evaluation failed\n"
COMPLETE_STATUS = {"schema_version": "1", "status": "benchmark-observed"}
COMPLETE_STATUS_BYTES = b'{"schema_version":"1","status":"benchmark-observed"}\n'
CLI_FLAGS = (
    "--plan",
    "--response-index",
    "--responses-dir",
    "--output-summary",
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
    _WIN_FILE_CREATE = 2
    _WIN_FILE_OPEN_REPARSE_POINT = 0x00200000
    _WIN_FILE_NON_DIRECTORY_FILE = 0x00000040
    _WIN_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
    _WIN_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _WIN_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _WIN_FILE_DIRECTORY_INFORMATION = 1
    _WIN_FILE_ID_INFO_CLASS = 0x12
    _WIN_FILE_RENAME_INFORMATION_CLASS = 10
    _WIN_FILE_DISPOSITION_INFORMATION_CLASS = 13
    _WIN_DELETE = 0x00010000
    _WIN_GENERIC_WRITE = 0x40000000
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

    class _WinFileRenameInformation(ctypes.Structure):
        _fields_ = [
            ("replace_if_exists", wintypes.BOOLEAN),
            ("root_directory", wintypes.HANDLE),
            ("file_name_length", wintypes.ULONG),
            ("file_name", wintypes.WCHAR * 1),
        ]

    class _WinFileDispositionInformation(ctypes.Structure):
        _fields_ = [("delete_file", wintypes.BOOLEAN)]

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
    _WIN_NT_SET_INFORMATION = _WIN_NTDLL.NtSetInformationFile
    _WIN_NT_SET_INFORMATION.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_WinIoStatusBlock),
        ctypes.c_void_p,
        wintypes.ULONG,
        ctypes.c_int,
    ]
    _WIN_NT_SET_INFORMATION.restype = ctypes.c_long


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


def _execution_attestation_errors(attestation: object, plan: dict) -> list[str]:
    errors: list[str] = []
    if not _exact_keys(
        attestation, ATTESTATION_KEYS, "execution attestation", errors
    ):
        return errors
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
    return errors


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

    errors.extend(_execution_attestation_errors(payload["execution_attestation"], plan))

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


def _windows_identities_match(
    stat_identity: object, handle_identity: object
) -> bool:
    """Compare Python stat identity with the native Windows handle identity."""
    if (
        type(stat_identity) is not tuple
        or len(stat_identity) != 2
        or type(handle_identity) is not tuple
        or len(handle_identity) != 2
    ):
        return False
    stat_volume, stat_file_id = stat_identity
    handle_volume, handle_file_id = handle_identity
    if (
        type(stat_volume) is not int
        or not 0 <= stat_volume <= 0xFFFFFFFFFFFFFFFF
        or type(handle_volume) is not int
        or not 0 <= handle_volume <= 0xFFFFFFFFFFFFFFFF
        or type(stat_file_id) is not bytes
        or len(stat_file_id) != 16
        or type(handle_file_id) is not bytes
        or len(handle_file_id) != 16
    ):
        return False
    if stat_file_id != handle_file_id:
        return False
    if 0 <= stat_volume <= 0xFFFFFFFF:
        return stat_volume == (handle_volume & 0xFFFFFFFF)
    return stat_volume == handle_volume


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
            or not _windows_identities_match(
                _windows_stat_identity(expected), identity
            )
        ):
            raise ValueError
    except BaseException:
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


def _windows_nt_open_relative(
    parent_handle: int,
    name: str,
    *,
    desired_access: int,
    disposition: int,
    options: int,
) -> int:
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
        desired_access,
        ctypes.byref(object_attributes),
        ctypes.byref(io_status),
        None,
        0,
        _WIN_SHARE_ALL,
        disposition,
        options,
        None,
        0,
    )
    if status < 0:
        raise ValueError
    return _windows_handle_number(child_handle)


def _windows_open_relative(parent_handle: int, name: str) -> int:
    return _windows_nt_open_relative(
        parent_handle,
        name,
        desired_access=(
            _WIN_FILE_LIST_DIRECTORY | _WIN_FILE_READ_ATTRIBUTES | _WIN_SYNCHRONIZE
        ),
        disposition=_WIN_FILE_OPEN,
        options=_WIN_FILE_OPEN_REPARSE_POINT | _WIN_FILE_SYNCHRONOUS_IO_NONALERT,
    )


def _windows_open_owned_file(parent_handle: int, name: str) -> int:
    return _windows_nt_open_relative(
        parent_handle,
        name,
        desired_access=_WIN_DELETE | _WIN_FILE_READ_ATTRIBUTES | _WIN_SYNCHRONIZE,
        disposition=_WIN_FILE_OPEN,
        options=(
            _WIN_FILE_OPEN_REPARSE_POINT
            | _WIN_FILE_NON_DIRECTORY_FILE
            | _WIN_FILE_SYNCHRONOUS_IO_NONALERT
        ),
    )


def _windows_create_owned_file(parent_handle: int, name: str) -> int:
    return _windows_nt_open_relative(
        parent_handle,
        name,
        desired_access=_WIN_DELETE | _WIN_FILE_READ_ATTRIBUTES | _WIN_SYNCHRONIZE,
        disposition=_WIN_FILE_CREATE,
        options=(
            _WIN_FILE_OPEN_REPARSE_POINT
            | _WIN_FILE_NON_DIRECTORY_FILE
            | _WIN_FILE_SYNCHRONOUS_IO_NONALERT
        ),
    )


def _windows_open_stage_writer(parent_handle: int, name: str) -> int:
    return _windows_nt_open_relative(
        parent_handle,
        name,
        desired_access=_WIN_GENERIC_WRITE | _WIN_FILE_READ_ATTRIBUTES | _WIN_SYNCHRONIZE,
        disposition=_WIN_FILE_OPEN,
        options=(
            _WIN_FILE_OPEN_REPARSE_POINT
            | _WIN_FILE_NON_DIRECTORY_FILE
            | _WIN_FILE_SYNCHRONOUS_IO_NONALERT
        ),
    )


def _windows_rename_owned(
    file_handle: int,
    parent_handle: int,
    destination_name: str,
    *,
    replace: bool,
) -> None:
    encoded = destination_name.encode("utf-16-le")
    name_offset = _WinFileRenameInformation.file_name.offset
    information_buffer = ctypes.create_string_buffer(name_offset + len(encoded))
    information = _WinFileRenameInformation.from_buffer(information_buffer)
    information.replace_if_exists = replace
    information.root_directory = wintypes.HANDLE(parent_handle)
    information.file_name_length = len(encoded)
    ctypes.memmove(
        ctypes.addressof(information_buffer) + name_offset, encoded, len(encoded)
    )
    io_status = _WinIoStatusBlock()
    status = _WIN_NT_SET_INFORMATION(
        wintypes.HANDLE(file_handle),
        ctypes.byref(io_status),
        information_buffer,
        len(information_buffer),
        _WIN_FILE_RENAME_INFORMATION_CLASS,
    )
    if status < 0:
        raise ValueError


def _windows_delete_owned(file_handle: int) -> None:
    information = _WinFileDispositionInformation(True)
    io_status = _WinIoStatusBlock()
    status = _WIN_NT_SET_INFORMATION(
        wintypes.HANDLE(file_handle),
        ctypes.byref(io_status),
        ctypes.byref(information),
        ctypes.sizeof(information),
        _WIN_FILE_DISPOSITION_INFORMATION_CLASS,
    )
    if status < 0:
        raise ValueError


def _windows_close_opened_files(
    opened_files: dict[str, _WindowsOpenedFile],
) -> None:
    for opened in opened_files.values():
        try:
            os.close(opened.descriptor)
        except OSError:
            pass


def _windows_open_response_tree(root: Path) -> dict[str, _WindowsOpenedFile]:
    opened_files: dict[str, _WindowsOpenedFile] = {}
    identities: set[tuple[int, bytes]] = set()
    pending_directories: list[
        tuple[
            int,
            Path,
            tuple[str, ...],
            tuple[tuple[str, int], ...] | None,
            int,
        ]
    ] = []
    root_handle = 0
    successful = False
    try:
        root_handle = _windows_open_root(root)
        pending_directories.append((root_handle, root, (), None, 0))
        root_handle = 0

        while pending_directories:
            (
                directory_handle,
                directory_path,
                relative_parts,
                entries,
                entry_index,
            ) = pending_directories[-1]
            if entries is None:
                _before_directory_scan(directory_path)
                _windows_require_path_matches_handle(
                    directory_path, directory_handle, directory=True
                )
                entries = tuple(
                    sorted(
                        _windows_directory_entries(directory_handle),
                        key=lambda item: item[0],
                    )
                )
                pending_directories[-1] = (
                    directory_handle,
                    directory_path,
                    relative_parts,
                    entries,
                    0,
                )
                continue

            if entry_index == len(entries):
                _windows_close_handle(directory_handle)
                pending_directories.pop()
                continue

            name, enumerated_attributes = entries[entry_index]
            pending_directories[-1] = (
                directory_handle,
                directory_path,
                relative_parts,
                entries,
                entry_index + 1,
            )
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
                _after_windows_file_precheck_before_relative_open(
                    directory_path, name
                )

            child_handle = _windows_open_relative(directory_handle, name)
            descriptor = -1
            try:
                _after_windows_relative_open(directory_path, name)
                attributes, identity, size = _windows_handle_info(child_handle)
                if (
                    attributes & _WIN_FILE_ATTRIBUTE_REPARSE_POINT
                    or bool(attributes & _WIN_FILE_ATTRIBUTE_DIRECTORY)
                    != is_directory
                ):
                    raise ValueError
                _windows_require_path_matches_handle(
                    child_path, child_handle, directory=is_directory
                )
                child_parts = (*relative_parts, name)
                if is_directory:
                    pending_directories.append(
                        (child_handle, child_path, child_parts, None, 0)
                    )
                    child_handle = 0
                else:
                    relative_path = "/".join(child_parts)
                    if relative_path in opened_files or identity in identities:
                        raise ValueError
                    identities.add(identity)
                    descriptor = msvcrt.open_osfhandle(
                        child_handle, os.O_RDONLY | OPEN_BINARY
                    )
                    child_handle = 0
                    opened_files[relative_path] = _WindowsOpenedFile(
                        descriptor, identity, size
                    )
                    descriptor = -1
            finally:
                if descriptor >= 0:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass
                _windows_close_handle(child_handle)

        successful = True
        return opened_files
    except Exception:
        raise ValueError("invalid response files") from None
    finally:
        _windows_close_handle(root_handle)
        for directory_handle, _, _, _, _ in reversed(pending_directories):
            _windows_close_handle(directory_handle)
        if not successful:
            _windows_close_opened_files(opened_files)


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
    opened: dict[str, _WindowsOpenedFile] = {}
    confirmed: dict[str, _WindowsOpenedFile] = {}
    transferred = False
    try:
        opened = _windows_open_response_tree(root)
        if set(opened) != expected_paths:
            raise ValueError
        confirmed = _windows_open_response_tree(root)
        if not _windows_same_opened_tree(opened, confirmed):
            raise ValueError
        transferred = True
        return opened
    except Exception:
        raise ValueError("invalid response files") from None
    finally:
        _windows_close_opened_files(confirmed)
        if not transferred:
            _windows_close_opened_files(opened)


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
    plan: dict,
    index: dict,
    responses_root: Path,
    *,
    forbidden_identities: frozenset[tuple[int, int]] = frozenset(),
    allow_incomplete_prefix: bool = False,
) -> tuple[dict, ...]:
    """Load verified UTF-8 text once, without retaining paths or raw response bytes."""
    try:
        errors = validate_response_index(index, plan)
    except IncompleteBenchmark:
        if not allow_incomplete_prefix:
            raise
        errors = []
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

        planned_prefix = plan["cells"][: len(index["records"])]
        for planned, record, file_descriptor in zip(
            planned_prefix, index["records"], ordered_descriptors, strict=True
        ):
            if _identity(os.fstat(file_descriptor)) in forbidden_identities:
                raise ValueError
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


def validate_response_prefix_evidence(
    plan: dict,
    index: dict,
    responses_root: Path,
    *,
    forbidden_identities: frozenset[tuple[int, int]] = frozenset(),
) -> IncompleteBenchmark:
    """Validate physical prefix evidence without scoring any response text."""
    try:
        validate_response_index(index, plan)
    except IncompleteBenchmark as incomplete:
        load_response_cells(
            plan,
            index,
            responses_root,
            forbidden_identities=forbidden_identities,
            allow_incomplete_prefix=True,
        )
        return incomplete
    raise ValueError("response evidence is not an incomplete canonical prefix")


def classify_direction(
    overall_difference: Fraction,
    improved: int,
    worsened: int,
    control_forbidden: int,
    intervention_forbidden: int,
    depth_differences: tuple[Fraction, ...],
) -> str:
    """Apply the predeclared exact direction rule with negative precedence."""
    negative = (
        overall_difference < 0
        or intervention_forbidden > control_forbidden
        or any(difference < 0 for difference in depth_differences)
    )
    positive = (
        overall_difference >= Fraction(1, 5)
        and improved > worsened
        and intervention_forbidden == 0
        and all(difference >= 0 for difference in depth_differences)
    )
    return (
        "negative-signal"
        if negative
        else "positive-signal"
        if positive
        else "mixed-or-null"
    )


def _six_decimal(value: Fraction) -> float:
    return float(f"{float(value):.6f}")


def _empty_pair_counts() -> dict[str, int]:
    return {"both_fail": 0, "both_pass": 0, "improved": 0, "worsened": 0}


def _pair_outcome(control_passed: bool, intervention_passed: bool) -> str:
    if control_passed and intervention_passed:
        return "both_pass"
    if control_passed:
        return "worsened"
    if intervention_passed:
        return "improved"
    return "both_fail"


def _stability(pass_count: int, repeats: int) -> str:
    if pass_count == repeats:
        return "stable-pass"
    if pass_count == 0:
        return "stable-fail"
    return "variable"


def _summed_counts(rows: list[dict], field: str, keys: frozenset[str]) -> dict:
    return {key: sum(row[field][key] for row in rows) for key in sorted(keys)}


def _aggregate_case_results(
    case_results: list[dict],
) -> tuple[dict, dict, dict, list[dict], str]:
    pairs = sum(sum(row["paired_counts"].values()) for row in case_results)
    control_passes = sum(row["control_passes"] for row in case_results)
    intervention_passes = sum(row["intervention_passes"] for row in case_results)
    overall_difference = Fraction(intervention_passes - control_passes, pairs)
    paired_counts = _summed_counts(case_results, "paired_counts", PAIR_COUNT_KEYS)
    forbidden_violations = _summed_counts(
        case_results, "forbidden_violations", FORBIDDEN_COUNT_KEYS
    )
    exact_depth_results = []
    depth_differences: list[Fraction] = []
    for output_depth in sorted({row["output_depth"] for row in case_results}):
        depth_rows = [
            row for row in case_results if row["output_depth"] == output_depth
        ]
        depth_pairs = sum(sum(row["paired_counts"].values()) for row in depth_rows)
        depth_control = sum(row["control_passes"] for row in depth_rows)
        depth_intervention = sum(row["intervention_passes"] for row in depth_rows)
        depth_difference = Fraction(depth_intervention - depth_control, depth_pairs)
        depth_differences.append(depth_difference)
        exact_depth_results.append(
            (
                output_depth,
                depth_rows,
                depth_pairs,
                depth_control,
                depth_intervention,
                depth_difference,
            )
        )
    direction = classify_direction(
        overall_difference,
        paired_counts["improved"],
        paired_counts["worsened"],
        forbidden_violations["control"],
        forbidden_violations["intervention"],
        tuple(depth_differences),
    )

    overall = {
        "control_passes": control_passes,
        "control_pass_rate": _six_decimal(Fraction(control_passes, pairs)),
        "difference": _six_decimal(overall_difference),
        "intervention_passes": intervention_passes,
        "intervention_pass_rate": _six_decimal(
            Fraction(intervention_passes, pairs)
        ),
        "pairs": pairs,
    }
    output_depth_results = []
    for (
        output_depth,
        depth_rows,
        depth_pairs,
        depth_control,
        depth_intervention,
        depth_difference,
    ) in exact_depth_results:
        output_depth_results.append(
            {
                "case_count": len(depth_rows),
                "control_passes": depth_control,
                "control_pass_rate": _six_decimal(
                    Fraction(depth_control, depth_pairs)
                ),
                "difference": _six_decimal(depth_difference),
                "forbidden_violations": _summed_counts(
                    depth_rows, "forbidden_violations", FORBIDDEN_COUNT_KEYS
                ),
                "intervention_passes": depth_intervention,
                "intervention_pass_rate": _six_decimal(
                    Fraction(depth_intervention, depth_pairs)
                ),
                "output_depth": output_depth,
                "paired_counts": _summed_counts(
                    depth_rows, "paired_counts", PAIR_COUNT_KEYS
                ),
                "pairs": depth_pairs,
            }
        )
    return (
        overall,
        paired_counts,
        forbidden_violations,
        output_depth_results,
        direction,
    )


def _case_results_from_facts(
    plan: dict,
    cases: dict[str, dict],
    facts_by_pair: dict[tuple[str, int], dict[str, dict]],
) -> list[dict]:
    results: list[dict] = []
    for case_id in plan["case_ids"]:
        paired_counts = _empty_pair_counts()
        control_passes = 0
        intervention_passes = 0
        forbidden = {"control": 0, "intervention": 0}
        for repeat in range(1, plan["repeats"] + 1):
            pair = facts_by_pair[(case_id, repeat)]
            control = pair["control"]
            intervention = pair["intervention"]
            paired_counts[
                _pair_outcome(control["passed"], intervention["passed"])
            ] += 1
            control_passes += int(control["passed"])
            intervention_passes += int(intervention["passed"])
            forbidden["control"] += control["forbidden_violations"]
            forbidden["intervention"] += intervention["forbidden_violations"]
        results.append(
            {
                "case_id": case_id,
                "control_passes": control_passes,
                "forbidden_violations": forbidden,
                "intervention_passes": intervention_passes,
                "output_depth": cases[case_id]["output_depth"],
                "paired_counts": paired_counts,
                "stability": {
                    "control": _stability(control_passes, plan["repeats"]),
                    "intervention": _stability(
                        intervention_passes, plan["repeats"]
                    ),
                },
            }
        )
    return results


def evaluate_benchmark(
    plan: dict, cells: tuple[dict, ...], execution_attestation: dict
) -> dict:
    """Evaluate every verified response exactly once and return aggregate-only facts."""
    if validate_benchmark_plan(plan):
        raise ValueError("invalid benchmark plan")
    if _execution_attestation_errors(execution_attestation, plan):
        raise ValueError("invalid execution attestation")
    if not isinstance(cells, tuple) or len(cells) != len(plan["cells"]):
        raise ValueError("invalid response cells")

    catalog, rubric = load_catalog(
        ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml"
    )
    cases = {case["id"]: case for case in catalog["cases"]}
    if list(cases) != plan["case_ids"]:
        raise ValueError("invalid benchmark catalog binding")

    facts_by_pair: dict[tuple[str, int], dict[str, dict]] = {}
    for planned, cell in zip(plan["cells"], cells, strict=True):
        if (
            not isinstance(cell, dict)
            or set(cell)
            != {"case_id", "condition", "repeat", "sequence", "text"}
            or any(cell[key] != planned[key] for key in planned)
            or not isinstance(cell["text"], str)
        ):
            raise ValueError("invalid response cells")
        evaluation = evaluate_response(
            cases[cell["case_id"]], rubric, cell["text"]
        )
        failed_forbidden = sum(
            not result.passed
            for result in evaluation.results
            if result.rule.startswith(("forbidden:", "forbidden-section:"))
        )
        fact = {
            "case_id": cell["case_id"],
            "condition": cell["condition"],
            "forbidden_violations": failed_forbidden,
            "passed": evaluation.passed,
            "repeat": cell["repeat"],
        }
        pair_key = (fact["case_id"], fact["repeat"])
        pair = facts_by_pair.setdefault(pair_key, {})
        if fact["condition"] in pair:
            raise ValueError("invalid response cells")
        pair[fact["condition"]] = fact

    expected_pairs = {
        (case_id, repeat)
        for case_id in plan["case_ids"]
        for repeat in range(1, plan["repeats"] + 1)
    }
    if set(facts_by_pair) != expected_pairs or any(
        set(pair) != {"control", "intervention"}
        for pair in facts_by_pair.values()
    ):
        raise ValueError("invalid response cells")

    case_results = _case_results_from_facts(plan, cases, facts_by_pair)
    (
        overall,
        paired_counts,
        forbidden_violations,
        output_depth_results,
        direction,
    ) = _aggregate_case_results(case_results)
    attestation_projection = deepcopy(execution_attestation)
    attestation_projection["assertion_basis"] = "externally-asserted"
    summary = {
        "benchmark_id": plan["benchmark_id"],
        "case_results": case_results,
        "catalog_sha256": plan["catalog_sha256"],
        "cell_counts": {"expected": len(plan["cells"]), "observed": len(cells)},
        "claim_boundaries": list(CLAIM_BOUNDARIES),
        "direction": direction,
        "execution_attestation": attestation_projection,
        "forbidden_violations": forbidden_violations,
        "model": deepcopy(plan["model"]),
        "output_depth_results": output_depth_results,
        "overall": overall,
        "paired_counts": paired_counts,
        "plan_sha256": hashlib.sha256(canonical_json_bytes(plan)).hexdigest(),
        "repeats": plan["repeats"],
        "rubric_sha256": plan["rubric_sha256"],
        "schema_version": "1",
        "skill": deepcopy(plan["skill"]),
        "status": "benchmark-observed",
        "synthetic_example": False,
    }
    if validate_benchmark_summary(summary):
        raise ValueError("invalid benchmark summary")
    return summary


def _nonnegative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _closed_nonnegative_counts(
    value: object, keys: frozenset[str], label: str, errors: list[str]
) -> bool:
    if not _exact_keys(value, keys, label, errors):
        return False
    assert isinstance(value, dict)
    if not all(_nonnegative_integer(value[key]) for key in keys):
        errors.append(f"{label}: counts must be nonnegative integers")
        return False
    return True


def _aggregate_shape(
    value: object, keys: frozenset[str], label: str, errors: list[str]
) -> bool:
    if not _exact_keys(value, keys, label, errors):
        return False
    assert isinstance(value, dict)
    integer_keys = {
        "case_count",
        "control_passes",
        "intervention_passes",
        "pairs",
    } & keys
    rate_keys = {
        "control_pass_rate",
        "difference",
        "intervention_pass_rate",
    } & keys
    if not all(_nonnegative_integer(value[key]) for key in integer_keys):
        errors.append(f"{label}: aggregate counts must be nonnegative integers")
        return False
    if not all(type(value[key]) is float for key in rate_keys):
        errors.append(f"{label}: rates and differences must be JSON decimals")
        return False
    if "output_depth" in keys and not isinstance(value["output_depth"], str):
        errors.append(f"{label}: output depth must be text")
        return False
    if "paired_counts" in keys and not _closed_nonnegative_counts(
        value["paired_counts"], PAIR_COUNT_KEYS, f"{label} paired counts", errors
    ):
        return False
    if "forbidden_violations" in keys and not _closed_nonnegative_counts(
        value["forbidden_violations"],
        FORBIDDEN_COUNT_KEYS,
        f"{label} forbidden violations",
        errors,
    ):
        return False
    return True


def validate_benchmark_summary(
    payload: object, *, allow_synthetic: bool = False
) -> list[str]:
    """Validate a closed summary and recompute every aggregate and direction."""
    errors: list[str] = []
    if not _exact_keys(payload, SUMMARY_KEYS, "benchmark summary", errors):
        return errors
    assert isinstance(payload, dict)
    if payload["schema_version"] != "1":
        errors.append("benchmark summary: unsupported schema version")
    if payload["status"] != "benchmark-observed":
        errors.append("benchmark summary: invalid status")
    if (
        not isinstance(payload["benchmark_id"], str)
        or SAFE_BENCHMARK_ID.fullmatch(payload["benchmark_id"]) is None
    ):
        errors.append("benchmark summary: invalid benchmark ID")
    repeats_valid = _nonnegative_integer(payload["repeats"]) and payload[
        "repeats"
    ] == 3
    if not repeats_valid:
        errors.append("benchmark summary: repeats must be exactly 3")
    synthetic_example = payload["synthetic_example"]
    if type(synthetic_example) is not bool:
        errors.append("benchmark summary: synthetic_example must be a boolean")
    elif synthetic_example and not allow_synthetic:
        errors.append("benchmark summary: synthetic examples require explicit opt-in")
    for key in ("plan_sha256", "catalog_sha256", "rubric_sha256"):
        if not _is_sha256(payload[key]):
            errors.append(f"benchmark summary: invalid {key}")
    if payload["claim_boundaries"] != CLAIM_BOUNDARIES:
        errors.append("benchmark summary: invalid claim boundaries")

    _exact_keys(payload["model"], MODEL_KEYS, "summary model", errors)
    if isinstance(payload["model"], dict) and set(payload["model"]) == MODEL_KEYS:
        model = payload["model"]
        if not all(
            _valid_identifier(model[key])
            for key in ("id", "provider", "seed_policy", "snapshot")
        ):
            errors.append("summary model: invalid identities")
        if not _nonnegative_integer(model["max_output_tokens"]):
            errors.append("summary model: invalid output limit")
        if any(
            isinstance(model[key], bool) or not isinstance(model[key], (int, float))
            or not math.isfinite(model[key])
            for key in ("temperature", "top_p")
        ):
            errors.append("summary model: invalid numeric settings")
    _exact_keys(payload["skill"], BINDING_KEYS, "summary Skill binding", errors)
    if isinstance(payload["skill"], dict) and set(payload["skill"]) == BINDING_KEYS:
        if not _valid_binding(payload["skill"]):
            errors.append("summary Skill binding: invalid public binding")

    attestation = payload["execution_attestation"]
    if _exact_keys(
        attestation,
        SUMMARY_ATTESTATION_KEYS,
        "summary execution attestation",
        errors,
    ):
        assert isinstance(attestation, dict)
        if attestation["assertion_basis"] != "externally-asserted":
            errors.append("summary execution attestation: invalid assertion basis")
        if _aware_datetime(attestation["completed_at"]) is None:
            errors.append("summary execution attestation: invalid completion time")
        for key in ATTESTATION_BOOLEAN_KEYS:
            if attestation[key] is not True:
                errors.append(f"summary execution attestation: {key} must be true")
        if isinstance(payload["model"], dict):
            identities = {
                "model_provider": payload["model"].get("provider"),
                "model_id": payload["model"].get("id"),
                "model_snapshot": payload["model"].get("snapshot"),
            }
            for key, expected in identities.items():
                if attestation[key] != expected:
                    errors.append(
                        f"summary execution attestation: {key} mismatch"
                    )
        for key in ("runner_name", "runner_version"):
            if not _valid_identifier(attestation[key]):
                errors.append(f"summary execution attestation: invalid {key}")

    try:
        catalog, _ = load_catalog(
            ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml"
        )
    except (OSError, ValueError):
        return [*errors, "benchmark summary: unavailable evaluation catalog"]
    expected_cases = catalog["cases"]
    if payload["catalog_sha256"] != hashlib.sha256(
        (ROOT / "evals/cases.yaml").read_bytes()
    ).hexdigest():
        errors.append("benchmark summary: catalog digest mismatch")
    if payload["rubric_sha256"] != hashlib.sha256(
        (ROOT / "evals/rubric.yaml").read_bytes()
    ).hexdigest():
        errors.append("benchmark summary: rubric digest mismatch")

    case_results = payload["case_results"]
    case_results_valid = (
        repeats_valid
        and isinstance(case_results, list)
        and len(case_results) == len(expected_cases)
    )
    if not case_results_valid:
        errors.append("benchmark summary: incomplete case results")
    else:
        for index, (row, case) in enumerate(
            zip(case_results, expected_cases, strict=True)
        ):
            label = f"case result {index}"
            if not _exact_keys(row, CASE_RESULT_KEYS, label, errors):
                case_results_valid = False
                continue
            assert isinstance(row, dict)
            if (
                row["case_id"] != case["id"]
                or row["output_depth"] != case["output_depth"]
            ):
                errors.append(f"{label}: catalog binding mismatch")
                case_results_valid = False
            if not all(
                _nonnegative_integer(row[key])
                and row[key] <= payload["repeats"]
                for key in ("control_passes", "intervention_passes")
            ):
                errors.append(f"{label}: invalid pass counts")
                case_results_valid = False
            paired_valid = _closed_nonnegative_counts(
                row["paired_counts"], PAIR_COUNT_KEYS, f"{label} paired counts", errors
            )
            forbidden_valid = _closed_nonnegative_counts(
                row["forbidden_violations"],
                FORBIDDEN_COUNT_KEYS,
                f"{label} forbidden violations",
                errors,
            )
            stability_valid = _exact_keys(
                row["stability"], STABILITY_KEYS, f"{label} stability", errors
            )
            if not (paired_valid and forbidden_valid and stability_valid):
                case_results_valid = False
                continue
            pairs = row["paired_counts"]
            if sum(pairs.values()) != payload["repeats"]:
                errors.append(f"{label}: paired counts do not equal repeats")
                case_results_valid = False
            if row["control_passes"] != pairs["both_pass"] + pairs["worsened"]:
                errors.append(f"{label}: control pass count is not paired-recomputable")
                case_results_valid = False
            if (
                row["intervention_passes"]
                != pairs["both_pass"] + pairs["improved"]
            ):
                errors.append(
                    f"{label}: intervention pass count is not paired-recomputable"
                )
                case_results_valid = False
            assert isinstance(row["stability"], dict)
            expected_stability = {
                "control": _stability(row["control_passes"], payload["repeats"]),
                "intervention": _stability(
                    row["intervention_passes"], payload["repeats"]
                ),
            }
            if row["stability"] != expected_stability:
                errors.append(f"{label}: stability mismatch")
                case_results_valid = False

    _aggregate_shape(payload["overall"], OVERALL_KEYS, "summary overall", errors)
    _closed_nonnegative_counts(
        payload["paired_counts"], PAIR_COUNT_KEYS, "summary paired counts", errors
    )
    _closed_nonnegative_counts(
        payload["forbidden_violations"],
        FORBIDDEN_COUNT_KEYS,
        "summary forbidden violations",
        errors,
    )
    depth_results = payload["output_depth_results"]
    if not isinstance(depth_results, list):
        errors.append("benchmark summary: output depth results must be a list")
    else:
        for index, row in enumerate(depth_results):
            _aggregate_shape(
                row, DEPTH_RESULT_KEYS, f"output depth result {index}", errors
            )

    if case_results_valid:
        (
            expected_overall,
            expected_paired,
            expected_forbidden,
            expected_depths,
            expected_direction,
        ) = _aggregate_case_results(case_results)
        if payload["overall"] != expected_overall:
            errors.append("benchmark summary: overall aggregate mismatch")
        if payload["paired_counts"] != expected_paired:
            errors.append("benchmark summary: paired aggregate mismatch")
        if payload["forbidden_violations"] != expected_forbidden:
            errors.append("benchmark summary: forbidden aggregate mismatch")
        if payload["output_depth_results"] != expected_depths:
            errors.append("benchmark summary: output depth aggregate mismatch")
        if payload["direction"] != expected_direction:
            errors.append("benchmark summary: direction mismatch")
        expected_cells = payload["repeats"] * len(case_results) * 2
        if payload["cell_counts"] != {
            "expected": expected_cells,
            "observed": expected_cells,
        }:
            errors.append("benchmark summary: cell counts mismatch")
    if not isinstance(payload["cell_counts"], dict) or set(payload["cell_counts"]) != {
        "expected",
        "observed",
    }:
        errors.append("benchmark summary: cell counts require exact keys")
    if not isinstance(payload["direction"], str) or payload["direction"] not in {
        "positive-signal",
        "mixed-or-null",
        "negative-signal",
    }:
        errors.append("benchmark summary: invalid direction")
    return errors


def canonical_summary_bytes(summary: dict) -> bytes:
    """Return canonical bytes only for a closed, internally recomputable summary."""
    if validate_benchmark_summary(summary):
        raise ValueError("invalid benchmark summary")
    return canonical_json_bytes(summary)


class _SafeArgumentParser(argparse.ArgumentParser):
    """Reject every parser branch with the fixed public error shape."""

    def error(self, message: str) -> None:
        self.exit(2)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if status == 2:
            _failure()
            raise SystemExit(status)
        super().exit(status, message)


def _argument_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        description=__doc__, allow_abbrev=False, add_help=False
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--response-index", type=Path, required=True)
    parser.add_argument("--responses-dir", type=Path, required=True)
    parser.add_argument("--output-summary", type=Path, required=True)
    return parser


def _absolute_path(path: Path) -> Path:
    """Normalize spelling without following a filesystem redirect."""
    return Path(os.path.abspath(os.fspath(path)))


def _require_link_free_chain(path: Path) -> None:
    current = path
    while True:
        current_stat = current.lstat()
        if _is_reparse_or_symlink(current_stat):
            raise ValueError("unsafe path")
        parent = current.parent
        if parent == current:
            return
        current = parent


def _open_external_regular(path: Path) -> tuple[Path, int, os.stat_result]:
    absolute = _absolute_path(path)
    _require_link_free_chain(absolute)
    resolved = ensure_external_path(absolute, ROOT)
    initial = absolute.lstat()
    if not stat.S_ISREG(initial.st_mode):
        raise ValueError("input must be a regular file")
    descriptor = os.open(absolute, os.O_RDONLY | OPEN_BINARY | OPEN_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or _identity(opened) != _identity(initial):
            raise ValueError("input identity changed")
        return resolved, descriptor, opened
    except Exception:
        os.close(descriptor)
        raise


def _external_directory(path: Path) -> tuple[Path, os.stat_result]:
    absolute = _absolute_path(path)
    _require_link_free_chain(absolute)
    resolved = ensure_external_path(absolute, ROOT)
    directory_stat = absolute.lstat()
    if not stat.S_ISDIR(directory_stat.st_mode):
        raise ValueError("responses path must be a directory")
    return resolved, directory_stat


def _safe_external_output(
    path: Path, responses_root: Path
) -> tuple[Path, os.stat_result, os.stat_result | None]:
    absolute = _absolute_path(path)
    _require_link_free_chain(absolute.parent)
    parent_stat = absolute.parent.lstat()
    if not stat.S_ISDIR(parent_stat.st_mode):
        raise ValueError("output parent must be a directory")
    output = ensure_external_path(absolute, ROOT)
    if output == responses_root or output.is_relative_to(responses_root):
        raise ValueError("output overlaps response inputs")
    try:
        output_stat = absolute.lstat()
    except FileNotFoundError:
        output_stat = None
    else:
        if (
            _is_reparse_or_symlink(output_stat)
            or not stat.S_ISREG(output_stat.st_mode)
            or output_stat.st_nlink != 1
        ):
            raise ValueError("output must be a regular file")
    return output, parent_stat, output_stat


def _read_stable_json(
    descriptor: int, path: Path, opened: os.stat_result
) -> object:
    raw = _read_descriptor(descriptor)
    confirmed = os.fstat(descriptor)
    current = path.lstat()
    if (
        _identity(confirmed) != _identity(opened)
        or _identity(current) != _identity(opened)
        or confirmed.st_size != opened.st_size
        or current.st_size != opened.st_size
    ):
        raise ValueError("input identity changed")

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
        result: dict = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    return json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("non-finite JSON value")
        ),
    )


def _same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return _identity(left) == _identity(right)


def _before_summary_commit(
    parent: Path, stage_name: str, output_name: str
) -> None:
    """Narrow race-injection seam before the identity-bound commit."""


def _before_summary_finish(
    parent: Path, stage_name: str, output_name: str
) -> None:
    """Narrow drift-injection seam after commit and before cleanup."""


def _close_summary_reference(reference: int) -> None:
    if os.name == "nt":
        value = _windows_handle_number(reference)
        if not _WIN_CLOSE_HANDLE(wintypes.HANDLE(value)):
            raise OSError("summary handle close failed")
        return
    os.close(reference)


def _close_summary_backup_owner(reference: int) -> None:
    _close_summary_reference(reference)


def _close_summary_stage_owner(reference: int) -> None:
    _close_summary_reference(reference)


def _close_summary_parent_reference(reference: int) -> None:
    _close_summary_reference(reference)


class _SummaryTransaction:
    """Own one parent, stage, and optional prior output through commit/rollback."""

    def __init__(
        self,
        output: Path,
        parent_stat: os.stat_result,
        output_stat: os.stat_result | None,
    ) -> None:
        self.parent_path = output.parent
        self.output_name = output.name
        self.parent_stat = parent_stat
        self.output_stat = output_stat
        self.parent_reference = 0
        self.stage_name: str | None = None
        self.stage_owner = 0
        self.backup_name: str | None = None
        self.backup_owner = 0
        self.committed = False
        if os.name == "nt":
            self.parent_reference = _windows_open_absolute(
                self.parent_path, list_directory=True
            )
            _, parent_identity, _ = _windows_handle_info(self.parent_reference)
            if not _windows_identities_match(
                _windows_stat_identity(parent_stat), parent_identity
            ):
                self.close()
                raise ValueError("output parent identity changed")
        else:
            self.parent_reference = os.open(
                self.parent_path, os.O_RDONLY | OPEN_DIRECTORY | OPEN_NOFOLLOW
            )
            if _identity(os.fstat(self.parent_reference)) != _identity(parent_stat):
                self.close()
                raise ValueError("output parent identity changed")

    def _require_parent_current(self) -> None:
        current = self.parent_path.lstat()
        if _is_reparse_or_symlink(current) or not stat.S_ISDIR(current.st_mode):
            raise ValueError("output parent changed")
        if os.name == "nt":
            _, held_identity, _ = _windows_handle_info(self.parent_reference)
            if (
                not _windows_identities_match(
                    _windows_stat_identity(self.parent_stat), held_identity
                )
                or not _windows_identities_match(
                    _windows_stat_identity(current), held_identity
                )
            ):
                raise ValueError("output parent changed")
        elif (
            _identity(os.fstat(self.parent_reference)) != _identity(self.parent_stat)
            or _identity(current) != _identity(self.parent_stat)
        ):
            raise ValueError("output parent changed")

    def _entry_identity(self, name: str) -> tuple[int, object] | None:
        if os.name == "nt":
            entries = dict(_windows_directory_entries(self.parent_reference))
            if name not in entries:
                return None
            handle = _windows_open_owned_file(self.parent_reference, name)
            try:
                attributes, identity, _ = _windows_handle_info(handle)
                if attributes & (
                    _WIN_FILE_ATTRIBUTE_DIRECTORY | _WIN_FILE_ATTRIBUTE_REPARSE_POINT
                ):
                    raise ValueError("unsafe transaction entry")
                return identity
            finally:
                _windows_close_handle(handle)
        try:
            current = os.stat(
                name,
                dir_fd=self.parent_reference,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return None
        if _is_reparse_or_symlink(current) or not stat.S_ISREG(current.st_mode):
            raise ValueError("unsafe transaction entry")
        return _identity(current)

    def _owner_identity(self, owner: int) -> tuple[int, object]:
        if os.name == "nt":
            attributes, identity, _ = _windows_handle_info(owner)
            if attributes & (
                _WIN_FILE_ATTRIBUTE_DIRECTORY | _WIN_FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ValueError("unsafe owned transaction file")
            return identity
        opened = os.fstat(owner)
        if not stat.S_ISREG(opened.st_mode):
            raise ValueError("unsafe owned transaction file")
        return _identity(opened)

    def _unique_name(self, label: str) -> str:
        for _ in range(128):
            candidate = f".{self.output_name}.{label}-{secrets.token_hex(16)}.tmp"
            if self._entry_identity(candidate) is None:
                return candidate
        raise ValueError("unable to allocate transaction name")

    def _open_existing_owner(self, name: str) -> int:
        if os.name == "nt":
            return _windows_open_owned_file(self.parent_reference, name)
        flags = getattr(os, "O_PATH", os.O_RDONLY) | OPEN_NOFOLLOW
        return os.open(name, flags, dir_fd=self.parent_reference)

    def _rename_owned(
        self, owner: int, source_name: str, destination_name: str, *, replace: bool
    ) -> None:
        if os.name == "nt":
            _windows_rename_owned(
                owner,
                self.parent_reference,
                destination_name,
                replace=replace,
            )
            return
        if not replace and self._entry_identity(destination_name) is not None:
            raise ValueError("transaction destination exists")
        if self._entry_identity(source_name) != self._owner_identity(owner):
            raise ValueError("transaction source identity changed")
        os.replace(
            source_name,
            destination_name,
            src_dir_fd=self.parent_reference,
            dst_dir_fd=self.parent_reference,
        )

    def _create_stage(self) -> int:
        assert self.stage_name is not None
        if os.name == "nt":
            self.stage_owner = _windows_create_owned_file(
                self.parent_reference, self.stage_name
            )
            writer_handle = _windows_open_stage_writer(
                self.parent_reference, self.stage_name
            )
            try:
                return msvcrt.open_osfhandle(
                    writer_handle, os.O_WRONLY | OPEN_BINARY
                )
            except Exception:
                _windows_close_handle(writer_handle)
                raise
        self.stage_owner = os.open(
            self.stage_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | OPEN_NOFOLLOW | OPEN_BINARY,
            0o600,
            dir_fd=self.parent_reference,
        )
        return os.dup(self.stage_owner)

    def prepare(self, payload: bytes) -> None:
        self._require_parent_current()
        current_output = self._entry_identity(self.output_name)
        if self.output_stat is None:
            if current_output is not None:
                raise ValueError("output appeared before transaction")
        else:
            expected_identity: tuple[int, object]
            if os.name == "nt":
                expected_identity = _windows_stat_identity(self.output_stat)
            else:
                expected_identity = _identity(self.output_stat)
            if (
                os.name == "nt"
                and not _windows_identities_match(expected_identity, current_output)
            ) or (os.name != "nt" and current_output != expected_identity):
                raise ValueError("output identity changed")
            self.backup_owner = self._open_existing_owner(self.output_name)
            owner_identity = self._owner_identity(self.backup_owner)
            if (
                os.name == "nt"
                and not _windows_identities_match(expected_identity, owner_identity)
            ) or (os.name != "nt" and owner_identity != expected_identity):
                raise ValueError("output identity changed")
            self.backup_name = self._unique_name("backup")
            self._rename_owned(
                self.backup_owner,
                self.output_name,
                self.backup_name,
                replace=False,
            )

        self.stage_name = self._unique_name("stage")
        writer = self._create_stage()
        with os.fdopen(writer, "wb") as staged_file:
            staged_file.write(payload)
            staged_file.flush()
            os.fsync(staged_file.fileno())
        if self._entry_identity(self.stage_name) != self._owner_identity(
            self.stage_owner
        ):
            raise ValueError("stage identity changed")

    def commit(self) -> None:
        if self.stage_name is None or not self.stage_owner:
            raise ValueError("transaction is not prepared")
        _before_summary_commit(
            self.parent_path, self.stage_name, self.output_name
        )
        self._require_parent_current()
        if self._entry_identity(self.output_name) is not None:
            raise ValueError("output appeared before commit")
        if self._entry_identity(self.stage_name) != self._owner_identity(
            self.stage_owner
        ):
            raise ValueError("stage identity changed before commit")
        self._rename_owned(
            self.stage_owner,
            self.stage_name,
            self.output_name,
            replace=False,
        )
        self.committed = True

    def _cleanup_posix_owner(self, owner: int, name: str) -> None:
        current = os.stat(
            name,
            dir_fd=self.parent_reference,
            follow_symlinks=False,
        )
        if (
            not stat.S_ISREG(current.st_mode)
            or _identity(current) != self._owner_identity(owner)
        ):
            raise ValueError("owned transaction name changed")
        os.unlink(name, dir_fd=self.parent_reference)

    def _delete_owner(self, owner: int, name: str) -> None:
        if os.name == "nt":
            _windows_delete_owned(owner)
        else:
            self._cleanup_posix_owner(owner, name)

    @staticmethod
    def _finalize_reference(reference: int, close_operation) -> None:
        # A Windows close wrapper can raise after CloseHandle already released
        # the object. Never retry or fall back on that raw numeric value: it may
        # already name an unrelated reused handle. Namespace state is settled
        # before this finalizer runs, so a possible process-lifetime leak until
        # CLI exit is safer than a double-close. POSIX close state can likewise
        # be indeterminate after failure, so it uses the same one-attempt edge.
        try:
            close_operation(reference)
        except Exception:
            pass

    def rollback(self) -> None:
        failure = False
        try:
            if self.stage_owner:
                try:
                    stage_name = (
                        self.output_name
                        if self.committed
                        else self.stage_name or ""
                    )
                    self._delete_owner(self.stage_owner, stage_name)
                except Exception:
                    failure = True
                self._finalize_reference(
                    self.stage_owner, _close_summary_stage_owner
                )
                self.stage_owner = 0
            if self.backup_owner:
                try:
                    self._rename_owned(
                        self.backup_owner,
                        self.backup_name or "",
                        self.output_name,
                        replace=True,
                    )
                except Exception:
                    failure = True
                self._finalize_reference(
                    self.backup_owner, _close_summary_backup_owner
                )
                self.backup_owner = 0
        finally:
            self.close()
        if failure:
            raise ValueError("summary rollback failed")

    def finish(self) -> None:
        if not self.committed or self.stage_name is None or not self.stage_owner:
            raise ValueError("transaction is not committed")
        _before_summary_finish(
            self.parent_path, self.stage_name, self.output_name
        )
        self._require_parent_current()
        if self._entry_identity(self.output_name) != self._owner_identity(
            self.stage_owner
        ):
            raise ValueError("committed output identity changed")

        # Backup deletion is the last operation that can still require rollback.
        # Keep every held identity open until it succeeds.
        if self.backup_owner:
            self._delete_owner(self.backup_owner, self.backup_name or "")
            self._finalize_reference(
                self.backup_owner, _close_summary_backup_owner
            )
            self.backup_owner = 0
        self._finalize_reference(self.stage_owner, _close_summary_stage_owner)
        self.stage_owner = 0
        self.close()

    def close(self) -> None:
        if self.parent_reference:
            self._finalize_reference(
                self.parent_reference, _close_summary_parent_reference
            )
            self.parent_reference = 0


def _write_stderr_chunk(payload: bytes) -> int:
    return os.write(sys.stderr.fileno(), payload)


def _failure() -> int:
    try:
        sys.stderr.buffer.flush()
        offset = 0
        while offset < len(CLI_ERROR):
            written = _write_stderr_chunk(CLI_ERROR[offset:])
            if (
                type(written) is not int
                or written <= 0
                or written > len(CLI_ERROR) - offset
            ):
                raise OSError("invalid fixed error write")
            offset += written
        sys.stderr.buffer.flush()
    except Exception:
        pass
    return 2


def _write_stdout(payload: dict) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(payload))
    sys.stdout.buffer.flush()


def _serialize_complete_status() -> bytes:
    serialized = canonical_json_bytes(COMPLETE_STATUS)
    if serialized != COMPLETE_STATUS_BYTES:
        raise ValueError("invalid complete status")
    return serialized


def _flush_stdout_before_status() -> None:
    sys.stdout.buffer.flush()


class _NotificationFailure(Exception):
    """Record only whether fixed notification bytes reached stdout."""

    def __init__(self, bytes_written: int) -> None:
        super().__init__()
        self.bytes_written = bytes_written


def _write_stdout_chunk(payload: bytes) -> int:
    return os.write(sys.stdout.fileno(), payload)


def _write_stdout_all(payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        try:
            written = _write_stdout_chunk(payload[offset:])
            if (
                type(written) is not int
                or written <= 0
                or written > len(payload) - offset
            ):
                raise OSError("invalid fixed status write")
        except Exception:
            raise _NotificationFailure(offset) from None
        offset += written


def _emit_complete_status() -> None:
    try:
        payload = _serialize_complete_status()
        _flush_stdout_before_status()
    except Exception:
        raise _NotificationFailure(0) from None
    _write_stdout_all(payload)


def main(argv: list[str] | None = None) -> int:
    """Evaluate one external response bundle without exposing untrusted content."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if any(arguments.count(flag) != 1 for flag in CLI_FLAGS):
        return _failure()
    try:
        args = _argument_parser().parse_args(arguments)
    except SystemExit:
        raise
    except Exception:
        return _failure()
    transaction: _SummaryTransaction | None = None
    descriptors: list[int] = []
    try:
        plan_path, plan_descriptor, plan_stat = _open_external_regular(args.plan)
        descriptors.append(plan_descriptor)
        index_path, index_descriptor, index_stat = _open_external_regular(
            args.response_index
        )
        descriptors.append(index_descriptor)
        responses_root, responses_stat = _external_directory(args.responses_dir)
        output, output_parent_stat, output_stat = _safe_external_output(
            args.output_summary, responses_root
        )

        if (
            plan_path == index_path
            or _same_identity(plan_stat, index_stat)
            or any(
                path.is_relative_to(responses_root)
                for path in (plan_path, index_path)
            )
            or any(
                output == path for path in (plan_path, index_path, responses_root)
            )
            or output_stat is not None
            and any(
                _same_identity(output_stat, item)
                for item in (plan_stat, index_stat, responses_stat)
            )
        ):
            raise ValueError("aliased benchmark paths")

        plan = _read_stable_json(plan_descriptor, plan_path, plan_stat)
        response_index = _read_stable_json(
            index_descriptor, index_path, index_stat
        )
        if not isinstance(plan, dict) or validate_benchmark_plan(plan):
            raise ValueError("invalid benchmark plan")
        if not isinstance(response_index, dict):
            raise ValueError("invalid response index")
        incomplete: IncompleteBenchmark | None = None
        try:
            index_errors = validate_response_index(response_index, plan)
        except IncompleteBenchmark as caught:
            incomplete = caught
            index_errors = []
        if index_errors:
            raise ValueError("invalid response index")

        forbidden_identities = {_identity(plan_stat), _identity(index_stat)}
        if output_stat is not None:
            forbidden_identities.add(_identity(output_stat))
        if incomplete is not None:
            validated_incomplete = validate_response_prefix_evidence(
                plan,
                response_index,
                responses_root,
                forbidden_identities=frozenset(forbidden_identities),
            )
            if (
                validated_incomplete.expected_count != incomplete.expected_count
                or validated_incomplete.observed_count != incomplete.observed_count
            ):
                raise ValueError("incomplete response counts changed")
            _write_stdout(
                {
                    "expected_count": incomplete.expected_count,
                    "observed_count": incomplete.observed_count,
                    "schema_version": "1",
                    "status": "benchmark-incomplete",
                }
            )
            return 3
        cells = load_response_cells(
            plan,
            response_index,
            responses_root,
            forbidden_identities=frozenset(forbidden_identities),
        )
        summary = evaluate_benchmark(
            plan,
            cells,
            response_index["execution_attestation"],
        )
        if validate_benchmark_summary(summary):
            raise ValueError("invalid benchmark summary")
        serialized = canonical_summary_bytes(summary)
        reparsed = json.loads(
            serialized.decode("utf-8", errors="strict"),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError("non-finite JSON value")
            ),
        )
        if (
            not isinstance(reparsed, dict)
            or validate_benchmark_summary(reparsed)
            or canonical_json_bytes(reparsed) != serialized
        ):
            raise ValueError("invalid canonical benchmark summary")

        for descriptor in descriptors:
            os.close(descriptor)
        descriptors.clear()
        transaction = _SummaryTransaction(
            output, output_parent_stat, output_stat
        )
        transaction.prepare(serialized)
        transaction.commit()
        transaction.finish()
        transaction = None
        try:
            _emit_complete_status()
        except _NotificationFailure as notification_failure:
            if notification_failure.bytes_written:
                return 2
            return _failure()
    except Exception:
        if transaction is not None:
            try:
                transaction.rollback()
            except Exception:
                pass
        return _failure()
    finally:
        for descriptor in descriptors:
            try:
                os.close(descriptor)
            except OSError:
                pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
