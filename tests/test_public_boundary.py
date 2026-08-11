from pathlib import Path
import subprocess
import sys

import pytest

from scripts.check_public_boundary import scan_repository


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "skills/clin-nav/references/tmucrd-public-profile.md"


def _initialize_git_repository(root: Path) -> None:
    subprocess.run(
        ["git", "init", "-q"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _force_track(root: Path, relative_path: str) -> None:
    subprocess.run(
        ["git", "add", "-f", "--", relative_path],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def test_scanner_blocks_private_dictionary_filename(tmp_path):
    path = tmp_path / "tmucrd-v2.16-dictionary.txt"
    path.write_text("synthetic test payload", encoding="utf-8")
    findings = scan_repository(tmp_path)
    assert any(item.rule == "private-filename" for item in findings)


def test_scanner_blocks_secret_pattern(tmp_path):
    path = tmp_path / "notes.md"
    secret = "api_" + "key = '" + "sk-" + ("x" * 24) + "'"
    path.write_text(secret, encoding="utf-8")
    findings = scan_repository(tmp_path)
    assert any(item.rule == "possible-secret" for item in findings)


def test_scanner_allows_public_profile(tmp_path):
    path = tmp_path / "tmucrd-public-profile.md"
    path.write_text(
        "public source snapshot; not a data dictionary",
        encoding="utf-8",
    )
    assert scan_repository(tmp_path) == []


def test_scanner_flags_pdf_files(tmp_path):
    (tmp_path / "public-paper.pdf").write_bytes(b"synthetic")
    findings = scan_repository(tmp_path)
    assert [(item.path, item.rule) for item in findings] == [
        ("public-paper.pdf", "pdf-file")
    ]


def test_scanner_flags_text_larger_than_limit(tmp_path):
    (tmp_path / "notes.md").write_text("0123456789", encoding="utf-8")
    findings = scan_repository(tmp_path, max_text_bytes=9)
    assert [(item.path, item.rule) for item in findings] == [
        ("notes.md", "large-text-file")
    ]


@pytest.mark.parametrize("filename", [".env", ".env.production"])
def test_scanner_unconditionally_rejects_force_tracked_env_files(
    tmp_path,
    filename,
):
    _initialize_git_repository(tmp_path)
    path = tmp_path / filename
    path.write_text("SERVICE_TOKEN=synthetic-secret-value", encoding="utf-8")
    _force_track(tmp_path, filename)

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (filename, "environment-file")
    ]


@pytest.mark.parametrize(
    "filename",
    ["private-dictionary.csv", "cohort.parquet"],
)
def test_scanner_rejects_non_allowlisted_data_artifacts(
    tmp_path,
    filename,
):
    path = tmp_path / filename
    path.write_bytes(b"synthetic data-shaped payload")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (filename, "data-artifact")
    ]


def test_scanner_allows_fixed_large_public_profile_path(tmp_path):
    path = (
        tmp_path
        / "skills/clin-nav/references/tmucrd-public-profile.md"
    )
    path.parent.mkdir(parents=True)
    path.write_text("0123456789", encoding="utf-8")
    assert scan_repository(tmp_path, max_text_bytes=9) == []


def test_scanner_skips_ignored_build_and_sdd_scratch(tmp_path):
    _initialize_git_repository(tmp_path)
    (tmp_path / ".gitignore").write_text(
        ".superpowers/sdd/\ndist/\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "--", ".gitignore"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    ignored = tmp_path / ".superpowers" / "sdd"
    ignored.mkdir(parents=True)
    (ignored / "tmucrd-v2.16-dictionary.txt").write_text(
        "api_" + "key = '" + "sk-" + ("x" * 24) + "'",
        encoding="utf-8",
    )
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "archive.pdf").write_bytes(b"synthetic")
    assert scan_repository(tmp_path) == []


def test_scanner_does_not_skip_force_tracked_sdd_private_content(tmp_path):
    _initialize_git_repository(tmp_path)
    path = tmp_path / ".superpowers/sdd/notes.md"
    path.parent.mkdir(parents=True)
    path.write_text("sk-" + ("x" * 24), encoding="utf-8")
    _force_track(tmp_path, ".superpowers/sdd/notes.md")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (".superpowers/sdd/notes.md", "possible-secret")
    ]


def test_scanner_scans_non_sdd_superpowers_content(tmp_path):
    directory = tmp_path / ".superpowers" / "not-sdd"
    directory.mkdir(parents=True)
    (directory / "private.pdf").write_bytes(b"synthetic")
    (directory / "notes.md").write_text("sk-" + ("x" * 24), encoding="utf-8")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (".superpowers/not-sdd/notes.md", "possible-secret"),
        (".superpowers/not-sdd/private.pdf", "pdf-file"),
    ]


def test_scanner_skips_only_the_repository_dot_worktrees_container(tmp_path):
    sibling_fixture = tmp_path / ".worktrees/feature/stale-codingbook.md"
    sibling_fixture.parent.mkdir(parents=True)
    sibling_fixture.write_text("synthetic negative fixture", encoding="utf-8")
    ordinary_fixture = tmp_path / "worktrees/feature/stale-codingbook.md"
    ordinary_fixture.parent.mkdir(parents=True)
    ordinary_fixture.write_text("synthetic public file", encoding="utf-8")
    nested_fixture = tmp_path / "docs/.worktrees/stale-codingbook.md"
    nested_fixture.parent.mkdir(parents=True)
    nested_fixture.write_text("synthetic nested private file", encoding="utf-8")

    assert [
        (finding.path, finding.rule)
        for finding in scan_repository(sibling_fixture.parent)
    ] == [("stale-codingbook.md", "private-filename")]
    assert [
        (finding.path, finding.rule)
        for finding in scan_repository(tmp_path)
    ] == [
        ("docs/.worktrees/stale-codingbook.md", "private-filename"),
        ("worktrees/feature/stale-codingbook.md", "private-filename"),
    ]


def test_scanner_skips_git_and_python_cache_directories(tmp_path):
    _initialize_git_repository(tmp_path)
    for directory in (".git", ".pytest_cache", "__pycache__"):
        path = tmp_path / directory / "archive.pdf"
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"synthetic")
    assert scan_repository(tmp_path) == []


def test_scanner_exempts_only_named_synthetic_eval_fixtures(tmp_path):
    for relative_path in (
        "tests/fixtures/baseline/stale-codingbook.md",
        "tests/fixtures/forward/stale-codingbook.md",
    ):
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic fixture", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere/stale-codingbook.md"
    elsewhere.parent.mkdir()
    elsewhere.write_text("synthetic fixture", encoding="utf-8")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        ("elsewhere/stale-codingbook.md", "private-filename")
    ]


def test_scanner_checks_secrets_inside_exempt_synthetic_eval_fixtures(tmp_path):
    path = tmp_path / "tests/fixtures/baseline/stale-codingbook.md"
    path.parent.mkdir(parents=True)
    path.write_text("sk-" + ("x" * 24), encoding="utf-8")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        ("tests/fixtures/baseline/stale-codingbook.md", "possible-secret")
    ]


def test_scanner_returns_findings_in_path_and_rule_order(tmp_path):
    (tmp_path / "z.pdf").write_bytes(b"synthetic")
    (tmp_path / "a-codebook.md").write_text("synthetic", encoding="utf-8")
    findings = scan_repository(tmp_path)
    assert [(item.path, item.rule) for item in findings] == [
        ("a-codebook.md", "private-filename"),
        ("z.pdf", "pdf-file"),
    ]


@pytest.mark.parametrize(
    "relative_path",
    [
        "study-data/participants.json",
        "study-governance/readiness.json",
        "evals/effectiveness/raw/answers.json",
        "evals/effectiveness/private/condition-key.json",
        "evals/effectiveness/participant-data/scores.json",
    ],
)
def test_scanner_rejects_human_study_private_paths(tmp_path, relative_path):
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True)
    path.write_text("synthetic boundary sentinel", encoding="utf-8")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (relative_path, "private-study-data")
    ]


def test_scanner_does_not_print_private_study_payload(tmp_path):
    payload = "participant-answer-must-not-appear"
    path = tmp_path / "study-data/answers.json"
    path.parent.mkdir()
    path.write_text(payload, encoding="utf-8")

    finding = scan_repository(tmp_path)[0]

    assert finding.detail == "human-study raw data is not permitted in the public project"
    assert payload not in finding.detail


def test_scanner_does_not_read_or_print_governance_payload(tmp_path):
    marker = "PRIVATE-GOVERNANCE-MARKER-7F31"
    path = tmp_path / "study-governance/readiness.json"
    path.parent.mkdir()
    path.write_text(marker, encoding="utf-8")

    finding = scan_repository(tmp_path)[0]

    assert (finding.path, finding.rule) == (
        "study-governance/readiness.json",
        "private-study-data",
    )
    assert marker not in finding.detail


@pytest.mark.parametrize(
    "relative_path",
    (
        "evals/effectiveness/recovery/real/recovery-record.json",
        "evals/effectiveness/recovery/incident-record.json",
        "evals/effectiveness/recovery/condition-key.json",
        "evals/effectiveness/recovery/human-task-pack.yaml",
    ),
)
def test_scanner_rejects_private_recovery_artifact_paths_without_content(
    tmp_path, relative_path
):
    marker = "PRIVATE-RECOVERY-CONTENT-MUST-NOT-APPEAR"
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(marker, encoding="utf-8")

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (relative_path, "private-recovery-artifact")
    ]
    assert all(marker not in item.detail for item in findings)


def test_scanner_does_not_read_private_recovery_artifact(tmp_path, monkeypatch):
    relative_path = "evals/effectiveness/recovery/real/opaque-record.json"
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True)
    path.write_text("synthetic sentinel", encoding="utf-8")
    original_read_text = Path.read_text

    def fail_on_private_recovery_read(self, *args, **kwargs):
        if self == path:
            raise AssertionError("private recovery artifact was read")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_on_private_recovery_read)

    findings = scan_repository(tmp_path)

    assert [(item.path, item.rule) for item in findings] == [
        (relative_path, "private-recovery-artifact")
    ]


def test_gitignore_keeps_study_governance_out_of_the_checkout():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "study-governance/" in lines


def test_public_profile_has_required_public_source_guards():
    text = PROFILE.read_text(encoding="utf-8")
    assert "public source snapshot" in text
    assert "not a data dictionary" in text
    assert "10.1136/bmjhci-2023-100890" in text


def test_public_profile_uses_formal_article_title_and_web_access_date():
    text = PROFILE.read_text(encoding="utf-8")
    assert (
        "Taipei Medical University Clinical Research Database: A collaborative "
        "hospital EHR database aligned with international common data standards"
        in text
    )
    assert "Accessed 2026-07-27." in text


def test_public_profile_rejects_version_like_private_schema_claim():
    assert "V2.16" not in PROFILE.read_text(encoding="utf-8")


def test_cli_returns_nonzero_without_printing_matched_secret(tmp_path):
    secret = "sk-" + ("x" * 24)
    (tmp_path / "notes.md").write_text(secret, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/check_public_boundary.py"), str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "notes.md: possible-secret:" in result.stdout
    assert secret not in result.stdout


def test_actual_repository_has_no_public_boundary_findings():
    assert scan_repository(ROOT) == []
