from pathlib import Path
import subprocess
import sys

from scripts.check_public_boundary import scan_repository


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "skills/clinical-data-research-navigator/references/tmucrd-public-profile.md"


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


def test_scanner_allows_fixed_large_public_profile_path(tmp_path):
    path = (
        tmp_path
        / "skills/clinical-data-research-navigator/references/tmucrd-public-profile.md"
    )
    path.parent.mkdir(parents=True)
    path.write_text("0123456789", encoding="utf-8")
    assert scan_repository(tmp_path, max_text_bytes=9) == []


def test_scanner_skips_ignored_build_and_sdd_scratch(tmp_path):
    ignored = tmp_path / ".superpowers" / "sdd"
    ignored.mkdir(parents=True)
    (ignored / "tmucrd-v2.16-dictionary.txt").write_text(
        "api_" + "key = '" + "sk-" + ("x" * 24) + "'",
        encoding="utf-8",
    )
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "archive.pdf").write_bytes(b"synthetic")
    assert scan_repository(tmp_path) == []


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


def test_scanner_skips_git_and_python_cache_directories(tmp_path):
    for directory in (".git", ".pytest_cache", "__pycache__"):
        path = tmp_path / directory / "archive.pdf"
        path.parent.mkdir()
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


def test_public_profile_has_required_public_source_guards():
    text = PROFILE.read_text(encoding="utf-8")
    assert "public source snapshot" in text
    assert "not a data dictionary" in text
    assert "10.1136/bmjhci-2023-100890" in text


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
