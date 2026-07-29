import errno
import hashlib
import json
from pathlib import Path
import stat
from zipfile import ZipFile, ZipInfo

import pytest

import scripts.install_local as install_local_module
from scripts.install_local import install_package, main
from scripts.package_skill import build_package


def _write_minimal_skill(skill: Path) -> None:
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: clinical-data-research-navigator\n"
        "description: Use when testing local installation.\n"
        "---\n"
        "# Skill\n",
        encoding="utf-8",
    )
    agents = skill / "agents"
    agents.mkdir()
    (agents / "openai.yaml").write_text(
        "interface:\n"
        "  display_name: Clinical Data Research Navigator\n"
        "  short_description: Test navigation.\n"
        "  default_prompt: Use $clinical-data-research-navigator for clinical-data research.\n",
        encoding="utf-8",
    )


def _build_test_package(tmp_path: Path):
    skill = tmp_path / "source" / "clinical-data-research-navigator"
    skill.parent.mkdir()
    _write_minimal_skill(skill)
    return build_package(skill, tmp_path / "package")


def _refresh_archive_hash(package) -> None:
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["archive_sha256"] = hashlib.sha256(
        package.archive.read_bytes()
    ).hexdigest()
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _set_first_declared_uncompressed_size(package, size: int) -> None:
    archive_bytes = bytearray(package.archive.read_bytes())
    central_directory = archive_bytes.index(b"PK\x01\x02")
    archive_bytes[central_directory + 24 : central_directory + 28] = (
        size.to_bytes(4, "little")
    )
    package.archive.write_bytes(archive_bytes)
    _refresh_archive_hash(package)


def _replace_archive_member(package, member_name: str, data: bytes) -> None:
    with ZipFile(package.archive) as zip_file:
        entries = [
            (info, zip_file.read(info))
            for info in zip_file.infolist()
        ]
    with ZipFile(package.archive, "w") as zip_file:
        for info, original_data in entries:
            zip_file.writestr(
                info,
                data if info.filename == member_name else original_data,
            )

    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    record = next(
        item for item in manifest["files"] if item["path"] == member_name
    )
    record["sha256"] = hashlib.sha256(data).hexdigest()
    record["size"] = len(data)
    manifest["archive_sha256"] = hashlib.sha256(
        package.archive.read_bytes()
    ).hexdigest()
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _append_declared_member(
    package,
    member: str | ZipInfo,
    data: bytes,
) -> None:
    name = member.filename if isinstance(member, ZipInfo) else member
    with ZipFile(package.archive, "a") as zip_file:
        zip_file.writestr(member, data)

    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["files"].append(
        {
            "path": name,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }
    )
    manifest["archive_sha256"] = hashlib.sha256(
        package.archive.read_bytes()
    ).hexdigest()
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def test_valid_package_installs_under_requested_destination(tmp_path):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"

    installed = install_package(package.archive, destination)

    assert installed == (
        destination.resolve() / "clinical-data-research-navigator"
    )
    assert (installed / "SKILL.md").read_text(encoding="utf-8").endswith(
        "# Skill\n"
    )


def test_existing_installation_is_refused_without_overwrite(tmp_path):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    installed.mkdir(parents=True)
    marker = installed / "keep.txt"
    marker.write_text("existing", encoding="utf-8")

    try:
        install_package(package.archive, destination)
    except FileExistsError:
        pass
    else:
        raise AssertionError("existing installation was not refused")

    assert marker.read_text(encoding="utf-8") == "existing"


@pytest.mark.parametrize("with_victim", [False, True], ids=["empty", "with-victim"])
def test_no_overwrite_race_never_replaces_a_competing_target(
    tmp_path,
    monkeypatch,
    with_victim,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    victim = installed / "victim.txt"
    victim_bytes = b"competitor-owned bytes"
    real_temporary_directory = install_local_module.tempfile.TemporaryDirectory

    def create_competing_target_after_initial_check(*args, **kwargs):
        installed.mkdir(parents=True)
        if with_victim:
            victim.write_bytes(victim_bytes)
        return real_temporary_directory(*args, **kwargs)

    monkeypatch.setattr(
        install_local_module.tempfile,
        "TemporaryDirectory",
        create_competing_target_after_initial_check,
    )

    with pytest.raises(FileExistsError, match="installation already exists"):
        install_package(package.archive, destination)

    assert installed.is_dir()
    if with_victim:
        assert victim.read_bytes() == victim_bytes
    else:
        assert list(installed.iterdir()) == []


def test_identity_check_path_swap_never_mutates_competing_directory(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    displaced = tmp_path / "displaced-installer-reservation"
    victim = installed / "victim.txt"
    victim_bytes = b"competitor-owned bytes"
    real_stat = Path.stat
    swap_triggered = False

    def swap_target_during_identity_check(path, *args, **kwargs):
        nonlocal swap_triggered
        if path == installed and not swap_triggered:
            swap_triggered = True
            installed.rename(displaced)
            installed.mkdir()
            victim.write_bytes(victim_bytes)
            return real_stat(displaced, *args, **kwargs)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", swap_target_during_identity_check)

    try:
        install_package(package.archive, destination)
    except FileExistsError:
        pass

    if swap_triggered:
        assert installed.is_dir()
        assert {path.name for path in installed.iterdir()} == {"victim.txt"}
        assert victim.read_bytes() == victim_bytes
    else:
        assert (installed / "SKILL.md").is_file()


def test_competitor_winning_at_atomic_publish_is_preserved(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    real_rename_no_replace = install_local_module._rename_no_replace
    competing_identity = None

    def competitor_wins_before_native_publish(source, target):
        nonlocal competing_identity
        target.mkdir()
        target_stat = target.stat(follow_symlinks=False)
        competing_identity = (target_stat.st_dev, target_stat.st_ino)
        return real_rename_no_replace(source, target)

    monkeypatch.setattr(
        install_local_module,
        "_rename_no_replace",
        competitor_wins_before_native_publish,
    )

    with pytest.raises(FileExistsError, match="installation already exists"):
        install_package(package.archive, destination)

    installed_stat = installed.stat(follow_symlinks=False)
    assert competing_identity is not None
    assert (installed_stat.st_dev, installed_stat.st_ino) == competing_identity
    assert list(installed.iterdir()) == []


def test_platform_family_reports_the_running_host():
    family = install_local_module._platform_family()

    if install_local_module.os.name == "nt":
        assert family == "windows"
    elif install_local_module.sys.platform.startswith("linux"):
        assert family == "linux"
    elif install_local_module.sys.platform == "darwin":
        assert family == "darwin"
    else:
        assert family == "unsupported"


def test_darwin_uses_atomic_exclusive_rename(tmp_path, monkeypatch):
    calls = []

    class FakeRename:
        argtypes = None
        restype = None

        def __call__(self, *args):
            calls.append(args)
            return 0

    class FakeLibc:
        renamex_np = FakeRename()

    source = tmp_path / "staged"
    target = tmp_path / "installed"
    monkeypatch.setattr(
        install_local_module,
        "_platform_family",
        lambda: "darwin",
    )
    monkeypatch.setattr(
        install_local_module.ctypes,
        "CDLL",
        lambda *_args, **_kwargs: FakeLibc(),
    )

    install_local_module._rename_no_replace(source, target)

    assert calls == [
        (
            bytes(source),
            bytes(target),
            install_local_module.DARWIN_RENAME_EXCL,
        )
    ]


@pytest.mark.parametrize("platform_family", ["linux", "darwin"])
def test_missing_native_no_replace_primitive_fails_closed(
    tmp_path,
    monkeypatch,
    platform_family,
):
    class FakeLibc:
        pass

    monkeypatch.setattr(
        install_local_module,
        "_platform_family",
        lambda: platform_family,
    )
    monkeypatch.setattr(
        install_local_module.ctypes,
        "CDLL",
        lambda *_args, **_kwargs: FakeLibc(),
    )

    with pytest.raises(OSError) as raised:
        install_local_module._rename_no_replace(
            tmp_path / "staged",
            tmp_path / "installed",
        )

    assert raised.value.errno == errno.ENOTSUP


def test_unsupported_platform_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        install_local_module,
        "_platform_family",
        lambda: "unsupported",
    )

    with pytest.raises(OSError) as raised:
        install_local_module._rename_no_replace(
            tmp_path / "staged",
            tmp_path / "installed",
        )

    assert raised.value.errno == errno.ENOTSUP


def test_overwrite_replaces_only_exact_skill_and_preserves_siblings(tmp_path):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    installed.mkdir(parents=True)
    stale = installed / "stale.txt"
    stale.write_text("remove me", encoding="utf-8")
    sibling = destination / "another-skill"
    sibling.mkdir()
    sibling_marker = sibling / "keep.txt"
    sibling_marker.write_text("keep me", encoding="utf-8")

    result = install_package(package.archive, destination, overwrite=True)

    assert result == installed.resolve()
    assert not stale.exists()
    assert sibling_marker.read_text(encoding="utf-8") == "keep me"
    assert not list(
        tmp_path.glob(".clinical-data-research-navigator-backup-*")
    )


def test_overwrite_option_also_installs_when_target_is_absent(tmp_path):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"

    installed = install_package(
        package.archive,
        destination,
        overwrite=True,
    )

    assert (installed / "SKILL.md").is_file()


@pytest.mark.parametrize("member_name", ["../outside.txt", "/outside.txt"])
def test_parent_or_absolute_zip_member_is_rejected_before_extraction(
    tmp_path,
    member_name,
):
    package = _build_test_package(tmp_path)
    with ZipFile(package.archive, "a") as zip_file:
        zip_file.writestr(member_name, b"not allowed")
    _refresh_archive_hash(package)
    destination = tmp_path / "selected-skills"
    outside = tmp_path / "outside.txt"

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        install_package(package.archive, destination)

    assert not outside.exists()
    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def _directory_zip_info() -> ZipInfo:
    info = ZipInfo("assets/")
    info.create_system = 3
    info.external_attr = (stat.S_IFDIR | 0o755) << 16
    return info


def _symlink_zip_info() -> ZipInfo:
    info = ZipInfo("assets/link")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    return info


def _dos_directory_zip_info() -> ZipInfo:
    info = ZipInfo("assets")
    info.create_system = 0
    info.external_attr = 0x10
    return info


@pytest.mark.parametrize(
    ("member", "data"),
    [
        ("D:../payload", b"drive relative"),
        ("./SKILL.md", b"dot alias"),
        ("agents//openai.yaml", b"separator alias"),
        (_directory_zip_info(), b""),
        (_symlink_zip_info(), b"SKILL.md"),
    ],
    ids=[
        "windows-drive-relative",
        "dot-alias",
        "repeated-separator",
        "directory-entry",
        "symlink-entry",
    ],
)
def test_noncanonical_or_nonregular_member_is_rejected_before_write(
    tmp_path,
    member,
    data,
):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, member, data)
    destination = tmp_path / "selected-skills"
    outside = tmp_path / "payload"

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        install_package(package.archive, destination)

    assert not outside.exists()
    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_dos_directory_attribute_is_rejected_before_write(tmp_path):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, _dos_directory_zip_info(), b"")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_casefolded_member_collision_is_rejected_before_write(tmp_path):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, "skill.md", b"case alias")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="portable path collision"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_unicode_normalized_member_collision_is_rejected_before_write(
    tmp_path,
):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, "assets/caf\u00e9.txt", b"composed")
    _append_declared_member(
        package,
        "assets/cafe\u0301.txt",
        b"decomposed",
    )
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="portable path collision"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


@pytest.mark.parametrize(
    "member_names",
    [
        ("assets", "assets/child.txt"),
        ("assets/child.txt", "assets"),
        ("Assets", "assets/child.txt"),
        ("assets/child.txt", "Assets"),
    ],
    ids=[
        "exact-ancestor-first",
        "exact-descendant-first",
        "casefolded-ancestor-first",
        "casefolded-descendant-first",
    ],
)
def test_portable_file_ancestor_conflict_is_rejected_before_staging(
    tmp_path,
    monkeypatch,
    member_names,
):
    package = _build_test_package(tmp_path)
    for member_name in member_names:
        _append_declared_member(
            package,
            member_name,
            member_name.encode("utf-8"),
        )
    destination = tmp_path / "selected-skills"
    staging_started = False
    real_temporary_directory = (
        install_local_module.tempfile.TemporaryDirectory
    )

    def track_staging(*args, **kwargs):
        nonlocal staging_started
        staging_started = True
        return real_temporary_directory(*args, **kwargs)

    monkeypatch.setattr(
        install_local_module.tempfile,
        "TemporaryDirectory",
        track_staging,
    )

    with pytest.raises(ValueError, match="portable path ancestor conflict"):
        install_package(package.archive, destination)

    assert not staging_started
    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()
    assert not list(
        tmp_path.glob(".clinical-data-research-navigator-*")
    )


def test_portable_sibling_members_with_common_directory_install(tmp_path):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, "assets/a.txt", b"a")
    _append_declared_member(package, "assets/b.txt", b"b")
    destination = tmp_path / "selected-skills"

    installed = install_package(package.archive, destination)

    assert (installed / "assets/a.txt").read_bytes() == b"a"
    assert (installed / "assets/b.txt").read_bytes() == b"b"


@pytest.mark.parametrize(
    "member_name",
    [
        "assets/trailing-dot.",
        "assets/trailing-space ",
        "assets/file.txt:stream",
    ],
    ids=["trailing-dot", "trailing-space", "ads-colon"],
)
def test_platform_ambiguous_component_is_rejected_before_write(
    tmp_path,
    member_name,
):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, member_name, b"ambiguous")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_manifest_hash_mismatch_is_rejected_before_extraction(tmp_path):
    package = _build_test_package(tmp_path)
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="hash mismatch"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_archive_checksum_mismatch_is_rejected_before_extraction(tmp_path):
    package = _build_test_package(tmp_path)
    with ZipFile(package.archive, "a") as zip_file:
        zip_file.writestr("extra.txt", b"changed archive")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="archive hash mismatch"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_manifest_for_different_archive_is_rejected_before_extraction(
    tmp_path,
):
    package = _build_test_package(tmp_path)
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["archive"] = "different-package.zip"
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="manifest archive mismatch"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "different-skill"),
        ("version", "9.9.9"),
    ],
)
def test_manifest_identity_mismatch_is_rejected_before_extraction(
    tmp_path,
    field,
    value,
):
    package = _build_test_package(tmp_path)
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest[field] = value
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="manifest identity mismatch"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_undeclared_archive_member_is_rejected_before_extraction(tmp_path):
    package = _build_test_package(tmp_path)
    with ZipFile(package.archive, "a") as zip_file:
        zip_file.writestr("undeclared.txt", b"not in manifest")
    _refresh_archive_hash(package)
    destination = tmp_path / "selected-skills"

    with pytest.raises(
        ValueError,
        match="archive members do not match manifest",
    ):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_duplicate_archive_member_is_rejected_before_extraction(tmp_path):
    package = _build_test_package(tmp_path)
    with ZipFile(package.archive) as zip_file:
        skill_data = zip_file.read("SKILL.md")
    with pytest.warns(UserWarning, match="Duplicate name"):
        with ZipFile(package.archive, "a") as zip_file:
            zip_file.writestr("SKILL.md", skill_data)
    _refresh_archive_hash(package)
    destination = tmp_path / "selected-skills"

    with pytest.raises(
        ValueError,
        match="archive members do not match manifest",
    ):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_manifest_member_missing_from_archive_is_rejected_before_extraction(
    tmp_path,
):
    package = _build_test_package(tmp_path)
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["files"].append(
        {
            "path": "references/missing.md",
            "sha256": hashlib.sha256(b"missing").hexdigest(),
            "size": len(b"missing"),
        }
    )
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "selected-skills"

    with pytest.raises(
        ValueError,
        match="archive members do not match manifest",
    ):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_manifest_size_mismatch_is_rejected_before_extraction(tmp_path):
    package = _build_test_package(tmp_path)
    manifest = json.loads(package.manifest.read_text(encoding="utf-8"))
    manifest["files"][0]["size"] += 1
    package.manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="size mismatch"):
        install_package(package.archive, destination)

    assert not (
        destination / "clinical-data-research-navigator"
    ).exists()


def test_manifest_size_limit_is_enforced_before_json_loading(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    monkeypatch.setattr(
        install_local_module,
        "MAX_MANIFEST_BYTES",
        package.manifest.stat().st_size - 1,
    )

    with pytest.raises(ValueError, match="manifest size limit exceeded"):
        install_package(package.archive, tmp_path / "selected-skills")


def test_archive_size_limit_is_enforced_before_hashing(tmp_path, monkeypatch):
    package = _build_test_package(tmp_path)
    monkeypatch.setattr(
        install_local_module,
        "MAX_ARCHIVE_BYTES",
        package.archive.stat().st_size - 1,
    )

    with pytest.raises(ValueError, match="archive size limit exceeded"):
        install_package(package.archive, tmp_path / "selected-skills")


def test_archive_member_count_limit_is_enforced_before_staging(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    monkeypatch.setattr(install_local_module, "MAX_MEMBER_COUNT", 1)

    with pytest.raises(ValueError, match="archive member count limit exceeded"):
        install_package(package.archive, tmp_path / "selected-skills")


def test_manifest_member_count_limit_is_enforced_before_archive_open(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    monkeypatch.setattr(install_local_module, "MAX_MANIFEST_FILE_COUNT", 1)

    with pytest.raises(ValueError, match="manifest member count limit exceeded"):
        install_package(package.archive, tmp_path / "selected-skills")


@pytest.mark.parametrize(
    ("limit_name", "message"),
    [
        ("MAX_MEMBER_COMPRESSED_BYTES", "ZIP member compressed size limit exceeded"),
        (
            "MAX_MEMBER_UNCOMPRESSED_BYTES",
            "ZIP member uncompressed size limit exceeded",
        ),
    ],
)
def test_archive_member_size_limits_are_enforced_from_zipinfo(
    tmp_path,
    monkeypatch,
    limit_name,
    message,
):
    package = _build_test_package(tmp_path)
    monkeypatch.setattr(install_local_module, limit_name, 1)

    with pytest.raises(ValueError, match=message):
        install_package(package.archive, tmp_path / "selected-skills")


def test_zip_bomb_style_declared_size_is_rejected_before_member_read(tmp_path):
    package = _build_test_package(tmp_path)
    _set_first_declared_uncompressed_size(
        package,
        install_local_module.MAX_MEMBER_UNCOMPRESSED_BYTES + 1,
    )

    with pytest.raises(
        ValueError,
        match="ZIP member uncompressed size limit exceeded",
    ):
        install_package(package.archive, tmp_path / "selected-skills")


@pytest.mark.parametrize(
    ("limit_name", "message"),
    [
        ("MAX_TOTAL_COMPRESSED_BYTES", "ZIP aggregate compressed size limit exceeded"),
        (
            "MAX_TOTAL_UNCOMPRESSED_BYTES",
            "ZIP aggregate uncompressed size limit exceeded",
        ),
    ],
)
def test_archive_aggregate_size_limits_are_enforced_before_staging(
    tmp_path,
    monkeypatch,
    limit_name,
    message,
):
    package = _build_test_package(tmp_path)
    monkeypatch.setattr(install_local_module, limit_name, 1)

    with pytest.raises(ValueError, match=message):
        install_package(package.archive, tmp_path / "selected-skills")


def test_installer_streams_archive_hashing_and_member_extraction(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)

    def reject_full_file_read(*_args, **_kwargs):
        raise AssertionError("installer attempted a full-file read")

    monkeypatch.setattr(Path, "read_bytes", reject_full_file_read)
    monkeypatch.setattr(ZipFile, "read", reject_full_file_read)

    installed = install_package(
        package.archive,
        tmp_path / "selected-skills",
    )

    assert (installed / "SKILL.md").is_file()


@pytest.mark.parametrize("existing_target", [False, True])
def test_invalid_extracted_skill_leaves_no_partial_replacement(
    tmp_path,
    existing_target,
):
    package = _build_test_package(tmp_path)
    _replace_archive_member(
        package,
        "SKILL.md",
        b"missing frontmatter\n",
    )
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    marker = installed / "existing.txt"
    if existing_target:
        installed.mkdir(parents=True)
        marker.write_text("preserve", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid extracted Skill"):
        install_package(
            package.archive,
            destination,
            overwrite=existing_target,
        )

    if existing_target:
        assert marker.read_text(encoding="utf-8") == "preserve"
    else:
        assert not installed.exists()


def test_failed_replacement_rolls_original_installation_back(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    installed.mkdir(parents=True)
    marker = installed / "existing.txt"
    marker.write_bytes(b"original bytes")
    real_replace = install_local_module.os.replace
    calls = 0

    def fail_commit(source, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("commit replacement failed")
        return real_replace(source, target)

    monkeypatch.setattr(install_local_module.os, "replace", fail_commit)

    with pytest.raises(OSError, match="commit replacement failed"):
        install_package(package.archive, destination, overwrite=True)

    assert marker.read_bytes() == b"original bytes"
    assert not list(
        tmp_path.glob(".clinical-data-research-navigator-backup-*")
    )


def test_failed_replacement_and_rollback_preserve_reported_backup(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clinical-data-research-navigator"
    installed.mkdir(parents=True)
    marker = installed / "existing.txt"
    marker.write_bytes(b"recoverable original")
    real_replace = install_local_module.os.replace
    calls = 0

    def fail_commit_and_rollback(source, target):
        nonlocal calls
        calls += 1
        if calls in {2, 3}:
            raise OSError(f"replacement failure {calls}")
        return real_replace(source, target)

    monkeypatch.setattr(
        install_local_module.os,
        "replace",
        fail_commit_and_rollback,
    )

    with pytest.raises(
        RuntimeError,
        match="recovery backup preserved at",
    ) as raised:
        install_package(package.archive, destination, overwrite=True)

    recovery_path = Path(raised.value.recovery_path)
    assert recovery_path.parent.parent == tmp_path
    assert (recovery_path / "existing.txt").read_bytes() == (
        b"recoverable original"
    )


def test_install_cli_requires_and_uses_selected_destination(
    tmp_path,
    capsys,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "cli-selected-skills"

    exit_code = main(
        [
            str(package.archive),
            "--destination",
            str(destination),
        ]
    )

    installed = (
        destination.resolve() / "clinical-data-research-navigator"
    )
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(installed)
    assert (installed / "SKILL.md").is_file()
