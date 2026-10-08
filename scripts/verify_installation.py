"""Read-only, bounded manifest-file diagnosis; host loaded version is not verified."""
from __future__ import annotations

import hashlib
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "skills/clin-nav/scripts"))

from bounded_json import parse_strict_json, read_bounded_stream
from scripts.package_contract import canonical_package_bytes, portable_path_key, validate_member_name, manifest_records, hash_stream
from scripts.package_skill import SEMVER
from scripts.install_local import MAX_MANIFEST_BYTES, MAX_MANIFEST_FILE_COUNT, MAX_MEMBER_UNCOMPRESSED_BYTES, MAX_TOTAL_UNCOMPRESSED_BYTES

MAX_FILE_BYTES = MAX_MEMBER_UNCOMPRESSED_BYTES
MAX_TOTAL_BYTES = MAX_TOTAL_UNCOMPRESSED_BYTES
MAX_ENTRIES = 4096
MAX_DEPTH = 32
REPARSE_POINT = 0x400
ERROR = "invalid installation input"


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError(ERROR)


def _digest(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_installation_manifest(payload: object) -> dict[str, dict]:
    """Validate all records and portable conflicts before any installed file opens."""
    try:
        raw = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        parse_strict_json(raw, max_bytes=MAX_MANIFEST_BYTES)
        _require(type(payload) is dict and set(payload) == {"name", "version", "archive", "archive_sha256", "files"})
        version = payload["version"]
        _require(payload["name"] == "clin-nav" and type(version) is str and len(version) <= 80 and SEMVER.fullmatch(version) is not None)
        _require(payload["archive"] == f"clin-nav-{version}.zip" and _digest(payload["archive_sha256"]))
        records = manifest_records(payload, max_records=MAX_MANIFEST_FILE_COUNT)
        _require("SKILL.md" in records)
        portable: set[tuple[str, ...]] = set()
        total = 0
        for name, record in records.items():
            validate_member_name(name, reject_windows_devices=True)
            key = portable_path_key(name)
            _require(key not in portable and record["size"] <= MAX_FILE_BYTES)
            portable.add(key)
            total += record["size"]
        _require(total <= MAX_TOTAL_BYTES)
        _require(all(key[:length] not in portable for key in portable for length in range(1, len(key))))
        return records
    except Exception:
        raise ValueError(ERROR) from None


CLI_ERROR = "installation verification failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)


def main(argv: list[str] | None = None) -> int:
    parser = _SafeArgumentParser(prog="verify_installation", description=__doc__, allow_abbrev=False)
    parser.add_argument("--skill-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--comparison", choices=("bytes", "canonical-text"), default="bytes")
    args = parser.parse_args(argv)
    try:
        summary = verify_installation(args.skill_dir, args.manifest, manifest_sha256=args.manifest_sha256, comparison=args.comparison)
    except Exception:
        sys.stderr.write(CLI_ERROR)
        return 2
    sys.stdout.write(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    return 3 if summary["status"] == "content-differs" else 0


def _plain(info: os.stat_result) -> None:
    _require(not stat.S_ISLNK(info.st_mode) and not (getattr(info, "st_file_attributes", 0) & REPARSE_POINT))


def _signature(info: os.stat_result) -> tuple:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, stat.S_IFMT(info.st_mode)


def _safe_path(path: Path, *, directory: bool) -> Path:
    # Inspect lexical ancestors BEFORE resolve can hide a link/junction.
    absolute = path.absolute()
    for candidate in (absolute, *absolute.parents):
        info = candidate.lstat()
        _plain(info)
        if candidate != absolute:
            _require(stat.S_ISDIR(info.st_mode))
    resolved = absolute.resolve(strict=True)
    info = resolved.lstat()
    _require(stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))
    return resolved


def _same_path(path: Path, expected: os.stat_result) -> None:
    current = path.lstat()
    _plain(current)
    _require(_signature(current) == _signature(expected))


def _stable_read(path: Path, *, limit: int, comparison: str, expected: os.stat_result | None = None) -> tuple[bytes | str, int]:
    _safe_path(path, directory=False)
    before = path.lstat()
    _plain(before)
    _require(stat.S_ISREG(before.st_mode) and 0 <= before.st_size <= limit)
    if expected is not None:
        _require(_signature(before) == _signature(expected))
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        _plain(opened)
        _require(_signature(opened) == _signature(before))
        # SAME descriptor is bounded/read/hashed and checked, never a second open.
        data = hash_stream(stream, max_bytes=limit) if comparison == "bytes" else read_bounded_stream(stream, max_bytes=limit)
        after = os.fstat(stream.fileno())
        _plain(after)
        _require(_signature(after) == _signature(opened))
        _same_path(path, opened)
    return data, before.st_size


def _walk(root: Path) -> tuple[dict[str, tuple[Path, os.stat_result]], dict[Path, os.stat_result]]:
    files: dict[str, tuple[Path, os.stat_result]] = {}
    directories = {root: root.lstat()}
    stack = [(root, 0)]
    count = 0
    portable: set[tuple[str, ...]] = set()
    while stack:
        parent, depth = stack.pop()
        _same_path(parent, directories[parent])
        with os.scandir(parent) as entries:
            for entry in entries:
                count += 1
                _require(count <= MAX_ENTRIES and depth + 1 <= MAX_DEPTH)
                path = Path(entry.path)
                info = path.lstat()
                _plain(info)
                name = path.relative_to(root).as_posix()
                validate_member_name(name, reject_windows_devices=True)
                key = portable_path_key(name)
                _require(key not in portable)
                portable.add(key)
                if stat.S_ISDIR(info.st_mode):
                    directories[path] = info
                    stack.append((path, depth + 1))
                else:
                    _require(stat.S_ISREG(info.st_mode))
                    files[name] = path, info
        _same_path(parent, directories[parent])
    return files, directories


def verify_installation(skill_dir: Path, manifest_path: Path, *, manifest_sha256: str, comparison: str = "bytes") -> dict:
    """Compare one selected tree. Best-effort change detection, not an atomic snapshot."""
    try:
        _require(_digest(manifest_sha256) and type(comparison) is str and comparison in {"bytes", "canonical-text"})
        root = _safe_path(skill_dir, directory=True)
        manifest = _safe_path(manifest_path, directory=False)
        _require(not manifest.is_relative_to(root) and not manifest.is_relative_to(ROOT))
        raw, _ = _stable_read(manifest, limit=MAX_MANIFEST_BYTES, comparison="raw")
        _require(hashlib.sha256(raw).hexdigest() == manifest_sha256)
        payload = parse_strict_json(raw, max_bytes=MAX_MANIFEST_BYTES)
        records = validate_installation_manifest(payload)
        files, directories = _walk(root)
        expected_names, found_names = set(records), set(files)
        common = expected_names & found_names
        _require(all(files[name][1].st_size <= MAX_FILE_BYTES for name in common))
        _require(sum(files[name][1].st_size for name in common) <= MAX_TOTAL_BYTES)
        matched = 0
        for name in sorted(common):
            for parent, info in directories.items():
                _same_path(parent, info)
            path, info = files[name]
            value, size = _stable_read(path, limit=MAX_FILE_BYTES, comparison=comparison, expected=info)
            if comparison == "canonical-text":
                value = canonical_package_bytes(value)
                size, value = len(value), hashlib.sha256(value).hexdigest()
            record = records[name]
            if size == record["size"] and value == record["sha256"]:
                matched += 1
        for parent, info in directories.items():
            _same_path(parent, info)
        ignored = {name for name in found_names - expected_names if "__pycache__" in Path(name).parts or Path(name).suffix in {".pyc", ".pyo"}}
        missing = len(expected_names - found_names)
        extra = len(found_names - expected_names - ignored)
        different = len(common) - matched
        success = "manifest-files-byte-identical" if comparison == "bytes" else "manifest-files-canonical-content-matches"
        return {"comparison": comparison, "manifest_version": payload["version"], "status": "content-differs" if missing or extra or different else success,
                "expected_file_count": len(records), "matched_file_count": matched, "missing_file_count": missing,
                "extra_file_count": extra, "different_file_count": different, "ignored_file_count": len(ignored), "loaded_version": "not-verified"}
    except Exception:
        raise ValueError(ERROR) from None


if __name__ == "__main__":
    raise SystemExit(main())
