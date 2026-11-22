import errno
import hashlib
import json
from pathlib import Path
import stat
from zipfile import ZipFile, ZipInfo

import pytest

import scripts.install_local as install_local_module
from scripts.install_local import PACKAGE_VERSION as INSTALLER_VERSION
from scripts.install_local import install_package, main
from scripts.package_skill import PACKAGE_VERSION as PACKAGER_VERSION
from scripts.package_skill import build_package


def _write_minimal_skill(skill: Path) -> None:
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: clin-nav\n"
        "description: Use when testing local installation.\n"
        "---\n"
        "# Skill\n",
        encoding="utf-8",
    )
    agents = skill / "agents"
    agents.mkdir()
    (agents / "openai.yaml").write_text(
        "interface:\n"
        "  display_name: ClinNav\n"
        "  short_description: Test navigation.\n"
        "  default_prompt: Use $clin-nav for clinical-data research.\n",
        encoding="utf-8",
    )


def _build_test_package(tmp_path: Path):
    skill = tmp_path / "source" / "clin-nav"
    skill.parent.mkdir()
    _write_minimal_skill(skill)
    return build_package(skill, tmp_path / "package")


def test_candidate_installer_version_matches_the_candidate_packager():
    assert INSTALLER_VERSION == "0.11.2"
    assert PACKAGER_VERSION == "0.11.2"


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
        destination.resolve() / "clin-nav"
    )
    assert (installed / "SKILL.md").read_text(encoding="utf-8").endswith(
        "# Skill\n"
    )


def test_existing_installation_is_refused_without_overwrite(tmp_path):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clin-nav"
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
    installed = destination / "clin-nav"
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
    installed = destination / "clin-nav"
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
    installed = destination / "clin-nav"
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
    installed = destination / "clin-nav"
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
        tmp_path.glob(".clin-nav-backup-*")
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
        destination / "clin-nav"
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
        destination / "clin-nav"
    ).exists()


def test_dos_directory_attribute_is_rejected_before_write(tmp_path):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, _dos_directory_zip_info(), b"")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="unsafe ZIP member"):
        install_package(package.archive, destination)

    assert not (
        destination / "clin-nav"
    ).exists()


def test_casefolded_member_collision_is_rejected_before_write(tmp_path):
    package = _build_test_package(tmp_path)
    _append_declared_member(package, "skill.md", b"case alias")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="portable path collision"):
        install_package(package.archive, destination)

    assert not (
        destination / "clin-nav"
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
        destination / "clin-nav"
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
        destination / "clin-nav"
    ).exists()
    assert not list(
        tmp_path.glob(".clin-nav-*")
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
        destination / "clin-nav"
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
        destination / "clin-nav"
    ).exists()


def test_archive_checksum_mismatch_is_rejected_before_extraction(tmp_path):
    package = _build_test_package(tmp_path)
    with ZipFile(package.archive, "a") as zip_file:
        zip_file.writestr("extra.txt", b"changed archive")
    destination = tmp_path / "selected-skills"

    with pytest.raises(ValueError, match="archive hash mismatch"):
        install_package(package.archive, destination)

    assert not (
        destination / "clin-nav"
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
        destination / "clin-nav"
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
        destination / "clin-nav"
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
        destination / "clin-nav"
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
        destination / "clin-nav"
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
        destination / "clin-nav"
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
        destination / "clin-nav"
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
    installed = destination / "clin-nav"
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
    installed = destination / "clin-nav"
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
        tmp_path.glob(".clin-nav-backup-*")
    )


def test_failed_replacement_and_rollback_preserve_reported_backup(
    tmp_path,
    monkeypatch,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    installed = destination / "clin-nav"
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
        destination.resolve() / "clin-nav"
    )
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(installed)
    assert (installed / "SKILL.md").is_file()


def _windows_set_test_dacl(path, sddl):
    """Apply a synthetic test policy to a test-owned tree only."""
    import ctypes
    from ctypes import wintypes
    api = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    pointer = ctypes.c_void_p()
    convert = api.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                        ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    convert.restype = wintypes.BOOL
    apply = api.SetFileSecurityW
    apply.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
    apply.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not convert(sddl, 1, ctypes.byref(pointer), None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        if not apply(str(path), 4 | 0x80000000, pointer):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.LocalFree(pointer)


def _windows_test_dacl(path):
    import ctypes
    from ctypes import wintypes
    api = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    descriptor = ctypes.c_void_p()
    output = ctypes.c_void_p()
    get = api.GetNamedSecurityInfoW
    get.argtypes = [wintypes.LPCWSTR, ctypes.c_int, wintypes.DWORD,
                   ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                   ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    get.restype = wintypes.DWORD
    convert = api.ConvertSecurityDescriptorToStringSecurityDescriptorW
    convert.argtypes = [ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD,
                        ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    convert.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    result = get(str(path), 1, 4, None, None, None, None, ctypes.byref(descriptor))
    if result:
        raise ctypes.WinError(result)
    try:
        if not convert(descriptor, 1, 4, ctypes.byref(output), None):
            raise ctypes.WinError(ctypes.get_last_error())
        return ctypes.wstring_at(output)
    finally:
        if output.value:
            kernel.LocalFree(output)
        kernel.LocalFree(descriptor)


@pytest.mark.skipif(install_local_module.os.name != "nt", reason="Windows DACL contract")
@pytest.mark.parametrize("overwrite", [False, True], ids=["new", "replace"])
def test_windows_install_inherits_selected_destination_policy(tmp_path, monkeypatch, overwrite):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    destination.mkdir()
    # Well-known SIDs only: owner, SYSTEM, administrators, authenticated readers.
    private = "D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)"
    _windows_set_test_dacl(destination, private + "(A;OICI;GRGX;;;AU)")
    old = destination / "clin-nav"
    if overwrite:
        old.mkdir()
        (old / "old-marker.txt").write_text("old", encoding="utf-8")
    real_temporary = install_local_module.tempfile.TemporaryDirectory

    def restricted_staging(*args, **kwargs):
        context = real_temporary(*args, **kwargs)
        _windows_set_test_dacl(Path(context.name), private)
        return context

    monkeypatch.setattr(install_local_module.tempfile, "TemporaryDirectory", restricted_staging)
    installed = install_package(package.archive, destination, overwrite=overwrite)
    for relative in [".", "SKILL.md", "agents", "agents/openai.yaml"]:
        assert ";;;AU)" in _windows_test_dacl(installed / relative), relative
    assert not (installed / "old-marker.txt").exists()
    assert (installed / "SKILL.md").read_text(encoding="utf-8").endswith("# Skill\n")


@pytest.mark.parametrize("overwrite", [False, True], ids=["new", "replace"])
def test_permission_preparation_failure_never_publishes_or_moves_old_install(
    tmp_path, monkeypatch, overwrite,
):
    package = _build_test_package(tmp_path)
    destination = tmp_path / "selected-skills"
    old = destination / "clin-nav"
    if overwrite:
        old.mkdir(parents=True)
        (old / "keep.txt").write_bytes(b"original")
    def reject_permissions(*args):
        raise PermissionError("synthetic destination policy failure")
    monkeypatch.setattr(install_local_module, "_prepare_staging_permissions", reject_permissions)
    with pytest.raises(PermissionError, match="synthetic destination policy failure"):
        install_package(package.archive, destination, overwrite=overwrite)
    if overwrite:
        assert (old / "keep.txt").read_bytes() == b"original"
        assert not (old / "SKILL.md").exists()
    else:
        assert not old.exists()
    assert not list(tmp_path.glob(".clin-nav-backup-*"))


def test_non_windows_permission_preparation_does_not_load_windows_libraries(tmp_path, monkeypatch):
    def reject_library(*args, **kwargs):
        raise AssertionError("Windows library loaded on another platform")
    monkeypatch.setattr(install_local_module, "_platform_family", lambda: "linux")
    monkeypatch.setattr(install_local_module.ctypes, "WinDLL", reject_library, raising=False)
    install_local_module._prepare_staging_permissions(tmp_path / "stage", tmp_path / "destination")


@pytest.mark.skipif(install_local_module.os.name != "nt", reason="Windows DACL contract")
@pytest.mark.parametrize("flags", ["OICI", "OICINP", "OI", ""], ids=["normal", "no-propagate", "files-only", "non-inheritable"])
@pytest.mark.parametrize("inherited", [False, True], ids=["explicit-parent", "inherited-parent"])
def test_windows_install_policy_matches_direct_created_tree(tmp_path, flags, inherited):
    package = _build_test_package(tmp_path)
    policy_root = tmp_path / "policy-root"
    policy_root.mkdir()
    policy = "D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)"
    policy += f"(A;{flags};GRGX;;;AU)"
    _windows_set_test_dacl(policy_root, policy)
    destination = policy_root / "skills"
    destination.mkdir()
    if not inherited:
        _windows_set_test_dacl(destination, policy)
    reference = destination / "reference"
    (reference / "agents").mkdir(parents=True)
    (reference / "SKILL.md").write_bytes(b"reference")
    (reference / "agents/openai.yaml").write_bytes(b"reference")
    installed = install_package(package.archive, destination)
    for relative in [".", "SKILL.md", "agents", "agents/openai.yaml"]:
        actual = _windows_test_dacl(installed / relative)
        expected = _windows_test_dacl(reference / relative)
        # AI records automatic-inheritance bookkeeping, not an ACE/access mask.
        # Keep ACE order, all ACE flags, P (protection) and AR significant.
        assert actual.replace("D:AI(", "D:(", 1) == expected.replace("D:AI(", "D:(", 1), relative


@pytest.mark.skipif(install_local_module.os.name != "nt", reason="Windows error semantics")
@pytest.mark.parametrize("failure", ["get", "set", "null"])
def test_windows_permission_api_failure_frees_descriptor(tmp_path, monkeypatch, failure):
    import ctypes
    from types import SimpleNamespace
    freed = []
    def get_security(name, kind, info, owner, group, dacl, sacl, descriptor):
        ctypes.cast(descriptor, ctypes.POINTER(ctypes.c_void_p))[0] = 77
        if failure != "null":
            ctypes.cast(dacl, ctypes.POINTER(ctypes.c_void_p))[0] = 88
        return 5 if failure == "get" else 0
    def set_security(*args):
        return 5
    def free(pointer):
        freed.append(pointer.value)
    api = SimpleNamespace(GetNamedSecurityInfoW=get_security, SetNamedSecurityInfoW=set_security)
    kernel = SimpleNamespace(LocalFree=free)
    monkeypatch.setattr(install_local_module.ctypes, "WinDLL",
                        lambda name, **kwargs: api if name == "advapi32" else kernel)
    with pytest.raises(OSError):
        install_local_module._prepare_staging_permissions(tmp_path / "stage", tmp_path / "destination")
    assert freed == [77]
