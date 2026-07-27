import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

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
