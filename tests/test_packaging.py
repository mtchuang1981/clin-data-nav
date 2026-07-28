from pathlib import Path
import json

from scripts.package_skill import build_package


def _write_minimal_skill(skill: Path) -> None:
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: clinical-data-research-navigator\n"
        "description: Use when testing packaging.\n"
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


def test_same_skill_produces_identical_archive_bytes(tmp_path):
    skill = tmp_path / "clinical-data-research-navigator"
    _write_minimal_skill(skill)

    first = build_package(skill, tmp_path / "first")
    second = build_package(skill, tmp_path / "second")

    assert first.archive.read_bytes() == second.archive.read_bytes()
    assert first.manifest.read_bytes() == second.manifest.read_bytes()


def test_package_excludes_repository_files(tmp_path):
    result = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path,
    )

    assert all(
        not name.startswith(("tests/", "docs/", ".git/"))
        for name in result.files
    )


def test_package_contains_rwe_routing_reference_but_no_second_skill(tmp_path):
    result = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path,
    )

    assert "references/rwe-question-routing.md" in result.files
    assert all("build-rwe-sap/" not in name for name in result.files)


def test_v011_package_and_manifest_names_match_release_version(tmp_path):
    result = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path,
    )
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))

    assert result.archive.name == "clinical-data-research-navigator-0.1.1.zip"
    assert (
        result.manifest.name
        == "clinical-data-research-navigator-0.1.1.manifest.json"
    )
    assert manifest["version"] == "0.1.1"
    assert manifest["archive"] == result.archive.name
