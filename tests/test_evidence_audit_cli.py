"""Synthetic external inputs, safe diagnostics and identical offline CLI entrypoints."""
import importlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import pytest
from test_evidence_audit import complete_pair, rebind, AS_OF, ROOT

CLIS = [ROOT / "scripts/check_evidence_audit.py", ROOT / "skills/clin-nav/scripts/check_evidence_audit.py"]
ERROR = "evidence audit validation failed\n"


def inputs(tmp_path):
    ledger, audit = complete_pair()
    ledger["claims"][0]["claim"] += " SYNTH_SECRET"
    audit["claims"][0]["notes"] = "SYNTH_SECRET"
    rebind(ledger, audit)
    paths = [tmp_path / "ledger.json", tmp_path / "audit.json"]
    for path, value in zip(paths, (ledger, audit)):
        path.write_text(json.dumps(value), encoding="utf-8")
    return paths


def run(cli, paths, extra=()):
    return subprocess.run([sys.executable, str(cli), "--ledger", str(paths[0]), "--audit", str(paths[1]), "--as-of", AS_OF, *extra], capture_output=True, text=True, check=False)


@pytest.mark.parametrize("state", ["complete", "review", "invalid"])
def test_repository_and_packaged_cli_have_same_summary_and_exit(tmp_path, state):
    paths = inputs(tmp_path)
    audit = json.loads(paths[1].read_text(encoding="utf-8"))
    if state == "review":
        audit["claims"][0]["support_fit"] = "overstated"
    elif state == "invalid":
        audit["SYNTH_SECRET"] = True
    paths[1].write_text(json.dumps(audit), encoding="utf-8")
    results = [run(cli, paths) for cli in CLIS]
    expected = {"complete": 0, "review": 3, "invalid": 2}[state]
    assert [(r.returncode, r.stdout, r.stderr) for r in results] == [(expected, results[0].stdout, results[0].stderr)] * 2
    assert results[0].stderr == (ERROR if expected == 2 else "")
    assert "SYNTH_SECRET" not in results[0].stdout + results[0].stderr
    assert all(str(p) not in results[0].stdout + results[0].stderr for p in paths)


@pytest.mark.parametrize("cli", CLIS)
@pytest.mark.parametrize("args", [["--unknown", "SYNTH_SECRET"], ["--led", "SYNTH_SECRET"], []])
def test_invalid_arguments_are_fixed_and_content_free(cli, args):
    result = subprocess.run([sys.executable, str(cli), *args], capture_output=True, text=True)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


@pytest.mark.parametrize("slot", [0, 1])
@pytest.mark.parametrize("cli", CLIS)
def test_cli_rejects_repository_input(tmp_path, slot, cli):
    paths = inputs(tmp_path)
    paths[slot] = ROOT / "skills/clin-nav/references/evidence-ledger-example.json"
    result = run(cli, paths)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


@pytest.mark.parametrize("slot", [0, 1])
def test_installed_cli_rejects_its_own_skill_inputs(tmp_path, slot):
    skill = tmp_path / "installed"
    shutil.copytree(ROOT / "skills/clin-nav", skill)
    paths = inputs(tmp_path)
    internal = skill / "references/input.json"
    shutil.copyfile(paths[slot], internal)
    paths[slot] = internal
    result = run(skill / "scripts/check_evidence_audit.py", paths)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


def test_resolved_link_to_protected_file_is_rejected(tmp_path):
    paths = inputs(tmp_path)
    link = tmp_path / "link.json"
    try:
        link.symlink_to(ROOT / "skills/clin-nav/references/evidence-ledger-example.json")
    except OSError:
        pytest.skip("file symlink unavailable")
    paths[0] = link
    result = run(CLIS[0], paths)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


@pytest.mark.parametrize("raw", ['{"duplicate":1,"duplicate":2}', 'NaN', '{"secret":"SYNTH_SECRET"', '[' * 13 + '0' + ']' * 13, ' ' * 262145], ids=["duplicate", "nonfinite", "truncated", "depth", "size"])
def test_cli_uses_strict_bounded_input(tmp_path, raw):
    paths = inputs(tmp_path)
    paths[1].write_text(raw, encoding="utf-8")
    result = run(CLIS[0], paths)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


def test_cli_rejects_directory_input(tmp_path):
    paths = inputs(tmp_path)
    paths[0] = tmp_path
    result = run(CLIS[0], paths)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


def test_cli_never_opens_network(tmp_path, monkeypatch, capsys):
    assert CLIS[1].is_file(), "packaged audit CLI is absent"
    module = importlib.import_module("check_evidence_audit")
    def forbidden(*args, **kwargs):
        raise AssertionError("network attempted")
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    paths = inputs(tmp_path)
    assert module.main(["--ledger", str(paths[0]), "--audit", str(paths[1]), "--as-of", AS_OF]) == 0
    out = capsys.readouterr()
    assert "SYNTH_SECRET" not in out.out and out.err == ""
