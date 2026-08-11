import hashlib
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
import tomllib

import pytest
import yaml

from scripts.install_local import PACKAGE_VERSION as INSTALLER_VERSION
from scripts.package_skill import PACKAGE_VERSION as PACKAGER_VERSION
from scripts.effectiveness_analysis import (
    ADJUDICATION_KEYS,
    CONDITION_KEY_KEYS,
    CONDITION_MAPPING_KEYS,
    CONTROLLED_COUNT_KEYS,
    CONTROLLED_REVIEW_KEYS,
    CRITERION_SCORE_KEYS,
    MANIFEST_KEYS,
    OBSERVATION_KEYS,
    RATER_SCORE_KEYS,
    RATINGS_LOCK_KEYS,
    SCORES_KEYS,
    SESSION_KEYS,
    SUS_RESPONSE_KEYS,
    task_success,
)
from scripts.effectiveness_contract import load_effectiveness_contract
from scripts.generate_study_assignments import validate_assignments


ROOT = Path(__file__).resolve().parents[1]
TERMINAL_ONBOARDING_COMMANDS = (
    "node --version",
    "npm --version",
    "npx --version",
    "npx skills add mtchuang1981/clin-data-nav",
    "npx skills update clin-nav --project --yes",
)
CODEX_ONBOARDING_INPUTS = (
    "/skills",
    "$clin-nav",
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
            "skills/clin-nav/references/"
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
            "skills/clin-nav/references/"
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
                        "../skills/clin-nav/"
                        "references/output-depths-and-learning-paths.md"
                    ),
                ),
                "assess-the-evidence": (
                    "./glossary.md#rwd",
                    "./installation.md",
                    "../examples/omop-phenotype-to-sql-spec.md",
                    (
                        "../skills/clin-nav/"
                        "references/rwe-question-routing.md"
                    ),
                ),
                "prepare-an-implementation": (
                    "./glossary.md#data-contract",
                    "./installation.md",
                    "../examples/synthetic-institutional-mapping.md",
                    (
                        "../skills/clin-nav/"
                        "references/institutional-adapter-contract.md"
                    ),
                    (
                        "../skills/clin-nav/"
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
                        "../skills/clin-nav/"
                        "references/output-depths-and-learning-paths.md"
                    ),
                ),
                "assess-the-evidence": (
                    "./glossary.zh-TW.md#rwd",
                    "./installation.zh-TW.md",
                    "../examples/omop-phenotype-to-sql-spec.md",
                    (
                        "../skills/clin-nav/"
                        "references/rwe-question-routing.md"
                    ),
                ),
                "prepare-an-implementation": (
                    "./glossary.zh-TW.md#data-contract",
                    "./installation.zh-TW.md",
                    "../examples/synthetic-institutional-mapping.md",
                    (
                        "../skills/clin-nav/"
                        "references/institutional-adapter-contract.md"
                    ),
                    (
                        "../skills/clin-nav/"
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


def test_dependabot_version_updates_are_bounded_and_reviewable():
    path = ROOT / ".github/dependabot.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert config["version"] == 2
    assert set(config) == {"version", "updates"}

    updates = config["updates"]
    by_ecosystem = {entry["package-ecosystem"]: entry for entry in updates}
    assert len(updates) == 2
    assert set(by_ecosystem) == {"pip", "github-actions"}

    forbidden_keys = {
        "assignees",
        "groups",
        "ignore",
        "registries",
        "reviewers",
        "target-branch",
    }
    for entry in updates:
        assert entry["directory"] == "/"
        assert entry["schedule"] == {"interval": "weekly"}
        assert entry["open-pull-requests-limit"] == 5
        assert forbidden_keys.isdisjoint(entry)

    assert by_ecosystem["pip"]["versioning-strategy"] == (
        "increase-if-necessary"
    )
    assert "versioning-strategy" not in by_ecosystem["github-actions"]


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
    assert 'test "$VERSION" = "0.5.0"' in build_runs[verify_index]
    assert 'archive="clin-nav-$VERSION.zip"' in build_runs[verify_index]
    assert 'manifest="clin-nav-$VERSION.manifest.json"' in build_runs[verify_index]
    assert 'notes="docs/releases/0.5.0.md"' in build_runs[verify_index]
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
    assert (
        'archive="release-bundle/clin-nav-$VERSION.zip"'
        in release_step["run"]
    )
    assert (
        'manifest="release-bundle/clin-nav-$VERSION.manifest.json"'
        in release_step["run"]
    )
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
    assert citation["version"] == "0.5.0"
    assert "date-released" not in citation
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_release_candidate_version_is_synchronized():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_zh_tw = (ROOT / "CHANGELOG.zh-TW.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "docs/releases/0.5.0.md").read_text(encoding="utf-8")

    candidate_version = "0.5.0"
    candidate_surfaces = {
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
    assert len(candidate_surfaces) == 7
    assert set(candidate_surfaces.values()) == {candidate_version}
    assert changelog.splitlines()[2] == "## 0.5.0 - Candidate"
    assert changelog_zh_tw.splitlines()[2] == "## 0.5.0 - 候選版"
    assert "date-released" not in citation
    assert "## 0.4.0 - 2026-08-10" in changelog
    assert "## 0.4.0 - 2026-08-10" in changelog_zh_tw

    # Published history remains immutable while current surfaces advance.
    assert "## 0.2.2 - 2026-07-29" in changelog
    assert "## 0.2.2 - 2026-07-29" in changelog_zh_tw


def test_candidate_package_version_is_synchronized_at_v050():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["version"] == "0.5.0"
    assert PACKAGER_VERSION == "0.5.0"
    assert INSTALLER_VERSION == "0.5.0"


@pytest.mark.parametrize(
    ("relative_path", "migration_heading", "next_heading", "required_claims"),
    (
        (
            "docs/installation.md",
            "## Migrate from the previous Skill ID",
            "## Update a project-local installation",
            (
                "Inspect the exact existing",
                "before removing or archiving anything",
                "Remove or archive only that verified directory",
                "Never delete a broad or unresolved path.",
                "Confirm `.agents/skills/clin-nav/SKILL.md` exists.",
                "restart the Skill host if required",
                "Use `/skills` to confirm",
                "invoke `$clin-nav`",
            ),
        ),
        (
            "docs/installation.zh-TW.md",
            "## 從先前的 Skill ID 遷移",
            "## 更新專案內的安裝",
            (
                "移除或封存任何內容前，先檢查確切的",
                "只移除或封存已確認的確切目錄",
                "絕對不要刪除範圍過大或尚未解析的路徑。",
                "確認 `.agents/skills/clin-nav/SKILL.md` 存在。",
                "需要時重新啟動 Skill host",
                "請用 `/skills` 確認",
                "叫用 `$clin-nav`",
            ),
        ),
    ),
)
def test_installation_guides_define_a_bounded_skill_id_migration(
    relative_path,
    migration_heading,
    next_heading,
    required_claims,
):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    migration = _markdown_section(text, migration_heading, next_heading)
    ordered_values = (
        "clinical-data-research-navigator",
        "clin-nav",
        "npx skills add mtchuang1981/clin-data-nav",
        "$clin-nav",
    )

    positions = [migration.index(value) for value in ordered_values]
    assert positions == sorted(positions)
    assert ".agents/skills/clinical-data-research-navigator" in migration
    for claim in required_claims:
        assert claim in migration
    assert "rm -rf" not in migration


@pytest.mark.parametrize(
    (
        "relative_path",
        "scope_start",
        "migration_heading",
        "next_heading",
        "archive_claim",
        "discovery_claim",
    ),
    (
        (
            "docs/installation.md",
            None,
            "## Migrate from the previous Skill ID",
            "## Update a project-local installation",
            "Move any archive outside `.agents/skills` and every other Skill discovery root.",
            "Use `/skills` to confirm `clinical-data-research-navigator` is absent and "
            "`clin-nav` is the only installed entry for this Skill.",
        ),
        (
            "docs/installation.zh-TW.md",
            None,
            "## 從先前的 Skill ID 遷移",
            "## 更新專案內的安裝",
            "若要封存，請將封存目錄移到 `.agents/skills` 及其他所有 Skill "
            "探索根目錄之外。",
            "請用 `/skills` 確認 `clinical-data-research-navigator` 已不存在，且 "
            "`clin-nav` 是這個 Skill 唯一的已安裝項目。",
        ),
        (
            "docs/releases/0.5.0.md",
            "## English",
            "### Migration",
            "### Limitations",
            "Move any archive outside `.agents/skills` and every other Skill discovery root.",
            "Use `/skills` to confirm `clinical-data-research-navigator` is absent and "
            "`clin-nav` is the only installed entry for this Skill.",
        ),
        (
            "docs/releases/0.5.0.md",
            "## 繁體中文",
            "### 遷移",
            "### 限制",
            "若要封存，請將封存目錄移到 `.agents/skills` 及其他所有 Skill "
            "探索根目錄之外。",
            "請用 `/skills` 確認 `clinical-data-research-navigator` 已不存在，且 "
            "`clin-nav` 是這個 Skill 唯一的已安裝項目。",
        ),
    ),
)
def test_migration_archives_leave_all_discovery_roots_and_discovery_is_unambiguous(
    relative_path,
    scope_start,
    migration_heading,
    next_heading,
    archive_claim,
    discovery_claim,
):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    if scope_start is not None:
        text = text.split(scope_start, 1)[1]
    migration = _markdown_section(text, migration_heading, next_heading)

    assert archive_claim in " ".join(migration.split())
    assert discovery_claim in " ".join(migration.split())


@pytest.mark.parametrize(
    ("relative_path", "section_heading", "next_heading", "required_claims"),
    (
        (
            "docs/installation.md",
            "## Historical v0.4.0 Release artifact verification (reference only)",
            "## Install from a source checkout",
            (
                "historical verification reference only",
                "not a current installation path",
                "not compatible with `$clin-nav`",
            ),
        ),
        (
            "docs/installation.zh-TW.md",
            "## 歷史 v0.4.0 Release 產物驗證（僅供參考）",
            "## 從原始碼簽出安裝",
            (
                "僅供歷史驗證參考",
                "不是目前的安裝方式",
                "不相容於 `$clin-nav`",
            ),
        ),
    ),
)
def test_v040_artifact_section_is_reference_only_and_cannot_install_the_old_skill(
    relative_path,
    section_heading,
    next_heading,
    required_claims,
):
    text = (ROOT / relative_path).read_text(encoding="utf-8")
    section = _markdown_section(text, section_heading, next_heading)
    normalized = " ".join(section.split())

    for claim in required_claims:
        assert claim in normalized
    for fact in (
        "v0.4.0",
        "clinical-data-research-navigator-$releaseVersion",
        "clinical-data-research-navigator-$release_version",
        "archive_sha256",
        "SHA-256",
    ):
        assert fact in section
    for install_step in (
        "Expand-Archive",
        "New-Item -ItemType Directory",
        "mkdir -p",
        "unzip ",
        "$skillDirectory",
        "skill_directory=",
    ):
        assert install_step not in section


def test_v050_static_notes_and_changelogs_state_candidate_limitations():
    notes = (ROOT / "docs/releases/0.5.0.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    changelog_zh_tw = (ROOT / "CHANGELOG.zh-TW.md").read_text(encoding="utf-8")

    assert notes.startswith("# Clinical Data Research Navigator v0.5.0\n")
    for heading in (
        "## English",
        "### Installation",
        "### Migration",
        "### Limitations",
        "### Verification",
        "## 繁體中文",
        "### 安裝",
        "### 遷移",
        "### 限制",
        "### 驗證",
    ):
        assert heading in notes
    assert "The rename does not establish human effectiveness." in notes
    assert "更名不能建立真人有效性證據。" in notes
    assert "effectiveness-recovery implementation remains pending" in notes
    assert "no replacement human pilot has reached green" in notes
    assert "effectiveness-recovery implementation remains pending" in changelog
    assert "no replacement human pilot has reached green" in changelog
    assert "有效性復原實作仍待完成" in changelog_zh_tw
    assert "尚無替代真人試行達到綠燈" in changelog_zh_tw


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


def test_v040_release_notes_are_static_bilingual_and_uploadable():
    notes = (ROOT / "docs" / "releases" / "0.4.0.md").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(notes.split()).casefold()

    assert notes.startswith("# Clinical Data Research Navigator v0.4.0\n")
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
        "npx skills add mtchuang1981/clin-data-nav",
        "clinical-data-research-navigator-0.4.0.zip",
        "clinical-data-research-navigator-0.4.0.manifest.json",
        "SHA-256",
        "synthetic",
        "no human pilot was conducted",
        "not proven effective",
        "合成",
        "未進行人類試行",
        "尚未證實有效",
    ):
        assert release_contract.casefold() in normalized


def _assert_v040_local_release_evidence_contract(report: str) -> None:
    normalized = " ".join(report.split())

    for identity in (
        "2f6d999241c0f49e6754ba28d56dea637abdbaf9",
        "codex/v0.4.0-release",
        "Python 3.13.13",
        "Python 3.11.9",
    ):
        assert identity in normalized

    fix = _evidence_subsection(
        report,
        "## Pre-publication security-policy fix",
        "## Runtime identity and repository path",
    )
    normalized_fix = " ".join(fix.split())
    for exact_fact in (
        "Fix base: `144e5eb1f7de146c2609618de9c4e03347e17cfe`.",
        "Functional implementation commit: `2f6d999241c0f49e6754ba28d56dea637abdbaf9`.",
        "The stale-contract baseline passed with `2 passed in 0.04s`.",
        "The updated contract then failed as intended with `2 failed in 0.31s`.",
        (
            "After the policy change, the focused GREEN was `2 passed in 0.16s` "
            "and the related regression set was `144 passed in 3.35s`."
        ),
        (
            "The evidence-refresh contract failed against the stale record with "
            "`1 failed in 0.25s` before this record was changed."
        ),
    ):
        assert normalized_fix.count(exact_fact) == 1

    implementation = _evidence_subsection(
        report,
        "## Implementation verification",
        "## Local release artifacts",
    )
    host = _evidence_subsection(
        implementation,
        "### Host Python 3.13.13",
        "### Official Python 3.11.9",
    )
    official = _evidence_subsection(
        implementation,
        "### Official Python 3.11.9",
        None,
    )
    assert _evidence_table_rows(host) == (
        (
            "`python -m pytest -q -p no:cacheprovider`",
            "0",
            "`557 passed in 25.08s`",
            "`26,273 ms`",
        ),
        (
            "`python scripts/validate_skill.py`",
            "0",
            "no output/findings",
            "`401 ms`",
        ),
        (
            "`python scripts/check_public_boundary.py`",
            "0",
            "no output/findings",
            "`182 ms`",
        ),
        (
            "`python scripts/package_skill.py --check-reproducible`",
            "0",
            "no output; reproducibility check accepted",
            "`104 ms`",
        ),
        (
            "`python scripts/render_eval_summary.py --check`",
            "0",
            "no output; checked-in deterministic Eval summary accepted",
            "`86 ms`",
        ),
        (
            "`python scripts/render_effectiveness_report.py --summary "
            "evals/effectiveness/examples/synthetic-summary.json --english "
            "evals/effectiveness/examples/synthetic-report.md "
            "--traditional-chinese "
            "evals/effectiveness/examples/synthetic-report.zh-TW.md --check`",
            "0",
            "no output; checked-in synthetic bilingual reports accepted",
            "`97 ms`",
        ),
    )
    assert _evidence_table_rows(official) == (
        (
            "`python -m pytest -q -p no:cacheprovider`",
            "0",
            "`557 passed in 24.24s`",
            "`25,017 ms`",
        ),
        ("`python scripts/validate_skill.py`", "0", "no output/findings", "`68 ms`"),
        (
            "`python scripts/check_public_boundary.py`",
            "0",
            "no output/findings",
            "`186 ms`",
        ),
        (
            "`python scripts/package_skill.py --check-reproducible`",
            "0",
            "no output; reproducibility check accepted",
            "`120 ms`",
        ),
        (
            "`python scripts/render_eval_summary.py --check`",
            "0",
            "no output; checked-in deterministic Eval summary accepted",
            "`110 ms`",
        ),
        (
            "`python scripts/render_effectiveness_report.py --summary "
            "evals/effectiveness/examples/synthetic-summary.json --english "
            "evals/effectiveness/examples/synthetic-report.md "
            "--traditional-chinese "
            "evals/effectiveness/examples/synthetic-report.zh-TW.md --check`",
            "0",
            "no output; checked-in synthetic bilingual reports accepted",
            "`123 ms`",
        ),
    )
    for official_runtime_fact in (
        "`C:\\tmp\\python-3.11.9-embed-amd64\\python.exe`",
        "`E:\\6GAI\\AGY\\clin-data-nav\\.worktrees\\v0.4.0-release`",
    ):
        assert official.count(official_runtime_fact) == 1

    artifacts = _evidence_subsection(
        report,
        "## Local release artifacts",
        "## Evidence and publication boundary",
    )
    artifact_rows = _evidence_table_rows(artifacts)
    assert artifact_rows[:3] == (
        (
            "`python scripts/package_skill.py --output-dir dist`",
            "0",
            "generated the clean ZIP and manifest",
            "`112 ms`",
        ),
        (
            "`python scripts/verify_release.py artifacts --archive "
            "dist/clinical-data-research-navigator-0.4.0.zip --manifest "
            "dist/clinical-data-research-navigator-0.4.0.manifest.json`",
            "0",
            "`release artifacts verified`",
            "`128 ms`",
        ),
        (
            "`python scripts/check_public_boundary.py "
            "<fresh-extracted-directory>`",
            "0",
            "no output/findings",
            "`121 ms`",
        ),
    )
    artifact_property_rows = artifact_rows[3:]
    assert artifact_property_rows == (
        ("ZIP filename", "`clinical-data-research-navigator-0.4.0.zip`"),
        ("ZIP size", "`18591` bytes"),
        (
            "ZIP SHA-256",
            "`ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded`",
        ),
        (
            "Manifest filename",
            "`clinical-data-research-navigator-0.4.0.manifest.json`",
        ),
        ("Manifest size", "`1265` bytes"),
        (
            "Manifest SHA-256",
            "`9fe69bfa0a5fd9f8ce58082c1989316ed5b46683d74176319ba6c1187063a85a`",
        ),
        (
            "Manifest `archive_sha256`",
            "`ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded`",
        ),
        ("ZIP file count", "`8`"),
    )
    artifact_by_property = dict(artifact_property_rows)
    assert artifact_by_property["Manifest `archive_sha256`"] == (
        artifact_by_property["ZIP SHA-256"]
    )
    assert "Manifest file records are sorted and unique." in normalized
    assert "ZIP members exactly equal the manifest paths." in normalized
    assert (
        "ZIP member sizes and SHA-256 values exactly equal the manifest records."
        in normalized
    )
    assert (
        "exact root schema `archive,archive_sha256,files,name,version`" in normalized
    )
    assert "exact per-file schema `path,sha256,size`" in normalized

    for boundary_statement in (
        "No human pilot was conducted.",
        "This evidence does not claim that the Skill is effective.",
        "The `v0.4.0` tag does not yet exist.",
        "The GitHub Release has not yet been published.",
    ):
        assert boundary_statement in normalized


def test_v040_local_release_evidence_records_verified_candidate():
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-local-release.md"
    ).read_text(encoding="utf-8")
    _assert_v040_local_release_evidence_contract(report)


def test_v040_local_release_evidence_binds_commands_to_each_runtime_section():
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-local-release.md"
    ).read_text(encoding="utf-8")
    official_heading = "### Official Python 3.11.9"
    artifacts_heading = "## Local release artifacts"
    official_start = report.index(official_heading)
    official_end = report.index(artifacts_heading, official_start)
    official_section = report[official_start:official_end]
    table_start = official_section.index("| Command | Exit | Result | Elapsed |")
    official_table = official_section[table_start:]
    official_without_table = official_section[:table_start]
    mutated = (
        report[:official_start]
        + official_table
        + official_without_table
        + report[official_end:]
    )

    with pytest.raises(AssertionError):
        _assert_v040_local_release_evidence_contract(mutated)


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            "| ZIP filename | `clinical-data-research-navigator-0.4.0.zip` |",
            "| ZIP filename | "
            "`clinical-data-research-navigator-0.4.0.manifest.json` |",
        ),
        (
            "| ZIP SHA-256 | "
            "`ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded` |",
            "| ZIP SHA-256 | "
            "`9fe69bfa0a5fd9f8ce58082c1989316ed5b46683d74176319ba6c1187063a85a` |",
        ),
        (
            "| Manifest `archive_sha256` | "
            "`ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded` |",
            "| Manifest `archive_sha256` | "
            "`9fe69bfa0a5fd9f8ce58082c1989316ed5b46683d74176319ba6c1187063a85a` |",
        ),
    ),
)
def test_v040_local_release_evidence_binds_artifact_properties_to_values(
    original,
    replacement,
):
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-local-release.md"
    ).read_text(encoding="utf-8")
    assert original in report
    mutated = report.replace(original, replacement, 1)

    with pytest.raises(AssertionError):
        _assert_v040_local_release_evidence_contract(mutated)


def _assert_v040_publication_evidence_contract(report: str) -> None:
    normalized = " ".join(report.split())

    for metadata_fact in (
        "- Evidence recorded: `2026-08-10` (`Asia/Taipei`)",
        "- Published version: `v0.4.0`",
        "- Release published: `2026-08-10T01:30:15Z`",
    ):
        assert normalized.count(metadata_fact) == 1
    immutable_boundary = (
        "This is a post-publication record of public, independently downloaded "
        "bytes. It does not claim that this later evidence commit is contained "
        "in the immutable v0.4.0 source tree."
    )
    assert normalized.count(immutable_boundary) == 1

    sentences = {
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])(?:\s+|$)", normalized)
        if sentence.strip()
    }
    for contradictory_claim in (
        "A human pilot proved the Skill effective.",
        "A human pilot was conducted.",
        "The Skill is effective.",
        "The Skill is clinically valid.",
        "The Skill is ready for real-world deployment.",
    ):
        assert contradictory_claim not in sentences

    identity = _evidence_subsection(
        report,
        "## Immutable publication identity",
        "## Public workflows and Release",
    )
    assert _evidence_table_rows(identity) == (
        (
            "Main candidate commit",
            "`a5b5ad01e8fe6c72e4ea7f317b0bc5eed8644d52`",
        ),
        (
            "Annotated tag object",
            "`a1c99c0296d490dd9c56b96343ab0c285717775a`",
        ),
        (
            "Peeled tag commit",
            "`a5b5ad01e8fe6c72e4ea7f317b0bc5eed8644d52`",
        ),
        ("Release ID", "`367634803`"),
    )

    workflows = _evidence_subsection(
        report,
        "## Public workflows and Release",
        "## Fresh public download",
    )
    assert _evidence_table_rows(workflows) == (
        (
            "Main validation",
            "`https://github.com/mtchuang1981/clin-data-nav/actions/runs/31328169760`",
        ),
        (
            "CodeQL",
            "`https://github.com/mtchuang1981/clin-data-nav/actions/runs/31328168985`",
        ),
        (
            "Guarded Release",
            "`https://github.com/mtchuang1981/clin-data-nav/actions/runs/31347179873`",
        ),
        (
            "Public Release",
            "`https://github.com/mtchuang1981/clin-data-nav/releases/tag/v0.4.0`",
        ),
    )

    fresh_directory_match = re.search(
        r"Fresh directory: `(?P<path>C:\\tmp\\clin-data-nav-v0\.4\.0-public-"
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})`",
        report,
    )
    assert fresh_directory_match is not None
    fresh_directory = fresh_directory_match.group("path")
    assert normalized.count(fresh_directory) == 1
    complete_download_command = (
        "gh release download v0.4.0 --repo mtchuang1981/clin-data-nav "
        '--pattern "clinical-data-research-navigator-0.4.0.zip" '
        '--pattern "clinical-data-research-navigator-0.4.0.manifest.json" '
        "--dir $freshDir"
    )
    assert normalized.count(complete_download_command) == 1
    for command in (
        "python scripts/verify_release.py artifacts --archive $archive --manifest $manifest",
        "Get-FileHash -LiteralPath $archive -Algorithm SHA256",
        "Get-FileHash -LiteralPath $manifest -Algorithm SHA256",
        "python - $archive $manifest",
        "python scripts/check_public_boundary.py $extractDir",
    ):
        assert command in normalized
    assert "The download directory did not exist before creation." in normalized
    assert "The new directory was empty before download." in normalized
    assert "The completed download contained exactly two files." in normalized
    assert "Every recorded verification command exited `0`." in normalized

    command_record = _evidence_subsection(
        report.replace("\r\n", "\n").replace("\r", "\n"),
        "## Fresh public download",
        "## Release asset metadata and independently measured bytes",
    )
    powershell_blocks = re.findall(
        r"```powershell\n(?P<body>.*?)\n```",
        command_record,
        flags=re.DOTALL,
    )
    python_blocks = re.findall(
        r"```python\n(?P<body>.*?)\n```",
        command_record,
        flags=re.DOTALL,
    )
    assert tuple(
        hashlib.sha256(block.encode("utf-8")).hexdigest()
        for block in powershell_blocks
    ) == (
        "9758c11941c0e7e0f6faed0bb5f671319031071b69a2475af24a3f9ab1eeeb9e",
        "744d3f98b044b99a72996ce07d2143493e3b18370f090c572e8e59ab7a70440c",
    )
    assert tuple(
        hashlib.sha256(block.encode("utf-8")).hexdigest()
        for block in python_blocks
    ) == ("0dd88ee4aa57dc52e8387c79e765dfa2be8cfcbb3d98186fc51779d963d6bc0e",)

    assets = _evidence_subsection(
        report,
        "## Release asset metadata and independently measured bytes",
        "## Manifest and ZIP inspection",
    )
    assert _evidence_table_rows(assets) == (
        (
            "ZIP",
            "`508116851`",
            "`clinical-data-research-navigator-0.4.0.zip`",
            "`18591`",
            "`18591`",
            "`sha256:ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded`",
            "`ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded`",
        ),
        (
            "Manifest",
            "`508116852`",
            "`clinical-data-research-navigator-0.4.0.manifest.json`",
            "`1265`",
            "`1265`",
            "`sha256:9fe69bfa0a5fd9f8ce58082c1989316ed5b46683d74176319ba6c1187063a85a`",
            "`9fe69bfa0a5fd9f8ce58082c1989316ed5b46683d74176319ba6c1187063a85a`",
        ),
    )

    inspection = _evidence_subsection(
        report,
        "## Manifest and ZIP inspection",
        "## Mutation and evidence boundaries",
    )
    inspection_rows = _evidence_table_rows(inspection)
    assert inspection_rows[0] == (
        "ZIP member",
        "Size (bytes)",
        "Independently calculated SHA-256",
    )
    member_rows = []
    for row in inspection_rows[1:]:
        assert len(row) == 3
        path, size, sha256 = row
        assert re.fullmatch(r"`[^`]+`", path)
        assert re.fullmatch(r"`[0-9]+`", size)
        assert re.fullmatch(r"`[0-9a-f]{64}`", sha256)
        member_rows.append((path[1:-1], int(size[1:-1]), sha256[1:-1]))
    assert tuple(member_rows) == (
        (
            "SKILL.md",
            11519,
            "feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c",
        ),
        (
            "agents/openai.yaml",
            286,
            "fcf1af72749d16bd0de63fa5008635f232fcb338ac8824d9bbc37cd92a9c8471",
        ),
        (
            "references/evidence-output-template.md",
            3496,
            "492a8550c33f5983397905b214ddebcafabbcc24c41e1552c5333835db717274",
        ),
        (
            "references/institutional-adapter-contract.md",
            3770,
            "3338101cba63b3c42dac3342671b6ab6fff288b44c799e6531e8a6a88c37f164",
        ),
        (
            "references/output-depths-and-learning-paths.md",
            5769,
            "ade86d6017b8968bf637f7a68970c68f88b9ae872a7830ab6721c8c80542b61a",
        ),
        (
            "references/retrieval-playbook.md",
            5253,
            "eade0851031d4411aed96cf285b681306c3500d004e6dc1906025d6d5ef357a7",
        ),
        (
            "references/rwe-question-routing.md",
            7460,
            "9301a0077f2647a669c47f476d33f0b60644b87a6b50628c680ba875b0656fe7",
        ),
        (
            "references/tmucrd-public-profile.md",
            2855,
            "fd0d531dded2679b6d4d1b6a3654339c82c9dbc7b29d75221df0074b888e78e1",
        ),
    )

    for exact_fact in (
        "Manifest `archive_sha256`: `ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded`.",
        "The manifest root keys were exactly `archive,archive_sha256,files,name,version`.",
        "The manifest version was exactly `0.4.0`.",
        "The manifest archive was exactly `clinical-data-research-navigator-0.4.0.zip`.",
        "The eight manifest file records were sorted and unique.",
        "Every file record had exactly `path,sha256,size`.",
        "ZIP members were unique and exactly matched the manifest paths in order.",
        "Every ZIP member size and SHA-256 matched its manifest record.",
        "The independently calculated ZIP SHA-256 equalled the manifest `archive_sha256`.",
        "Both local sizes and both local SHA-256 values exactly matched the GitHub asset metadata and digests.",
        "The remote annotated tag was not moved, recreated, or replaced.",
        "The GitHub Release was not edited, and neither published asset was replaced.",
        "The Release workflow was not rerun.",
        "No human pilot was conducted.",
        "This evidence does not claim that the Skill is effective.",
    ):
        assert normalized.count(exact_fact) == 1


def test_v040_publication_report_records_exact_public_evidence():
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    _assert_v040_publication_evidence_contract(report)


@pytest.mark.parametrize(
    "contradictory_claim",
    (
        "A human pilot proved the Skill effective.",
        "A human pilot was conducted.",
        "The Skill is effective.",
        "The Skill is clinically valid.",
        "The Skill is ready for real-world deployment.",
    ),
)
def test_v040_publication_evidence_rejects_contradictory_positive_claims(
    contradictory_claim,
):
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    mutated = f"{report.rstrip()}\n\n{contradictory_claim}\n"

    with pytest.raises(AssertionError):
        _assert_v040_publication_evidence_contract(mutated)


@pytest.mark.parametrize(
    "removed_fact",
    (
        "- Evidence recorded: `2026-08-10` (`Asia/Taipei`)\n",
        "- Published version: `v0.4.0`\n",
        "- Release published: `2026-08-10T01:30:15Z`\n",
        (
            "This is a post-publication record of public, independently "
            "downloaded bytes.\nIt does not claim that this later evidence "
            "commit is contained in the immutable\nv0.4.0 source tree.\n"
        ),
    ),
)
def test_v040_publication_evidence_locks_metadata_and_immutable_tag_boundary(
    removed_fact,
):
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    assert removed_fact in report
    mutated = report.replace(removed_fact, "", 1)

    with pytest.raises(AssertionError):
        _assert_v040_publication_evidence_contract(mutated)


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            ' --pattern "clinical-data-research-navigator-0.4.0.zip"',
            "",
        ),
        (
            ' --pattern "clinical-data-research-navigator-0.4.0.manifest.json"',
            "",
        ),
        (" --dir $freshDir", " --dir $extractDir"),
        (
            (
                '--pattern "clinical-data-research-navigator-0.4.0.zip" '
                '--pattern "clinical-data-research-navigator-0.4.0.manifest.json"'
            ),
            (
                '--pattern "clinical-data-research-navigator-0.4.0.manifest.json" '
                '--pattern "clinical-data-research-navigator-0.4.0.zip"'
            ),
        ),
    ),
)
def test_v040_publication_evidence_binds_complete_download_command(
    original,
    replacement,
):
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    assert original in report
    mutated = report.replace(original, replacement, 1)

    with pytest.raises(AssertionError):
        _assert_v040_publication_evidence_contract(mutated)


def test_v040_publication_command_lock_normalizes_lf_and_crlf():
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    lf_report = report.replace("\r\n", "\n").replace("\r", "\n")
    crlf_report = lf_report.replace("\n", "\r\n")

    _assert_v040_publication_evidence_contract(lf_report)
    _assert_v040_publication_evidence_contract(crlf_report)


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            "gh api repos/mtchuang1981/clin-data-nav/releases/tags/v0.4.0",
            "gh api repos/mtchuang1981/clin-data-nav/releases/latest",
        ),
        (
            "$localSize = (Get-Item -LiteralPath $local).Length",
            "$localSize = $asset.size",
        ),
        (
            "Get-FileHash -LiteralPath $local -Algorithm SHA256",
            "Get-FileHash -LiteralPath $local -Algorithm SHA512",
        ),
        ("`python - $archive $manifest`", "`python - $manifest $archive`"),
        ("with ZipFile(archive) as zip_file:", "with ZipFile(manifest) as zip_file:"),
    ),
)
def test_v040_publication_evidence_binds_independent_verification_commands(
    original,
    replacement,
):
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    assert original in report
    mutated = report.replace(original, replacement, 1)

    with pytest.raises(AssertionError):
        _assert_v040_publication_evidence_contract(mutated)


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            "| `SKILL.md` | `11519` | "
            "`feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |\n",
            "",
        ),
        (
            "| `SKILL.md` | `11519` | "
            "`feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |",
            "| `SKILL.txt` | `11519` | "
            "`feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |",
        ),
        (
            "| `SKILL.md` | `11519` | "
            "`feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |",
            "| `SKILL.md` | `11518` | "
            "`feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |",
        ),
        (
            "| `SKILL.md` | `11519` | "
            "`feb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |",
            "| `SKILL.md` | `11519` | "
            "`0eb006a65eb8971641f9a8f1fccf547929dde81550ffc3760484596c2cd9061c` |",
        ),
    ),
    ids=("row-deletion", "path", "size", "sha256"),
)
def test_v040_publication_evidence_binds_exact_member_rows(
    original,
    replacement,
):
    report = (
        ROOT / "docs/verification/2026-08-10-v0.4.0-publication.md"
    ).read_text(encoding="utf-8")
    assert original in report
    mutated = report.replace(original, replacement, 1)

    with pytest.raises(AssertionError):
        _assert_v040_publication_evidence_contract(mutated)


def test_release_process_requires_a_committed_post_release_evidence_report():
    process = " ".join(
        (ROOT / "docs/release.md").read_text(encoding="utf-8").split()
    )

    assert "new dated verification report" in process
    assert "commit and push" in process
    assert "tag object" in process
    assert "asset IDs" in process
    assert "SHA-256" in process


def test_v030_publication_report_records_exact_public_evidence():
    report = (
        ROOT / "docs/verification/2026-08-09-v0.3.0-publication.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(report.split())

    required = (
        "6cf9593dd8a520f56e1e6e5b0bf2cb7d40b97791",
        "87ca8f379f6751fc465dbcd6ae8f430dabc73523",
        "31263843137",
        "31263961241",
        "https://github.com/mtchuang1981/clin-data-nav/releases/tag/v0.3.0",
        "506494592",
        "506494593",
        "18591",
        "1265",
        "ce6a67a268e4266d094db31406a9c5dda3f005c3b6a5355ec851ea87abf3aded",
        "d3862e00fcf499fa453e6cac05b6f3e21f9b2a9d735d2579a4a5b834caee42bc",
        "scripts/verify_release.py artifacts",
    )
    for value in required:
        assert value in normalized

    assert "branch protection: disabled" in normalized
    assert "rulesets: none" in normalized
    assert "topics: none" in normalized
    assert "private vulnerability reporting: disabled" in normalized
    assert "Dependabot security updates: disabled" in normalized
    assert "No external repository setting was changed" in normalized


def test_github_settings_evidence_records_verified_post_change_state():
    report = (
        ROOT / "docs/verification/2026-08-09-github-settings.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(report.split())

    for topic in (
        "agent-skills",
        "cdisc",
        "clinical-research",
        "omop",
        "rwe",
        "sas",
    ):
        assert topic in normalized
    for required_state in (
        "branch protection: enabled",
        "strict: true",
        "enforce administrators: false",
        "force pushes: disabled",
        "branch deletion: disabled",
        "rulesets: none",
        "private vulnerability reporting: enabled",
        "vulnerability alerts: enabled",
        "Dependabot security updates: enabled",
        "paused: false",
        "test (ubuntu-latest)",
        "test (windows-latest)",
        "compare-packages",
        "14755a9a0d3daabfd252f6fa12ee7361ef56754f",
        "31266889594",
    ):
        assert required_state.casefold() in normalized.casefold()
    assert "No tag or GitHub Release was changed" in normalized


def test_codeql_default_setup_guidance_and_evidence_are_auditable():
    guide = (ROOT / "docs/repository-settings.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT / "docs/verification/2026-08-09-codeql-default-setup.md"
    ).read_text(encoding="utf-8")
    normalized_guide = " ".join(guide.split())
    normalized_evidence = " ".join(evidence.split())

    for guide_contract in (
        "## CodeQL default setup",
        "`actions`",
        "`python`",
        "`default`",
        "`remote`",
        "`standard`",
        "`weekly`",
        "not currently a required check",
        "zero results do not prove",
    ):
        assert guide_contract.casefold() in normalized_guide.casefold()

    for evidence_contract in (
        "0aff8038bb52457e9868fab9ea9a43dda9b4235c",
        "https://github.com/mtchuang1981/clin-data-nav/actions/runs/31269886134",
        "93133943497",
        "93133943498",
        "1590243272",
        "1590243578",
        "17 rules",
        "43 rules",
        "zero results",
        "zero open code-scanning alerts",
        "zero job annotations, warnings, or failures",
        "test (ubuntu-latest)",
        "test (windows-latest)",
        "compare-packages",
        "No branch-protection setting was changed",
        "No tag or GitHub Release was changed",
        "zero findings do not prove",
    ):
        assert evidence_contract.casefold() in normalized_evidence.casefold()


def test_readmes_put_a_real_first_success_path_in_the_first_30_nonblank_lines():
    documents = (
        (
            "README.md",
            "$clin-nav What is ADaM",
            "Expected first line: `Output depth: quick explanation`",
            (
                "- A direct plain-language definition and why ADaM matters in context.",
                "- One or two common confusions or limits, followed by a short governing-source list.",
            ),
        ),
        (
            "README.zh-TW.md",
            "$clin-nav ADaM 是什麼",
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
            prompt="$clin-nav What is ADaM",
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
            "current verified Release is `v0.4.0`",
            ("target version for the next release", "not yet a claim"),
        ),
        (
            (ROOT / "docs/installation.zh-TW.md").read_text(encoding="utf-8"),
            TRADITIONAL_CHINESE_ONBOARDING_CONTRACT,
            "目前已驗證的 Release 是 `v0.4.0`",
            ("下一個 Release", "不表示"),
        ),
    )

    for text, onboarding_contract, published_claim, stale_claims in documents:
        _assert_readme_onboarding_contract(text, **onboarding_contract)
        normalized = " ".join(text.split())
        assert published_claim in normalized
        for stale_claim in stale_claims:
            assert stale_claim not in normalized
        assert 'releaseVersion = "0.4.0"' in text
        assert 'release_version="0.4.0"' in text
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
                    "$clin-nav"
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
                    "`$clin-nav` are entered in\n"
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


def test_citation_points_to_the_public_repository_without_an_unpublished_date():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )

    repository_url = "https://github.com/mtchuang1981/clin-data-nav"
    assert citation["url"] == repository_url
    assert citation["repository-code"] == repository_url
    assert "date-released" not in citation


def test_security_policy_has_supported_versions_and_safe_confidential_reporting():
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    normalized = " ".join(security.split())

    assert "| Version | Supported |" in security
    assert "`0.4.x` | Yes" in normalized
    assert "`< 0.4` | No" in normalized
    assert "`0.3.x` | Yes" not in normalized
    assert "`0.2.x` | Yes" not in normalized
    for prohibited_public_material in (
        "secrets",
        "PII",
        "private data dictionaries",
    ):
        assert prohibited_public_material in normalized
    assert "public issue" in normalized
    assert "As of 2026-08-10, that line is `0.4.x`." in normalized
    assert "On 2026-08-09 (Asia/Taipei)" in normalized
    assert "private vulnerability reporting is enabled" in normalized
    assert "security/advisories/new" in normalized
    assert "private vulnerability reporting is not enabled" not in normalized
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


def test_effectiveness_docs_distinguish_contract_evals_from_human_evidence():
    eval_readme = (ROOT / "evals/README.md").read_text(encoding="utf-8")
    effectiveness = (
        ROOT / "evals/effectiveness/README.md"
    ).read_text(encoding="utf-8")

    assert "response contracts" in eval_readme
    assert "does not prove real-use effectiveness" in eval_readme
    assert "offline dry run" in effectiveness
    assert "separately authorized human pilot" in effectiveness
    assert "no telemetry" in effectiveness


GOVERNANCE_READINESS_NAVIGATION_MARKERS = (
    "governance/README.md",
    "validate_governance_readiness.py",
    "ready-for-institutional-review",
    "not-authorized-to-recruit",
)


def _governance_readiness_navigation_errors(text: str) -> list[str]:
    return [
        marker
        for marker in GOVERNANCE_READINESS_NAVIGATION_MARKERS
        if marker not in text
    ]


def test_effectiveness_readme_routes_governance_readiness_without_authorizing_people():
    text = (ROOT / "evals/effectiveness/README.md").read_text(encoding="utf-8")

    assert _governance_readiness_navigation_errors(text) == []


@pytest.mark.parametrize("marker", GOVERNANCE_READINESS_NAVIGATION_MARKERS)
def test_effectiveness_readme_governance_navigation_detects_missing_marker(marker):
    text = (ROOT / "evals/effectiveness/README.md").read_text(encoding="utf-8")
    assert marker in text
    mutated = text.replace(marker, "removed-governance-marker", 1)

    assert _governance_readiness_navigation_errors(mutated) == [marker]


EFFECTIVENESS_METHOD_URLS = (
    "https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf",
    "https://airc.nist.gov/",
    "https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/",
    "https://hci-studies.org/methods-and-measures/downloads/SUS_Brooke1996.pdf",
    "https://www.bmj.com/content/390/bmj-2024-083405",
)
EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS = (
    (
        "## 1. Purpose and evidence boundary",
        "## 1. 目的與證據邊界",
    ),
    (
        "## 2. Governance and authorization",
        "## 2. 治理與授權",
    ),
    (
        "## 3. Eligibility and strata",
        "## 3. 納入條件與分層",
    ),
    (
        "## 4. Four-task balanced crossover",
        "## 4. 四任務平衡交叉設計",
    ),
    (
        "## 5. Standardized task execution",
        "## 5. 標準化任務執行",
    ),
    (
        "## 6. Environment manifest and version stop rule",
        "## 6. 環境 manifest 與版本停止規則",
    ),
    (
        "## 7. Human-task commitment and leakage rule",
        "## 7. 人類任務承諾與外洩規則",
    ),
    (
        "## 8. Safety-gated primary outcome",
        "## 8. 通過安全門檻的主要結果",
    ),
    (
        "## 9. Secondary outcomes and fixed scoring",
        "## 9. 次要結果與固定計分",
    ),
    (
        "## 10. Blinded ratings and adjudication",
        "## 10. 盲化評分與第三人裁定",
    ),
    (
        "## 11. Ratings lock, agreement gate, and explicit unlock",
        "## 11. 評分鎖定、一致性閘門與明確解盲",
    ),
    (
        "## 12. Paired exploratory analysis",
        "## 12. 配對探索性分析",
    ),
    (
        "## 13. Practical difference and later power scenarios",
        "## 13. 實務差異與後續檢定力情境",
    ),
    (
        "## 14. Completion threshold and non-positive reporting",
        "## 14. 完成門檻與非正向結果報告",
    ),
    (
        "## 15. Raw-data, incident, and publication boundaries",
        "## 15. 原始資料、事件與發布邊界",
    ),
    (
        "## 16. Method references",
        "## 16. 方法參考資料",
    ),
)


EFFECTIVENESS_CANONICAL_FACTS = (
    (
        "purpose-boundary",
        "The exploratory pilot evaluates product task performance on synthetic tasks and does not establish real-use effectiveness or clinical validity.",
        "探索性先導研究評估合成任務的產品任務表現，不證明真實使用效果或臨床效度。",
    ),
    (
        "separate-authorization",
        "The protocol does not authorize recruitment, collection, unlock, analysis, or publication; ethics review, consent, storage platform, retention, access, and incident decisions remain separate.",
        "本規格不授權招募、蒐集、解盲、分析或發布；倫理審查、同意、儲存平台、保留、存取與事件處理決定須另行辦理。",
    ),
    (
        "fixed-strata",
        "The fixed pilot has 8 beginners and 8 professionals, with eligibility frozen before recruitment.",
        "固定先導研究包含初學者 8 人與專業者 8 人，納入條件於招募前固定。",
    ),
    (
        "balanced-crossover",
        "Each participant receives four tasks in a 2:2 intervention-control balanced crossover, one task per output depth and never both variants of a pair.",
        "每位參與者在 2:2 介入對照平衡交叉設計中接受四個任務，每個輸出深度各一個，且不會同時收到同一配對的兩個版本。",
    ),
    (
        "standardized-execution",
        "Both conditions use the same standardized ten-minute orientation; every task starts in a fresh conversation with fixed time limits and rest between tasks.",
        "兩個條件使用相同的標準化十分鐘導覽；每個任務從全新對話開始，採固定時限，並於任務間休息。",
    ),
    (
        "environment-stop",
        "The manifest fixes one environment fingerprint; any model, Skill, surface, or material setting change stops the open batch and prevents silent pooling, while offline tooling makes no external model call.",
        "manifest 固定單一環境指紋；模型、Skill、介面或重要設定一旦改變，就停止開放批次且不得直接合併，離線工具也不會呼叫外部模型。",
    ),
    (
        "commitment-leakage",
        "The external task pack uses a fresh 32-byte nonce and SHA-256 commitment; early leakage stops the batch and requires a new pack, nonce, and commitment.",
        "外部任務包使用新的 32-byte nonce 與 SHA-256 承諾；若提前外洩，須停止批次並更換任務包、nonce 與承諾。",
    ),
    (
        "primary-safety",
        "Primary success requires every mandatory criterion and no critical violation; the fixed critical categories are invented-schema, false-executable-status, rwd-rwe-confusion, unsupported-causal-claim, fabricated-citation, unreviewed-search-as-authority, missing-tte-readiness, and private-data-request-or-exposure; quality criteria are secondary and cannot offset safety.",
        "主要成功須完成所有必答判準且沒有重大違規；固定重大違規類別為 invented-schema、false-executable-status、rwd-rwe-confusion、unsupported-causal-claim、fabricated-citation、unreviewed-search-as-authority、missing-tte-readiness 與 private-data-request-or-exposure；品質判準屬次要結果，不能抵銷安全問題。",
    ),
    (
        "secondary-scoring",
        "NASA-TLX uses six integer ratings from 0 through 100 and six integer weights from 0 through 5 that sum to 15, with score sum(rating * weight) / 15; SUS uses ten integer responses from 1 through 5, transforms odd items to response - 1 and even items to 5 - response, and multiplies the sum by 2.5; a quality rate with no applicable criteria is null and not estimable.",
        "NASA-TLX 使用六個 0 到 100 的整數評分與六個 0 到 5、總和為 15 的整數權重，分數為 sum(rating * weight) / 15；SUS 使用十個 1 到 5 的整數作答，奇數題轉為 response - 1、偶數題轉為 5 - response，再將總和乘以 2.5；沒有適用品質判準時，品質率為 null 且不可估計。",
    ),
    (
        "blinded-rating",
        "Two independent raters receive only opaque answer codes and condition-free material; any disagreement requires third-person adjudication while original ratings remain unchanged.",
        "兩位獨立評分者只會收到不透明答案代碼與不含條件標示的材料；任何不一致均須由第三人裁定，原始評分保持不變。",
    ),
    (
        "lock-unlock",
        "The raw blinded score bytes are locked before agreement review; raw agreement below 0.80 or an estimable kappa below 0.60 blocks condition-key unlock, which requires explicit --unlock-after-ratings-lock.",
        "一致性檢查前須鎖定原始盲化分數位元組；原始一致率低於 0.80 或可估計 kappa 低於 0.60 時禁止以 condition key 解盲，且解盲必須明確傳入 --unlock-after-ratings-lock。",
    ),
    (
        "paired-analysis",
        "The paired analysis calculates the risk difference, paired distribution, and denominators directly from observed participant differences; only applicable 95% confidence intervals use participant-cluster bootstrap with the manifest's fixed seed and resample count; technical failures are handled conservatively and no null-hypothesis significance test is performed.",
        "配對分析直接從觀察到的參與者差異計算風險差、配對分布與分母；只有適用的 95% 信賴區間使用 manifest 固定種子與重抽次數的參與者群聚 bootstrap；技術失敗採保守方式處理，且不做虛無假設顯著性檢定。",
    ),
    (
        "power-rule",
        "The practical threshold is an absolute 20 percentage points; later power scenarios are conservative, do not use the pilot point estimate alone, and remain deferred until after the pilot.",
        "實務門檻為絕對 20 個百分點；後續檢定力情境採保守設定，不得只使用先導研究點估計值，並延後至先導研究完成後。",
    ),
    (
        "completion-reporting",
        "At least 14 of 16 participants must complete all four tasks for exploratory interpretation; positive, neutral, and negative findings use the same report structure, and endpoints cannot change after results are seen.",
        "至少 14/16 位參與者須完成全部四個任務，才進行探索性解讀；正向、中性與負向發現皆使用相同報告結構，且看到結果後不得變更終點。",
    ),
    (
        "data-boundary",
        "Raw human-study data stay outside the repository under least-privilege access, retention, and incident controls; no participant row may be published, only aggregate outputs, and packaging does not run a human study.",
        "人類研究原始資料須留在儲存庫外，並受最小權限存取、保留與事件處理規範管控；不得發布參與者資料列，只能發布彙總輸出，且封裝不代表執行人類研究。",
    ),
    (
        "method-references",
        "The protocol uses the five fixed method references listed in this section.",
        "本規格使用本節列出的五項固定方法參考資料。",
    ),
)
EFFECTIVENESS_REDUNDANT_FACT_MARKERS = (
    ("does not establish", "不代表已證明"),
    ("does not authorize", "不代表已核准"),
    ("8 beginners", "初學者 8 人"),
    ("2:2 balanced crossover", "2:2 平衡交叉"),
    ("same ten-minute interface orientation", "相同的十分鐘介面導覽"),
    ("stop the open batch", "停止目前開放批次"),
    ("32-byte nonce", "32-byte nonce"),
    ("requires every predeclared mandatory criterion", "滿足所有預先指定的必備準則"),
    ("sum to 15", "總和為 15"),
    ("Two independent raters score", "兩位獨立評分者以"),
    ("Raw binary agreement must be at least", "二元原始一致率至少"),
    ("95% participant-cluster bootstrap", "95% 參與者叢集 bootstrap"),
    ("absolute 20 percentage points", "絕對 20 個百分點"),
    ("At least 14 of 16", "至少 14/16"),
    ("stay outside the repository", "都留在招募前核准的儲存庫外位置"),
    (None, None),
)
ENGLISH_CANONICAL_FACT_PATTERN = re.compile(
    r"^\*\*Canonical fact `(?P<fact_id>[a-z0-9-]+)`:"
    r"\*\* (?P<statement>.+)$",
    flags=re.MULTILINE,
)
TRADITIONAL_CHINESE_CANONICAL_FACT_PATTERN = re.compile(
    r"^\*\*固定事實 `(?P<fact_id>[a-z0-9-]+)`："
    r"\*\* (?P<statement>.+)$",
    flags=re.MULTILINE,
)


def _assert_effectiveness_canonical_facts(
    english: str,
    traditional_chinese: str,
) -> None:
    english_facts = {}
    chinese_facts = {}
    for index, (fact_id, english_statement, chinese_statement) in enumerate(
        EFFECTIVENESS_CANONICAL_FACTS
    ):
        english_heading, chinese_heading = EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS[
            index
        ]
        next_english = (
            EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS[index + 1][0]
            if index + 1 < len(EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS)
            else None
        )
        next_chinese = (
            EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS[index + 1][1]
            if index + 1 < len(EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS)
            else None
        )
        english_section = _markdown_section(english, english_heading, next_english)
        chinese_section = _markdown_section(
            traditional_chinese, chinese_heading, next_chinese
        )
        assert ENGLISH_CANONICAL_FACT_PATTERN.findall(english_section) == [
            (fact_id, english_statement)
        ]
        assert TRADITIONAL_CHINESE_CANONICAL_FACT_PATTERN.findall(chinese_section) == [
            (fact_id, chinese_statement)
        ]
        english_match = ENGLISH_CANONICAL_FACT_PATTERN.search(english_section)
        chinese_match = TRADITIONAL_CHINESE_CANONICAL_FACT_PATTERN.search(
            chinese_section
        )
        assert english_match is not None
        assert chinese_match is not None
        english_remainder = " ".join(
            (
                english_section[: english_match.start()]
                + english_section[english_match.end() :]
            ).split()
        )
        chinese_remainder = " ".join(
            (
                chinese_section[: chinese_match.start()]
                + chinese_section[chinese_match.end() :]
            ).split()
        )
        english_duplicate, chinese_duplicate = EFFECTIVENESS_REDUNDANT_FACT_MARKERS[
            index
        ]
        if english_duplicate is not None:
            assert english_duplicate not in english_remainder
        if chinese_duplicate is not None:
            assert chinese_duplicate not in chinese_remainder
        english_facts[fact_id] = english_statement
        chinese_facts[fact_id] = chinese_statement

    expected_fact_ids = [fact[0] for fact in EFFECTIVENESS_CANONICAL_FACTS]
    assert list(english_facts) == expected_fact_ids
    assert list(chinese_facts) == expected_fact_ids
    assert len(english_facts) == len(chinese_facts) == 16


def _assert_effectiveness_protocol_contract(
    english: str,
    traditional_chinese: str,
) -> None:
    english_headings = [item[0] for item in EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS]
    chinese_headings = [item[1] for item in EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS]
    assert re.findall(r"^## .+$", english, flags=re.MULTILINE) == english_headings
    assert re.findall(
        r"^## .+$", traditional_chinese, flags=re.MULTILINE
    ) == chinese_headings

    for index, (english_heading, chinese_heading) in enumerate(
        EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS
    ):
        next_english = (
            english_headings[index + 1] if index + 1 < len(english_headings) else None
        )
        next_chinese = (
            chinese_headings[index + 1] if index + 1 < len(chinese_headings) else None
        )
        english_section = _markdown_section(english, english_heading, next_english)
        chinese_section = _markdown_section(
            traditional_chinese, chinese_heading, next_chinese
        )
        assert english_section.startswith(english_heading)
        assert chinese_section.startswith(chinese_heading)

    for url in EFFECTIVENESS_METHOD_URLS:
        assert english.count(url) == 1
        assert traditional_chinese.count(url) == 1


def _markdown_section(text: str, heading: str, next_heading: str | None) -> str:
    assert text.count(heading) == 1
    start = text.index(heading)
    end = text.index(next_heading, start) if next_heading is not None else len(text)
    return text[start:end]


def test_effectiveness_protocols_fix_the_approved_design_and_stay_bilingual():
    english = (ROOT / "evals/effectiveness/protocol.md").read_text(
        encoding="utf-8"
    )
    traditional_chinese = (
        ROOT / "evals/effectiveness/protocol.zh-TW.md"
    ).read_text(encoding="utf-8")

    _assert_effectiveness_protocol_contract(english, traditional_chinese)
    _assert_effectiveness_canonical_facts(english, traditional_chinese)


def test_effectiveness_docs_name_exactly_eight_fingerprint_fields_and_separate_other_validation():
    english_protocol = (ROOT / "evals/effectiveness/protocol.md").read_text(
        encoding="utf-8"
    )
    chinese_protocol = (
        ROOT / "evals/effectiveness/protocol.zh-TW.md"
    ).read_text(encoding="utf-8")
    schema = (ROOT / "evals/effectiveness/input-schema.md").read_text(
        encoding="utf-8"
    )
    exact_fields = (
        "`skill_version`, `skill_commit`, `codex_surface`, `model`, "
        "`reasoning_effort`, `service_tier`, `python_version`, and `platform`"
    )
    separate = (
        "Protocol commit, study dates, task-commitment verification, assignment "
        "version, and bootstrap settings are separately validated and are not "
        "hashed into this fingerprint."
    )

    normalized_english = " ".join(english_protocol.split())
    normalized_schema = " ".join(schema.split())
    normalized_chinese = "".join(chinese_protocol.split())
    assert exact_fields in normalized_english
    assert exact_fields in normalized_schema
    assert separate in normalized_english
    assert separate in normalized_schema
    assert (
        "研究規格commit、研究日期、任務承諾驗證、分派版本與bootstrap設定"
        "另行驗證，不會雜湊進此指紋。"
    ) in normalized_chinese


@pytest.mark.parametrize(
    ("fact_id", "replacement"),
    [
        (
            "standardized-execution",
            "Each condition uses a condition-specific orientation",
        ),
        (
            "environment-stop",
            "A model or version change does not stop the open batch.",
        ),
        (
            "blinded-rating",
            "Blinded raters receive condition-labelled material.",
        ),
        (
            "completion-reporting",
            "At most 14 of 16 participants must complete all four tasks.",
        ),
        (
            "secondary-scoring",
            "NASA-TLX divides the weighted sum by 6 and SUS reverses the odd/even transformations.",
        ),
        (
            "paired-analysis",
            "Paired distributions and denominators are bootstrap estimates.",
        ),
    ],
)
def test_effectiveness_protocol_contract_rejects_semantic_reversals(
    fact_id,
    replacement,
):
    english = (ROOT / "evals/effectiveness/protocol.md").read_text(
        encoding="utf-8"
    )
    traditional_chinese = (
        ROOT / "evals/effectiveness/protocol.zh-TW.md"
    ).read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^(\*\*Canonical fact `{re.escape(fact_id)}`:\*\* ).+$",
        flags=re.MULTILINE,
    )
    mutated, replacement_count = pattern.subn(rf"\1{replacement}", english)
    assert replacement_count == 1
    assert mutated != english

    with pytest.raises(AssertionError):
        _assert_effectiveness_canonical_facts(mutated, traditional_chinese)


@pytest.mark.parametrize(
    ("language", "old", "replacement"),
    [
        ("en", "20 percentage points", "twenty percentage points"),
        ("zh-TW", "14/16", "十四位"),
        ("en", EFFECTIVENESS_METHOD_URLS[0], "https://example.invalid/reference"),
    ],
)
def test_effectiveness_protocol_contract_rejects_missing_facts(
    language,
    old,
    replacement,
):
    english = (ROOT / "evals/effectiveness/protocol.md").read_text(
        encoding="utf-8"
    )
    traditional_chinese = (
        ROOT / "evals/effectiveness/protocol.zh-TW.md"
    ).read_text(encoding="utf-8")
    if language == "en":
        english = english.replace(old, replacement, 1)
    else:
        traditional_chinese = traditional_chinese.replace(old, replacement, 1)

    with pytest.raises(AssertionError):
        _assert_effectiveness_protocol_contract(english, traditional_chinese)
        _assert_effectiveness_canonical_facts(english, traditional_chinese)


def test_effectiveness_protocol_contract_rejects_reordered_sections():
    english = (ROOT / "evals/effectiveness/protocol.md").read_text(
        encoding="utf-8"
    )
    traditional_chinese = (
        ROOT / "evals/effectiveness/protocol.zh-TW.md"
    ).read_text(encoding="utf-8")
    fourth = EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS[3][0]
    fifth = EFFECTIVENESS_PROTOCOL_SECTION_CONTRACTS[4][0]
    reordered = english.replace(fourth, "__FOURTH_SECTION__", 1)
    reordered = reordered.replace(fifth, fourth, 1).replace(
        "__FOURTH_SECTION__", fifth, 1
    )

    with pytest.raises(AssertionError):
        _assert_effectiveness_protocol_contract(reordered, traditional_chinese)


EFFECTIVENESS_COMMAND_BLOCKS = (
    "python scripts/validate_governance_readiness.py --input <external-dir>/governance-readiness.json",
    "python -m pytest tests/test_effectiveness_contract.py -q",
    "python scripts/generate_study_assignments.py --study-id pilot-v1 --seed 20260809 --output <external-dir>/assignments.json",
    "python scripts/commit_human_task_pack.py create --task-pack <external-dir>/human-tasks.yaml --nonce-output <external-dir>/human-tasks.nonce --commitment-output <external-dir>/human-task-commitment.json",
    "python scripts/commit_human_task_pack.py verify --task-pack <external-dir>/human-tasks.yaml --nonce-file <external-dir>/human-tasks.nonce --commitment <external-dir>/human-task-commitment.json",
    "python scripts/analyze_effectiveness.py agreement-check --study-manifest <external-dir>/study-manifest.json --scores <external-dir>/blinded-scores.json --ratings-lock <external-dir>/ratings-lock.json --output-summary <external-dir>/agreement-summary.json",
    "python scripts/analyze_effectiveness.py analyze --study-manifest <external-dir>/study-manifest.json --scores <external-dir>/blinded-scores.json --ratings-lock <external-dir>/ratings-lock.json --condition-key <external-dir>/condition-key.json --unlock-after-ratings-lock --output-summary <external-dir>/aggregate-summary.json",
    "python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check",
)


def _assert_effectiveness_command_map_contract(text: str) -> None:
    command_blocks = tuple(
        " ".join(match.group("body").split())
        for match in FENCED_BLOCK_PATTERN.finditer(text)
    )
    assert command_blocks == EFFECTIVENESS_COMMAND_BLOCKS

    assignment, agreement, analyze = (
        command_blocks[2],
        command_blocks[5],
        command_blocks[6],
    )
    assert "validate_assignments(rows, catalog, study_id, seed)" in text
    assert text.index(assignment) < text.index(agreement) < text.index(analyze)
    assert {token for token in agreement.split() if token.startswith("--")} == {
        "--study-manifest",
        "--scores",
        "--ratings-lock",
        "--output-summary",
    }
    assert "--condition-key" not in agreement
    assert "--unlock-after-ratings-lock" not in agreement
    assert {token for token in analyze.split() if token.startswith("--")} == {
        "--study-manifest",
        "--scores",
        "--ratings-lock",
        "--condition-key",
        "--unlock-after-ratings-lock",
        "--output-summary",
    }
    assert "exit code 3" in text
    assert "recalibrate-and-rescore-before-unlock" in text
    assert "eligible-for-locked-unlock" in text
    assert text.index("recalibrate-and-rescore-before-unlock") < text.index(analyze)


def _swap_once(text: str, left: str, right: str) -> str:
    assert text.count(left) == 1
    assert text.count(right) == 1
    return text.replace(left, "__LEFT_COMMAND__", 1).replace(
        right, left, 1
    ).replace("__LEFT_COMMAND__", right, 1)


def test_effectiveness_command_map_matches_current_cli_and_unlock_gate():
    text = (ROOT / "evals/effectiveness/README.md").read_text(encoding="utf-8")

    _assert_effectiveness_command_map_contract(text)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda text: text.replace(
            "--ratings-lock <external-dir>/ratings-lock.json --output-summary",
            "--ratings-lock <external-dir>/ratings-lock.json --condition-key <external-dir>/condition-key.json --output-summary",
            1,
        ),
        lambda text: text.replace(" --unlock-after-ratings-lock", "", 1),
        lambda text: text.replace(
            "validate_assignments(rows, catalog, study_id, seed)",
            "validate_assignments(rows, catalog)",
            1,
        ),
        lambda text: _swap_once(
            text,
            EFFECTIVENESS_COMMAND_BLOCKS[5],
            EFFECTIVENESS_COMMAND_BLOCKS[6],
        ),
    ],
)
def test_effectiveness_command_map_rejects_unsafe_argument_or_order_drift(mutate):
    text = (ROOT / "evals/effectiveness/README.md").read_text(encoding="utf-8")
    mutated = mutate(text)
    assert mutated != text

    with pytest.raises(AssertionError):
        _assert_effectiveness_command_map_contract(mutated)


EFFECTIVENESS_SCHEMA_KEY_GROUPS = {
    "manifest": frozenset(
        {
            "schema_version",
            "study_id",
            "protocol_commit",
            "skill_version",
            "skill_commit",
            "codex_surface",
            "model",
            "reasoning_effort",
            "service_tier",
            "python_version",
            "platform",
            "study_started_at",
            "study_ended_at",
            "task_commitment_sha256",
            "task_commitment_verified",
            "bootstrap_seed",
            "bootstrap_resamples",
            "sessions",
        }
    ),
    "session": frozenset(
        {
            "participant_code",
            "stratum",
            "assignment_version",
            "session_date",
            "environment_fingerprint",
        }
    ),
    "scores": frozenset(
        {
            "schema_version",
            "study_id",
            "protocol_deviations",
            "study_limitations",
            "observations",
            "rater_scores",
            "adjudications",
            "sus_responses",
        }
    ),
    "observation": frozenset(
        {
            "answer_id",
            "participant_code",
            "stratum",
            "task_pair_id",
            "task_variant",
            "output_depth",
            "order",
            "started_at",
            "ended_at",
            "completion_status",
            "completion_seconds",
            "mandatory_complete",
            "quality_met",
            "quality_applicable",
            "quality_score",
            "critical_violation",
            "criterion_scores",
            "nasa_tlx_ratings",
            "nasa_tlx_weights",
            "confidence_before",
            "confidence_after",
            "understanding_before",
            "understanding_after",
        }
    ),
    "criterion_score": frozenset({"criterion_id", "applicable", "met"}),
    "rater_score": frozenset(
        {"answer_id", "rater_code", "success", "critical_violation", "ordinal_quality"}
    ),
    "adjudication": frozenset(
        {
            "answer_id",
            "adjudicator_code",
            "final_success",
            "final_critical_violation",
            "final_ordinal_quality",
            "rationale_code",
        }
    ),
    "sus_response": frozenset({"participant_code", "items"}),
    "controlled_review": frozenset({"review_status", "items"}),
    "controlled_count": frozenset({"category_id", "count"}),
    "ratings_lock": frozenset(
        {
            "schema_version",
            "study_id",
            "scores_sha256",
            "ratings_complete",
            "rater_codes",
            "locked_at",
        }
    ),
    "condition_key": frozenset({"schema_version", "study_id", "mappings"}),
    "condition_mapping": frozenset({"answer_id", "condition"}),
}
IMPLEMENTED_EFFECTIVENESS_SCHEMA_KEY_GROUPS = {
    "manifest": MANIFEST_KEYS,
    "session": SESSION_KEYS,
    "scores": SCORES_KEYS,
    "observation": OBSERVATION_KEYS,
    "criterion_score": CRITERION_SCORE_KEYS,
    "rater_score": RATER_SCORE_KEYS,
    "adjudication": ADJUDICATION_KEYS,
    "sus_response": SUS_RESPONSE_KEYS,
    "controlled_review": CONTROLLED_REVIEW_KEYS,
    "controlled_count": CONTROLLED_COUNT_KEYS,
    "ratings_lock": RATINGS_LOCK_KEYS,
    "condition_key": CONDITION_KEY_KEYS,
    "condition_mapping": CONDITION_MAPPING_KEYS,
}
def _effectiveness_yaml_contract(
    text: str,
    heading: str,
    next_heading: str,
) -> dict:
    body = _markdown_section(text, heading, next_heading)
    matches = list(FENCED_BLOCK_PATTERN.finditer(body))
    assert len(matches) == 1
    assert matches[0].group("language").strip() == "yaml"
    parsed = yaml.safe_load(matches[0].group("body"))
    assert isinstance(parsed, dict)
    return parsed


def _production_assignment_contract(tmp_path: Path) -> dict:
    output = tmp_path / "assignments.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/generate_study_assignments.py",
            "--study-id",
            "contract-test",
            "--seed",
            "20260809",
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    rows = payload["assignments"]
    catalog, _ = load_effectiveness_contract(
        ROOT / "evals/effectiveness/offline-tasks.yaml",
        ROOT / "evals/effectiveness/rubric.yaml",
    )
    assert validate_assignments(
        rows,
        catalog,
        payload["study_id"],
        payload["seed"],
    ) == []
    parameters = tuple(inspect.signature(validate_assignments).parameters)
    assert parameters == ("rows", "catalog", "study_id", "seed")
    return {
        "assignment_top_level_keys": tuple(payload),
        "assignment_row_keys": tuple(rows[0]),
        "validator_api": f"validate_assignments({', '.join(parameters)})",
    }


def _assert_primary_outcome_contract(contract: dict) -> None:
    assert set(contract) == {
        "primary_success_truth_table",
        "quality_criteria_affect_primary",
    }
    assert contract["quality_criteria_affect_primary"] is False
    truth_table = contract["primary_success_truth_table"]
    assert isinstance(truth_table, list)
    assert len(truth_table) == 4
    observed_inputs = set()
    for row in truth_table:
        assert set(row) == {
            "mandatory_complete",
            "critical_violation",
            "success",
        }
        mandatory = row["mandatory_complete"]
        critical = row["critical_violation"]
        documented_success = row["success"]
        assert type(mandatory) is bool
        assert type(critical) is bool
        assert type(documented_success) is bool
        observed_inputs.add((mandatory, critical))
        expected = mandatory and not critical
        assert documented_success is expected
        for quality_met, quality_applicable in ((0, 0), (0, 3), (3, 3)):
            observation = {
                "completion_status": "completed",
                "mandatory_complete": mandatory,
                "quality_met": quality_met,
                "quality_applicable": quality_applicable,
                "critical_violation": critical,
            }
            assert task_success(observation) is documented_success
    assert observed_inputs == {
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    }


def _assert_effectiveness_input_schema_contract(
    text: str,
    production_assignment: dict | None = None,
) -> None:
    assignment_contract = _effectiveness_yaml_contract(
        text,
        "## Normative assignment contract",
        "## 1. Study manifest",
    )
    assert set(assignment_contract) == {
        "assignment_top_level_keys",
        "assignment_row_keys",
        "validator_api",
    }
    if production_assignment is not None:
        for key in ("assignment_top_level_keys", "assignment_row_keys"):
            documented = assignment_contract[key]
            production = production_assignment[key]
            assert len(documented) == len(production)
            assert set(documented) == set(production)
        assert (
            assignment_contract["validator_api"]
            == production_assignment["validator_api"]
        )

    primary_contract = _effectiveness_yaml_contract(
        text,
        "### Normative primary-outcome truth table",
        "### Original rater rows",
    )
    _assert_primary_outcome_contract(primary_contract)
    primary_section = _markdown_section(
        text,
        "### Normative primary-outcome truth table",
        "### Original rater rows",
    )
    primary_fences = list(FENCED_BLOCK_PATTERN.finditer(primary_section))
    assert len(primary_fences) == 1
    primary_block = primary_fences[0].group(0)
    assert text.count(primary_block) == 1
    outside_primary_block = " ".join(text.replace(primary_block, "", 1).split())
    assert (
        "Final success must match mandatory completion with no critical violation."
        not in outside_primary_block
    )

    normalized = " ".join(text.split())
    documented_groups = {
        "manifest": _backtick_key_set(
            _between(normalized, "The manifest has exactly these keys:", "Commit fields are")
        ),
        "session": _backtick_key_set(
            _between(
                normalized,
                "`sessions` contains exactly 16 rows. Every row has exactly:",
                "Participant codes are exactly",
            )
        ),
        "scores": _backtick_key_set(
            _between(normalized, "The top-level object has exactly", ". It contains no condition")
        ),
        "controlled_review": _backtick_key_set(
            _between(
                normalized,
                "Each controlled review object has exactly",
                ". Each `items` value",
            )
        ),
        "controlled_count": _backtick_key_set(
            _between(
                normalized,
                "Each controlled count row has exactly",
                ". Counts are positive",
            )
        ),
        "observation": _backtick_key_set(
            _between(normalized, "Every observation has exactly:", "`answer_id` is 16")
        ),
        "criterion_score": _backtick_key_set(
            _between(normalized, "Every criterion row has exactly", ": - mandatory criteria")
        ),
        "rater_score": _backtick_key_set(
            _between(
                normalized,
                "unscored answers have none. A row has exactly",
                ". Rater codes",
            )
        ),
        "adjudication": _backtick_key_set(
            _between(
                normalized,
                "Complete agreement forbids adjudication. A row has exactly",
                ". The adjudicator",
            )
        ),
        "sus_response": _backtick_key_set(
            _between(normalized, "Each `sus_responses` row has exactly", ". Participant codes")
        ),
        "ratings_lock": _backtick_key_set(
            _between(normalized, "The lock has exactly", ". `scores_sha256`")
        ),
        "condition_key": _backtick_key_set(
            _between(normalized, "The key has exactly", ". Each mapping")
        ),
        "condition_mapping": _backtick_key_set(
            _between(normalized, "Each mapping has exactly", ", where condition is")
        ),
    }
    assert IMPLEMENTED_EFFECTIVENESS_SCHEMA_KEY_GROUPS == EFFECTIVENESS_SCHEMA_KEY_GROUPS
    assert documented_groups == EFFECTIVENESS_SCHEMA_KEY_GROUPS
    assert sum(len(fields) for fields in EFFECTIVENESS_SCHEMA_KEY_GROUPS.values()) == 85

    for marker in (
        "`criterion_scores` is in the task contract's exact order",
        "mandatory criteria always have `applicable: true` and boolean `met`",
        "when applicable, `met` is boolean",
        "when not applicable, `met` is JSON null",
        "`abandoned` and `technical_failure` are unscored.",
        "The following fields are JSON null",
        "All quality criteria may be N/A.",
        "quality_applicable=0",
        "quality_met=0",
        "quality rate is null and not estimable",
        "criterion_scores",
        "`review_status` is mandatory",
        "`reviewed-none` requires an empty `items` list",
        "`reviewed-with-findings` requires at least one controlled count row",
        "Free text, identifiers, and condition fields are forbidden",
    ):
        assert marker in normalized


def _between(text: str, start_marker: str, end_marker: str) -> str:
    assert text.count(start_marker) == 1
    start = text.index(start_marker) + len(start_marker)
    end = text.index(end_marker, start)
    return text[start:end]


def _backtick_key_set(text: str) -> frozenset[str]:
    return frozenset(re.findall(r"`([a-z][a-z0-9_]*)`", text))


def test_effectiveness_input_schema_records_strict_rows_and_quality_na(tmp_path):
    text = (ROOT / "evals/effectiveness/input-schema.md").read_text(
        encoding="utf-8"
    )

    _assert_effectiveness_input_schema_contract(
        text,
        _production_assignment_contract(tmp_path),
    )


@pytest.mark.parametrize(
    ("old", "replacement"),
    [
        ("`task_commitment_verified`;", ""),
        ("`rater_codes`, and `locked_at`", "`rater_codes`"),
        (
            "`criterion_id`, `applicable`, and `met`",
            "`criterion_id`, `applicable`, `met`, and `unexpected`",
        ),
        ("All quality criteria may be N/A.", "All quality criteria are applicable."),
    ],
)
def test_effectiveness_input_schema_contract_rejects_field_or_na_drift(
    old,
    replacement,
):
    text = (ROOT / "evals/effectiveness/input-schema.md").read_text(
        encoding="utf-8"
    )
    mutated = text.replace(old, replacement, 1)
    assert mutated != text

    with pytest.raises(AssertionError):
        _assert_effectiveness_input_schema_contract(mutated)


@pytest.mark.parametrize(
    ("old", "replacement"),
    [
        ("  - seed\n", ""),
        ("  - variant\n", ""),
        (
            "validator_api: validate_assignments(rows, catalog, study_id, seed)",
            "validator_api: validate_assignments(rows, catalog)",
        ),
        (
            "  - mandatory_complete: true\n"
            "    critical_violation: true\n"
            "    success: false",
            "  - mandatory_complete: true\n"
            "    critical_violation: true\n"
            "    success: true",
        ),
    ],
)
def test_effectiveness_input_schema_contract_rejects_assignment_or_primary_drift(
    tmp_path,
    old,
    replacement,
):
    text = (ROOT / "evals/effectiveness/input-schema.md").read_text(
        encoding="utf-8"
    )
    mutated = text.replace(old, replacement, 1)
    assert mutated != text

    with pytest.raises(AssertionError):
        _assert_effectiveness_input_schema_contract(
            mutated,
            _production_assignment_contract(tmp_path),
        )


def test_effectiveness_input_schema_rejects_primary_rule_outside_normative_yaml():
    text = (ROOT / "evals/effectiveness/input-schema.md").read_text(
        encoding="utf-8"
    )
    duplicate = (
        "Final success must match mandatory completion with no critical violation."
    )
    mutated = text.replace(
        "### Adjudication rows\n",
        f"### Adjudication rows\n\n{duplicate}\n",
        1,
    )
    assert mutated != text

    with pytest.raises(AssertionError):
        _assert_effectiveness_input_schema_contract(mutated)


def test_effectiveness_navigation_and_architecture_preserve_public_boundary():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(
        encoding="utf-8"
    )
    architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    assert "evals/effectiveness/README.md" in english
    assert "evals/effectiveness/README.md" in traditional_chinese
    assert "has proven effective" not in english
    assert "已證明有效" not in traditional_chinese
    for marker in (
        "External raw storage",
        "Condition-blinded scoring",
        "Ratings lock and agreement gate",
        "Condition-key unlock",
        "Aggregate analysis",
        "Public bilingual report",
        "independent from the existing deterministic response-contract Evals",
        "no external model call in CI",
        "does not include effectiveness raw data or run a human study",
    ):
        assert marker in architecture
    assert "Do not place human data anywhere under the repository checkout." in contributing


EFFECTIVENESS_FRAMEWORK_EVIDENCE_SECTIONS = (
    "## Test-driven final-fix evidence",
    "## Official Python 3.11.9 runtime",
    "## Final-fix focused checks",
    "## Functional-commit command observations",
    "## Evidence refresh boundary",
    "## Complete diff and public-boundary audit",
    "## Evidence and authority boundary",
)

EFFECTIVENESS_FRAMEWORK_FOCUSED_COMMAND = (
    "python -m pytest -q "
    "tests/test_effectiveness_analysis.py::test_direct_unlock_recomputes_and_enforces_blinded_agreement_gate "
    "tests/test_effectiveness_analysis.py::test_clopper_pearson_extreme_confidence_is_finite_ordered_and_centrally_symmetric "
    "tests/test_effectiveness_analysis.py::test_controlled_protocol_review_is_strict_condition_free_and_deterministic "
    "tests/test_effectiveness_analysis.py::test_nonzero_controlled_deviations_and_limitations_reach_summary_and_reports "
    "tests/test_effectiveness_analysis.py::test_conservative_missingness_treats_control_technical_failure_as_success "
    "tests/test_effectiveness_reports.py::test_non_synthetic_report_does_not_call_observed_interval_illustrative "
    "tests/test_effectiveness_reports.py::test_bilingual_publication_rolls_back_first_replace_when_second_replace_fails "
    "tests/test_effectiveness_reports.py::test_bilingual_publication_preserves_coherent_backups_when_publish_and_rollback_fail "
    "tests/test_study_assignments.py::test_assignment_validator_rejects_fixed_schedule_or_answer_id_tampering "
    "tests/test_project_metadata.py::test_effectiveness_docs_name_exactly_eight_fingerprint_fields_and_separate_other_validation"
)
EFFECTIVENESS_FRAMEWORK_EVIDENCE_LF_UTF8_SHA256 = (
    "970f08b70460e74279febd67cbc2ec35ddd0b2ee43d739150a38d0483ee3fd28"
)


def _evidence_metadata_items(preamble: str) -> tuple[str, ...]:
    items: list[str] = []
    current: list[str] = []
    for line in preamble.splitlines():
        if line.startswith("- "):
            if current:
                items.append(" ".join(current))
            current = [line]
        elif current and line.startswith("  "):
            current.append(line.strip())
        elif current:
            items.append(" ".join(current))
            current = []
    if current:
        items.append(" ".join(current))
    return tuple(items)


def _evidence_subsection(text: str, heading: str, next_heading: str | None) -> str:
    assert text.count(heading) == 1
    start = text.index(heading)
    end = text.index(next_heading, start) if next_heading is not None else len(text)
    return text[start:end]


def _evidence_table_rows(section: str) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if cells[0] in {"Property", "Command"}:
            continue
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        rows.append(cells)
    return tuple(rows)


def _assert_effectiveness_framework_evidence_contract(text: str) -> None:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert digest == EFFECTIVENESS_FRAMEWORK_EVIDENCE_LF_UTF8_SHA256

    headings = tuple(re.findall(r"^## .+$", text, flags=re.MULTILINE))
    assert headings == EFFECTIVENESS_FRAMEWORK_EVIDENCE_SECTIONS
    assert text.endswith("\n")

    preamble = text[: text.index(EFFECTIVENESS_FRAMEWORK_EVIDENCE_SECTIONS[0])]
    assert preamble.startswith("# v0.4.0 Effectiveness Framework Verification\n")
    assert _evidence_metadata_items(preamble) == (
        "- Verification date: `2026-08-09` (`Asia/Taipei`, UTC+08:00; Windows zone `Taipei Standard Time`)",
        "- Observation captured: `2026-08-09T22:15:42+08:00`",
        "- Branch: `codex/effectiveness-evaluation-design`",
        "- Implementation HEAD: `c6c9bee7ea8fd507f92bc72012666eb93cd2beb8`",
        "- Host interpreter: `Python 3.13.13`",
        "- Target interpreter: official `Python 3.11.9` 64-bit embeddable runtime",
    )
    normalized_preamble = " ".join(preamble.split())
    for exact_fact in (
        "The exact implementation object identified by this record is the clean Implementation HEAD above.",
        "Fresh runs at that object produced `550 passed in 23.13s` under the host interpreter and `550 passed in 23.97s` under the target interpreter.",
        "The evidence document and its lock test necessarily follow the implementation object.",
        "The evidence commit contains only those two evidence files and is verified again after commit.",
        "this record identifies the immutable functional object rather than attempting to self-identify the later evidence commit.",
    ):
        assert normalized_preamble.count(exact_fact) == 1

    tdd = _evidence_subsection(
        text,
        "## Test-driven final-fix evidence",
        "## Official Python 3.11.9 runtime",
    )
    normalized_tdd = " ".join(tdd.split())
    for exact_fact in (
        "The initial five-node batch produced `3 failed, 2 passed`",
        "The strict controlled-review batch produced `9 failed, 2 passed`.",
        "the direct library unlock test still failed because no exception was raised for ineligible agreement.",
        "No failure was bypassed by weakening an assertion",
        "Injecting failures into primary replace call 2 and rollback call 3 reproduced the loss of the only old English copy because unconditional final cleanup deleted both backups.",
        "That new regression was RED before the recovery fix and GREEN after rollback errors were aggregated and recoverable bilingual backups were preserved.",
    ):
        assert normalized_tdd.count(exact_fact) == 1

    runtime = _evidence_subsection(
        text,
        "## Official Python 3.11.9 runtime",
        "## Final-fix focused checks",
    )
    assert _evidence_table_rows(runtime) == (
        (
            "Source URL",
            "`https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip`",
        ),
        ("Download size", "`11,249,023` bytes"),
        (
            "Locally computed SHA-256",
            "`009D6BF7E3B2DDCA3D784FA09F90FE54336D5B60F0E0F305C37F400BF83CFD3B`",
        ),
        (
            "Runtime",
            "`3.11.9 (tags/v3.11.9:de54cf5, Apr 2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]`",
        ),
        (
            "Temporary executable",
            "`C:\\tmp\\python-3.11.9-embed-amd64\\python.exe`",
        ),
    )
    normalized_runtime = " ".join(runtime.split())
    for exact_fact in (
        "The ZIP hash is the locally observed download hash, not a claim that it was independently matched to a separately published checksum.",
        "`pytest 9.0.2`, `PyYAML 6.0.3`",
        "`yaml.__with_libyaml__ == False`",
        "No installer, project dependency, declared Python support, PATH, file association, or tracked file was changed for this runtime.",
    ):
        assert normalized_runtime.count(exact_fact) == 1

    framework = _evidence_subsection(
        text,
        "## Final-fix focused checks",
        "## Functional-commit command observations",
    )
    normalized_framework = " ".join(framework.split())
    for exact_fact in (
        "The focused pytest command exited `0` with `17 passed in 1.15s` and verified:",
        "direct library calls independently recompute and enforce the blinded agreement unlock gate;",
        "protocol-deviation and study-limitation review objects are mandatory, condition-free, closed-schema, controlled, unique, and deterministically ordered;",
        "failure of the second bilingual report replacement restores both previous files and leaves no temporary or backup file; if that rollback also fails, the transaction raises a deterministic recovery-required error, cleans safe staged files, and preserves both old-language backups as a coherent pair;",
        "the environment fingerprint is documented as exactly eight hashed fields, with other manifest facts separately validated.",
        "All examples and fixtures used by these checks are synthetic.",
        "They contain no human answer text, participant data, real condition key, or institutional metadata.",
    ):
        assert normalized_framework.count(exact_fact) == 1
    command_blocks = re.findall(
        r"```text\n(?P<body>.+?)\n```",
        framework,
        flags=re.DOTALL,
    )
    assert command_blocks == [EFFECTIVENESS_FRAMEWORK_FOCUSED_COMMAND]

    functional = _evidence_subsection(
        text,
        "## Functional-commit command observations",
        "## Evidence refresh boundary",
    )
    functional_host = _evidence_subsection(
        functional,
        "### Host Python 3.13.13",
        "### Target Python 3.11.9",
    )
    functional_target = _evidence_subsection(
        functional,
        "### Target Python 3.11.9",
        None,
    )
    assert _evidence_table_rows(functional_host) == (
        ("`python -m pytest -q`", "0", "`550 passed in 23.13s`", "`24,198 ms`"),
        ("`python scripts/validate_skill.py`", "0", "no output/findings", "`59 ms`"),
        ("`python scripts/check_public_boundary.py`", "0", "no output/findings", "`193 ms`"),
        ("`python scripts/package_skill.py --check-reproducible`", "0", "no output; reproducibility check accepted", "`95 ms`"),
        ("`python scripts/render_eval_summary.py --check`", "0", "no output; checked-in deterministic Eval summary accepted", "`90 ms`"),
        ("`python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check`", "0", "no output; both checked-in synthetic reports accepted", "`114 ms`"),
        ("`git diff --check main...HEAD`", "0", "no output/whitespace errors in the committed branch diff", "`52 ms`"),
        ("`git status --short`", "0", "no output; functional worktree clean", "`52 ms`"),
    )
    assert _evidence_table_rows(functional_target) == (
        ("`python -m pytest -q`", "0", "`550 passed in 23.97s`", "`24,843 ms`"),
        ("`python scripts/validate_skill.py`", "0", "no output/findings", "`78 ms`"),
        ("`python scripts/check_public_boundary.py`", "0", "no output/findings", "`187 ms`"),
        ("`python scripts/package_skill.py --check-reproducible`", "0", "no output; reproducibility check accepted", "`107 ms`"),
        ("`python scripts/render_eval_summary.py --check`", "0", "no output; checked-in deterministic Eval summary accepted", "`110 ms`"),
        ("`python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check`", "0", "no output; both checked-in synthetic reports accepted", "`119 ms`"),
    )

    refresh = _evidence_subsection(
        text,
        "## Evidence refresh boundary",
        "## Complete diff and public-boundary audit",
    )
    normalized_refresh = " ".join(refresh.split())
    for exact_fact in (
        "This refresh changes only this immutable record and its SHA-locked contract in `tests/test_project_metadata.py`; it does not alter the functional implementation object.",
        "Post-evidence-commit full suites, required gates, renderer checks, diff checks, and final status are recorded in the final-fix execution report.",
        "This avoids claiming observations from a commit before that commit exists.",
    ):
        assert normalized_refresh.count(exact_fact) == 1

    audit = _evidence_subsection(
        text,
        "## Complete diff and public-boundary audit",
        "## Evidence and authority boundary",
    )
    normalized_audit = " ".join(audit.split())
    for exact_fact in (
        "The complete committed `main...HEAD` diff was loaded for review and contained no binary patch.",
        "At the functional object, `git diff --check main...HEAD` and `git status --short` both exited `0`",
        "the fresh `python scripts/check_public_boundary.py` scan also exited `0` with no findings.",
        "The changed-path review found no change to `pyproject.toml`, `.github/`, `docs/release.md`, `docs/releases/`, `CITATION.cff`, or `CHANGELOG.md`",
        "There is no tracked assignment file, participant-level dataset, human answer, blinded score file, ratings lock, condition key, nonce, confidential task pack, or external model snapshot represented as deterministic evidence.",
    ):
        assert normalized_audit.count(exact_fact) == 1

    authority = _evidence_subsection(
        text,
        "## Evidence and authority boundary",
        None,
    )
    normalized_authority = " ".join(authority.split())
    for exact_fact in (
        "There was no external model call for this verification.",
        "There was no human recruitment or data collection, no actual human task commitment, no real ratings lock or condition-key unlock, no tag or settings change, and no v0.4.0 Release.",
        "No pilot was completed or conducted, and there are no real participant outcomes.",
        "The only outcome example is synthetic and aggregate-only.",
        "This record does not claim that the Skill is effective, clinically valid, causally valid, or ready for real-use deployment.",
        "Completing the framework commit does not authorize governance, recruitment, human data collection, rating, unlock, analysis, or publication activity.",
        "Remaining external steps require separate authorization and observed inputs:",
    ):
        assert normalized_authority.count(exact_fact) == 1


def test_effectiveness_framework_evidence_is_dated_and_does_not_claim_a_pilot():
    text = (
        ROOT
        / "docs/verification/2026-08-09-v0.4.0-effectiveness-framework.md"
    ).read_text(encoding="utf-8")
    _assert_effectiveness_framework_evidence_contract(text)


@pytest.mark.parametrize(
    "contradictory_claim",
    (
        "The pilot was completed.",
        "The Skill was proven effective.",
        "An external model call was made.",
        "Participants were recruited.",
        "Human data were collected.",
        "An actual human task commitment was created.",
        "A tag was created.",
        "The v0.4.0 Release was published.",
        "Repository settings were changed.",
        "Real participant outcomes were reported.",
        "No external model call was made, and the pilot was completed.",
        "We completed the pilot.",
        "We proved the Skill effective.",
        "We recruited participants and collected human data.",
    ),
)
def test_effectiveness_framework_evidence_rejects_contradictory_positive_claims(
    contradictory_claim,
):
    text = (
        ROOT
        / "docs/verification/2026-08-09-v0.4.0-effectiveness-framework.md"
    ).read_text(encoding="utf-8")
    mutated = f"{text.rstrip()}\n\n{contradictory_claim}\n"

    with pytest.raises(AssertionError):
        _assert_effectiveness_framework_evidence_contract(mutated)


@pytest.mark.parametrize(
    "negated_claim",
    (
        "No pilot was completed.",
        "This record does not claim that the Skill was proven effective.",
        "No external model call was made.",
        "No participants were recruited and no human data were collected.",
        "No actual human task commitment was created.",
        "No tag was created, no v0.4.0 Release was published, and repository settings were not changed.",
        "No real participant outcomes were reported.",
    ),
)
def test_effectiveness_framework_evidence_rejects_even_negated_content_mutations(
    negated_claim,
):
    text = (
        ROOT
        / "docs/verification/2026-08-09-v0.4.0-effectiveness-framework.md"
    ).read_text(encoding="utf-8")
    mutated = f"{text.rstrip()}\n\n{negated_claim}\n"

    with pytest.raises(AssertionError):
        _assert_effectiveness_framework_evidence_contract(mutated)


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        (
            "Verification date: `2026-08-09`",
            "Verification date: `2026-08-10`",
        ),
        (
            "Implementation HEAD: `c6c9bee7ea8fd507f92bc72012666eb93cd2beb8`",
            "Implementation HEAD: `06c9bee7ea8fd507f92bc72012666eb93cd2beb8`",
        ),
        ("`550 passed in 23.13s`", "`551 passed in 23.13s`"),
        (
            "`python scripts/validate_skill.py` | 0 |",
            "`python scripts/validate_skill.py` | 1 |",
        ),
        (
            "No pilot was completed or conducted, and there are no real participant\n"
            "outcomes.",
            "A pilot was completed, and there are real participant outcomes.",
        ),
    ),
)
def test_effectiveness_framework_evidence_rejects_audited_fact_mutations(
    original,
    replacement,
):
    text = (
        ROOT
        / "docs/verification/2026-08-09-v0.4.0-effectiveness-framework.md"
    ).read_text(encoding="utf-8")
    assert original in text
    mutated = text.replace(original, replacement, 1)

    with pytest.raises(AssertionError):
        _assert_effectiveness_framework_evidence_contract(mutated)


def test_effectiveness_framework_evidence_lock_normalizes_lf_and_crlf():
    text = (
        ROOT
        / "docs/verification/2026-08-09-v0.4.0-effectiveness-framework.md"
    ).read_text(encoding="utf-8")
    lf_text = text.replace("\r\n", "\n").replace("\r", "\n")
    crlf_text = lf_text.replace("\n", "\r\n")

    _assert_effectiveness_framework_evidence_contract(lf_text)
    _assert_effectiveness_framework_evidence_contract(crlf_text)
