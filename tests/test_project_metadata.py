from pathlib import Path
import re
import tomllib

import pytest
import yaml

from scripts.install_local import PACKAGE_VERSION as INSTALLER_VERSION
from scripts.package_skill import PACKAGE_VERSION as PACKAGER_VERSION


ROOT = Path(__file__).resolve().parents[1]
TERMINAL_ONBOARDING_COMMANDS = (
    "node --version",
    "npm --version",
    "npx skills add mtchuang1981/clin-data-nav",
    "npx skills update clinical-data-research-navigator --project --yes",
)
CODEX_ONBOARDING_INPUTS = (
    "/skills",
    "$clinical-data-research-navigator",
)
TERMINAL_FENCE_LANGUAGES = {"bash", "sh", "shell", "powershell", "pwsh"}
FENCED_BLOCK_PATTERN = re.compile(
    r"^[ \t]*```(?P<language>[^\n`]*)[ \t]*\n"
    r"(?P<body>.*?)"
    r"^[ \t]*```[ \t]*$",
    flags=re.MULTILINE | re.DOTALL,
)
ENGLISH_ONBOARDING_CONTRACT = {
    "headings": (
        "## Quick start prerequisites",
        "## Quick start",
        "## 60-second first success",
        "## Public boundary",
    ),
    "not_terminal_phrase": "not terminal commands",
    "clarification_phrase": "question clarification",
    "missing_information_phrase": "missing-information list",
}
TRADITIONAL_CHINESE_ONBOARDING_CONTRACT = {
    "headings": (
        "## 快速開始的必要條件",
        "## 快速開始",
        "## 60 秒完成第一次使用",
        "## 公開邊界",
    ),
    "not_terminal_phrase": "不是終端機指令",
    "clarification_phrase": "問題釐清",
    "missing_information_phrase": "缺少資訊清單",
}


def _assert_readme_onboarding_contract(
    text: str,
    *,
    headings: tuple[str, str, str, str],
    not_terminal_phrase: str,
    clarification_phrase: str,
    missing_information_phrase: str,
) -> None:
    for command in (*TERMINAL_ONBOARDING_COMMANDS, *CODEX_ONBOARDING_INPUTS):
        assert command in text
    assert ".agents/skills" in text
    for heading in headings:
        assert heading in text
    for phrase in (
        not_terminal_phrase,
        clarification_phrase,
        missing_information_phrase,
    ):
        assert phrase in text

    lines = text.splitlines()
    heading_positions = []
    for heading in headings:
        assert lines.count(heading) == 1, (
            f"onboarding heading must appear exactly once: {heading}"
        )
        heading_positions.append(lines.index(heading))
    assert heading_positions == sorted(heading_positions), (
        "onboarding sections must appear in the required order"
    )

    onboarding = "\n".join(
        lines[heading_positions[0] : heading_positions[-1]]
    )
    blocks = [
        (match["language"].strip(), match["body"])
        for match in FENCED_BLOCK_PATTERN.finditer(onboarding)
    ]
    bash_blocks = [body for language, body in blocks if language == "bash"]
    terminal_blocks = [
        body
        for language, body in blocks
        if language in TERMINAL_FENCE_LANGUAGES
    ]
    bash_lines = {
        line.strip()
        for body in bash_blocks
        for line in body.splitlines()
    }
    for command in TERMINAL_ONBOARDING_COMMANDS:
        assert command in bash_lines, (
            f"terminal command must be an exact line in a bash block: {command}"
        )
    joined_terminal_blocks = "\n".join(terminal_blocks)
    for codex_input in CODEX_ONBOARDING_INPUTS:
        assert codex_input not in joined_terminal_blocks, (
            f"Codex input must not appear in a terminal block: {codex_input}"
        )

    quick_start = "\n".join(
        lines[heading_positions[1] : heading_positions[2]]
    )
    quick_start_prose = FENCED_BLOCK_PATTERN.sub("", quick_start)
    sentences = " ".join(quick_start_prose.split()).replace("。", ".").split(".")
    assert any(
        "Codex" in sentence
        and not_terminal_phrase in sentence
        and all(
            codex_input in sentence
            for codex_input in CODEX_ONBOARDING_INPUTS
        )
        for sentence in sentences
    ), "Codex inputs must be identified together as non-terminal inputs"


def test_pyproject_declares_explicit_setuptools_package_boundary():
    project = tomllib.loads(
        (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert project["build-system"] == {
        "requires": ["setuptools>=68"],
        "build-backend": "setuptools.build_meta",
    }
    assert project["tool"]["setuptools"]["packages"] == ["scripts"]


def test_ci_has_dual_platform_read_only_jobs_and_required_commands():
    workflow_path = ROOT / ".github/workflows/validate.yml"
    workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))
    job = workflow["jobs"]["test"]

    assert workflow["permissions"] == {"contents": "read"}
    assert job["runs-on"] == "${{ matrix.os }}"
    assert set(job["strategy"]["matrix"]["os"]) == {
        "ubuntu-latest",
        "windows-latest",
    }
    rendered = workflow_path.read_text(encoding="utf-8")
    for command in (
        'python -m pip install -e ".[dev]"',
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    ):
        assert command in rendered
    assert "continue-on-error" not in rendered
    assert "secrets." not in rendered


def test_workflows_pin_official_actions_to_full_commit_shas():
    allowed_actions = {
        "actions/checkout",
        "actions/setup-python",
        "actions/upload-artifact",
        "actions/download-artifact",
    }

    for relative_path in (
        ".github/workflows/validate.yml",
        ".github/workflows/release.yml",
    ):
        workflow = yaml.load(
            (ROOT / relative_path).read_text(encoding="utf-8"),
            Loader=yaml.BaseLoader,
        )
        action_references = [
            step["uses"]
            for job in workflow["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        ]

        assert action_references
        for reference in action_references:
            action, separator, commit = reference.partition("@")
            assert separator == "@"
            assert action in allowed_actions
            assert re.fullmatch(r"[0-9a-f]{40}", commit)


def test_release_workflow_is_manual_fail_closed_and_least_privilege():
    path = ROOT / ".github/workflows/release.yml"
    rendered = path.read_text(encoding="utf-8")
    workflow = yaml.load(rendered, Loader=yaml.BaseLoader)

    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["jobs"]) == {
        "preflight",
        "validate",
        "build",
        "publish",
    }
    assert set(workflow["jobs"]["preflight"]["outputs"]) == {
        "version",
        "commit",
        "tag_object",
    }
    assert workflow["jobs"]["validate"]["needs"] == "preflight"
    assert set(workflow["jobs"]["build"]["needs"]) == {
        "preflight",
        "validate",
    }
    assert set(workflow["jobs"]["build"]["outputs"]) == {
        "artifact_id",
        "artifact_digest",
        "checksum_sha256",
    }
    assert workflow["jobs"]["publish"]["permissions"] == {"contents": "write"}
    assert set(workflow["jobs"]["publish"]["needs"]) == {
        "preflight",
        "validate",
        "build",
    }
    for job_name in ("preflight", "validate", "build"):
        checkout = next(
            step
            for step in workflow["jobs"][job_name]["steps"]
            if step.get("uses", "").startswith("actions/checkout@")
        )
        assert checkout["with"]["persist-credentials"] == "false"
    for job_name in ("validate", "build"):
        checkout = next(
            step
            for step in workflow["jobs"][job_name]["steps"]
            if step.get("uses", "").startswith("actions/checkout@")
        )
        assert checkout["with"]["ref"] == (
            "${{ needs.preflight.outputs.commit }}"
        )

    build_steps = workflow["jobs"]["build"]["steps"]
    build_rendered = "\n".join(
        step.get("run", "") for step in build_steps
    )
    upload_step = next(
        step
        for step in build_steps
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert upload_step["id"] == "upload"
    assert upload_step["with"]["if-no-files-found"] == "error"
    assert "python scripts/package_skill.py" in build_rendered
    assert "python scripts/verify_release.py artifacts" in build_rendered
    assert "release-notes.md" in build_rendered
    assert "release-bundle.sha256" in build_rendered

    publish_steps = workflow["jobs"]["publish"]["steps"]
    assert all(
        not step.get("uses", "").startswith(
            ("actions/checkout@", "actions/setup-python@")
        )
        for step in publish_steps
    )
    assert not any(
        forbidden in step.get("run", "")
        for step in publish_steps
        for forbidden in (
            "python ",
            "pip ",
            "scripts/",
            "git checkout",
        )
    )
    download_step = next(
        step
        for step in publish_steps
        if step.get("uses", "").startswith("actions/download-artifact@")
    )
    assert download_step["with"]["artifact-ids"] == (
        "${{ needs.build.outputs.artifact_id }}"
    )
    verify_step = next(
        step
        for step in publish_steps
        if step.get("name") == "Verify release bundle transit integrity"
    )
    release_step = next(
        step
        for step in publish_steps
        if step.get("name") == "Recheck remote state and publish immutable Release"
    )
    assert "GH_TOKEN" not in verify_step.get("env", {})
    assert "sha256sum --check" in verify_step["run"]
    assert "CHECKSUM_SHA256" in verify_step["env"]
    assert "gh release create" not in verify_step["run"]
    assert release_step["env"]["GH_TOKEN"] == "${{ github.token }}"
    assert "python scripts/" not in release_step["run"]
    assert "git ls-remote" in release_step["run"]
    assert "refs/tags/$TAG^{}" in release_step["run"]
    assert "/releases/tags/$TAG" in release_step["run"]
    assert release_step["run"].index("git ls-remote") < release_step["run"].index(
        "gh release create"
    )
    assert release_step["run"].index("/releases/tags/$TAG") < release_step[
        "run"
    ].index("gh release create")
    assert rendered.count("GH_TOKEN:") == 1
    assert rendered.count("contents: write") == 1
    assert "python scripts/verify_release.py ref" in rendered
    assert "python scripts/verify_release.py artifacts" in rendered
    assert "python scripts/package_skill.py" in rendered
    assert 'git rev-parse "$TAG^{tag}"' in rendered
    assert 'git rev-parse "$TAG^{commit}"' in rendered
    assert "git ls-remote" in rendered
    assert "VERIFIED_TAG_OBJECT" in rendered
    assert "VERIFIED_COMMIT" in rendered
    assert "gh release create" in rendered
    assert "--verify-tag" in rendered
    assert "continue-on-error" not in rendered
    assert "release edit" not in rendered
    assert "git tag -f" not in rendered


def test_citation_and_license_metadata():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert citation["title"] == "Clinical Data Research Navigator"
    assert citation["version"] == "0.2.2"
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_release_version_is_synchronized():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_zh_tw = (ROOT / "CHANGELOG.zh-TW.md").read_text(encoding="utf-8")

    assert project["project"]["version"] == "0.2.2"
    assert citation["version"] == "0.2.2"
    assert PACKAGER_VERSION == "0.2.2"
    assert INSTALLER_VERSION == "0.2.2"
    assert "## 0.2.2 - 2026-07-29" in changelog
    assert "## 0.2.2 - 2026-07-29" in changelog_zh_tw


def test_v022_release_notes_are_static_uploadable_notes_without_candidate_state():
    notes = (
        ROOT / "docs" / "releases" / "0.2.2.md"
    ).read_text(encoding="utf-8")

    assert notes.startswith("# Clinical Data Research Navigator v0.2.2\n")
    for candidate_state in (
        "pending",
        "this commit is pushed",
        "此 commit 推送",
        "觸發與發布",
    ):
        assert candidate_state not in notes
    assert "npx skills add mtchuang1981/clin-data-nav" in notes


def test_readmes_document_quick_start_verified_installation_and_activation():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    for text in (english, traditional_chinese):
        assert "npx skills add mtchuang1981/clin-data-nav" in text
        assert ".agents/skills" in text
        assert "/skills" in text
        assert "$HOME/.agents/skills" in text
        assert "$clinical-data-research-navigator" in text
        assert "v0.2.1" in text
        assert "SHA-256" in text

    assert "## Quick start" in english
    assert "from the root of the project" in english
    assert "## Verified manual installation from GitHub Release" in english
    assert "## Use the Skill" in english

    assert "## 快速開始" in traditional_chinese
    assert "要使用此 Skill 的專案根目錄" in traditional_chinese
    assert "## 經驗證的 GitHub Release 手動安裝" in traditional_chinese
    assert "## 使用 Skill" in traditional_chinese

    for text, manual_heading, next_heading in (
        (
            english,
            "## Verified manual installation from GitHub Release",
            "## Install from source",
        ),
        (
            traditional_chinese,
            "## 經驗證的 GitHub Release 手動安裝",
            "## 從原始碼安裝",
        ),
    ):
        manual_install = text.split(manual_heading, maxsplit=1)[1].split(
            next_heading,
            maxsplit=1,
        )[0]
        assert 'releaseVersion = "0.2.1"' in manual_install
        assert 'release_version="0.2.1"' in manual_install
        assert "v0.2.2" not in manual_install


def test_readmes_define_prerequisites_command_boundaries_and_first_success():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    _assert_readme_onboarding_contract(
        english,
        **ENGLISH_ONBOARDING_CONTRACT,
    )
    _assert_readme_onboarding_contract(
        traditional_chinese,
        **TRADITIONAL_CHINESE_ONBOARDING_CONTRACT,
    )


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
        pytest.param(
            lambda text: text.replace(
                "## Quick start prerequisites",
                "## temporary heading",
                1,
            )
            .replace("## Quick start", "## Quick start prerequisites", 1)
            .replace("## temporary heading", "## Quick start", 1),
            "required order",
            id="section-order",
        ),
        pytest.param(
            lambda text: text.replace(
                "```bash\nnode --version",
                "```text\nnode --version",
                1,
            ),
            "exact line in a bash block",
            id="terminal-command-outside-bash",
        ),
        pytest.param(
            lambda text: text.replace(
                "node --version\nnpm --version",
                (
                    "node --version\n"
                    "npm --version\n"
                    "/skills\n"
                    "$clinical-data-research-navigator"
                ),
                1,
            ),
            "must not appear in a terminal block",
            id="codex-input-inside-bash",
        ),
        pytest.param(
            lambda text: text.replace(
                (
                    "`/skills` and\n"
                    "`$clinical-data-research-navigator` are entered in\n"
                    "Codex; they are not terminal commands."
                ),
                (
                    "`Skill discovery` and\n"
                    "`Skill invocation` are entered in\n"
                    "Codex; they are not terminal commands."
                ),
                1,
            ),
            "identified together as non-terminal inputs",
            id="codex-input-outside-explanation",
        ),
    ),
)
def test_readme_onboarding_contract_rejects_misplaced_instructions(
    mutation,
    expected_error,
):
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    misplaced = mutation(english)

    assert misplaced != english
    with pytest.raises(AssertionError, match=expected_error):
        _assert_readme_onboarding_contract(
            misplaced,
            **ENGLISH_ONBOARDING_CONTRACT,
        )


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
