from pathlib import Path
import tomllib

import yaml

from scripts.install_local import PACKAGE_VERSION as INSTALLER_VERSION
from scripts.package_skill import PACKAGE_VERSION as PACKAGER_VERSION


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
    assert citation["version"] == "0.2.0"
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_release_version_is_synchronized():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_zh_tw = (ROOT / "CHANGELOG.zh-TW.md").read_text(encoding="utf-8")

    assert project["project"]["version"] == "0.2.0"
    assert citation["version"] == "0.2.0"
    assert PACKAGER_VERSION == "0.2.0"
    assert INSTALLER_VERSION == "0.2.0"
    assert "## 0.2.0 - 2026-07-28" in changelog
    assert "## 0.2.0 - 2026-07-28" in changelog_zh_tw


def test_readmes_document_quick_start_verified_installation_and_activation():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    for text in (english, traditional_chinese):
        assert "npx skills add mtchuang1981/clin-data-nav" in text
        assert ".agents/skills" in text
        assert "/skills" in text
        assert "$HOME/.agents/skills" in text
        assert "$clinical-data-research-navigator" in text
        assert "v0.2.0" in text
        assert "SHA-256" in text

    assert "## Quick start" in english
    assert "from the root of the project" in english
    assert "## Verified manual installation from GitHub Release" in english
    assert "## Use the Skill" in english

    assert "## 快速開始" in traditional_chinese
    assert "要使用此 Skill 的專案根目錄" in traditional_chinese
    assert "## 經驗證的 GitHub Release 手動安裝" in traditional_chinese
    assert "## 使用 Skill" in traditional_chinese


def test_readmes_explain_cdisc_models_and_python_runtime_boundary():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    assert "## New to clinical-data standards?" in english
    assert "## 第一次接觸臨床資料標準？" in traditional_chinese
    for term in ("CDISC", "SDTM", "ADaM"):
        assert term in english
        assert term in traditional_chinese
    for official_url in (
        "https://www.cdisc.org/standards",
        "https://www.cdisc.org/standards/foundational/sdtm",
        "https://www.cdisc.org/standards/foundational/adam",
    ):
        assert official_url in english
        assert official_url in traditional_chinese

    assert "Collected or received study data" in english
    assert "收集或接收的研究資料" in traditional_chinese
    assert "Using the installed Skill does not require Python." in english
    assert "使用已安裝的 Skill 不需要 Python。" in traditional_chinese
    assert "## Contributor setup (Python 3.11)" in english
    assert "## 貢獻者環境（Python 3.11）" in traditional_chinese
    assert "not every clinical-data question" in english
    assert "不是每一個臨床資料問題" in traditional_chinese

    english_posix = english.split("POSIX shell:", 1)[1].split(
        "## Install from a source checkout",
        1,
    )[0]
    chinese_posix = traditional_chinese.split("POSIX shell：", 1)[1].split(
        "## 從原始碼安裝",
        1,
    )[0]
    assert "python -c" not in english_posix
    assert "python -c" not in chinese_posix


def test_readmes_explain_rwe_routing_and_optional_build_rwe_sap():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    assert "## Real-world evidence and causal-study routing" in english
    assert "## 真實世界證據與因果研究路由" in traditional_chinese
    assert "RWD is not automatically RWE." in english
    assert "RWD 不會自動成為 RWE。" in traditional_chinese
    assert "causal-comparative" in english
    assert "因果比較" in traditional_chinese
    assert "`build-rwe-sap` is optional and is not bundled" in english
    assert "`build-rwe-sap` 是選配項目，並未內附" in traditional_chinese
    assert "never installs it automatically" in english
    assert "不會自動安裝" in traditional_chinese
    assert "Normal Core use does not require `build-rwe-sap`" in english
    assert "一般 Core 功能不需要 `build-rwe-sap`" in traditional_chinese


def test_citation_has_required_cff_1_2_schema_shape_and_author():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert isinstance(citation, dict)
    assert citation["cff-version"] == "1.2.0"
    assert citation["type"] == "software"
    for field in ("message", "title", "version", "license"):
        assert isinstance(citation[field], str) and citation[field].strip()
    assert citation["authors"] == [
        {"name": "Clinical Data Research Navigator contributors"}
    ]
    for author in citation["authors"]:
        assert isinstance(author, dict)
        assert (
            isinstance(author.get("name"), str)
            and author["name"].strip()
        ) or (
            isinstance(author.get("family-names"), str)
            and author["family-names"].strip()
        )


def test_contribution_provenance_evidence_is_required_without_private_documents():
    contributing = " ".join(
        (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8").split()
    )
    pr_template = " ".join(
        (ROOT / ".github/pull_request_template.md").read_text(
            encoding="utf-8"
        ).split()
    )
    for text in (contributing, pr_template):
        assert "auditable provenance" in text
        assert "source URL or identifier" in text
        assert "license, permission, or attestation" in text
        assert (
            "do not submit private or login-gated documents as evidence"
            in text.lower()
        )


def test_architecture_separates_independent_gates_from_packaging():
    architecture = " ".join(
        (ROOT / "docs/architecture.md").read_text(encoding="utf-8").split()
    )
    assert "Scanner --> Packager" not in architecture
    assert "Evaluator --> Packager" not in architecture
    assert "independent verification gates" in architecture
    assert "only validator is the packager's direct dependency" in architecture
    assert "does not imply that the boundary scan or evaluator passed" in architecture


def test_architecture_describes_ci_network_boundary_accurately():
    architecture = " ".join(
        (ROOT / "docs/architecture.md").read_text(encoding="utf-8").split()
    )
    assert "CI is offline" not in architecture
    assert "credential-free" in architecture
    assert "After dependency acquisition" in architecture
    assert "no institutional or external LLM network calls" in architecture
