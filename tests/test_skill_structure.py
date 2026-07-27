from pathlib import Path

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
