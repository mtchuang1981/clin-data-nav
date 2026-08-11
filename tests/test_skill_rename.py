from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
ACTIVE_SKILL = SKILLS / "clin-nav"
OLD_SKILL = SKILLS / "clinical-data-research-navigator"
HISTORICAL_ROOTS = (
    ROOT / "docs/releases",
    ROOT / "docs/verification",
    ROOT / "docs/superpowers/specs",
    ROOT / "docs/superpowers/plans",
)
ACTIVE_TEXT_FILES = (
    ROOT / "README.md",
    ROOT / "README.zh-TW.md",
    ROOT / "docs/architecture.md",
    ROOT / "docs/glossary.md",
    ROOT / "docs/glossary.zh-TW.md",
    ROOT / "docs/installation.md",
    ROOT / "docs/installation.zh-TW.md",
    ROOT / "docs/learning-paths.md",
    ROOT / "docs/learning-paths.zh-TW.md",
    ROOT / "docs/release.md",
)


def test_repository_has_exactly_one_clin_nav_skill():
    assert sorted(path.name for path in SKILLS.iterdir() if path.is_dir()) == [
        "clin-nav"
    ]
    assert ACTIVE_SKILL.is_dir()
    assert not OLD_SKILL.exists()


def test_clin_nav_metadata_and_invocation_are_synchronized():
    frontmatter = yaml.safe_load(
        (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
    )
    metadata = yaml.safe_load(
        (ACTIVE_SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
    )["interface"]
    assert frontmatter["name"] == "clin-nav"
    assert metadata["display_name"] == "ClinNav"
    assert "$clin-nav" in metadata["default_prompt"]
    assert "$clinical-data-research-navigator" not in metadata["default_prompt"]


def test_active_user_documents_use_only_the_new_invocation_and_paths():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE_TEXT_FILES)
    assert "$clin-nav" in combined
    assert "skills/clin-nav/" in combined
    assert "$clinical-data-research-navigator" not in combined
    assert "skills/clinical-data-research-navigator/" not in combined


def test_released_history_still_contains_the_original_skill_identity():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for root in HISTORICAL_ROOTS
        for path in root.rglob("*.md")
    )
    assert "clinical-data-research-navigator" in combined
