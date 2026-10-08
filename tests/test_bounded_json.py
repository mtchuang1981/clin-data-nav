"""Strict bounded input must reject ambiguity without leaking evidence."""
import importlib
import io
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/clin-nav/scripts"))


@pytest.fixture
def reader():
    assert importlib.util.find_spec("bounded_json") is not None, "bounded strict JSON reader is absent"
    return importlib.import_module("bounded_json")


def test_limit_accepts_exact_bytes_and_rejects_one_extra(reader):
    assert reader.parse_strict_json(b"{}", max_bytes=2) == {}
    with pytest.raises(ValueError):
        reader.parse_strict_json(b"{}", max_bytes=1)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'{"nested":{"a":1,"a":2}}',
                                 b'NaN', b'Infinity', b'-Infinity', b'1e999'])
def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(reader, raw):
    with pytest.raises(ValueError):
        reader.parse_strict_json(raw, max_bytes=262144)


def test_depth_counts_containers_not_escaped_text(reader):
    assert reader.parse_strict_json(b'[' * 12 + b'0' + b']' * 12, max_bytes=100) == [[[[[[[[[[[[0]]]]]]]]]]]]
    with pytest.raises(ValueError):
        reader.parse_strict_json(b'[' * 13 + b'0' + b']' * 13, max_bytes=100)
    assert reader.parse_strict_json(b'{"x":"[\\\"{]"}', max_bytes=100, max_depth=1) == {"x": '["{]'}


@pytest.mark.parametrize("raw", [b'\xff', b'\xef\xbb\xbf{}', b'{}{}', b'{"SYNTH_SECRET":}', b'1' * 5000],
                         ids=["invalid-utf8", "bom", "trailing", "sensitive-malformed", "oversized-integer"])
def test_parse_errors_do_not_echo_evidence(reader, raw):
    with pytest.raises(ValueError) as error:
        reader.parse_strict_json(raw, max_bytes=10000)
    assert "SYNTH_SECRET" not in str(error.value)
    assert len(str(error.value)) < 80


@pytest.mark.parametrize("kwargs", [{"max_bytes": True}, {"max_bytes": 0}, {"max_bytes": -1},
                                    {"max_bytes": "2"}, {"max_bytes": 2, "max_depth": True},
                                    {"max_bytes": 2, "max_depth": 0}])
def test_invalid_parser_limits_are_rejected(reader, kwargs):
    with pytest.raises(ValueError):
        reader.parse_strict_json(b"{}", **kwargs)


def test_reader_never_uses_unbounded_read(reader, monkeypatch, tmp_path):
    path = tmp_path / "synthetic.json"
    path.write_bytes(b'{}')
    requested = []

    class Guarded(io.BytesIO):
        def read(self, size=-1):
            assert 0 < size <= 3
            requested.append(size)
            return super().read(size)

    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: Guarded(b'{"a": 1}'))
    assert reader.read_bounded_bytes(path, max_bytes=8, chunk_bytes=3) == b'{"a": 1}'
    assert requested and requested[-1] == 1
    with pytest.raises(ValueError):
        reader.read_bounded_bytes(path, max_bytes=7, chunk_bytes=3)


@pytest.mark.parametrize("chunk", [True, 0, -1, "65536"])
def test_invalid_stream_chunk_is_rejected(reader, tmp_path, chunk):
    path = tmp_path / "synthetic.json"
    path.write_bytes(b'{}')
    with pytest.raises(ValueError):
        reader.read_bounded_bytes(path, max_bytes=2, chunk_bytes=chunk)


def test_read_strict_json_is_read_only(reader, tmp_path):
    path = tmp_path / "synthetic.json"
    path.write_bytes(b'{"x": [true, null, 1.5]}')
    before = path.read_bytes(), path.stat().st_mtime_ns
    assert reader.read_strict_json(path, max_bytes=100) == {"x": [True, None, 1.5]}
    assert (path.read_bytes(), path.stat().st_mtime_ns) == before


def test_open_descriptor_reader_has_same_exact_limit(reader):
    assert reader.read_bounded_stream(io.BytesIO(b"{}"), max_bytes=2, chunk_bytes=1) == b"{}"
    with pytest.raises(ValueError):
        reader.read_bounded_stream(io.BytesIO(b"{} "), max_bytes=2, chunk_bytes=1)
