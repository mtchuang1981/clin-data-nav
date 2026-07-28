from pathlib import Path, PurePosixPath, PureWindowsPath
import re

import yaml


REFERENCE_RE = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)")
BACKTICK_CODE_RE = re.compile(r"`([^`\r\n]+)`")
REFERENCE_ROOTS = {"agents", "assets", "references", "scripts"}


def _is_backtick_reference(value: str) -> bool:
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    normalized_parts = value.replace("\\", "/").split("/")
    return (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or value.startswith(("./", ".\\", "../", "..\\"))
        or normalized_parts[0] in REFERENCE_ROOTS
    )


def _reference_path_error(skill_dir: Path, relative: str) -> str | None:
    path = PurePosixPath(relative)
    windows_path = PureWindowsPath(relative)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or "\\" in relative
        or any(part in {"", ".", ".."} for part in relative.split("/"))
        or path.as_posix() != relative
    ):
        return f"unsafe reference path: {relative}"

    skill_root = skill_dir.resolve()
    referenced = (skill_dir / Path(*path.parts)).resolve(strict=False)
    if not referenced.is_relative_to(skill_root):
        return f"unsafe reference path: {relative}"
    if not referenced.is_file():
        return f"missing reference: {relative}"
    return None


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["missing SKILL.md"]
    text = skill_file.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        return ["SKILL.md must contain YAML frontmatter"]
    try:
        metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return ["SKILL.md: invalid YAML frontmatter"]
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
    backtick_references = [
        value
        for value in BACKTICK_CODE_RE.findall(parts[2])
        if _is_backtick_reference(value)
    ]
    references = dict.fromkeys(
        REFERENCE_RE.findall(parts[2]) + backtick_references
    )
    for relative in references:
        reference_error = _reference_path_error(skill_dir, relative)
        if reference_error is not None:
            errors.append(reference_error)

    openai_file = skill_dir / "agents/openai.yaml"
    if not openai_file.is_file():
        errors.append("missing agents/openai.yaml")
        return errors
    try:
        openai_metadata = yaml.safe_load(
            openai_file.read_text(encoding="utf-8")
        )
    except yaml.YAMLError:
        errors.append("agents/openai.yaml: invalid YAML")
        return errors
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
    if isinstance(default_prompt, str) and len(default_prompt) > 200:
        errors.append("default prompt must not exceed 200 Unicode code points")
    if (
        not isinstance(default_prompt, str)
        or not default_prompt.endswith((".", "!", "?"))
        or not default_prompt[:-1].strip()
        or any(terminator in default_prompt[:-1] for terminator in ".!?")
    ):
        errors.append(
            "default prompt must be exactly one non-empty sentence ending in '.', '!', or '?'"
        )
    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    failures = validate_skill(root / "skills/clinical-data-research-navigator")
    if failures:
        raise SystemExit("\n".join(failures))
