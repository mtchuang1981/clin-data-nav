"""Final extracted-development-package parity; no historical pilot rerun."""
import json
import subprocess
import sys
from zipfile import ZipFile
import pytest
from scripts.package_skill import build_package
from test_evidence_audit import complete_pair, ROOT, AS_OF


@pytest.mark.parametrize("state", ["complete", "review", "invalid"])
def test_repository_and_extracted_zip_audit_parity(tmp_path, state):
    package = build_package(ROOT / "skills/clin-nav", tmp_path / "package")
    extracted = tmp_path / "extracted"
    with ZipFile(package.archive) as archive:
        archive.extractall(extracted)
    ledger, audit = complete_pair()
    if state == "review": audit["claims"][0]["support_fit"] = "overstated"
    if state == "invalid": audit["SYNTH_SECRET"] = True
    paths = tmp_path / "ledger.json", tmp_path / "audit.json"
    for path, value in zip(paths, (ledger, audit)):
        path.write_text(json.dumps(value), encoding="utf-8")
    results = []
    for cli in (ROOT / "scripts/check_evidence_audit.py", extracted / "scripts/check_evidence_audit.py"):
        result = subprocess.run([sys.executable, str(cli), "--ledger", str(paths[0]), "--audit", str(paths[1]), "--as-of", AS_OF], capture_output=True, text=True)
        results.append((result.returncode, result.stdout, result.stderr))
    assert results[0] == results[1]
    assert results[0][0] == {"complete": 0, "review": 3, "invalid": 2}[state]
