"""Optional route and packaged synthetic example, not a new source-verification pilot."""
import hashlib
import json
from zipfile import ZipFile
from test_evidence_audit import ROOT
from evidence_audit import audit_ledger_sha256, validate_evidence_audit
from scripts.package_skill import build_package


def test_audit_reference_example_is_synthetic_valid_and_packaged(tmp_path):
    refs = ROOT / "skills/clin-nav/references"
    ledger = json.loads((refs / "evidence-ledger-example.json").read_text(encoding="utf-8"))
    audit = json.loads((refs / "evidence-audit-example.json").read_text(encoding="utf-8"))
    assert audit["ledger_sha256"] == audit_ledger_sha256(ledger)
    assert validate_evidence_audit(ledger, audit, as_of=audit["checked_on"]) == []
    assert "synthetic" in audit["sources"][0]["notes"].lower()
    package = build_package(ROOT / "skills/clin-nav", tmp_path / "package")
    with ZipFile(package.archive) as archive:
        assert {"scripts/evidence_audit.py", "scripts/check_evidence_audit.py", "scripts/bounded_json.py", "references/evidence-audit.md", "references/evidence-audit-example.json"} <= set(archive.namelist())


def test_optional_route_preserves_old_ledger_and_quick_contract():
    skill = (ROOT / "skills/clin-nav/SKILL.md").read_text(encoding="utf-8")
    assert "references/evidence-audit.md" in skill
    assert "only when the user requests source-freshness or citation review" in skill
    quick = (ROOT / "skills/clin-nav/references/evidence-output-template.md").read_text(encoding="utf-8").split("## Quick Explanation")[1].split("## Evidence Navigation")[0]
    assert "audit" not in quick
    raw = (ROOT / "skills/clin-nav/references/evidence-ledger-example.json").read_text(encoding="utf-8")
    canonical = json.dumps(json.loads(raw), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == "bca235e82887a5f5783e2161d5f88466b0d16bc0a1fd252601b4a744c6308d08"
    for name in ("evidence-ledger.md", "evidence-output-template.md"):
        assert "evidence-audit.md" in (ROOT / "skills/clin-nav/references" / name).read_text(encoding="utf-8")


def test_audit_reference_states_manual_limits_and_closed_contract():
    text = (ROOT / "skills/clin-nav/references/evidence-audit.md").read_text(encoding="utf-8")
    for phrase in ("262,144", "100", "20", "80", "2,048", "4,000", "12", "prepared_on <= checked_on <= --as-of", "not truth", "pilot-failed", "closed", "not-performed", "source_checks", "entry_points", "recorded-checks-complete"):
        assert phrase in text
