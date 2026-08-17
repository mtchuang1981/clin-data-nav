"""Validate externally asserted benchmark responses without provider verification."""

from __future__ import annotations

from datetime import datetime
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys


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


def _external_regular_root(responses_root: Path) -> Path:
    try:
        root_stat = responses_root.lstat()
        if _is_reparse_or_symlink(root_stat) or not stat.S_ISDIR(root_stat.st_mode):
            raise ValueError
        return ensure_external_path(responses_root, ROOT)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("invalid response files") from None


def _scan_regular_files(root: Path) -> dict[str, os.stat_result]:
    observed: dict[str, os.stat_result] = {}
    identities: set[tuple[int, int]] = set()
    pending = [root]
    try:
        while pending:
            directory = pending.pop()
            with os.scandir(directory) as entries:
                for entry in entries:
                    entry_path = Path(entry.path)
                    entry_stat = entry_path.lstat()
                    if _is_reparse_or_symlink(entry_stat):
                        raise ValueError
                    if stat.S_ISDIR(entry_stat.st_mode):
                        pending.append(entry_path)
                    elif stat.S_ISREG(entry_stat.st_mode):
                        relative = entry_path.relative_to(root).as_posix()
                        identity = (entry_stat.st_dev, entry_stat.st_ino)
                        if identity in identities:
                            raise ValueError
                        identities.add(identity)
                        observed[relative] = entry_stat
                    else:
                        raise ValueError
    except (OSError, RuntimeError, ValueError):
        raise ValueError("invalid response files") from None
    return observed


def load_response_cells(
    plan: dict, index: dict, responses_root: Path
) -> tuple[dict, ...]:
    """Load verified UTF-8 text once, without retaining paths or raw response bytes."""
    errors = validate_response_index(index, plan)
    if errors:
        raise ValueError("invalid response index")

    root = _external_regular_root(Path(responses_root))
    observed = _scan_regular_files(root)
    expected_paths = {record["relative_path"] for record in index["records"]}
    if set(observed) != expected_paths:
        raise ValueError("invalid response files")

    cells: list[dict] = []
    try:
        for planned, record in zip(plan["cells"], index["records"], strict=True):
            response_path = root.joinpath(*PurePosixPath(record["relative_path"]).parts)
            current_stat = response_path.lstat()
            if (
                _is_reparse_or_symlink(current_stat)
                or not stat.S_ISREG(current_stat.st_mode)
                or (current_stat.st_dev, current_stat.st_ino)
                != (observed[record["relative_path"]].st_dev, observed[record["relative_path"]].st_ino)
            ):
                raise ValueError
            raw = response_path.read_bytes()
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
    return tuple(cells)
