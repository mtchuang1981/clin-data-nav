"""Pin public installation examples to their intended release and trust root."""
from pathlib import Path

import pytest
import yaml
import re

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


@pytest.mark.parametrize(("name", "maturity"), [
    ("teae-to-sas-spec.md", "dictionary-specified"),
    ("omop-phenotype-to-sql-spec.md", "conceptual"),
    ("synthetic-institutional-mapping.md", "dictionary-specified"),
])
def test_examples_match_implementation_contract(name, maturity):
    text = (ROOT / "examples" / name).read_text(encoding="utf-8")
    for field in ("Output depth", "Decision", "Confirmed facts", "Assumptions", "Limitations", "Sources actually consulted"):
        assert re.search(rf"(?m)^{field}:\s+\S", text)
    assert "Output depth: implementation specification" in text
    sections = re.findall(r"(?m)^## (.+)$", text)
    assert sections == ["Governing evidence", "Data contract", "Code maturity", "Validation gaps", "Execution gate"]
    maturity_section = text.split("## Code maturity", 1)[1].split("\n## ", 1)[0]
    assert maturity in maturity_section
    assert not set(("conceptual", "dictionary-specified", "parameterized", "executable", "validated")) - {maturity} & set(re.findall(r"`([^`]+)`", maturity_section))
    assert "SPECIFICATION ONLY — NOT EXECUTABLE" in text and "unmet" in text.casefold()
    assert "| Gap | Blocks | Next safe action | Responsible role | Completion evidence |" in text
    assert "Work still possible" in text
    if maturity == "dictionary-specified":
        assumptions = re.search(r"(?m)^Assumptions: (.+)$", text).group(1)
        assert "synthetic" in assumptions.casefold() and "approved dictionary" in assumptions.casefold()
        facts = re.search(r"(?m)^Confirmed facts: (.+)$", text).group(1)
        assert "approved dictionary" not in facts.casefold()


def test_formal_gaps_are_actionable_without_changing_quick_shape():
    refs = ROOT / "skills/clin-nav/references"
    template = (refs / "evidence-output-template.md").read_text(encoding="utf-8")
    assert "| Gap | Blocks | Next safe action | Responsible role | Completion evidence |" in template
    for clause in ("unknown", "unavailable", "not reviewed", "known failure", "pending approval", "conflict", "Work still possible", "new authorization", "role is unknown"):
        assert clause in template
    for path in (ROOT / "skills/clin-nav/SKILL.md", refs / "output-depths-and-learning-paths.md"):
        text = path.read_text(encoding="utf-8")
        assert "actionable gaps" in text.casefold() and "evidence-output-template.md" in text
    quick = template.split("## Quick Explanation", 1)[1].split("\n## ", 1)[0]
    assert "without a fixed header" in quick
    assert "Responsible role" not in quick


def test_research_gaps_do_not_require_physical_execution_gates():
    text = (ROOT / "skills/clin-nav/references/evidence-output-template.md").read_text(encoding="utf-8")
    research = text.split("## Research Design", 1)[1].split("\n## Implementation Specification", 1)[0]
    assert "design-appropriate review" in research
    assert "does not require metadata or fixtures" in research


@pytest.mark.parametrize(("name", "optional", "python", "trust", "bytes_limit"), [
    ("installation.md", "Optional read-only", "does not require Python", "trusted publication", "not byte-identical"),
    ("installation.zh-TW.md", "選用的唯讀", "不需要 Python", "可信發布依據", "不代表逐位元組相同"),
])
def test_integrity_diagnostic_is_optional_and_cannot_verify_loaded_version(name, optional, python, trust, bytes_limit):
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    for required in ("scripts/verify_installation.py", "--manifest-sha256", "--comparison", "canonical-text", "loaded_version: not-verified", "__pycache__", ".pyc", ".pyo", optional, python, trust, bytes_limit):
        assert required in text
    assert "self-created receipt" in text if name == "installation.md" else "自行產生的 receipt" in text
    readme = (ROOT / ("README.md" if name == "installation.md" else "README.zh-TW.md")).read_text(encoding="utf-8")
    assert "#optional-read-only-installation-diagnosis" in readme if name == "installation.md" else "#選用的唯讀安裝診斷" in readme
