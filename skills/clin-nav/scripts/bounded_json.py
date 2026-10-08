"""Bounded, unambiguous JSON input; no network, writes, or evidence echo."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import BinaryIO


def _positive(value: object) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError("invalid JSON input")


def read_bounded_stream(stream: BinaryIO, *, max_bytes: int, chunk_bytes: int = 65536) -> bytes:
    """Read a caller-owned descriptor without exceeding the bounded probe."""
    _positive(max_bytes)
    _positive(chunk_bytes)
    chunks = []
    total = 0
    while True:
        chunk = stream.read(min(chunk_bytes, max_bytes - total + 1))
        if type(chunk) is not bytes:
            raise ValueError("invalid JSON input")
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        if total > max_bytes:
            raise ValueError("invalid JSON input")
        chunks.append(chunk)


def read_bounded_bytes(path: Path, *, max_bytes: int, chunk_bytes: int = 65536) -> bytes:
    _positive(max_bytes)
    _positive(chunk_bytes)
    with path.open("rb") as stream:
        return read_bounded_stream(stream, max_bytes=max_bytes, chunk_bytes=chunk_bytes)


def _check_depth(text: str, max_depth: int) -> None:
    depth = 0
    quoted = escaped = False
    for character in text:
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
        elif character == '"':
            quoted = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise ValueError("invalid JSON input")
        elif character in "]}":
            depth -= 1


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("invalid JSON input")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("invalid JSON input")


def parse_strict_json(data: bytes, *, max_bytes: int, max_depth: int = 12) -> object:
    _positive(max_bytes)
    _positive(max_depth)
    if type(data) is not bytes or len(data) > max_bytes:
        raise ValueError("invalid JSON input")
    try:
        text = data.decode("utf-8")
        _check_depth(text, max_depth)
        result = json.loads(text, object_pairs_hook=_unique_pairs, parse_constant=_reject_constant)
        pending = [result]
        while pending:
            value = pending.pop()
            if type(value) is float and not math.isfinite(value):
                raise ValueError("invalid JSON input")
            if type(value) is dict:
                pending.extend(value.values())
            elif type(value) is list:
                pending.extend(value)
        return result
    except (UnicodeError, ValueError, RecursionError):
        raise ValueError("invalid JSON input") from None


def read_strict_json(path: Path, *, max_bytes: int, max_depth: int = 12) -> object:
    return parse_strict_json(read_bounded_bytes(path, max_bytes=max_bytes),
                             max_bytes=max_bytes, max_depth=max_depth)
