from pathlib import Path
import re

import yaml


REFERENCE_RE = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)")


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["missing SKILL.md"]
    text = skill_file.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        return ["SKILL.md must contain YAML frontmatter"]
    metadata = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict) or set(metadata) != {"name", "description"}:
        errors.append("frontmatter only permits name and description")
        metadata = metadata if isinstance(metadata, dict) else {}
    if metadata.get("name") != skill_dir.name:
        errors.append("skill name must match directory name")
    description = metadata.get("description", "")
    if not isinstance(description, str) or not description.startswith("Use when"):
        errors.append("description must start with 'Use when'")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")
    for relative in REFERENCE_RE.findall(parts[2]):
        if not (skill_dir / relative).is_file():
            errors.append(f"missing reference: {relative}")

    openai_file = skill_dir / "agents/openai.yaml"
    if not openai_file.is_file():
        errors.append("missing agents/openai.yaml")
        return errors
    openai_metadata = yaml.safe_load(openai_file.read_text(encoding="utf-8"))
    interface = (
        openai_metadata.get("interface", {})
        if isinstance(openai_metadata, dict)
        else {}
    )
    if not isinstance(interface, dict):
        interface = {}
    if interface.get("display_name") != "Clinical Data Research Navigator":
        errors.append("display name mismatch")
    if not isinstance(interface.get("short_description"), str) or not interface[
        "short_description"
    ]:
        errors.append("short description must be a non-empty string")
    default_prompt = interface.get("default_prompt")
    if not isinstance(default_prompt, str) or "clinical-data" not in default_prompt:
        errors.append("default prompt must contain clinical-data")
    if not isinstance(default_prompt, str) or (
        "$clinical-data-research-navigator" not in default_prompt
    ):
        errors.append(
            "default prompt must mention $clinical-data-research-navigator"
        )
    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    failures = validate_skill(root / "skills/clinical-data-research-navigator")
    if failures:
        raise SystemExit("\n".join(failures))
