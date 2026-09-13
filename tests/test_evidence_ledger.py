import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = ROOT / "skills/clin-nav/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from evidence_ledger import summarize_evidence_ledger, validate_evidence_ledger


CLI = ROOT / "scripts/check_evidence_ledger.py"
PACKAGED_CLI = SKILL_SCRIPTS / "check_evidence_ledger.py"
EXAMPLE = ROOT / "skills/clin-nav/references/evidence-ledger-example.json"
CLI_ERROR = "evidence ledger validation failed\n"


def complete_payload() -> dict:
    return {
        "schema_version": "1",
        "ledger_id": "synthetic-rwd-review",
        "prepared_on": "2026-09-10",
        "sources": [
            {
                "source_id": "source-official-1",
                "title": "Synthetic official guidance",
                "stable_identifier": "urn:example:official-guidance",
                "authority_level": "official",
                "publication_date": "2026-01-15",
                "version_or_snapshot": "synthetic-v1",
                "review_status": "reviewed",
                "reviewed_on": "2026-09-09",
                "review_due_on": "2027-03-09",
                "applicability": "Synthetic public RWD example only.",
                "limitations": "Not institutional metadata.",
            }
        ],
        "claims": [
            {
                "claim_id": "claim-rwd-definition",
                "claim": "Synthetic definition claim.",
                "claim_type": "external-fact",
                "source_ids": ["source-official-1"],
                "evidence_location": "Synthetic section 1",
                "support_status": "direct-support",
                "applicability": "Terminology explanation only.",
                "limitations": "Does not establish local data fitness.",
            }
        ],
    }


def run_cli(cli: Path, path: Path, as_of: str = "2026-09-13") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(cli), "--input", str(path), "--as-of", as_of],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_complete_reviewed_ledger_is_valid_and_within_review_window():
    payload = complete_payload()

    assert validate_evidence_ledger(payload, as_of="2026-09-13") == []
    assert summarize_evidence_ledger(payload, as_of="2026-09-13") == {
        "as_of": "2026-09-13",
        "claim_count": 1,
        "not_assessed_claim_ids": [],
        "partial_support_claim_ids": [],
        "review_due_source_ids": [],
        "schema_version": "1",
        "source_count": 1,
        "status": "complete",
        "unavailable_source_ids": [],
        "unidentified_source_ids": [],
        "unknown_freshness_source_ids": [],
        "unreviewed_source_ids": [],
        "unsupported_claim_ids": [],
    }


def test_due_date_is_computed_from_cli_as_of_and_does_not_mean_invalid_source():
    payload = complete_payload()

    summary = summarize_evidence_ledger(payload, as_of="2027-03-09")

    assert summary["status"] == "review-required"
    assert summary["review_due_source_ids"] == ["source-official-1"]
    assert summary["unsupported_claim_ids"] == []


@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.update(extra=True),
        lambda value: value.pop("claims"),
        lambda value: value.__setitem__("schema_version", 1),
        lambda value: value.__setitem__("ledger_id", "Contains Spaces"),
        lambda value: value.__setitem__("prepared_on", "2026/09/10"),
        lambda value: value.__setitem__("sources", {}),
        lambda value: value.__setitem__("claims", {}),
    ),
)
def test_top_level_schema_mutations_fail_closed(mutate):
    payload = complete_payload()
    mutate(payload)

    assert validate_evidence_ledger(payload, as_of="2026-09-13")


def test_empty_ledger_cannot_receive_a_complete_status():
    payload = complete_payload()
    payload["sources"] = []
    payload["claims"] = []

    errors = validate_evidence_ledger(payload, as_of="2026-09-13")

    assert "claims must not be empty" in errors


def test_source_and_claim_rows_use_closed_schemas():
    payload = complete_payload()
    payload["sources"][0]["private_note"] = "must not be accepted"
    payload["claims"][0]["confidence"] = 0.9

    errors = validate_evidence_ledger(payload, as_of="2026-09-13")

    assert "source row 0 unexpected key: private_note" in errors
    assert "claim row 0 unexpected key: confidence" in errors


@pytest.mark.parametrize(
    ("review_status", "reviewed_on", "support_status", "expected_fragment"),
    (
        ("reviewed", None, "direct-support", "reviewed_on is required"),
        ("not-reviewed", "2026-09-09", "not-assessed", "reviewed_on must be null"),
        ("unavailable", "2026-09-09", "not-assessed", "reviewed_on must be null"),
        ("not-reviewed", None, "direct-support", "requires reviewed sources"),
        ("unavailable", None, "partial-support", "requires reviewed sources"),
        ("not-reviewed", None, "unsupported", "requires reviewed sources"),
    ),
)
def test_unreviewed_or_unavailable_sources_cannot_support_assessed_claims(
    review_status, reviewed_on, support_status, expected_fragment
):
    payload = complete_payload()
    payload["sources"][0]["review_status"] = review_status
    payload["sources"][0]["reviewed_on"] = reviewed_on
    payload["claims"][0]["support_status"] = support_status

    errors = validate_evidence_ledger(payload, as_of="2026-09-13")

    assert any(expected_fragment in error for error in errors)


def test_duplicate_ids_and_dangling_source_references_fail_closed():
    payload = complete_payload()
    payload["sources"].append(copy.deepcopy(payload["sources"][0]))
    payload["claims"][0]["source_ids"] = ["missing-source"]

    errors = validate_evidence_ledger(payload, as_of="2026-09-13")

    assert "duplicate source_id: source-official-1" in errors
    assert "claim claim-rwd-definition references unknown source_id" in errors


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("publication_date", "2026-09-14"),
        ("reviewed_on", "2026-09-14"),
        ("review_due_on", "2026/10/01"),
    ),
)
def test_invalid_or_future_evidence_dates_fail_closed(field, value):
    payload = complete_payload()
    payload["sources"][0][field] = value

    errors = validate_evidence_ledger(payload, as_of="2026-09-13")

    assert errors


def test_assessed_support_requires_sources_and_evidence_location():
    payload = complete_payload()
    payload["claims"][0]["source_ids"] = []
    payload["claims"][0]["evidence_location"] = None

    errors = validate_evidence_ledger(payload, as_of="2026-09-13")

    assert any("requires at least one source" in error for error in errors)
    assert any("requires evidence_location" in error for error in errors)


def test_valid_open_items_are_summarized_without_raw_claim_or_source_text():
    payload = complete_payload()
    payload["sources"][0]["review_status"] = "not-reviewed"
    payload["sources"][0]["reviewed_on"] = None
    payload["sources"][0]["review_due_on"] = None
    payload["claims"][0]["support_status"] = "not-assessed"
    payload["claims"][0]["evidence_location"] = None

    summary = summarize_evidence_ledger(payload, as_of="2026-09-13")
    serialized = json.dumps(summary)

    assert summary["status"] == "review-required"
    assert summary["unreviewed_source_ids"] == ["source-official-1"]
    assert summary["unknown_freshness_source_ids"] == ["source-official-1"]
    assert summary["not_assessed_claim_ids"] == ["claim-rwd-definition"]
    assert payload["sources"][0]["title"] not in serialized
    assert payload["claims"][0]["claim"] not in serialized


def test_unknown_stable_identifier_is_null_and_requires_follow_up():
    payload = complete_payload()
    payload["sources"][0]["stable_identifier"] = None

    assert validate_evidence_ledger(payload, as_of="2026-09-13") == []
    summary = summarize_evidence_ledger(payload, as_of="2026-09-13")
    assert summary["status"] == "review-required"
    assert summary["unidentified_source_ids"] == ["source-official-1"]


def test_checked_in_example_is_synthetic_valid_and_packaged():
    payload = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    assert payload["ledger_id"].startswith("synthetic-")
    assert validate_evidence_ledger(payload, as_of="2026-09-13") == []
    assert PACKAGED_CLI.is_file()


@pytest.mark.parametrize("cli", (CLI, PACKAGED_CLI))
def test_cli_returns_zero_for_complete_external_ledger(tmp_path, cli):
    path = tmp_path / "evidence-ledger.json"
    path.write_text(json.dumps(complete_payload()), encoding="utf-8")

    result = run_cli(cli, path)

    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "complete"
    assert result.stderr == ""


def test_cli_returns_three_for_valid_ledger_requiring_review(tmp_path):
    payload = complete_payload()
    payload["sources"][0]["review_due_on"] = "2026-09-13"
    path = tmp_path / "evidence-ledger.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_cli(CLI, path)

    assert result.returncode == 3
    assert json.loads(result.stdout)["review_due_source_ids"] == [
        "source-official-1"
    ]
    assert result.stderr == ""


def test_cli_rejects_repository_internal_input_without_disclosure():
    result = run_cli(CLI, EXAMPLE)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert str(EXAMPLE) not in result.stderr


def test_cli_rejects_invalid_input_without_disclosing_content(tmp_path):
    path = tmp_path / "private-ledger.json"
    marker = "PRIVATE-EVIDENCE-MARKER-7F31"
    path.write_text('{"marker": "' + marker, encoding="utf-8")

    result = run_cli(CLI, path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    for hidden in (str(path), marker, "Traceback"):
        assert hidden not in result.stdout + result.stderr


def test_cli_rejects_as_of_before_ledger_preparation(tmp_path):
    path = tmp_path / "evidence-ledger.json"
    path.write_text(json.dumps(complete_payload()), encoding="utf-8")

    result = run_cli(CLI, path, as_of="2026-09-09")

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
