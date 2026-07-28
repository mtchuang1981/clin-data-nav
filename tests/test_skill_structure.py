from pathlib import Path
import shutil

import pytest

from scripts.validate_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/clinical-data-research-navigator"


def write_valid_skill(skill: Path) -> None:
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        f"name: {skill.name}\n"
        "description: Use when testing valid metadata.\n"
        "---\n"
        "# Test Skill\n",
        encoding="utf-8",
    )
    agents = skill / "agents"
    agents.mkdir()
    (agents / "openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Clinical Data Research Navigator"\n'
        '  short_description: "A valid test description"\n'
        '  default_prompt: "Use $clinical-data-research-navigator for a clinical-data question."\n',
        encoding="utf-8",
    )


def test_public_skill_structure_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_validator_rejects_extra_frontmatter_key(tmp_path):
    skill = tmp_path / "bad-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: bad-skill\n"
        "description: Use when testing invalid metadata.\n"
        "version: 1\n"
        "---\n"
        "# Bad Skill\n",
        encoding="utf-8",
    )
    assert "frontmatter only permits name and description" in validate_skill(skill)


def test_validator_rejects_missing_reference(tmp_path):
    skill = tmp_path / "bad-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: bad-skill\n"
        "description: Use when testing missing references.\n"
        "---\n"
        "# Bad Skill\n"
        "Read [missing](references/missing.md).\n",
        encoding="utf-8",
    )
    assert "missing reference: references/missing.md" in validate_skill(skill)


def test_validator_rejects_backtick_reference_that_escapes_skill_root(
    tmp_path,
):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    (skill / "references").mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside Skill root\n", encoding="utf-8")
    skill_file = skill / "SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8")
        + "\nRead `references/../../outside.md`.\n",
        encoding="utf-8",
    )

    assert (
        "unsafe reference path: references/../../outside.md"
        in validate_skill(skill)
    )


@pytest.mark.parametrize(
    "relative",
    [
        r"references\..\..\outside.md",
        r"references/..\..\outside.md",
        "/tmp/outside.md",
        r"C:\outside.md",
        "./references/../../outside.md",
        r"\outside.md",
        r"References\..\..\outside.md",
        "References/../../outside.md",
    ],
    ids=[
        "windows-separators",
        "mixed-separators",
        "posix-absolute",
        "windows-drive",
        "dot-prefixed",
        "windows-root-relative",
        "casefolded-windows-root",
        "casefolded-posix-root",
    ],
)
def test_validator_rejects_unsafe_backtick_path_syntax(tmp_path, relative):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    skill_file = skill / "SKILL.md"
    skill_file.write_text(
        skill_file.read_text(encoding="utf-8")
        + f"\nRead `{relative}`.\n",
        encoding="utf-8",
    )

    assert f"unsafe reference path: {relative}" in validate_skill(skill)


@pytest.mark.parametrize(
    "relative_path",
    [
        "references/retrieval-playbook.md",
        "references/evidence-output-template.md",
        "references/institutional-adapter-contract.md",
        "references/tmucrd-public-profile.md",
        "references/rwe-question-routing.md",
    ],
)
def test_validator_checks_each_real_backtick_reference(
    tmp_path,
    relative_path,
):
    assert (SKILL_DIR / relative_path).is_file()
    skill = tmp_path / SKILL_DIR.name
    shutil.copytree(SKILL_DIR, skill)
    (skill / relative_path).unlink()

    assert f"missing reference: {relative_path}" in validate_skill(skill)


def test_validator_reports_invalid_skill_frontmatter_yaml_without_raising(
    tmp_path,
):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: [unterminated\n"
        "---\n"
        "# Bad Skill\n",
        encoding="utf-8",
    )

    assert validate_skill(skill) == ["SKILL.md: invalid YAML frontmatter"]


def test_validator_reports_invalid_openai_yaml_without_raising(tmp_path):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    (skill / "agents/openai.yaml").write_text(
        "interface: [unterminated\n",
        encoding="utf-8",
    )

    assert validate_skill(skill) == ["agents/openai.yaml: invalid YAML"]


def test_validator_rejects_mismatched_display_name(tmp_path):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Incorrect Name"\n'
        '  short_description: "A valid test description"\n'
        '  default_prompt: "Use $clinical-data-research-navigator for a clinical-data question."\n',
        encoding="utf-8",
    )
    assert "display name mismatch" in validate_skill(skill)


def test_validator_requires_skill_invocation_in_default_prompt(tmp_path):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Clinical Data Research Navigator"\n'
        '  short_description: "A valid test description"\n'
        '  default_prompt: "Use this skill for a clinical-data question."\n',
        encoding="utf-8",
    )
    assert "default prompt must mention $clinical-data-research-navigator" in validate_skill(skill)


def test_validator_accepts_a_single_short_default_prompt(tmp_path):
    skill = tmp_path / "valid-skill"
    write_valid_skill(skill)

    assert validate_skill(skill) == []


def test_validator_rejects_a_multi_sentence_default_prompt(tmp_path):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Clinical Data Research Navigator"\n'
        '  short_description: "A valid test description"\n'
        '  default_prompt: "Use $clinical-data-research-navigator for a clinical-data question. Then continue."\n',
        encoding="utf-8",
    )

    assert (
        "default prompt must be exactly one non-empty sentence ending in '.', '!', or '?'"
        in validate_skill(skill)
    )


def test_validator_rejects_an_overlong_default_prompt(tmp_path):
    skill = tmp_path / "bad-skill"
    write_valid_skill(skill)
    prefix = "Use $clinical-data-research-navigator for a clinical-data question "
    default_prompt = prefix + "x" * (201 - len(prefix) - 1) + "."
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Clinical Data Research Navigator"\n'
        '  short_description: "A valid test description"\n'
        f'  default_prompt: "{default_prompt}"\n',
        encoding="utf-8",
    )

    assert "default prompt must not exceed 200 Unicode code points" in validate_skill(
        skill
    )


def test_validator_accepts_an_exactly_200_code_point_default_prompt(tmp_path):
    skill = tmp_path / "valid-skill"
    write_valid_skill(skill)
    prefix = "Use $clinical-data-research-navigator for a clinical-data question "
    default_prompt = prefix + "x" * (200 - len(prefix) - 1) + "."
    assert len(default_prompt) == 200
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        '  display_name: "Clinical Data Research Navigator"\n'
        '  short_description: "A valid test description"\n'
        f'  default_prompt: "{default_prompt}"\n',
        encoding="utf-8",
    )

    assert validate_skill(skill) == []
