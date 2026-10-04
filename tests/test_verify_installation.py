"""Read-only diagnosis using only synthetic externally installed packages."""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
from zipfile import ZipFile
import pytest
from scripts.package_skill import build_package
from test_packaging import _write_minimal_skill


@pytest.fixture
def core():
    assert importlib.util.find_spec("scripts.verify_installation") is not None, "installation verifier is absent"
    return importlib.import_module("scripts.verify_installation")


def make_installed_package(tmp_path, *, version="0.8.0"):
    source = tmp_path / "source" / "clin-nav"
    source.parent.mkdir()
    _write_minimal_skill(source)
    package = build_package(source, tmp_path / "package", package_version=version)
    installed = tmp_path / "installed"
    with ZipFile(package.archive) as archive:
        archive.extractall(installed)
    return installed, package.manifest, hashlib.sha256(package.manifest.read_bytes()).hexdigest()


def rewrite(manifest, edit):
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    edit(payload)
    manifest.write_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}


def verify(core, fixture, **kwargs):
    skill, manifest, digest = fixture
    return core.verify_installation(skill, manifest, manifest_sha256=digest, **kwargs)


def test_exact_manifest_files_match_without_writes(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    before = snapshot(tmp_path)
    result = verify(core, fixture)
    assert result == {"comparison": "bytes", "manifest_version": "0.8.0", "status": "manifest-files-byte-identical", "expected_file_count": 2, "matched_file_count": 2, "missing_file_count": 0, "extra_file_count": 0, "different_file_count": 0, "ignored_file_count": 0, "loaded_version": "not-verified"}
    assert snapshot(tmp_path) == before


def test_trusted_historical_manifest_is_supported(core, tmp_path):
    assert verify(core, make_installed_package(tmp_path, version="0.7.0"))["manifest_version"] == "0.7.0"


@pytest.mark.parametrize("change", ["missing", "extra", "hash", "size"])
def test_missing_extra_and_content_changes_are_differences(core, tmp_path, change):
    fixture = make_installed_package(tmp_path)
    member = fixture[0] / "SKILL.md"
    if change == "missing":
        member.unlink()
    elif change == "extra":
        (fixture[0] / "extra.txt").write_bytes(b"SYNTH_SECRET")
    elif change == "hash":
        member.write_bytes(b"X" * len(member.read_bytes()))
    else:
        member.write_bytes(b"X")
    result = verify(core, fixture)
    assert result["status"] == "content-differs"
    key = {"missing": "missing_file_count", "extra": "extra_file_count", "hash": "different_file_count", "size": "different_file_count"}[change]
    assert result[key] == 1
    assert "SYNTH_SECRET" not in json.dumps(result)


def test_canonical_matches_do_not_claim_bytes_identical(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    path = fixture[0] / "SKILL.md"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert verify(core, fixture)["status"] == "content-differs"
    assert verify(core, fixture, comparison="canonical-text")["status"] == "manifest-files-canonical-content-matches"
    path.write_bytes(path.read_bytes() + b" ")
    assert verify(core, fixture, comparison="canonical-text")["status"] == "content-differs"


def invalid_payload():
    return {"name": "clin-nav", "version": "0.8.0", "archive": "clin-nav-0.8.0.zip", "archive_sha256": "0" * 64, "files": [{"path": "SKILL.md", "size": 0, "sha256": "0" * 64}]}


@pytest.mark.parametrize(("field", "value"), [("name", "other"), ("version", "v0.8.0"), ("version", "１.0.0"), ("version", "1" * 81), ("archive", "clin-nav-0.7.0.zip"), ("archive_sha256", "A" * 64), ("files", []), ("files", [{"path": "other", "size": 0, "sha256": "0" * 64}])])
def test_manifest_contract_rejects_untrusted_shapes(core, field, value):
    payload = invalid_payload()
    payload[field] = value
    with pytest.raises(ValueError, match="invalid installation input"):
        core.validate_installation_manifest(payload)


@pytest.mark.parametrize("path", ["C:relative", "/absolute", "../outside", "a\\b", "a//b", "a/./b", "a:stream", "a.", "a ", "CON.txt", "a/AUX", "a\x01", "a\x7f"])
def test_unsafe_paths_rejected_before_any_member_open(core, tmp_path, monkeypatch, path):
    fixture = make_installed_package(tmp_path)
    digest = rewrite(fixture[1], lambda p: p["files"].append({"path": path, "size": 0, "sha256": "0" * 64}))
    original = Path.open
    def guard(p, *args, **kwargs):
        assert not p.is_relative_to(fixture[0]), "member opened before complete manifest validation"
        return original(p, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guard)
    with pytest.raises(ValueError):
        verify(core, (fixture[0], fixture[1], digest))


@pytest.mark.parametrize("paths", [["SKILL.md", "skill.MD"], ["a/e\u0301", "a/\u00e9"], ["a", "A/b"]])
def test_portable_collision_and_ancestor_conflict(core, paths):
    payload = invalid_payload()
    payload["files"] += [{"path": p, "size": 0, "sha256": "0" * 64} for p in paths]
    with pytest.raises(ValueError):
        core.validate_installation_manifest(payload)


def test_record_file_total_and_version_limits(core):
    payload = invalid_payload()
    payload["version"] = "1" * 76 + ".0.0"
    payload["archive"] = f'clin-nav-{payload["version"]}.zip'
    assert len(payload["version"]) == 80
    assert core.validate_installation_manifest(payload)
    payload = invalid_payload()
    payload["files"] = [{"path": "SKILL.md" if i == 0 else f"f-{i}", "size": 0, "sha256": "0" * 64} for i in range(256)]
    assert len(core.validate_installation_manifest(payload)) == 256
    payload["files"].append({"path": "over", "size": 0, "sha256": "0" * 64})
    with pytest.raises(ValueError): core.validate_installation_manifest(payload)
    payload = invalid_payload()
    for size in (True, -1, 1.0, 10 * 1024 * 1024 + 1):
        payload["files"][0]["size"] = size
        with pytest.raises(ValueError): core.validate_installation_manifest(payload)
    payload["files"] = [{"path": "SKILL.md" if i == 0 else f"f-{i}", "size": 10 * 1024 * 1024, "sha256": "0" * 64} for i in range(4)]
    assert core.validate_installation_manifest(payload)
    payload["files"].append({"path": "over", "size": 1, "sha256": "0" * 64})
    with pytest.raises(ValueError): core.validate_installation_manifest(payload)


@pytest.mark.parametrize("bad_digest", ["", "A" * 64, "0" * 64, True])
def test_manifest_trust_checked_before_member_open(core, tmp_path, monkeypatch, bad_digest):
    fixture = make_installed_package(tmp_path)
    original = Path.open
    def guard(p, *args, **kwargs):
        assert not p.is_relative_to(fixture[0])
        return original(p, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guard)
    with pytest.raises(ValueError):
        core.verify_installation(fixture[0], fixture[1], manifest_sha256=bad_digest)


@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'NaN', b'1e999', b'\xff', b'[]', b'{"SYNTH_SECRET":true}', b'[' * 13 + b'0' + b']' * 13], ids=["duplicate", "nan", "overflow", "encoding", "list", "unknown", "depth"])
def test_strict_manifest_after_trusted_raw_hash(core, tmp_path, raw):
    fixture = make_installed_package(tmp_path)
    fixture[1].write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    with pytest.raises(ValueError): verify(core, (fixture[0], fixture[1], digest))


def test_manifest_bytes_exact_and_over_limit(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    raw = fixture[1].read_bytes()
    raw += b" " * (1024 * 1024 - len(raw))
    fixture[1].write_bytes(raw)
    assert verify(core, (fixture[0], fixture[1], hashlib.sha256(raw).hexdigest()))["status"] == "manifest-files-byte-identical"
    raw += b" "
    fixture[1].write_bytes(raw)
    with pytest.raises(ValueError): verify(core, (fixture[0], fixture[1], hashlib.sha256(raw).hexdigest()))


def test_manifest_cannot_be_inside_installation_or_source_repo(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    internal = fixture[0] / "receipt.json"
    internal.write_bytes(fixture[1].read_bytes())
    with pytest.raises(ValueError): core.verify_installation(fixture[0], internal, manifest_sha256=fixture[2])
    repo = Path(__file__).resolve().parents[1]
    with pytest.raises(ValueError): core.verify_installation(fixture[0], repo / "pyproject.toml", manifest_sha256="0" * 64)


def test_extra_files_are_not_opened_and_cache_is_counted(core, tmp_path, monkeypatch):
    fixture = make_installed_package(tmp_path)
    ignored = fixture[0] / "__pycache__"
    ignored.mkdir()
    (ignored / "any.dat").write_bytes(b"ignored")
    (fixture[0] / "extra.pyc").write_bytes(b"ignored")
    extra = fixture[0] / "extra.txt"
    extra.write_bytes(b"SYNTH_SECRET")
    original = Path.open
    def guard(p, *args, **kwargs):
        assert p != extra and ignored not in p.parents and p.suffix != ".pyc"
        return original(p, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guard)
    result = verify(core, fixture)
    assert result["extra_file_count"] == 1 and result["ignored_file_count"] == 2


def test_declared_bytecode_is_not_ignored(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    raw = b"synthetic bytecode"
    (fixture[0] / "declared.pyc").write_bytes(raw)
    digest = rewrite(fixture[1], lambda p: p["files"].append({"path": "declared.pyc", "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}))
    result = verify(core, (fixture[0], fixture[1], digest))
    assert result["matched_file_count"] == 3 and result["ignored_file_count"] == 0


@pytest.mark.parametrize("where", ["root", "member", "cache", "manifest", "ancestor"])
def test_links_rejected_even_under_cache_or_ancestors(core, tmp_path, where):
    fixture = make_installed_package(tmp_path)
    installed, manifest, digest = fixture
    link = tmp_path / "linked"
    target = installed
    if where == "member":
        link, target = installed / "linked.md", manifest
    elif where == "cache":
        (installed / "__pycache__").mkdir()
        link, target = installed / "__pycache__/linked", manifest
    elif where == "manifest":
        target = manifest
    elif where == "ancestor":
        target = tmp_path / "package"
    try:
        link.symlink_to(target, target_is_directory=target.is_dir())
    except OSError:
        pytest.skip("symlink privileges unavailable")
    if where == "root": installed = link
    if where == "manifest": manifest = link
    if where == "ancestor": manifest = link / manifest.name
    with pytest.raises(ValueError): core.verify_installation(installed, manifest, manifest_sha256=digest)


def test_reparse_attributes_rejected_in_ignored_cache(core, tmp_path, monkeypatch):
    fixture = make_installed_package(tmp_path)
    cache = fixture[0] / "__pycache__"
    cache.mkdir()
    original = Path.lstat
    def wrapped(p):
        result = original(p)
        if p == cache:
            return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
        return result
    monkeypatch.setattr(Path, "lstat", wrapped)
    with pytest.raises(ValueError): verify(core, fixture)


def test_traversal_depth_and_entry_limits(core, tmp_path, monkeypatch):
    fixture = make_installed_package(tmp_path)
    assert core.MAX_ENTRIES == 4096 and core.MAX_DEPTH == 32
    monkeypatch.setattr(core, "MAX_ENTRIES", 3)  # two files plus their agents directory
    assert verify(core, fixture)["matched_file_count"] == 2
    (fixture[0] / "extra").mkdir()
    with pytest.raises(ValueError): verify(core, fixture)
    monkeypatch.setattr(core, "MAX_ENTRIES", 4096)
    path = fixture[0]
    for _ in range(32):
        path /= "d"
        path.mkdir()
    assert verify(core, fixture)["status"] == "manifest-files-byte-identical"
    (path / "over").mkdir()
    with pytest.raises(ValueError): verify(core, fixture)


@pytest.mark.parametrize("race", ["identity", "poststat", "growth"])
def test_open_fstat_poststat_and_growth_races_are_invalid(core, tmp_path, monkeypatch, race):
    fixture = make_installed_package(tmp_path)
    member = fixture[0] / "SKILL.md"
    if race == "identity":
        original = os.fstat
        def fake(fd):
            current = original(fd)
            if stat.S_ISREG(current.st_mode) and current.st_size == member.stat().st_size:
                return SimpleNamespace(st_mode=current.st_mode, st_dev=current.st_dev, st_ino=current.st_ino + 1, st_size=current.st_size, st_mtime_ns=current.st_mtime_ns, st_file_attributes=0)
            return current
        monkeypatch.setattr(os, "fstat", fake)
    else:
        original = Path.open
        class Mutating:
            def __init__(self, stream): self.stream = stream; self.done = False
            def __enter__(self): return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def fileno(self): return self.stream.fileno()
            def read(self, size=-1):
                assert size > 0
                data = self.stream.read(size)
                if not self.done:
                    self.done = True
                    if race == "poststat": os.utime(member, ns=(member.stat().st_atime_ns, member.stat().st_mtime_ns + 1000000000))
                    else:
                        with original(member, "ab") as writer: writer.write(b"X" * (10 * 1024 * 1024 + 1))
                return data
        def opened(p, *args, **kwargs):
            stream = original(p, *args, **kwargs)
            return Mutating(stream) if p == member else stream
        monkeypatch.setattr(Path, "open", opened)
    with pytest.raises(ValueError): verify(core, fixture)


def test_actual_member_file_and_total_limits(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    member = fixture[0] / "SKILL.md"
    raw = b"a" * (10 * 1024 * 1024)
    member.write_bytes(raw)
    digest = rewrite(fixture[1], lambda p: p["files"][0].update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    assert verify(core, (fixture[0], fixture[1], digest))["status"] == "manifest-files-byte-identical"
    with member.open("ab") as stream: stream.write(b"a")
    with pytest.raises(ValueError): verify(core, (fixture[0], fixture[1], digest))


def test_unsupported_special_file_invalid(core, tmp_path, monkeypatch):
    fixture = make_installed_package(tmp_path)
    member = fixture[0] / "SKILL.md"
    original = Path.lstat
    def wrapped(p):
        if p == member: return SimpleNamespace(st_mode=stat.S_IFIFO, st_file_attributes=0)
        return original(p)
    monkeypatch.setattr(Path, "lstat", wrapped)
    with pytest.raises(ValueError): verify(core, fixture)


def test_closed_manifest_and_record_fields_do_not_leak(core):
    for mutate in (lambda p: p.update(SYNTH_SECRET=True), lambda p: p["files"][0].update(SYNTH_SECRET=True)):
        payload = invalid_payload()
        mutate(payload)
        with pytest.raises(ValueError, match="^invalid installation input$"):
            core.validate_installation_manifest(payload)


def test_raw_installed_total_limit_is_separate_from_declared_total(core, tmp_path, monkeypatch):
    fixture = make_installed_package(tmp_path)
    expected = sum(p.stat().st_size for p in fixture[0].rglob("*") if p.is_file())
    assert core.MAX_TOTAL_BYTES == 40 * 1024 * 1024
    monkeypatch.setattr(core, "MAX_TOTAL_BYTES", expected)
    assert verify(core, fixture)["status"] == "manifest-files-byte-identical"
    with (fixture[0] / "SKILL.md").open("ab") as stream: stream.write(b"X")
    with pytest.raises(ValueError): verify(core, fixture)


def test_canonical_binary_differences_are_not_normalized(core, tmp_path):
    fixture = make_installed_package(tmp_path)
    raw = b"a\x00\r\n"
    member = fixture[0] / "binary.dat"
    member.write_bytes(raw)
    digest = rewrite(fixture[1], lambda p: p["files"].append({"path": "binary.dat", "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}))
    member.write_bytes(b"a\x00\n")
    assert verify(core, (fixture[0], fixture[1], digest), comparison="canonical-text")["status"] == "content-differs"


def test_real_junction_rejected_under_cache_if_platform_permits(core, tmp_path):
    if os.name != "nt": pytest.skip("Windows junction contract")
    import subprocess
    fixture = make_installed_package(tmp_path)
    cache = fixture[0] / "__pycache__"
    target = tmp_path / "target"
    target.mkdir()
    # Creation only: no cross-shell enumeration, deletion or moving.
    result = subprocess.run(["cmd", "/c", "mklink", "/J", str(cache), str(target)], capture_output=True)
    if result.returncode: pytest.skip("junction creation unavailable")
    assert cache.lstat().st_file_attributes & 0x400
    with pytest.raises(ValueError): verify(core, fixture)
