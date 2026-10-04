"""Narrow helpers preserve legacy packaging while exposing strict diagnostic mode."""
import hashlib
import importlib
import io
import os
from pathlib import Path
import subprocess
import sys
import pytest
from scripts import package_skill, install_local
from test_packaging import _write_minimal_skill


@pytest.fixture
def core():
    assert importlib.util.find_spec("scripts.package_contract") is not None, "package helper API is absent"
    return importlib.import_module("scripts.package_contract")


@pytest.mark.parametrize(("raw", "expected"), [(b'a\r\nb\rc', b'a\nb\nc'), (b'a\x00\r\n', b'a\x00\r\n'), (b'\xff\r\n', b'\xff\r\n'), (b' a ', b' a '), ('e\u0301\r'.encode(), 'e\u0301\n'.encode())])
def test_canonical_bytes_normalize_only_text_line_endings(core, raw, expected):
    assert core.canonical_package_bytes(raw) == expected


@pytest.mark.parametrize("name", ["C:relative", "/absolute", "a\\b", "", ".", "..", "a/../b", "a//b", "a/./b", "a/", "a:b", "a.", "a "])
def test_paths_reject_existing_unsafe_names(core, name):
    for strict in (False, True):
        with pytest.raises(ValueError):
            core.validate_member_name(name, reject_windows_devices=strict)


@pytest.mark.parametrize("name", ["CON", "con.txt", "aux/X", "PRN.md", "NUL", "com1", "LPT9.log", "a/COM\u00b9.md", "a/LPT\u00b2", "a\x00", "a\x1f", "a\x7f"])
def test_strict_paths_reject_windows_devices_and_controls_without_widening_legacy(core, name):
    core.validate_member_name(name, reject_windows_devices=False)
    with pytest.raises(ValueError):
        core.validate_member_name(name, reject_windows_devices=True)


def test_portable_key_uses_nfc_and_casefold(core):
    assert core.portable_path_key("A/e\u0301.md") == core.portable_path_key("a/\u00e9.MD")
    core.validate_member_name("references/normal.md", reject_windows_devices=True)


def record(path="SKILL.md", size=0):
    return {"path": path, "sha256": "0" * 64, "size": size}


@pytest.mark.parametrize("size", [True, -1, 1.0, "1"])
def test_manifest_records_reject_invalid_size(core, size):
    with pytest.raises(ValueError, match="invalid manifest file record"):
        core.manifest_records({"files": [record(size=size)]})


def test_manifest_records_exact_limit_duplicates_and_closed_fields(core):
    records = [record(f"file-{i}") for i in range(256)]
    assert len(core.manifest_records({"files": records})) == 256
    with pytest.raises(ValueError, match="member count limit"):
        core.manifest_records({"files": records + [record("extra")]})
    with pytest.raises(ValueError, match="duplicate manifest file path"):
        core.manifest_records({"files": [record(), record()]})
    with pytest.raises(ValueError):
        core.manifest_records({"files": [{**record(), "extra": 0}]})


def test_hash_stream_is_bounded_and_uses_fixed_chunks(core):
    class Guard(io.BytesIO):
        def read(self, size=-1):
            assert 0 < size <= 2
            return super().read(size)
    assert core.hash_stream(Guard(b"abc"), max_bytes=3, chunk_bytes=2) == hashlib.sha256(b"abc").hexdigest()
    with pytest.raises(ValueError):
        core.hash_stream(Guard(b"abcd"), max_bytes=3, chunk_bytes=2)
    assert core.hash_stream(io.BytesIO(b""), max_bytes=0) == hashlib.sha256(b"").hexdigest()
    assert core.hash_stream(Guard(b"abc"), chunk_bytes=2) == hashlib.sha256(b"abc").hexdigest()


@pytest.mark.parametrize(("maximum", "chunk"), [(True, 2), (-1, 2), (1, True), (1, 0)])
def test_hash_parameters_reject_invalid_limits(core, maximum, chunk):
    with pytest.raises(ValueError):
        core.hash_stream(io.BytesIO(b"x"), max_bytes=maximum, chunk_bytes=chunk)


def test_legacy_wrappers_forward_monkeypatched_constants(core, monkeypatch):
    monkeypatch.setattr(install_local, "MAX_MANIFEST_FILE_COUNT", 1)
    with pytest.raises(ValueError, match="member count limit"):
        install_local._manifest_records({"files": [record(), record("second")]})
    monkeypatch.setattr(install_local, "READ_CHUNK_BYTES", 1)
    class Guard(io.BytesIO):
        def read(self, size=-1):
            assert size == 1
            return super().read(size)
    assert install_local._hash_stream(Guard(b"abc")) == hashlib.sha256(b"abc").hexdigest()


def test_packager_refactor_preserves_legacy_bytes(core, tmp_path, monkeypatch):
    skill = tmp_path / "clin-nav"
    _write_minimal_skill(skill)
    refs = skill / "references"
    refs.mkdir()
    (refs / "line.md").write_bytes(b'a\r\nb\rc')
    (refs / "binary.dat").write_bytes(b'\xff\r\n')
    result = package_skill.build_package(skill, tmp_path / "normal")
    def legacy(path: Path) -> bytes:
        data = path.read_bytes()
        if b"\x00" in data:
            return data
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return data
        return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    monkeypatch.setattr(package_skill, "_canonical_package_bytes", legacy)
    reference = package_skill.build_package(skill, tmp_path / "legacy")
    assert result.archive.read_bytes() == reference.archive.read_bytes()
    assert result.manifest.read_bytes() == reference.manifest.read_bytes()


def test_direct_installer_uses_local_helper_when_an_older_scripts_package_is_on_pythonpath(core, tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "__init__.py").write_text("", encoding="utf-8")
    (scripts / "validate_skill.py").write_text("def validate_skill(path): return []\n", encoding="utf-8")
    environment = dict(os.environ, PYTHONPATH=str(tmp_path))
    result = subprocess.run([sys.executable, str(Path(install_local.__file__).resolve()), "--help"], cwd=tmp_path, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout
