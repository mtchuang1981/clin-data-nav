from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_ci_has_read_only_permissions_and_required_commands():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    )
    assert workflow["permissions"] == {"contents": "read"}
    rendered = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    for command in (
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    ):
        assert command in rendered
    assert "secrets." not in rendered


def test_citation_and_license_metadata():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert citation["title"] == "Clinical Data Research Navigator"
    assert citation["version"] == "0.1.0"
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
