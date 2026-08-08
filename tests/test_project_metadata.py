from pathlib import Path
import re
import subprocess
import sys
import tomllib

import pytest
import yaml

from scripts.install_local import PACKAGE_VERSION as INSTALLER_VERSION
from scripts.package_skill import PACKAGE_VERSION as PACKAGER_VERSION


ROOT = Path(__file__).resolve().parents[1]
TERMINAL_ONBOARDING_COMMANDS = (
    "node --version",
    "npm --version",
    "npx --version",
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
    "not_terminal_phrase": "not terminal commands",
    "clarification_phrase": "question clarification",
    "missing_information_phrase": "missing-information list",
}
TRADITIONAL_CHINESE_ONBOARDING_CONTRACT = {
    "not_terminal_phrase": "不是終端機指令",
    "clarification_phrase": "問題釐清",
    "missing_information_phrase": "缺少資訊清單",
}
VALIDATION_BADGE_IMAGE = (
    "https://github.com/mtchuang1981/clin-data-nav/"
    "actions/workflows/validate.yml/badge.svg?branch=main"
)
VALIDATION_BADGE_LINK = (
    "https://github.com/mtchuang1981/clin-data-nav/"
    "actions/workflows/validate.yml?query=branch%3Amain"
)
README_NAVIGATION_TARGETS = {
    "README.md": (
        "docs/installation.md",
        "docs/glossary.md",
        "docs/learning-paths.md",
        "examples/teae-to-sas-spec.md",
        "examples/omop-phenotype-to-sql-spec.md",
        "examples/synthetic-institutional-mapping.md",
        (
            "skills/clinical-data-research-navigator/references/"
            "evidence-output-template.md"
        ),
        "CONTRIBUTING.md",
        "SECURITY.md",
        "docs/release.md",
    ),
    "README.zh-TW.md": (
        "docs/installation.zh-TW.md",
        "docs/glossary.zh-TW.md",
        "docs/learning-paths.zh-TW.md",
        "examples/teae-to-sas-spec.md",
        "examples/omop-phenotype-to-sql-spec.md",
        "examples/synthetic-institutional-mapping.md",
        (
            "skills/clinical-data-research-navigator/references/"
            "evidence-output-template.md"
        ),
        "CONTRIBUTING.md",
        "SECURITY.md",
        "docs/release.md",
    ),
}
INSTALLATION_TROUBLESHOOTING_CONTRACTS = (
    (
        "missing-node",
        ("node", "npm", "npx", "PATH"),
        ("Node.js", "restart"),
    ),
    (
        "install-command-failure",
        ("npx skills add", "repository", "network"),
        ("diagnostic", "retry"),
    ),
    (
        "activation-failure",
        (".agents/skills", "/skills", "SKILL.md"),
        ("project root", "restart"),
    ),
    (
        "stale-after-update",
        ("npx skills update", "/skills"),
        ("restart", "project"),
    ),
    (
        "download-failure",
        ("ZIP", "manifest", "Release"),
        ("same release", "retry"),
    ),
    (
        "manifest-mismatch",
        ("SHA-256", "manifest"),
        ("do not extract", "download"),
    ),
    (
        "existing-target",
        ("already exists", "refuse"),
        ("inspect", "different destination"),
    ),
    (
        "python-setup-failure",
        ("Python 3.11", "python --version"),
        ("virtual environment", "dependency"),
    ),
)
TRADITIONAL_CHINESE_TROUBLESHOOTING_CONTRACTS = (
    (
        "missing-node",
        ("node", "npm", "npx", "PATH"),
        ("Node.js", "重新啟動"),
    ),
    (
        "install-command-failure",
        ("npx skills add", "儲存庫", "網路"),
        ("診斷", "重新執行"),
    ),
    (
        "activation-failure",
        (".agents/skills", "/skills", "SKILL.md"),
        ("專案根目錄", "重新啟動"),
    ),
    (
        "stale-after-update",
        ("npx skills update", "/skills"),
        ("重新啟動", "專案"),
    ),
    (
        "download-failure",
        ("ZIP", "manifest", "Release"),
        ("同一個 Release", "重新下載"),
    ),
    (
        "manifest-mismatch",
        ("SHA-256", "manifest"),
        ("不要解壓縮", "下載"),
    ),
    (
        "existing-target",
        ("已存在", "拒絕"),
        ("檢查", "另一個目的目錄"),
    ),
    (
        "python-setup-failure",
        ("Python 3.11", "python --version"),
        ("虛擬環境", "相依套件"),
    ),
)
GLOSSARY_TERM_KEYS = (
    "clinical-research",
    "cdisc",
    "sdtm",
    "adam",
    "omop-cdm",
    "rwd",
    "rwe",
    "pico",
    "target-trial-emulation",
    "estimand",
    "phenotype",
    "authority-level",
    "data-contract",
    "execution-gate",
    "code-maturity",
    "fixture",
    "adapter",
    "governing-artifact",
    "provenance",
    "grain",
    "key-and-join-cardinality",
    "time-zero",
    "specification-only-versus-executable",
    "sas",
    "validation-gap",
)
LEARNING_PATH_IDS = (
    "learn-the-terms",
    "assess-the-evidence",
    "prepare-an-implementation",
)


def _assert_readme_onboarding_contract(
    text: str,
    *,
    not_terminal_phrase: str,
    clarification_phrase: str,
    missing_information_phrase: str,
) -> None:
    for command in TERMINAL_ONBOARDING_COMMANDS:
        assert command in text
    for codex_input in CODEX_ONBOARDING_INPUTS:
        assert codex_input in text, (
            "Codex inputs must be identified together as non-terminal inputs"
        )
    assert ".agents/skills" in text
    for phrase in (
        not_terminal_phrase,
        clarification_phrase,
        missing_information_phrase,
    ):
        assert phrase in text

    blocks = [
        (match["language"].strip(), match["body"])
        for match in FENCED_BLOCK_PATTERN.finditer(text)
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
    terminal_lines = {
        line.strip()
        for body in terminal_blocks
        for line in body.splitlines()
    }
    for codex_input in CODEX_ONBOARDING_INPUTS:
        assert codex_input not in terminal_lines, (
            f"Codex input must not appear in a terminal block: {codex_input}"
        )

    prose = FENCED_BLOCK_PATTERN.sub("", text)
    sentences = " ".join(prose.split()).replace("。", ".").split(".")
    assert any(
        "Codex" in sentence
        and not_terminal_phrase in sentence
        and all(
            codex_input in sentence
            for codex_input in CODEX_ONBOARDING_INPUTS
        )
        for sentence in sentences
    ), "Codex inputs must be identified together as non-terminal inputs"


def _nonblank_line_index(text: str, marker: str) -> int:
    nonblank_lines = [line for line in text.splitlines() if line.strip()]
    return next(
        index for index, line in enumerate(nonblank_lines) if marker in line
    )


def _assert_first_success_order(
    text: str,
    *,
    prompt: str,
    marker: str,
    summary_lines: tuple[str, str],
) -> None:
    """Require the six onboarding elements in the approved first-success order."""
    sequence = (
        VALIDATION_BADGE_IMAGE,
        "npx skills add mtchuang1981/clin-data-nav",
        prompt,
        marker,
        *summary_lines,
    )
    positions = []
    for element in sequence:
        assert element in text
        position = _nonblank_line_index(text, element)
        assert position < 30
        positions.append(position)
    assert positions == sorted(positions)
    assert len(set(positions)) == len(positions)


def _markdown_link_targets(text: str) -> set[str]:
    return {
        target
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)
    }


def _troubleshooting_sections(text: str) -> dict[str, str]:
    anchors = tuple(
        re.findall(r'^<a id="(troubleshoot-[a-z0-9-]+)"></a>$', text, re.MULTILINE)
    )
    sections = _sections_after_anchors(text, anchors)
    return {
        anchor.removeprefix("troubleshoot-"): section
        for anchor, section in sections.items()
    }


def _document_anchor_ids(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r'^<a id="([a-z0-9-]+)"></a>$', text, re.MULTILINE))


def _sections_after_anchors(
    text: str,
    anchors: tuple[str, ...],
) -> dict[str, str]:
    sections = {}
    for index, anchor in enumerate(anchors):
        start_marker = f'<a id="{anchor}"></a>'
        start = text.index(start_marker) + len(start_marker)
        if index + 1 < len(anchors):
            end = text.index(f'<a id="{anchors[index + 1]}"></a>', start)
        else:
            end = len(text)
        sections[anchor] = text[start:end]
    return sections


def test_beginner_glossaries_have_aligned_term_keys_and_authoritative_sources():
    english = (ROOT / "docs/glossary.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "docs/glossary.zh-TW.md").read_text(
        encoding="utf-8"
    )

    assert _document_anchor_ids(english) == GLOSSARY_TERM_KEYS
    assert _document_anchor_ids(traditional_chinese) == GLOSSARY_TERM_KEYS
    for text in (english, traditional_chinese):
        for official_url in (
            "https://www.cdisc.org/standards/foundational/sdtm",
            "https://www.cdisc.org/standards/foundational/adam",
            "https://ohdsi.github.io/CommonDataModel/",
            (
                "https://www.fda.gov/science-research/"
                "science-and-research-special-topics/real-world-evidence"
            ),
            (
                "https://www.fda.gov/regulatory-information/"
                "search-fda-guidance-documents/e9r1-statistical-principles-"
                "clinical-trials-addendum-estimands-and-sensitivity-analysis-"
                "clinical"
            ),
            (
                "https://www.nice.org.uk/corporate/ecd9/chapter/"
                "methods-for-real-world-studies-of-comparative-effects"
            ),
        ):
            assert official_url in text


def test_beginner_glossaries_explain_model_purposes_and_validation_boundary():
    english = " ".join(
        (ROOT / "docs/glossary.md").read_text(encoding="utf-8").split()
    )
    traditional_chinese = " ".join(
        (ROOT / "docs/glossary.zh-TW.md").read_text(encoding="utf-8").split()
    )

    for phrase in (
        "SDTM organizes study data for regulatory submission",
        "ADaM supports analysis",
        "OMOP CDM standardizes observational data",
        "None of these standards makes source data automatically valid.",
    ):
        assert phrase in english
    for phrase in (
        "SDTM 會整理提交主管機關的研究資料",
        "ADaM 支援分析",
        "OMOP CDM 將觀察性資料標準化",
        "這些標準都不會讓來源資料自動變成有效資料。",
    ):
        assert phrase in traditional_chinese


def test_bilingual_rwd_definitions_preserve_the_varied_source_authority_meaning():
    """The zh-TW definition must not narrow RWD to routine care alone."""
    english_document = (ROOT / "docs/glossary.md").read_text(encoding="utf-8")
    chinese_document = (ROOT / "docs/glossary.zh-TW.md").read_text(
        encoding="utf-8"
    )
    english = english_document.split('<a id="rwd"></a>', 1)[1].split(
        '<a id="rwe"></a>', 1
    )[0]
    traditional_chinese = chinese_document.split(
        '<a id="rwd"></a>', 1
    )[1].split('<a id="rwe"></a>', 1)[0]

    for phrase in (
        "routinely collected",
        "patient health status",
        "health-care delivery",
    ):
        assert phrase in english
    for phrase in ("多種來源", "例行收集", "病人健康狀態", "醫療服務提供"):
        assert phrase in traditional_chinese


def test_beginner_learning_paths_are_aligned_and_do_not_require_code():
    documents = (
        (
            (ROOT / "docs/learning-paths.md").read_text(encoding="utf-8"),
            (
                "Goal",
                "Prerequisites",
                "Starting prompt",
                "Expected depth",
                "Cannot prove",
                "Next reading",
                "Stop or escalate when",
            ),
            ":",
            {
                "learn-the-terms": (
                    "./glossary.md#cdisc",
                    "./installation.md",
                    "../examples/teae-to-sas-spec.md",
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/output-depths-and-learning-paths.md"
                    ),
                ),
                "assess-the-evidence": (
                    "./glossary.md#rwd",
                    "./installation.md",
                    "../examples/omop-phenotype-to-sql-spec.md",
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/rwe-question-routing.md"
                    ),
                ),
                "prepare-an-implementation": (
                    "./glossary.md#data-contract",
                    "./installation.md",
                    "../examples/synthetic-institutional-mapping.md",
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/institutional-adapter-contract.md"
                    ),
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/evidence-output-template.md"
                        "#implementation-specification"
                    ),
                ),
            },
            "Not every path ends in code.",
        ),
        (
            (ROOT / "docs/learning-paths.zh-TW.md").read_text(encoding="utf-8"),
            (
                "目標",
                "先備條件",
                "起始提示",
                "預期深度",
                "無法證明",
                "接著閱讀",
                "停止或升級條件",
            ),
            "：",
            {
                "learn-the-terms": (
                    "./glossary.zh-TW.md#cdisc",
                    "./installation.zh-TW.md",
                    "../examples/teae-to-sas-spec.md",
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/output-depths-and-learning-paths.md"
                    ),
                ),
                "assess-the-evidence": (
                    "./glossary.zh-TW.md#rwd",
                    "./installation.zh-TW.md",
                    "../examples/omop-phenotype-to-sql-spec.md",
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/rwe-question-routing.md"
                    ),
                ),
                "prepare-an-implementation": (
                    "./glossary.zh-TW.md#data-contract",
                    "./installation.zh-TW.md",
                    "../examples/synthetic-institutional-mapping.md",
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/institutional-adapter-contract.md"
                    ),
                    (
                        "../skills/clinical-data-research-navigator/"
                        "references/evidence-output-template.md"
                        "#implementation-specification"
                    ),
                ),
            },
            "不是每條路徑都要以程式碼收尾。",
        ),
    )

    for text, field_labels, colon, expected_links, no_code_claim in documents:
        assert _document_anchor_ids(text) == LEARNING_PATH_IDS
        sections = _sections_after_anchors(text, LEARNING_PATH_IDS)
        for path_id, section in sections.items():
            for label in field_labels:
                assert section.count(f"**{label}{colon}**") == 1
            for expected_link in expected_links[path_id]:
                assert expected_link in section
        assert no_code_claim in text

    assert "`quick explanation`" in documents[0][0]
    assert "`evidence navigation`" in documents[0][0]
    assert "`research design`" in documents[0][0]
    assert "`implementation specification`" in documents[0][0]
    assert "`quick explanation`" in documents[1][0]
    assert "`evidence navigation`" in documents[1][0]
    assert "`research design`" in documents[1][0]
    assert "`implementation specification`" in documents[1][0]


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
    workflow = yaml.load(
        workflow_path.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    job = workflow["jobs"]["test"]

    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["on"] == {
        "pull_request": "",
        "push": {"branches": ["main"]},
    }
    assert job["runs-on"] == "${{ matrix.os }}"
    assert job["strategy"]["matrix"]["os"] == [
        "ubuntu-latest",
        "windows-latest",
    ]

    steps = job["steps"]
    gate_commands = (
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    )
    run_commands = [step["run"] for step in steps if "run" in step]
    gate_indices = [run_commands.index(command) for command in gate_commands]
    build_index = run_commands.index(
        "python scripts/package_skill.py --output-dir dist"
    )
    assert gate_indices == sorted(gate_indices)
    assert max(gate_indices) < build_index

    upload_steps = [
        (index, step)
        for index, step in enumerate(steps)
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    assert len(upload_steps) == 1
    upload_index, upload_step = upload_steps[0]
    assert upload_index > next(
        index
        for index, step in enumerate(steps)
        if step.get("run") == "python scripts/package_skill.py --output-dir dist"
    )
    assert upload_step["with"] == {
        "name": "package-${{ runner.os }}-${{ github.sha }}",
        "path": "dist/*.zip\ndist/*.manifest.json\n",
        "if-no-files-found": "error",
        "retention-days": "1",
    }

    compare_job = workflow["jobs"]["compare-packages"]
    assert compare_job["needs"] == "test"
    assert compare_job["runs-on"] == "ubuntu-latest"
    assert compare_job["permissions"] == {"contents": "read"}
    compare_steps = compare_job["steps"]
    checkout = next(
        step
        for step in compare_steps
        if step.get("uses", "").startswith("actions/checkout@")
    )
    assert checkout["with"] == {
        "ref": "${{ github.sha }}",
        "persist-credentials": "false",
    }
    setup_python = next(
        step
        for step in compare_steps
        if step.get("uses", "").startswith("actions/setup-python@")
    )
    assert setup_python["with"] == {"python-version": "3.11"}
    downloads = [
        step["with"]
        for step in compare_steps
        if step.get("uses", "").startswith("actions/download-artifact@")
    ]
    assert downloads == [
        {
            "name": "package-Linux-${{ github.sha }}",
            "path": "candidate-packages/Linux",
        },
        {
            "name": "package-Windows-${{ github.sha }}",
            "path": "candidate-packages/Windows",
        },
    ]
    compare_runs = [step["run"] for step in compare_steps if "run" in step]
    assert compare_runs == [
        "python scripts/compare_packages.py --first candidate-packages/Linux --second candidate-packages/Windows"
    ]
    assert all("pip" not in command for command in compare_runs)

    for candidate_job in workflow["jobs"].values():
        assert candidate_job.get("permissions", {"contents": "read"}) == {
            "contents": "read"
        }

    rendered = workflow_path.read_text(encoding="utf-8")
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


def test_validation_workflow_uses_verified_node24_action_pins():
    path = ROOT / ".github/workflows/validate.yml"
    rendered = path.read_text(encoding="utf-8")
    workflow = yaml.load(rendered, Loader=yaml.BaseLoader)
    expected_pins = {
        "actions/checkout": (
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            "v7.0.1",
        ),
        "actions/setup-python": (
            "5fda3b95a4ea91299a34e894583c3862153e4b97",
            "v7.0.0",
        ),
        "actions/upload-artifact": (
            "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
            "v7.0.1",
        ),
        "actions/download-artifact": (
            "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
            "v8.0.1",
        ),
    }
    references = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "uses" in step
    ]

    for action, (commit, version) in expected_pins.items():
        matching_references = [
            reference
            for reference in references
            if reference.startswith(f"{action}@")
        ]
        assert matching_references
        assert set(matching_references) == {f"{action}@{commit}"}
        assert rendered.count(f"{action}@{commit} # {version}") == len(
            matching_references
        )


def test_release_workflow_uses_verified_node24_action_pins():
    path = ROOT / ".github/workflows/release.yml"
    rendered = path.read_text(encoding="utf-8")
    workflow = yaml.load(rendered, Loader=yaml.BaseLoader)
    expected_pins = {
        "actions/checkout": (
            "3d3c42e5aac5ba805825da76410c181273ba90b1",
            "v7.0.1",
        ),
        "actions/setup-python": (
            "5fda3b95a4ea91299a34e894583c3862153e4b97",
            "v7.0.0",
        ),
        "actions/upload-artifact": (
            "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
            "v7.0.1",
        ),
        "actions/download-artifact": (
            "3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c",
            "v8.0.1",
        ),
    }
    references = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "uses" in step
    ]

    for action, (commit, version) in expected_pins.items():
        matching_references = [
            reference
            for reference in references
            if reference.startswith(f"{action}@")
        ]
        assert matching_references
        assert set(matching_references) == {f"{action}@{commit}"}
        assert rendered.count(f"{action}@{commit} # {version}") == len(
            matching_references
        )


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
    validate_job = workflow["jobs"]["validate"]
    assert validate_job["runs-on"] == "${{ matrix.os }}"
    assert validate_job["strategy"]["matrix"]["os"] == [
        "ubuntu-latest",
        "windows-latest",
    ]
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

    validate_steps = validate_job["steps"]
    validate_runs = [step["run"] for step in validate_steps if "run" in step]
    gate_commands = (
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    )
    gate_indices = [validate_runs.index(command) for command in gate_commands]
    candidate_build = "python scripts/package_skill.py --output-dir dist"
    candidate_build_index = validate_runs.index(candidate_build)
    assert gate_indices == sorted(gate_indices)
    assert max(gate_indices) < candidate_build_index
    validate_upload_index, validate_upload = next(
        (index, step)
        for index, step in enumerate(validate_steps)
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert validate_upload_index > next(
        index
        for index, step in enumerate(validate_steps)
        if step.get("run") == candidate_build
    )
    assert validate_upload["with"] == {
        "name": (
            "package-${{ runner.os }}-"
            "${{ needs.preflight.outputs.commit }}"
        ),
        "path": "dist/*.zip\ndist/*.manifest.json\n",
        "if-no-files-found": "error",
        "retention-days": "1",
    }

    assert workflow["jobs"]["build"]["permissions"] == {"contents": "read"}
    build_steps = workflow["jobs"]["build"]["steps"]
    build_runs = [step["run"] for step in build_steps if "run" in step]
    build_rendered = "\n".join(build_runs)
    setup_python = next(
        step
        for step in build_steps
        if step.get("uses", "").startswith("actions/setup-python@")
    )
    assert setup_python["with"] == {"python-version": "3.11"}
    downloads = [
        step["with"]
        for step in build_steps
        if step.get("uses", "").startswith("actions/download-artifact@")
    ]
    assert downloads == [
        {
            "name": (
                "package-Linux-${{ needs.preflight.outputs.commit }}"
            ),
            "path": "candidate-packages/Linux",
        },
        {
            "name": (
                "package-Windows-${{ needs.preflight.outputs.commit }}"
            ),
            "path": "candidate-packages/Windows",
        },
    ]
    compare_index = next(
        index
        for index, command in enumerate(build_runs)
        if "python scripts/compare_packages.py" in command
    )
    verify_index = next(
        index
        for index, command in enumerate(build_runs)
        if "python scripts/verify_release.py artifacts" in command
    )
    assert compare_index < verify_index
    assert (
        "python scripts/compare_packages.py "
        "--first candidate-packages/Linux "
        "--second candidate-packages/Windows"
    ) in build_runs[compare_index]
    assert 'candidate-packages/Linux/$archive' in build_runs[verify_index]
    assert 'candidate-packages/Linux/$manifest' in build_runs[verify_index]
    assert 'cp "candidate-packages/Linux/$archive"' in build_runs[verify_index]
    assert 'cp "candidate-packages/Linux/$manifest"' in build_runs[verify_index]
    assert 'test "$VERSION" = "0.3.0"' in build_runs[verify_index]
    assert 'notes="docs/releases/0.3.0.md"' in build_runs[verify_index]
    assert "python scripts/package_skill.py" not in build_rendered
    assert all("pip " not in command for command in build_runs)
    assert "dist/" not in build_rendered
    upload_step = next(
        step
        for step in build_steps
        if step.get("uses", "").startswith("actions/upload-artifact@")
    )
    assert upload_step["id"] == "upload"
    assert upload_step["with"]["if-no-files-found"] == "error"
    assert "python scripts/verify_release.py artifacts" in build_rendered
    assert "release-notes.md" in build_rendered
    assert "release-bundle.sha256" in build_rendered

    publish_steps = workflow["jobs"]["publish"]["steps"]
    publish_rendered = "\n".join(
        step.get("run", "") for step in publish_steps
    )
    assert all(
        not step.get("uses", "").startswith(
            ("actions/checkout@", "actions/setup-python@")
        )
        for step in publish_steps
    )
    assert not re.search(
        r"\b(?:python(?:3(?:\.\d+)?)?|pip(?:3)?)\b", publish_rendered
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
    assert download_step["with"] == {
        "artifact-ids": "${{ needs.build.outputs.artifact_id }}",
        "path": "release-bundle",
        "merge-multiple": "true",
    }
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
    assert "release-bundle/release-bundle.sha256" in verify_step["run"]
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
    ].index("git ls-remote")
    assert release_step["run"].index("git ls-remote") < release_step[
        "run"
    ].index('test "$remote_tag_object" = "$VERIFIED_TAG_OBJECT"')
    assert release_step["run"].index(
        'test "$remote_commit" = "$VERIFIED_COMMIT"'
    ) < release_step["run"].index("gh release create")
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
    assert all(
        job.get("permissions", {"contents": "read"}) == {"contents": "read"}
        for name, job in workflow["jobs"].items()
        if name != "publish"
    )


def test_citation_and_license_metadata():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert citation["title"] == "Clinical Data Research Navigator"
    assert citation["version"] == "0.3.0"
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_release_version_is_synchronized():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_zh_tw = (ROOT / "CHANGELOG.zh-TW.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "docs/releases/0.3.0.md").read_text(encoding="utf-8")

    current_version = "0.3.0"
    active_surfaces = {
        "pyproject": project["project"]["version"],
        "citation": citation["version"],
        "packager": PACKAGER_VERSION,
        "installer": INSTALLER_VERSION,
        "changelog": changelog.splitlines()[2]
        .removeprefix("## ")
        .split(" - ", 1)[0],
        "changelog-zh-TW": changelog_zh_tw.splitlines()[2]
        .removeprefix("## ")
        .split(" - ", 1)[0],
        "release-notes": release_notes.splitlines()[0].rsplit("v", 1)[1],
    }

    assert len(active_surfaces) == 7
    assert set(active_surfaces.values()) == {current_version}
    assert "## 0.3.0 - 2026-08-08" in changelog
    assert "## 0.3.0 - 2026-08-08" in changelog_zh_tw
    assert citation["date-released"] == "2026-08-08"

    # Published history remains immutable while current surfaces advance.
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


def test_v030_release_notes_are_static_bilingual_and_uploadable():
    notes = (
        ROOT / "docs" / "releases" / "0.3.0.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(notes.split())

    assert notes.startswith("# Clinical Data Research Navigator v0.3.0\n")
    for heading in (
        "## English",
        "### Installation",
        "### Verification",
        "### Limitations",
        "## 繁體中文",
        "### 安裝",
        "### 驗證",
        "### 限制",
    ):
        assert heading in notes
    for release_contract in (
        "four output depths",
        "beginner navigation",
        "12 baseline/forward fixture pairs",
        "byte-identical",
        "metadata",
        "npx skills add mtchuang1981/clin-data-nav",
        "SHA-256",
        "archive_sha256",
        "四種輸出深度",
        "初學者導覽",
        "12 組 baseline／forward fixture",
        "位元組完全相同",
        "詮釋資料",
    ):
        assert release_contract.casefold() in normalized.casefold()

    for candidate_or_external_claim in (
        "- [ ]",
        "generated date",
        "generated on",
        "local path",
        "will be published",
        "will be available",
        "E:\\",
        "Zenodo",
        "DOI",
        "Plugin-directory",
        "branch protection",
        "private vulnerability reporting",
        "Dependabot",
        "候選檢查清單",
        "產生日期",
        "本機路徑",
        "將會發布",
        "將會提供",
        "分支保護",
        "私人漏洞回報",
    ):
        assert candidate_or_external_claim.casefold() not in notes.casefold()


def test_readmes_put_a_real_first_success_path_in_the_first_30_nonblank_lines():
    documents = (
        (
            "README.md",
            "$clinical-data-research-navigator What is ADaM",
            "Expected first line: `Output depth: quick explanation`",
            (
                "- A direct plain-language definition and why ADaM matters in context.",
                "- One or two common confusions or limits, followed by a short governing-source list.",
            ),
        ),
        (
            "README.zh-TW.md",
            "$clinical-data-research-navigator ADaM 是什麼",
            "預期第一行：`Output depth: quick explanation`",
            (
                "- 直接用白話定義 ADaM，並說明它在此情境的重要性。",
                "- 列出一至兩項常見混淆或限制，再附上精簡的主導來源清單。",
            ),
        ),
    )

    for relative_path, prompt, marker, summary_lines in documents:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert f"[![Validation]({VALIDATION_BADGE_IMAGE})]({VALIDATION_BADGE_LINK})" in text
        _assert_first_success_order(
            text,
            prompt=prompt,
            marker=marker,
            summary_lines=summary_lines,
        )


def test_readme_first_success_guard_rejects_a_missing_expected_summary_line():
    """The old three-marker guard missed a partially deleted expected result."""
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    summary_lines = (
        "- A direct plain-language definition and why ADaM matters in context.",
        "- One or two common confusions or limits, followed by a short governing-source list.",
    )
    mutated = text.replace(summary_lines[1], "")

    with pytest.raises(AssertionError):
        _assert_first_success_order(
            mutated,
            prompt="$clinical-data-research-navigator What is ADaM",
            marker="Expected first line: `Output depth: quick explanation`",
            summary_lines=summary_lines,
        )


def test_readmes_identify_the_installable_agent_skill_without_a_plugin_listing_claim():
    english = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    traditional_chinese = " ".join(
        (ROOT / "README.zh-TW.md").read_text(encoding="utf-8").split()
    )

    assert "installable Agent Skill" in english
    assert "does not claim a public Plugin-directory listing" in english
    assert "可安裝的 Agent Skill" in traditional_chinese
    assert "不宣稱已刊登於公開 Plugin 目錄" in traditional_chinese


def test_readmes_link_every_first_party_user_and_maintainer_destination():
    for relative_path, expected_targets in README_NAVIGATION_TARGETS.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        targets = _markdown_link_targets(text)
        for target in expected_targets:
            assert target in targets
            assert (ROOT / target).is_file(), f"missing linked file: {target}"


def test_installation_guides_preserve_quick_update_verified_and_source_paths():
    documents = (
        (
            (ROOT / "docs/installation.md").read_text(encoding="utf-8"),
            ENGLISH_ONBOARDING_CONTRACT,
            "target version for the next release is `0.3.0`",
            "not yet a claim that `v0.3.0` is published",
        ),
        (
            (ROOT / "docs/installation.zh-TW.md").read_text(encoding="utf-8"),
            TRADITIONAL_CHINESE_ONBOARDING_CONTRACT,
            "下一個 Release 的目標版本是 `0.3.0`",
            "不表示 `v0.3.0` 已經發布",
        ),
    )

    for text, onboarding_contract, target_claim, prerelease_claim in documents:
        _assert_readme_onboarding_contract(text, **onboarding_contract)
        normalized = " ".join(text.split())
        assert target_claim in normalized
        assert prerelease_claim in normalized
        assert 'releaseVersion = "0.3.0"' in text
        assert 'release_version="0.3.0"' in text
        assert "$HOME/.agents/skills" in text
        assert "SHA-256" in text
        assert "archive_sha256" in text
        assert "scripts/package_skill.py" in text
        assert "scripts/install_local.py" in text
        assert "--overwrite" in text
        assert "v0.2.2" not in text


def test_installation_guides_have_stage_specific_fail_closed_recovery():
    documents = (
        ("docs/installation.md", INSTALLATION_TROUBLESHOOTING_CONTRACTS),
        (
            "docs/installation.zh-TW.md",
            TRADITIONAL_CHINESE_TROUBLESHOOTING_CONTRACTS,
        ),
    )
    for relative_path, contracts in documents:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        sections = _troubleshooting_sections(text)
        assert tuple(sections) == tuple(
            contract[0] for contract in contracts
        )
        normalized_sections = {
            key: value.casefold() for key, value in sections.items()
        }
        for key, diagnosis_markers, recovery_markers in contracts:
            section = normalized_sections[key]
            for marker in (*diagnosis_markers, *recovery_markers):
                assert marker.casefold() in section, f"{relative_path}: {key}: {marker}"
        assert "--no-verify" not in text
        assert "Remove-Item -Recurse" not in text
        assert "rm -rf" not in text


def test_installation_and_contributor_docs_separate_skill_use_from_python_tooling():
    english_installation = (ROOT / "docs/installation.md").read_text(encoding="utf-8")
    chinese_installation = (ROOT / "docs/installation.zh-TW.md").read_text(
        encoding="utf-8"
    )
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "instruction-only installed Skill does not require Python" in english_installation
    assert "安裝後只包含操作指引與參考文件的 Skill 不需要 Python" in chinese_installation
    assert "Python 3.11" in contributing
    assert 'python -m pip install -e ".[dev]"' in contributing
    for command in (
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    ):
        assert command in contributing


def test_installation_guides_preserve_codex_and_chatgpt_activation_routes():
    english = " ".join(
        (ROOT / "docs/installation.md").read_text(encoding="utf-8").split()
    )
    traditional_chinese = " ".join(
        (ROOT / "docs/installation.zh-TW.md").read_text(encoding="utf-8").split()
    )

    assert "Codex CLI or the IDE extension" in english
    assert "ChatGPT desktop app" in english
    assert "open `Skills`" in english
    assert "Plugins → Skills" in english
    assert "upload" in english
    assert "does not install it into ChatGPT" in english
    assert "https://help.openai.com/en/articles/20001066" in english
    assert "https://learn.chatgpt.com/docs/build-skills" in english
    assert "Codex CLI 或 IDE 擴充功能" in traditional_chinese
    assert "ChatGPT 桌面版" in traditional_chinese
    assert "開啟 `Skills`" in traditional_chinese
    assert "Plugins → Skills" in traditional_chinese
    assert "上傳" in traditional_chinese
    assert "不會把它安裝到 ChatGPT" in traditional_chinese
    assert "https://help.openai.com/en/articles/20001066" in traditional_chinese
    assert "https://learn.chatgpt.com/docs/build-skills" in traditional_chinese


def test_installation_guides_use_the_current_chatgpt_upload_path_in_order():
    documents = (
        (
            "docs/installation.md",
            "interface may vary",
            "plan and workspace allow uploads",
        ),
        (
            "docs/installation.zh-TW.md",
            "介面可能不同",
            "方案與工作區允許上傳",
        ),
    )
    upload_path = "Plugins → Skills → Create → Upload from computer"
    official_url = (
        "https://help.openai.com/en/articles/"
        "20001066-skills-in-chatgpt"
    )

    for relative_path, variation_note, permission_note in documents:
        text = " ".join((ROOT / relative_path).read_text(encoding="utf-8").split())
        assert upload_path in text
        assert official_url in text
        assert variation_note in text
        assert permission_note in text


def test_source_checkout_uses_packager_output_and_refuses_an_existing_target(
    tmp_path,
):
    documents = (
        (
            (ROOT / "docs/installation.md").read_text(encoding="utf-8"),
            "## Install from a source checkout",
            "## Troubleshooting",
        ),
        (
            (ROOT / "docs/installation.zh-TW.md").read_text(encoding="utf-8"),
            "## 從原始碼簽出安裝",
            "## 疑難排解",
        ),
    )
    for text, start_heading, end_heading in documents:
        section = text.split(start_heading, 1)[1].split(end_heading, 1)[0]
        assert (
            'package_output="$(python scripts/package_skill.py '
            '--output-dir "$package_directory")"'
        ) in section
        assert "sed -n '1p'" in section
        assert "sed -n '2p'" in section
        assert 'test -f "$archive_path"' in section
        assert 'test -f "$manifest_path"' in section
        assert (
            'python scripts/install_local.py \\\n'
            '  "$archive_path" \\\n'
            '  --destination "$HOME/.agents/skills"'
        ) in section
        source_command = next(
            match["body"]
            for match in FENCED_BLOCK_PATTERN.finditer(section)
            if match["language"].strip() == "bash"
        )
        assert "--overwrite" not in source_command
        assert "clinical-data-research-navigator-0.3.0.zip" not in section

    package_directory = tmp_path / "package"
    package_result = subprocess.run(
        [
            sys.executable,
            "scripts/package_skill.py",
            "--output-dir",
            str(package_directory),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    output_paths = package_result.stdout.splitlines()
    assert len(output_paths) == 2
    archive_path, manifest_path = map(Path, output_paths)
    assert archive_path.is_file()
    assert manifest_path.is_file()

    destination = tmp_path / "installed-skills"
    install_command = [
        sys.executable,
        "scripts/install_local.py",
        str(archive_path),
        "--destination",
        str(destination),
    ]
    first_install = subprocess.run(
        install_command,
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert Path(first_install.stdout.strip()).is_dir()

    refused_install = subprocess.run(
        install_command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert refused_install.returncode != 0
    assert "installation already exists" in refused_install.stderr


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    (
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
    english = (ROOT / "docs/installation.md").read_text(encoding="utf-8")
    misplaced = mutation(english)

    assert misplaced != english
    with pytest.raises(AssertionError, match=expected_error):
        _assert_readme_onboarding_contract(
            misplaced,
            **ENGLISH_ONBOARDING_CONTRACT,
        )


def test_installation_guides_keep_zip_verification_free_of_python_one_liners():
    english = (ROOT / "docs/installation.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "docs/installation.zh-TW.md").read_text(
        encoding="utf-8"
    )

    english_posix = english.split("POSIX shell:", 1)[1].split(
        "## Install from a source checkout",
        1,
    )[0]
    chinese_posix = traditional_chinese.split("POSIX shell：", 1)[1].split(
        "## 從原始碼簽出安裝",
        1,
    )[0]
    assert "python -c" not in english_posix
    assert "python -c" not in chinese_posix


def test_readmes_preserve_cdisc_rwe_and_optional_handoff_discovery():
    english = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    traditional_chinese = " ".join(
        (ROOT / "README.zh-TW.md").read_text(encoding="utf-8").split()
    )

    for term in ("CDISC", "SDTM", "ADaM", "RWD", "RWE"):
        assert term in english
        assert term in traditional_chinese
    assert "RWD is not automatically RWE." in english
    assert "RWD 不會自動成為 RWE。" in traditional_chinese
    assert "causal-comparative" in english
    assert "因果比較" in traditional_chinese
    assert "`build-rwe-sap` is optional and not bundled" in english
    assert "`build-rwe-sap` 是選配項目，未內附" in traditional_chinese
    assert "never installs it automatically" in english
    assert "不會自動安裝" in traditional_chinese


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


def test_citation_points_to_the_public_repository_with_the_verified_release_date():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )

    repository_url = "https://github.com/mtchuang1981/clin-data-nav"
    assert citation["url"] == repository_url
    assert citation["repository-code"] == repository_url
    assert citation["date-released"] == "2026-08-08"


def test_security_policy_has_supported_versions_and_safe_confidential_reporting():
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    normalized = " ".join(security.split())

    assert "| Version | Supported |" in security
    assert "0.2.x" in security
    for prohibited_public_material in (
        "secrets",
        "PII",
        "private data dictionaries",
    ):
        assert prohibited_public_material in normalized
    assert "public issue" in normalized
    assert "2026-08-02" in normalized
    assert "private vulnerability reporting is not enabled" in normalized
    assert "non-sensitive request for private coordination" in normalized
    assert "best effort" in normalized
    assert not re.search(
        r"\bwithin\s+\d+\s+(?:business\s+)?(?:hours?|days?)\b",
        normalized,
        flags=re.IGNORECASE,
    )
    for response_step in (
        "Stop merge and distribution",
        "Remove branch or pull request access",
        "Rotate potentially affected credentials",
        "GitHub's sensitive-data removal procedure",
        "Do not rely on a later deletion commit to erase history",
    ):
        assert response_step in normalized


def test_repository_settings_is_a_post_change_operator_checklist_not_state_evidence():
    settings = (ROOT / "docs/repository-settings.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(settings.split())

    assert "operator checklist" in normalized
    assert "explicitly approved change" in normalized
    assert "documentation is not proof that a setting is enabled" in normalized
    assert "post-change re-read" in normalized
    assert "Ubuntu" in normalized
    assert "Windows" in normalized
    assert "required status checks" in normalized
    for topic in (
        "clinical-research",
        "rwe",
        "cdisc",
        "omop",
        "sas",
        "agent-skills",
    ):
        assert f"`{topic}`" in settings
    assert "private vulnerability reporting" in normalized
    assert "Dependabot security updates" in normalized
    assert "optional Zenodo evaluation" in normalized
    for decision_input in (
        "citation goal",
        "maintainer account/integration",
        "deposition ownership",
        "DOI verification",
    ):
        assert decision_input in normalized
    assert "no DOI is claimed without a verified deposition" in normalized
    assert "gh api" in settings
    assert "Settings" in settings


def test_repository_settings_require_all_stable_validation_check_names():
    """Omitting the comparator would permit merges before package identity is proven."""
    workflow = yaml.load(
        (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    assert "compare-packages" in workflow["jobs"]

    settings = (ROOT / "docs/repository-settings.md").read_text(encoding="utf-8")
    required_checks = (
        "test (ubuntu-latest)",
        "test (windows-latest)",
        "compare-packages",
    )
    for check in required_checks:
        assert f"`{check}`" in settings
    positions = [settings.index(f"`{check}`") for check in required_checks]
    assert positions == sorted(positions)
    required_section = settings.split("## Required status checks", 1)[1].split(
        "## Repository topics", 1
    )[0]
    for check in required_checks:
        assert f"- `{check}`" in required_section


def test_readmes_use_the_official_skill_and_plugin_product_boundary():
    english = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    traditional_chinese = " ".join(
        (ROOT / "README.zh-TW.md").read_text(encoding="utf-8").split()
    )

    assert "packages instructions, resources, and optional scripts" in english
    assert "separate distribution package" in english
    assert "封裝操作指引、資源與選用指令碼" in traditional_chinese
    assert "另一種發布套件" in traditional_chinese
    for document in (english, traditional_chinese):
        assert "https://learn.chatgpt.com/docs/build-skills" in document
        assert "https://help.openai.com/en/articles/20001066" in document


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
