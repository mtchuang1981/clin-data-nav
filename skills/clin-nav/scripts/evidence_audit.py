"""Offline consistency checks for human-recorded evidence audits, not truth checks."""
from __future__ import annotations

from datetime import date
import hashlib
import ipaddress
import json
import re
from urllib.parse import urlsplit

from bounded_json import parse_strict_json
from evidence_ledger import ID_PATTERN, validate_evidence_ledger, summarize_evidence_ledger

MAX_BYTES = 262144
TOP = {"schema_version", "ledger_id", "ledger_sha256", "checked_on", "sources", "claims"}
SOURCE = {"source_id", "retrieval_url", "access_status", "authority_role", "use_scope", "version_status", "status_basis_url", "newer_source_search", "notes"}
SEARCH = {"performed_on", "entry_points", "result", "notes"}
CLAIM = {"claim_id", "source_checks", "authority_fit", "support_fit", "notes"}
CHECK = {"source_id", "evidence_location", "locator_status"}
ACCESS = {"opened": "reviewed", "conflicted": "reviewed", "abstract-only": "not-reviewed", "unavailable": "unavailable", "not-attempted": "not-reviewed"}


def _bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def audit_ledger_sha256(ledger: dict) -> str:
    """Hash a caller-validated ledger, preserving text and array order."""
    return hashlib.sha256(_bytes(ledger)).hexdigest()


def _require(condition: bool) -> None:
    if not condition:
        raise ValueError("invalid evidence audit input")


def _keys(value: object, expected: set[str]) -> None:
    _require(type(value) is dict and set(value) == expected)


def _text(value: object, limit: int = 4000) -> bool:
    return type(value) is str and bool(value.strip()) and len(value) <= limit


def _id(value: object) -> bool:
    return _text(value, 80) and ID_PATTERN.fullmatch(value) is not None


def _enum(value: object, choices: object) -> bool:
    return type(value) is str and value in choices


def _date(value: object) -> date:
    _require(type(value) is str and len(value) == 10)
    parsed = date.fromisoformat(value)
    _require(parsed.isoformat() == value)
    return parsed


def _url(value: object) -> bool:
    if value is None:
        return True
    if not _text(value, 2048) or any(ord(c) < 33 or ord(c) == 127 for c in value) or "\\" in value:
        return False
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.username is not None or parsed.password is not None
                or "?" in value or "#" in value or parsed.port == 0):
            return False
        host = host.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost") or "." not in host:
            return False
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            pass
        labels = host.encode("idna").decode("ascii").split(".")
        return all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in labels)
    except (ValueError, UnicodeError):
        return False


def _rows(value: object, identity: str, expected: set[str]) -> dict[str, dict]:
    _require(type(value) is list and len(value) <= 100)
    rows: dict[str, dict] = {}
    for row in value:
        _keys(row, expected)
        record_id = row[identity]
        _require(_id(record_id) and record_id not in rows)
        rows[record_id] = row
    return rows


def validate_evidence_audit(ledger: object, audit: object, *, as_of: str) -> list[str]:
    """Return only closed diagnostics. Never echo legacy validator diagnostics."""
    try:
        for payload in (ledger, audit):
            parse_strict_json(_bytes(payload), max_bytes=MAX_BYTES, max_depth=12)
        _require(type(ledger) is dict and not validate_evidence_ledger(ledger, as_of=as_of))
        _require(_id(ledger["ledger_id"]))
        _require(all(len(ledger[field]) <= 100 for field in ("sources", "claims")))
        _require(all(_id(row["source_id"]) for row in ledger["sources"]))
        _require(all(_id(row["claim_id"]) and all(_id(i) for i in row["source_ids"]) for row in ledger["claims"]))
        _keys(audit, TOP)
        _require(audit["schema_version"] == "1" and _id(audit["ledger_id"]) and audit["ledger_id"] == ledger["ledger_id"])
        _require(type(audit["ledger_sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", audit["ledger_sha256"]) is not None)
        if audit["ledger_sha256"] != audit_ledger_sha256(ledger):
            return ["ledger-hash-mismatch"]
        checked = _date(audit["checked_on"])
        _require(_date(ledger["prepared_on"]) <= checked <= _date(as_of))
        sources = _rows(audit["sources"], "source_id", SOURCE)
        claims = _rows(audit["claims"], "claim_id", CLAIM)
        originals = {row["source_id"]: row for row in ledger["sources"]}
        original_claims = {row["claim_id"]: row for row in ledger["claims"]}
        _require(set(sources) == set(originals) and set(claims) == set(original_claims))
        for source_id, row in sources.items():
            _require(_url(row["retrieval_url"]) and _url(row["status_basis_url"]) and _text(row["notes"]))
            _require(_enum(row["access_status"], ACCESS) and ACCESS[row["access_status"]] == originals[source_id]["review_status"])
            _require(_enum(row["authority_role"], {"governing", "official-product", "peer-reviewed-method", "implementation", "discovery-only"}))
            _require(_enum(row["use_scope"], {"current", "historical", "development", "not-assessed"}))
            _require(_enum(row["version_status"], {"current", "superseded", "in-development", "unknown"}))
            for field in ("publication_date", "reviewed_on"):
                if originals[source_id][field] is not None:
                    _require(_date(originals[source_id][field]) <= checked)
            search = row["newer_source_search"]
            _keys(search, SEARCH)
            _require(_text(search["notes"]) and _enum(search["result"], {"no-newer-found", "newer-found", "unavailable", "not-performed", "not-applicable"}))
            entries = search["entry_points"]
            _require(type(entries) is list and len(entries) <= 20 and all(type(u) is str and _url(u) for u in entries))
            _require(len(entries) == len(set(entries)))
            if search["result"] in {"not-performed", "not-applicable"}:
                _require(search["performed_on"] is None and not entries)
            else:
                _require(bool(entries) and _date(search["performed_on"]) <= checked)
            _require(not (row["use_scope"] == "current" and search["result"] == "not-applicable"))
        for claim_id, row in claims.items():
            _require(_text(row["notes"]))
            _require(_enum(row["authority_fit"], {"appropriate", "insufficient", "conflicted", "not-assessed", "not-applicable"}))
            _require(_enum(row["support_fit"], {"appropriate", "overstated", "understated", "not-assessed", "not-applicable"}))
            original = original_claims[claim_id]
            if "not-applicable" in (row["authority_fit"], row["support_fit"]):
                _require(original["claim_type"] == "request-provided" and not original["source_ids"])
            checks = _rows(row["source_checks"], "source_id", CHECK)
            _require(set(checks) == set(original["source_ids"]))
            for source_id, check in checks.items():
                _require(_enum(check["locator_status"], {"verified", "not-verified", "unavailable"}))
                _require(check["evidence_location"] is None or _text(check["evidence_location"]))
                if check["locator_status"] == "verified":
                    _require(_text(check["evidence_location"]) and sources[source_id]["access_status"] in {"opened", "conflicted"})
        return []
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        return ["invalid-input"]


def summarize_evidence_audit(ledger: dict, audit: dict, *, as_of: str) -> dict:
    """Union legacy gaps and recorded audit gaps without interpreting human notes."""
    if validate_evidence_audit(ledger, audit, as_of=as_of):
        raise ValueError("invalid evidence audit input")
    legacy = summarize_evidence_ledger(ledger, as_of=as_of)
    source_items: dict[str, set[str]] = {}
    claim_items: dict[str, set[str]] = {}

    def add(items: dict, identity: str, reason: str) -> None:
        items.setdefault(identity, set()).add(reason)

    for key, reason in (("review_due_source_ids", "ledger-review-due"), ("unknown_freshness_source_ids", "ledger-freshness-unknown"), ("unreviewed_source_ids", "ledger-source-not-reviewed"), ("unavailable_source_ids", "ledger-source-unavailable"), ("unidentified_source_ids", "ledger-source-unidentified")):
        for identity in legacy[key]:
            add(source_items, identity, reason)
    for key, reason in (("partial_support_claim_ids", "ledger-partial-support"), ("unsupported_claim_ids", "ledger-unsupported"), ("not_assessed_claim_ids", "ledger-not-assessed")):
        for identity in legacy[key]:
            add(claim_items, identity, reason)
    for row in audit["sources"]:
        identity = row["source_id"]
        conditions = [(row["access_status"] != "opened", "source-not-opened"), (row["use_scope"] == "not-assessed", "scope-not-assessed"), (row["version_status"] == "unknown", "version-unknown"), (row["status_basis_url"] is None, "status-basis-missing")]
        search = row["newer_source_search"]["result"]
        conditions += [(search == "unavailable", "newer-search-unavailable"), (search == "not-performed", "newer-search-not-performed")]
        if row["use_scope"] == "current":
            conditions += [(row["version_status"] == "superseded", "current-source-superseded"), (row["version_status"] == "in-development", "current-source-in-development"), (search == "newer-found", "current-newer-found")]
        for applies, reason in conditions:
            if applies:
                add(source_items, identity, reason)
    for row in audit["claims"]:
        identity = row["claim_id"]
        if any(check["locator_status"] != "verified" for check in row["source_checks"]):
            add(claim_items, identity, "locator-not-verified")
        for field, prefix in (("authority_fit", "authority"), ("support_fit", "support")):
            if row[field] not in {"appropriate", "not-applicable"}:
                add(claim_items, identity, f"{prefix}-{row[field]}")
    return {"schema_version": "1", "ledger_id": ledger["ledger_id"], "as_of": as_of,
            "status": "needs-review" if source_items or claim_items else "recorded-checks-complete",
            "ledger_status": legacy["status"], "source_count": len(ledger["sources"]), "claim_count": len(ledger["claims"]),
            "source_review_items": [{"source_id": i, "reasons": sorted(source_items[i])} for i in sorted(source_items)],
            "claim_review_items": [{"claim_id": i, "reasons": sorted(claim_items[i])} for i in sorted(claim_items)]}
