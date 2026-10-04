"""Small package primitives shared by existing wrappers and read-only diagnosis."""
from __future__ import annotations

import hashlib
from pathlib import PurePosixPath, PureWindowsPath
import re
from typing import BinaryIO
import unicodedata


def canonical_package_bytes(data: bytes) -> bytes:
    if b"\x00" in data:
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def portable_path_key(name: str) -> tuple[str, ...]:
    return tuple(unicodedata.normalize("NFC", component).casefold() for component in name.split("/"))


def validate_member_name(name: str, *, reject_windows_devices: bool = False) -> None:
    if not isinstance(name, str):
        raise ValueError("unsafe package member name")
    path, windows = PurePosixPath(name), PureWindowsPath(name)
    components = name.split("/")
    if (not name or "\\" in name or windows.drive or path.is_absolute() or windows.is_absolute()
            or any(c in {"", ".", ".."} or c.endswith((".", " ")) or ":" in c for c in components)
            or path.as_posix() != name):
        raise ValueError("unsafe package member name")
    if reject_windows_devices:
        for component in components:
            basename = component.split(".", 1)[0].rstrip(" ").upper()
            if (any(ord(c) < 32 or ord(c) == 127 for c in component)
                    or basename in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
                    or re.fullmatch(r"(?:COM|LPT)[1-9¹²³]", basename)):
                raise ValueError("unsafe package member name")


def manifest_records(manifest: dict, *, max_records: int = 256) -> dict[str, dict]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("manifest files must be a list")
    if len(files) > max_records:
        raise ValueError("manifest member count limit exceeded")
    records: dict[str, dict] = {}
    for record in files:
        if not isinstance(record, dict) or set(record) != {"path", "sha256", "size"}:
            raise ValueError("invalid manifest file record")
        path, digest, size = record["path"], record["sha256"], record["size"]
        if (not isinstance(path, str) or not path or not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)
                or not isinstance(size, int) or isinstance(size, bool) or size < 0):
            raise ValueError("invalid manifest file record")
        if path in records:
            raise ValueError("duplicate manifest file path")
        records[path] = record
    return records


def hash_stream(stream: BinaryIO, *, max_bytes: int | None = None, chunk_bytes: int = 65536) -> str:
    if (type(chunk_bytes) is not int or chunk_bytes <= 0
            or (max_bytes is not None and (type(max_bytes) is not int or max_bytes < 0))):
        raise ValueError("invalid stream limit")
    digest = hashlib.sha256()
    total = 0
    while True:
        size = chunk_bytes if max_bytes is None else min(chunk_bytes, max_bytes - total + 1)
        chunk = stream.read(size)
        if not isinstance(chunk, bytes):
            raise ValueError("invalid stream input")
        if not chunk:
            return digest.hexdigest()
        total += len(chunk)
        if max_bytes is not None and total > max_bytes:
            raise ValueError("stream size limit exceeded")
        digest.update(chunk)
