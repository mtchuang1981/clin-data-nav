"""Synthetic audit contracts preserve, rather than erase, review gaps."""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest

from test_evidence_ledger import complete_payload

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/clin-nav/scripts"))
AS_OF = "2026-10-02"


def rebind(ledger, audit):
    data = json.dumps(ledger, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    audit["ledger_sha256"] = hashlib.sha256(data).hexdigest()


def complete_pair():
    ledger = complete_payload()
    ledger["prepared_on"] = "2026-10-01"
    ledger["sources"][0]["reviewed_on"] = "2026-10-01"
    audit = {
        "schema_version": "1", "ledger_id": ledger["ledger_id"], "ledger_sha256": "",
        "checked_on": AS_OF,
        "sources": [{"source_id": "source-official-1", "retrieval_url": "https://example.org/synthetic",
                     "access_status": "opened", "authority_role": "official-product", "use_scope": "current",
                     "version_status": "current", "status_basis_url": "https://example.org/status",
                     "newer_source_search": {"performed_on": AS_OF, "entry_points": ["https://example.org/search"],
                                             "result": "no-newer-found", "notes": "Synthetic search only."},
                     "notes": "Synthetic current scope, not actual source verification."}],
        "claims": [{"claim_id": "claim-rwd-definition", "source_checks": [
                       {"source_id": "source-official-1", "evidence_location": "Synthetic section 1", "locator_status": "verified"}],
                    "authority_fit": "appropriate", "support_fit": "appropriate", "notes": "Synthetic assessment only."}],
    }
    rebind(ledger, audit)
    return ledger, audit


@pytest.fixture
def core():
    assert importlib.util.find_spec("evidence_audit") is not None, "evidence audit API is absent"
    return importlib.import_module("evidence_audit")


def test_complete_pair_has_recorded_checks_complete(core):
    ledger, audit = complete_pair()
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    summary = core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)
    assert summary == {"schema_version": "1", "ledger_id": "synthetic-rwd-review", "as_of": AS_OF,
                       "status": "recorded-checks-complete", "ledger_status": "complete",
                       "source_count": 1, "claim_count": 1, "source_review_items": [], "claim_review_items": []}


def test_hash_ignores_object_key_order_but_not_claim_changes(core):
    ledger, audit = complete_pair()
    assert core.audit_ledger_sha256(dict(reversed(list(ledger.items())))) == audit["ledger_sha256"]
    ledger["claims"][0]["claim"] += " Changed."
    assert core.audit_ledger_sha256(ledger) != audit["ledger_sha256"]
    assert "ledger-hash-mismatch" in core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
    ledger["sources"].append({**ledger["sources"][0], "source_id": "source-second"})
    first = core.audit_ledger_sha256(ledger)
    ledger["sources"].reverse()
    assert core.audit_ledger_sha256(ledger) != first


@pytest.mark.parametrize("field", ["sources", "claims"])
@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate"])
def test_audit_requires_exact_ids(core, field, mutation):
    ledger, audit = complete_pair()
    if mutation == "missing":
        audit[field] = []
    else:
        row = copy.deepcopy(audit[field][0])
        if mutation == "extra":
            row["source_id" if field == "sources" else "claim_id"] = "unknown-extra"
        audit[field].append(row)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate"])
def test_exact_per_source_locators(core, mutation):
    ledger, audit = complete_pair()
    ledger["sources"].append({**ledger["sources"][0], "source_id": "source-second"})
    audit["sources"].append(copy.deepcopy(audit["sources"][0]))
    audit["sources"][-1]["source_id"] = "source-second"
    ledger["claims"][0]["source_ids"].append("source-second")
    audit["claims"][0]["source_checks"].append({"source_id": "source-second", "evidence_location": "Synthetic section 2", "locator_status": "verified"})
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    checks = audit["claims"][0]["source_checks"]
    if mutation == "missing":
        checks.pop()
    elif mutation == "extra":
        checks.append({**checks[0], "source_id": "unknown-extra"})
    else:
        checks.append(copy.deepcopy(checks[0]))
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize(("status", "reason"), [("partial-support", "ledger-partial-support"),
                                               ("unsupported", "ledger-unsupported"), ("not-assessed", "ledger-not-assessed")])
def test_ledger_review_items_are_never_cleared_by_audit(core, status, reason):
    ledger, audit = complete_pair()
    ledger["claims"][0]["support_status"] = status
    rebind(ledger, audit)
    result = core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)
    assert result["status"] == "needs-review" and result["ledger_status"] == "review-required"
    assert reason in result["claim_review_items"][0]["reasons"]


@pytest.mark.parametrize(("field", "value", "reason"), [("review_due_on", AS_OF, "ledger-review-due"),
                                                        ("stable_identifier", None, "ledger-source-unidentified"),
                                                        ("review_due_on", None, "ledger-freshness-unknown")])
def test_source_ledger_gaps_remain(core, field, value, reason):
    ledger, audit = complete_pair()
    ledger["sources"][0][field] = value
    rebind(ledger, audit)
    result = core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)
    assert result["status"] == "needs-review"
    assert reason in result["source_review_items"][0]["reasons"]


def test_request_provided_na_still_requires_ledger_review(core):
    ledger, audit = complete_pair()
    ledger["claims"][0].update(claim_type="request-provided", source_ids=[], evidence_location=None, support_status="not-assessed")
    audit["claims"][0].update(source_checks=[], authority_fit="not-applicable", support_fit="not-applicable")
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    assert core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)["status"] == "needs-review"


@pytest.mark.parametrize("scope", ["current", "historical", "development", "not-assessed"])
@pytest.mark.parametrize("version", ["current", "superseded", "in-development", "unknown"])
def test_freshness_is_scope_aware(core, scope, version):
    ledger, audit = complete_pair()
    ledger["sources"][0]["applicability"] = f"Synthetic {scope} scope only."
    audit["sources"][0].update(use_scope=scope, version_status=version)
    rebind(ledger, audit)
    result = core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)
    review = scope == "not-assessed" or version == "unknown" or (scope == "current" and version != "current")
    assert result["status"] == ("needs-review" if review else "recorded-checks-complete")


@pytest.mark.parametrize("scope", ["current", "historical", "development", "not-assessed"])
def test_not_performed_search_always_needs_review(core, scope):
    ledger, audit = complete_pair()
    ledger["sources"][0]["applicability"] = f"Synthetic {scope} scope only."
    audit["sources"][0]["use_scope"] = scope
    audit["sources"][0]["newer_source_search"].update(performed_on=None, entry_points=[], result="not-performed")
    rebind(ledger, audit)
    assert core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)["status"] == "needs-review"


def test_current_not_applicable_is_invalid_but_historical_is_valid(core):
    ledger, audit = complete_pair()
    audit["sources"][0]["newer_source_search"].update(performed_on=None, entry_points=[], result="not-applicable")
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
    audit["sources"][0]["use_scope"] = "historical"
    ledger["sources"][0]["applicability"] = "Synthetic historical scope only."
    rebind(ledger, audit)
    assert core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)["status"] == "recorded-checks-complete"


@pytest.mark.parametrize("scope", ["current", "historical", "development"])
def test_newer_found_is_not_automatically_wrong_for_historical_scope(core, scope):
    ledger, audit = complete_pair()
    ledger["sources"][0]["applicability"] = f"Synthetic {scope} scope only."
    audit["sources"][0]["use_scope"] = scope
    audit["sources"][0]["newer_source_search"]["result"] = "newer-found"
    rebind(ledger, audit)
    assert core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)["status"] == ("needs-review" if scope == "current" else "recorded-checks-complete")


@pytest.mark.parametrize(("field", "value", "reason"), [("support_fit", "overstated", "support-overstated"),
    ("support_fit", "understated", "support-understated"), ("support_fit", "not-assessed", "support-not-assessed"),
    ("authority_fit", "insufficient", "authority-insufficient"), ("authority_fit", "conflicted", "authority-conflicted"),
    ("authority_fit", "not-assessed", "authority-not-assessed")])
def test_recorded_fit_gaps_are_valid_but_need_review(core, field, value, reason):
    ledger, audit = complete_pair()
    audit["claims"][0][field] = value
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    result = core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)
    assert result["status"] == "needs-review" and reason in result["claim_review_items"][0]["reasons"]


@pytest.mark.parametrize(("access", "status", "verified", "valid"), [
    ("opened", "reviewed", True, True), ("conflicted", "reviewed", True, True),
    ("abstract-only", "not-reviewed", False, True), ("unavailable", "unavailable", False, True),
    ("not-attempted", "not-reviewed", False, True), ("opened", "not-reviewed", False, False),
    ("abstract-only", "reviewed", True, False), ("unavailable", "not-reviewed", False, False)])
def test_access_and_locator_compatibility(core, access, status, verified, valid):
    ledger, audit = complete_pair()
    ledger["sources"][0].update(review_status=status, reviewed_on="2026-10-01" if status == "reviewed" else None)
    if status != "reviewed":
        ledger["claims"][0].update(support_status="not-assessed", evidence_location=None)
    audit["sources"][0]["access_status"] = access
    audit["claims"][0]["source_checks"][0].update(locator_status="verified" if verified else "not-verified", evidence_location="Synthetic section 1" if verified else None)
    rebind(ledger, audit)
    assert (core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []) is valid


@pytest.mark.parametrize("url", ["http://example.org", "https://user:pass@example.org", "https://example.org?key=SYNTH_SECRET",
    "https://example.org/#SYNTH_SECRET", "https://localhost/x", "https://127.0.0.1/x", "https://[::1]/x", "https://server/x"])
def test_private_or_credential_urls_are_invalid_without_echo(core, url):
    ledger, audit = complete_pair()
    audit["sources"][0]["retrieval_url"] = url
    errors = core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
    assert errors and all("SYNTH_SECRET" not in error and url not in error for error in errors)


@pytest.mark.parametrize("row_path", [(), ("sources", 0), ("sources", 0, "newer_source_search"), ("claims", 0), ("claims", 0, "source_checks", 0)])
def test_closed_fields_reject_sensitive_extra_keys(core, row_path):
    ledger, audit = complete_pair()
    row = audit
    for part in row_path:
        row = row[part]
    row["SYNTH_SECRET"] = "private sentinel"
    errors = core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
    assert errors and "SYNTH_SECRET" not in json.dumps(errors)


@pytest.mark.parametrize(("field", "value"), [("access_status", []), ("authority_role", True), ("notes", " "),
    ("version_status", "future-unknown-enum"), ("use_scope", {}), ("source_id", "x" * 81)])
def test_invalid_source_types_and_values_are_invalid(core, field, value):
    ledger, audit = complete_pair()
    audit["sources"][0][field] = value
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize("value", ["2026-10-03", "2026-09-30", "20261002", "not-a-date", True])
def test_checked_date_binding(core, value):
    ledger, audit = complete_pair()
    audit["checked_on"] = value
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_observation_dates_cannot_follow_checked_date(core):
    ledger, audit = complete_pair()
    audit["sources"][0]["newer_source_search"]["performed_on"] = "2026-10-03"
    assert core.validate_evidence_audit(ledger, audit, as_of="2026-10-04")
    audit["sources"][0]["newer_source_search"]["performed_on"] = AS_OF
    ledger["sources"][0]["reviewed_on"] = "2026-10-03"
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of="2026-10-04")


@pytest.mark.parametrize(("field", "length"), [("notes", 4000), ("retrieval_url", 2048)])
def test_text_and_url_exact_limits_are_not_truncated(core, field, length):
    ledger, audit = complete_pair()
    prefix = "https://example.org/" if field == "retrieval_url" else ""
    audit["sources"][0][field] = prefix + "a" * (length - len(prefix))
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    audit["sources"][0][field] += "a"
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_entry_point_limit_and_uniqueness(core):
    ledger, audit = complete_pair()
    search = audit["sources"][0]["newer_source_search"]
    search["entry_points"] = [f"https://example.org/synth/{index}" for index in range(20)]
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    search["entry_points"].append("https://example.org/synth/20")
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
    search["entry_points"] = ["https://example.org/x"] * 2
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_verified_locator_requires_location(core):
    ledger, audit = complete_pair()
    audit["claims"][0]["source_checks"][0]["evidence_location"] = None
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_non_request_claim_cannot_claim_not_applicable_fit(core):
    ledger, audit = complete_pair()
    audit["claims"][0]["authority_fit"] = "not-applicable"
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize("field", ["sources", "claims"])
def test_record_count_exact_limit_and_one_over(core, field):
    ledger, audit = complete_pair()
    identity = "source_id" if field == "sources" else "claim_id"
    ledger[field] = [{**copy.deepcopy(ledger[field][0]), identity: f"record-{i}"} for i in range(100)]
    audit[field] = [{**copy.deepcopy(audit[field][0]), identity: f"record-{i}"} for i in range(100)]
    if field == "sources":
        ledger["claims"][0]["source_ids"] = ["record-0"]
        audit["claims"][0]["source_checks"][0]["source_id"] = "record-0"
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    ledger[field].append({**copy.deepcopy(ledger[field][0]), identity: "record-over"})
    audit[field].append({**copy.deepcopy(audit[field][0]), identity: "record-over"})
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_per_claim_check_count_at_limit(core):
    ledger, audit = complete_pair()
    ledger["sources"] = [{**copy.deepcopy(ledger["sources"][0]), "source_id": f"record-{i}"} for i in range(100)]
    audit["sources"] = [{**copy.deepcopy(audit["sources"][0]), "source_id": f"record-{i}"} for i in range(100)]
    ledger["claims"][0]["source_ids"] = [f"record-{i}" for i in range(100)]
    audit["claims"][0]["source_checks"] = [{**copy.deepcopy(audit["claims"][0]["source_checks"][0]), "source_id": f"record-{i}"} for i in range(100)]
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    audit["claims"][0]["source_checks"].append(copy.deepcopy(audit["claims"][0]["source_checks"][0]))
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_id_limit_at_80_not_81(core):
    ledger, audit = complete_pair()
    ledger["ledger_id"] = audit["ledger_id"] = "a" * 80
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    ledger["ledger_id"] = audit["ledger_id"] = "a" * 81
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_audit_summary_does_not_echo_notes_or_urls(core):
    ledger, audit = complete_pair()
    audit["claims"][0].update(support_fit="overstated", notes="SYNTH_SECRET")
    result = core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)
    encoded = json.dumps(result)
    assert "SYNTH_SECRET" not in encoded and "example.org" not in encoded
    assert result == core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize(("status", "reason"), [("not-performed", "newer-search-not-performed"), ("unavailable", "newer-search-unavailable")])
def test_search_failure_reason_is_preserved(core, status, reason):
    ledger, audit = complete_pair()
    search = audit["sources"][0]["newer_source_search"]
    search["result"] = status
    if status == "not-performed":
        search.update(performed_on=None, entry_points=[])
    assert reason in core.summarize_evidence_audit(ledger, audit, as_of=AS_OF)["source_review_items"][0]["reasons"]


@pytest.mark.parametrize("field", ["schema_version", "ledger_id", "ledger_sha256"])
def test_audit_version_and_identity_binding(core, field):
    ledger, audit = complete_pair()
    audit[field] = "mismatched"
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize(("field", "value"), [("authority_fit", []), ("support_fit", True), ("notes", " ")])
def test_invalid_claim_types_do_not_raise_or_leak(core, field, value):
    ledger, audit = complete_pair()
    audit["claims"][0][field] = value
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize(("path", "limit"), [(("claims", 0, "notes"), 4000),
    (("claims", 0, "source_checks", 0, "evidence_location"), 4000),
    (("sources", 0, "newer_source_search", "notes"), 4000), (("sources", 0, "status_basis_url"), 2048)])
def test_every_bounded_audit_text_slot(core, path, limit):
    ledger, audit = complete_pair()
    row = audit
    for part in path[:-1]:
        row = row[part]
    prefix = "https://example.org/" if limit == 2048 else ""
    row[path[-1]] = prefix + "a" * (limit - len(prefix))
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    row[path[-1]] += "a"
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


@pytest.mark.parametrize("result", ["no-newer-found", "newer-found", "unavailable"])
def test_performed_search_requires_date_entry_points_and_notes(core, result):
    ledger, audit = complete_pair()
    search = audit["sources"][0]["newer_source_search"]
    search.update(result=result, performed_on=None)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
    search.update(performed_on=AS_OF, entry_points=[])
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)


def test_direct_api_still_bounds_serialized_ledger(core):
    ledger, audit = complete_pair()
    ledger["claims"][0]["claim"] = ""
    raw = json.dumps(ledger, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ledger["claims"][0]["claim"] = "a" * (262144 - len(raw))
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF) == []
    ledger["claims"][0]["claim"] += "a"
    rebind(ledger, audit)
    assert core.validate_evidence_audit(ledger, audit, as_of=AS_OF)
