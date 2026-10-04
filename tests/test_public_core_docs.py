"""Pin public installation examples to their intended release and trust root."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(("name", "heading"), [
    ("installation.md", "## Current verified v0.8.0 Release artifact verification"),
    ("installation.zh-TW.md", "## 目前已驗證的 v0.8.0 Release 產物核對"),
])
def test_current_release_asset_names_are_consistent(name, heading):
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    assert "clin-nav-0.8.0.zip" in section
    assert "clin-nav-0.8.0.manifest.json" in section
    assert "clin-nav-0.7.0." not in section
    assert 'release_version="0.4.0"' in text


def test_release_docs_describe_dispatch_sha_not_tag_checkout():
    workflow = yaml.safe_load((ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8"))
    for name in ("preflight", "validate", "build"):
        checkout = [step for step in workflow["jobs"][name]["steps"]
                    if str(step.get("uses", "")).startswith("actions/checkout@")]
        assert checkout and all(step["with"]["ref"] == "${{ github.sha }}" for step in checkout)
    text = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
    assert "refs/heads/main" in text
    assert "github.sha" in text
    assert "tag does not control checkout" in text.casefold()
