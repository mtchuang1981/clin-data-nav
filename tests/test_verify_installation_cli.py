"""Fixed safe CLI output, no network/host actions and synthetic-only fixtures."""
import hashlib
import importlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import pytest
from test_verify_installation import make_installed_package, snapshot, rewrite

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/verify_installation.py"
ERROR = "installation verification failed\n"


def args(fixture):
    root, manifest, digest = fixture
    return ["--skill-dir", str(root), "--manifest", str(manifest), "--manifest-sha256", digest]


@pytest.mark.parametrize("state", ["complete", "review", "invalid"])
def test_cli_exit_status_is_zero_three_or_two(tmp_path, state):
    fixture = make_installed_package(tmp_path)
    if state == "review": (fixture[0] / "extra.txt").write_text("SYNTH_SECRET")
    if state == "invalid":
        digest = rewrite(fixture[1], lambda p: p.update(SYNTH_SECRET="private sentinel"))
        fixture = fixture[0], fixture[1], digest
    result = subprocess.run([sys.executable, str(CLI), *args(fixture)], capture_output=True, text=True)
    assert result.returncode == {"complete": 0, "review": 3, "invalid": 2}[state]
    assert result.stderr == (ERROR if state == "invalid" else "")
    if state == "invalid": assert result.stdout == ""
    else: assert json.loads(result.stdout)["loaded_version"] == "not-verified"
    assert "SYNTH_SECRET" not in result.stdout + result.stderr
    assert all(str(p) not in result.stdout + result.stderr for p in fixture[:2])


@pytest.mark.parametrize("arguments", [["--unknown", "SYNTH_SECRET"], ["--skill", "SYNTH_SECRET"], [], ["--comparison", "SYNTH_SECRET"]])
def test_invalid_arguments_are_fixed_and_do_not_echo(arguments):
    result = subprocess.run([sys.executable, str(CLI), *arguments], capture_output=True, text=True)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


def test_unreadable_manifest_has_fixed_error(tmp_path):
    fixture = make_installed_package(tmp_path)
    result = subprocess.run([sys.executable, str(CLI), *args((fixture[0], tmp_path / "SYNTH_SECRET-missing.json", fixture[2]))], capture_output=True, text=True)
    assert (result.returncode, result.stdout, result.stderr) == (2, "", ERROR)


def test_cli_is_read_only_and_never_calls_network_or_host(tmp_path, monkeypatch, capsys):
    module = importlib.import_module("scripts.verify_installation")
    fixture = make_installed_package(tmp_path)
    before = snapshot(tmp_path)
    def forbidden(*args, **kwargs): raise AssertionError("external action attempted")
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert module.main(args(fixture)) == 0
    assert snapshot(tmp_path) == before
    out = capsys.readouterr()
    assert out.err == "" and json.loads(out.out)["status"] == "manifest-files-byte-identical"


def test_canonical_cli_result_is_explicit(tmp_path):
    fixture = make_installed_package(tmp_path)
    member = fixture[0] / "SKILL.md"
    member.write_bytes(member.read_bytes().replace(b"\n", b"\r\n"))
    result = subprocess.run([sys.executable, str(CLI), *args(fixture), "--comparison", "canonical-text"], capture_output=True, text=True)
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout)["status"] == "manifest-files-canonical-content-matches"


def test_help_is_static_without_local_paths():
    result = subprocess.run([sys.executable, str(CLI), "--help"], capture_output=True, text=True)
    assert result.returncode == 0 and result.stderr == ""
    assert "usage: verify_installation" in result.stdout and str(ROOT) not in result.stdout
