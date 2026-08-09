import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

import scripts.commit_human_task_pack as commitment_module
from scripts.commit_human_task_pack import (
    SCHEME,
    _commitment_digest,
    build_commitment,
    canonical_task_pack_bytes,
    verify_commitment,
)
from scripts.effectiveness_contract import load_effectiveness_contract


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals/effectiveness/offline-tasks.yaml"
RUBRIC = ROOT / "evals/effectiveness/rubric.yaml"
EXAMPLE = ROOT / "evals/effectiveness/examples/human-task-commitment.example.json"
CLI_ERROR = "human task commitment operation failed\n"


def test_lf_and_crlf_task_packs_have_the_same_commitment(tmp_path):
    lf = tmp_path / "lf.yaml"
    crlf = tmp_path / "crlf.yaml"
    payload = "schema_version: '1'\ntask_pairs: []\n"
    lf.write_bytes(payload.encode("utf-8"))
    crlf.write_bytes(payload.replace("\n", "\r\n").encode("utf-8"))
    nonce = bytes.fromhex("00" * 32)

    assert build_commitment(
        canonical_task_pack_bytes(lf), nonce, {"task_pairs": []}
    )["commitment_sha256"] == build_commitment(
        canonical_task_pack_bytes(crlf), nonce, {"task_pairs": []}
    )["commitment_sha256"]


def test_commitment_contains_metadata_but_not_nonce_or_prompt_text():
    canonical = b"schema_version: '1'\ntask_pairs: []\n"
    nonce = bytes.fromhex("ab" * 32)
    commitment = build_commitment(canonical, nonce, {"task_pairs": []})
    serialized = json.dumps(commitment, sort_keys=True)

    assert nonce.hex() not in serialized
    assert "prompt" not in serialized
    assert commitment["scheme"] == "sha256-nonce-task-pack-v1"
    assert commitment["canonical_task_bytes"] == len(canonical)
    assert set(commitment) == {
        "schema_version",
        "scheme",
        "commitment_sha256",
        "canonical_task_bytes",
        "pair_count",
        "depth_counts",
        "pair_ids",
    }


def test_verify_rejects_changed_task_pack_and_changed_nonce(tmp_path):
    task_pack = tmp_path / "human-tasks.yaml"
    original = b"schema_version: '1'\ntask_pairs: []\n"
    nonce = bytes.fromhex("12" * 32)
    task_pack.write_bytes(original)
    commitment = build_commitment(
        canonical_task_pack_bytes(task_pack), nonce, {"task_pairs": []}
    )

    task_pack.write_bytes(original + b"# changed\n")
    assert verify_commitment(task_pack, nonce, commitment) == [
        "commitment_sha256 mismatch"
    ]

    task_pack.write_bytes(original)
    changed_nonce = bytes([nonce[0] ^ 1]) + nonce[1:]
    assert verify_commitment(task_pack, changed_nonce, commitment) == [
        "commitment_sha256 mismatch"
    ]


def test_create_cli_rejects_nonce_output_inside_repository(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/commit_human_task_pack.py"),
            "create",
            "--task-pack",
            str(tmp_path / "external-human-tasks.yaml"),
            "--nonce-output",
            str(ROOT / "human-task-pack.nonce"),
            "--commitment-output",
            str(tmp_path / "commitment.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR


def test_create_cli_hides_malformed_yaml_or_invalid_contract_details(tmp_path):
    marker = "CREATE-TASK-MARKER-9f32"
    task_pack = tmp_path / f"{marker}.yaml"
    nonce_output = tmp_path / f"{marker}.nonce"
    commitment_output = tmp_path / f"{marker}.json"
    for contents in (
        f"task_pairs: [\n{marker}\n",
        f'schema_version: "1"\ntask_pairs: []\n{marker}: invalid\n',
    ):
        task_pack.write_text(contents, encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/commit_human_task_pack.py"),
                "create",
                "--task-pack",
                str(task_pack),
                "--nonce-output",
                str(nonce_output),
                "--commitment-output",
                str(commitment_output),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 2
        assert result.stdout == ""
        assert result.stderr == CLI_ERROR
        assert marker not in result.stderr
        assert str(task_pack) not in result.stderr
        assert not nonce_output.exists()
        assert not commitment_output.exists()


def test_create_uses_32_byte_nonce_and_exclusive_external_creation(tmp_path, monkeypatch):
    task_pack = tmp_path / "public-synthetic-tasks.yaml"
    nonce_output = tmp_path / "public-example.nonce"
    commitment_output = tmp_path / "commitment.json"
    task_pack.write_bytes(TASKS.read_bytes())
    requested_sizes = []

    def fixed_token_bytes(size):
        requested_sizes.append(size)
        return bytes.fromhex("00" * 32)

    monkeypatch.setattr(commitment_module.secrets, "token_bytes", fixed_token_bytes)
    args = SimpleNamespace(
        task_pack=task_pack,
        rubric=RUBRIC,
        nonce_output=nonce_output,
        commitment_output=commitment_output,
    )

    commitment_module._create(args)

    assert requested_sizes == [32]
    assert nonce_output.read_bytes() == bytes.fromhex("00" * 32)
    assert json.loads(commitment_output.read_text(encoding="utf-8"))["scheme"] == SCHEME
    with pytest.raises(FileExistsError):
        commitment_module._create(args)


def test_public_example_is_exactly_recomputed_with_zero_nonce():
    catalog, _ = load_effectiveness_contract(TASKS, RUBRIC)
    expected = {
        "example_only": True,
        "commitment": build_commitment(
            canonical_task_pack_bytes(TASKS), bytes.fromhex("00" * 32), catalog
        ),
    }
    actual = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    serialized = json.dumps(actual, sort_keys=True)

    assert set(actual) == {"example_only", "commitment"}
    assert actual["example_only"] is True
    assert set(actual["commitment"]) == set(expected["commitment"])
    assert '"nonce"' not in serialized
    assert '"prompt"' not in serialized
    assert "00" * 32 not in serialized
    assert EXAMPLE.read_bytes() == (
        json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def test_verify_cli_allows_a_post_lock_task_pack_inside_repository(tmp_path):
    catalog, _ = load_effectiveness_contract(TASKS, RUBRIC)
    nonce = bytes.fromhex("00" * 32)
    nonce_path = tmp_path / "nonce.bin"
    commitment_path = tmp_path / "commitment.json"
    nonce_path.write_bytes(nonce)
    commitment_path.write_text(
        json.dumps(
            build_commitment(canonical_task_pack_bytes(TASKS), nonce, catalog),
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/commit_human_task_pack.py"),
            "verify",
            "--task-pack",
            str(TASKS),
            "--nonce-file",
            str(nonce_path),
            "--commitment",
            str(commitment_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_verify_cli_hides_task_nonce_commitment_and_path_details(tmp_path):
    marker = "VERIFY-MARKER-1d7c"
    task_pack = tmp_path / f"{marker}-task.yaml"
    nonce_path = tmp_path / f"{marker}-nonce.bin"
    commitment_path = tmp_path / f"{marker}-commitment.json"
    task_pack.write_text(f"task_pairs: [\n{marker}\n", encoding="utf-8")
    nonce_path.write_bytes(bytes.fromhex("00" * 32))
    canonical = canonical_task_pack_bytes(task_pack)
    commitment_path.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "scheme": SCHEME,
                "commitment_sha256": _commitment_digest(
                    canonical, bytes.fromhex("00" * 32)
                ),
                "canonical_task_bytes": len(canonical),
                "pair_count": 0,
                "depth_counts": {},
                "pair_ids": [],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/commit_human_task_pack.py"),
            "verify",
            "--task-pack",
            str(task_pack),
            "--nonce-file",
            str(nonce_path),
            "--commitment",
            str(commitment_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert marker not in result.stderr
    assert str(task_pack) not in result.stderr


def test_verify_cli_hides_nonce_commitment_schema_and_mismatch_details(tmp_path):
    marker = "NONCE-MARKER-6b0e"
    catalog, _ = load_effectiveness_contract(TASKS, RUBRIC)
    commitment = build_commitment(
        canonical_task_pack_bytes(TASKS), bytes.fromhex("00" * 32), catalog
    )
    nonce_path = tmp_path / f"{marker}-nonce.bin"
    commitment_path = tmp_path / f"{marker}-commitment.json"

    for nonce, commitment_contents in (
        (marker.encode("utf-8"), json.dumps(commitment)),
        (
            (marker.encode("utf-8") + b"x" * 32)[:32],
            json.dumps(commitment),
        ),
        (bytes.fromhex("00" * 32), f'{{"broken": "{marker}"'),
        (bytes.fromhex("00" * 32), json.dumps({"marker": marker})),
    ):
        nonce_path.write_bytes(nonce)
        commitment_path.write_text(commitment_contents, encoding="utf-8")

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/commit_human_task_pack.py"),
                "verify",
                "--task-pack",
                str(TASKS),
                "--nonce-file",
                str(nonce_path),
                "--commitment",
                str(commitment_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 2
        assert result.stdout == ""
        assert result.stderr == CLI_ERROR
        assert marker not in result.stderr
        assert str(nonce_path) not in result.stderr
        assert str(commitment_path) not in result.stderr
